"""
보건복지위원회 일정 자동 검색 스크립트
대상: health.na.go.kr (국회 보건복지위원회)
검색 범위: 앞으로 2주 이내 응급의료 관련 토론회·공청회·세미나·간담회
"""

import asyncio
import json
import csv
import re
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# ── 상수 ──────────────────────────────────────────────────────────────────────

BASE_URL     = "https://health.na.go.kr"
ASSEMBLY_BASE_URL = "https://www.assembly.go.kr"

EVENT_TYPES    = ["토론회", "공청회", "세미나", "간담회", "청문회", "소위원회", "전체회의", "회의"]
TOPIC_KEYWORDS = ["응급의료", "응급", "구급", "구조", "응급실", "외상", "중증", "응급처치", "응급환자"]

# assembly.go.kr 전용 필터 (보건복지위 외 전체 위원회 대상)
ASSEMBLY_EVENT_FILTER   = {"토론회", "공청회", "간담회"}
ASSEMBLY_TOPIC_KEYWORDS = ["응급의료", "응급실", "응급", "구급", "중증외상", "필수의료"]

UPCOMING_DAYS = 14   # 앞으로 N일
LOOKBACK_DAYS = 0    # 예정 일정만 수집 (과거 제외)

# 실제 회의/행사 판단 — 이 키워드가 있어야 포함
_MEETING_TYPES = {"회의", "공청회", "토론회", "간담회", "청문회", "소위원회", "전체회의", "심사"}
# 문서/게시물 제목 패턴 — 이 키워드가 있으면 무조건 제외
_DOC_EXCLUDE   = {
    "자료집", "자료실", "보도자료", "활동소식", "결과보고", "보고서",
    "게시물", "첨부", ".hwp", ".pdf", ".docx", ".xlsx", ".zip",
    "결과물", "회의록", "속기록", "참고자료", "검토보고", "심사보고",
}
# 과거 날짜를 괄호로 언급하는 제목 패턴 (예: "공청회(2026.03.10) 자료집")
_PAST_DATE_RE  = re.compile(r"\(\s*\d{4}[.\-]\d{1,2}[.\-]\d{1,2}\s*\)")

# ── 확인된 페이지 구조 ─────────────────────────────────────────────────────────
#
# [일정목록] schlList.do?menuNo=2000048
#   table[0]: 달력 (헤더=일월화수목금토, 셀에 날짜+이벤트 텍스트)
#   table[1] class=cmitSchlListTable: 번호/위원회명/제목/회기/회의일자/미리보기/다운로드 (AJAX)
#
# [자료실] cmtEstn/list.do?menuNo=2000116
#   table[0]: 번호/위원회명/게시판/제목/작성일/미리보기/다운로드
#             └→ 게시판 컬럼: '공청회/간담회/세미나', '양식/서식', '특위' 등
#
# [게시판] BCMT2076/list.do?menuNo=2000110
#   table[0]: 번호/위원회/제목/작성일/구분/미리보기/첨부파일/조회
#             └→ 구분 컬럼: '공청회' 등
#
# [활동소식] B0000051/list.do?menuNo=2000037
#   table[0]: 번호/위원회명/제목/작성일/미리보기/다운로드/조회

# ── 날짜 유틸리티 ─────────────────────────────────────────────────────────────

_DATE_RE = re.compile(r"(\d{4})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})")


def parse_date(raw: str) -> datetime | None:
    if not raw:
        return None
    m = _DATE_RE.search(raw.strip())
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _in_window(date_str: str) -> bool:
    dt = parse_date(date_str)
    if dt is None:
        return False
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return today - timedelta(days=LOOKBACK_DAYS) <= dt <= today + timedelta(days=UPCOMING_DAYS)


def _is_upcoming(date_str: str) -> bool:
    dt = parse_date(date_str)
    if dt is None:
        return False
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return today <= dt <= today + timedelta(days=UPCOMING_DAYS)


# ── 텍스트 필터 ───────────────────────────────────────────────────────────────

def _hit_event(text: str) -> bool:
    return any(ev in text for ev in EVENT_TYPES)


def _hit_topic(text: str) -> bool:
    return any(kw in text for kw in TOPIC_KEYWORDS)


def _is_junk(title: str) -> bool:
    t = title.strip()
    return (
        len(t) < 4
        or bool(re.search(r"\.(hwp|pdf|docx?|xlsx?|zip|ppt[x]?)$", t, re.I))
        or t in {"미리보기", "다운로드", "이름파일명", "첨부파일", "조회", "자료"}
    )


def _is_actual_meeting(title: str) -> bool:
    """자료집·게시물이 아닌 실제 회의/행사 제목이면 True."""
    t = title.strip()
    # 문서·보도자료·자료실 키워드가 있으면 제외
    if any(ex in t for ex in _DOC_EXCLUDE):
        return False
    # 괄호 안 과거 날짜 언급(예: "공청회(2026.03.10)") → 자료 게시물로 판단, 제외
    if _PAST_DATE_RE.search(t):
        return False
    # 회의·행사 키워드가 있어야 포함
    return any(mt in t for mt in _MEETING_TYPES)


# ── URL 헬퍼 ─────────────────────────────────────────────────────────────────

def _abs(href: str) -> str:
    href = (href or "").strip()
    if not href or "javascript" in href:
        return ""
    return href if href.startswith("http") else BASE_URL + (href if href.startswith("/") else "/" + href)


def _parse_schl_url(href: str) -> str:
    """JavaScript fnView/goView 링크에서 cmtSchSn 추출해 상세 URL 반환."""
    if not href:
        return ""
    href = href.strip()
    if "javascript" not in href.lower():
        return _abs(href)
    m = re.search(r"['\"](\d{5,})['\"]", href)
    if m:
        return (f"{BASE_URL}/cmmit/schl/cmitSchl/view.do"
                f"?menuNo=2000048&cmtSchSn={m.group(1)}")
    return ""


def _make(title: str, date_str: str, url: str, source: str,
          category: str = "") -> dict:
    return {
        "title":         title.strip(),
        "date":          date_str,
        "is_upcoming":   _is_upcoming(date_str),
        "event_type":    category or next((ev for ev in EVENT_TYPES if ev in title), "기타"),
        "topic_keyword": next((kw for kw in TOPIC_KEYWORDS if kw in title), ""),
        "url":           url,
        "source":        source,
        "collected_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ── 1. 달력 파싱 (schlList.do) ────────────────────────────────────────────────

async def _scrape_calendar(page) -> list[dict]:
    """
    일정목록 달력 파싱.
    셀 텍스트에서 날짜(숫자)와 이벤트 라벨을 추출한다.
    """
    url = f"{BASE_URL}/cmmit/schl/cmitSchl/schlList.do?menuNo=2000048"
    print(f"\n[달력/일정목록] {url}")
    items: list[dict] = []

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
    except Exception:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
        except Exception as e:
            print(f"  달력 페이지 접속 실패: {e}")
            return items

    # 달력 헤더에서 현재 연월 파악
    year = month = 0
    month_el = await page.query_selector(".cal-tit, .calendar-title, h3.tit, .sch-tit")
    if month_el:
        month_text = (await month_el.inner_text()).strip()
        m = re.search(r"(\d{4})[년.\s]+(\d{1,2})[월]?", month_text)
        if m:
            year, month = int(m.group(1)), int(m.group(2))
    if not year:
        # URL 파라미터나 현재 날짜로 추정
        now = datetime.now()
        year, month = now.year, now.month

    # 달력 테이블에서 날짜+이벤트 추출
    calendar_table = await page.query_selector("table:first-of-type")
    if not calendar_table:
        print("  달력 테이블 없음")
    else:
        tbody = await calendar_table.query_selector("tbody")
        if tbody:
            rows = await tbody.query_selector_all("tr")
            for row in rows:
                cells = await row.query_selector_all("td")
                for cell in cells:
                    text = (await cell.inner_text()).strip()
                    if not text:
                        continue
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if not lines:
                        continue
                    # 첫 줄이 날짜(숫자)인지 확인
                    if not re.match(r"^\d{1,2}$", lines[0]):
                        continue
                    day = int(lines[0])
                    try:
                        dt = datetime(year, month, day)
                    except ValueError:
                        continue
                    date_str = dt.strftime("%Y-%m-%d")

                    # a 태그 기준으로 이벤트 라벨과 상세 링크 추출
                    anchors = await cell.query_selector_all("a")
                    for a_el in anchors:
                        a_text = (await a_el.inner_text()).strip()
                        if not a_text or re.match(r"^\d{1,2}$", a_text):
                            continue
                        # 다중 줄 텍스트를 '-'로 결합 (예: "전체회의\n제1차 전체회의")
                        parts = [p.strip() for p in a_text.split("\n") if p.strip()]
                        label = "-".join(parts) if len(parts) > 1 else (parts[0] if parts else "")
                        if not label or _is_junk(label):
                            continue
                        if not _is_actual_meeting(label):
                            continue
                        if not _in_window(date_str):
                            continue
                        href = (await a_el.get_attribute("href")) or ""
                        link = _parse_schl_url(href) or url
                        items.append(_make(label, date_str, link, "달력/일정목록"))

    # cmitSchlListTable: AJAX 로딩 시도 (날짜 범위 파라미터로 재요청)
    today = datetime.now()
    from_date = today.strftime("%Y%m%d")
    to_date   = (today + timedelta(days=UPCOMING_DAYS)).strftime("%Y%m%d")
    ajax_url  = (f"{BASE_URL}/cmmit/schl/cmitSchl/schlList.do"
                 f"?menuNo=2000048&fromDate={from_date}&toDate={to_date}")
    ajax_items: list[dict] = []
    try:
        await page.goto(ajax_url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        try:
            await page.wait_for_selector("table.cmitSchlListTable", timeout=10000)
        except Exception:
            pass
        schl_table = await page.query_selector("table.cmitSchlListTable tbody")
        if schl_table:
            rows = await schl_table.query_selector_all("tr")
            print(f"  cmitSchlListTable 데이터 행: {len(rows)}")
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) < 5:
                    continue
                # 헤더: 번호/위원회명/제목/회기/회의일자
                title_col = 2; date_col = 4
                title = (await cols[title_col].inner_text()).strip()
                date_str = (await cols[date_col].inner_text()).strip()
                a = await cols[title_col].query_selector("a")
                if a:
                    href = (await a.get_attribute("href")) or ""
                    link = _parse_schl_url(href) or ajax_url
                else:
                    link = ajax_url

                if _is_junk(title) or not _in_window(date_str):
                    continue
                if not _is_actual_meeting(title):
                    continue

                # 전체 제목에 회의 유형 접두어가 없으면 자동으로 붙임
                ev_type = next((ev for ev in EVENT_TYPES if ev in title), "")
                if ev_type and not title.startswith(ev_type):
                    display_title = f"{ev_type}-{title}"
                else:
                    display_title = title

                ajax_items.append(_make(display_title, date_str, link, "일정목록"))
        else:
            print("  cmitSchlListTable 없음 (AJAX 미로드)")
    except Exception as e:
        print(f"  AJAX 시도 실패: {e}")

    # AJAX 항목이 있으면 달력 항목 중 동일 날짜+회의유형 중복 제거
    if ajax_items:
        ajax_keys = {(it["date"], it["event_type"]) for it in ajax_items}
        items = [it for it in items
                 if (it["date"], it["event_type"]) not in ajax_keys]
    items.extend(ajax_items)

    print(f"  수집: {len(items)}건 (달력 이벤트 + 일정 테이블)")
    return items


# ── 2. 자료실 파싱 (cmtEstn) ─────────────────────────────────────────────────
#   헤더: 번호/위원회명/게시판/제목/작성일/미리보기/다운로드
#   게시판 컬럼(idx=2)으로 이벤트 유형 판단

async def _scrape_estn(page) -> list[dict]:
    base_url = f"{BASE_URL}/cmmit/cmtEstn/cmtEstn/list.do?menuNo=2000116"
    print(f"\n[자료실] {base_url}")
    items: list[dict] = []

    for page_no in range(1, 6):
        url = base_url if page_no == 1 else f"{base_url}&pageIndex={page_no}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(0.8)
        except Exception as e:
            print(f"  p{page_no} 실패: {e}"); break

        table = await page.query_selector("table:first-of-type tbody")
        if not table:
            break
        rows = await table.query_selector_all("tr")
        page_items = []

        for row in rows:
            cols = await row.query_selector_all("td")
            if len(cols) < 5:
                continue
            # idx: 0=번호 1=위원회명 2=게시판 3=제목 4=작성일
            category  = (await cols[2].inner_text()).strip()  # 게시판
            title_col = cols[3]
            date_str  = (await cols[4].inner_text()).strip()

            # 이벤트 유형 필터 (게시판 컬럼 기준)
            if not _hit_event(category):
                continue

            a = await title_col.query_selector("a")
            title = (await a.inner_text()).strip() if a else (await title_col.inner_text()).strip()
            link  = _abs((await a.get_attribute("href")) or "") if a else url

            if _is_junk(title) or not _in_window(date_str):
                continue

            # 응급의료 키워드 체크 (없어도 일단 포함 – 별도 필드로 표기)
            page_items.append(_make(title, date_str, link, "자료실", category))

        items.extend(page_items)
        if not page_items:
            break  # 더 이상 데이터 없음

    print(f"  수집: {len(items)}건")
    return items


# ── 3. 게시판 파싱 (BCMT2076) ─────────────────────────────────────────────────
#   헤더: 번호/위원회/제목/작성일/구분/미리보기/첨부파일/조회
#   구분 컬럼(idx=4)으로 이벤트 유형 판단

async def _scrape_board(page) -> list[dict]:
    base_url = f"{BASE_URL}/cmmit/bbs/BCMT2076/list.do?menuNo=2000110"
    print(f"\n[게시판] {base_url}")
    items: list[dict] = []

    for page_no in range(1, 6):
        url = base_url if page_no == 1 else f"{base_url}&pageIndex={page_no}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(0.8)
        except Exception as e:
            print(f"  p{page_no} 실패: {e}"); break

        table = await page.query_selector("table:first-of-type tbody")
        if not table:
            break
        rows = await table.query_selector_all("tr")
        page_items = []

        for row in rows:
            cols = await row.query_selector_all("td")
            if len(cols) < 5:
                continue
            # idx: 0=번호 1=위원회 2=제목 3=작성일 4=구분
            title_col = cols[2]
            date_str  = (await cols[3].inner_text()).strip()
            category  = (await cols[4].inner_text()).strip()  # 구분

            if not _hit_event(category) and not _hit_event(
                    (await title_col.inner_text()).strip()):
                continue

            a = await title_col.query_selector("a")
            title = (await a.inner_text()).strip() if a else (await title_col.inner_text()).strip()
            link  = _abs((await a.get_attribute("href")) or "") if a else url

            if _is_junk(title) or not _in_window(date_str):
                continue
            if not _is_actual_meeting(title):
                continue

            page_items.append(_make(title, date_str, link, "게시판", category))

        items.extend(page_items)
        if not page_items:
            break

    print(f"  수집: {len(items)}건")
    return items


# ── 4. 활동소식 파싱 (B0000051) ───────────────────────────────────────────────
#   헤더: 번호/위원회명/제목/작성일/미리보기/다운로드/조회
#   제목에서 이벤트 유형 탐지

async def _scrape_activity(page) -> list[dict]:
    base_url = f"{BASE_URL}/cmmit/bbs/B0000051/list.do?menuNo=2000037"
    print(f"\n[활동소식] {base_url}")
    items: list[dict] = []

    for page_no in range(1, 4):
        url = base_url if page_no == 1 else f"{base_url}&pageIndex={page_no}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(0.8)
        except Exception as e:
            print(f"  p{page_no} 실패: {e}"); break

        table = await page.query_selector("table:first-of-type tbody")
        if not table:
            break
        rows = await table.query_selector_all("tr")
        page_items = []

        for row in rows:
            cols = await row.query_selector_all("td")
            if len(cols) < 4:
                continue
            # idx: 0=번호 1=위원회명 2=제목 3=작성일
            title_col = cols[2]
            date_str  = (await cols[3].inner_text()).strip()

            a = await title_col.query_selector("a")
            title = (await a.inner_text()).strip() if a else (await title_col.inner_text()).strip()
            link  = _abs((await a.get_attribute("href")) or "") if a else url

            if _is_junk(title) or not _in_window(date_str):
                continue
            if not (_hit_event(title) or _hit_topic(title)):
                continue

            page_items.append(_make(title, date_str, link, "활동소식"))

        items.extend(page_items)
        if not page_items:
            break

    print(f"  수집: {len(items)}건")
    return items


# ── 5. 국회도서관 세미나 일정 (ampos.nanet.go.kr) ────────────────────────────────

NANET_BASE = "https://ampos.nanet.go.kr:7443"
# nanet 필터: 이벤트 유형 AND 키워드 모두 포함해야 통과
_NANET_EVENT_FILTER   = {"토론회", "공청회", "간담회", "세미나", "포럼", "심포지엄"}
_NANET_TOPIC_KEYWORDS = [
    "응급의료", "응급실", "응급", "구급", "중증외상", "필수의료",
    "중증응급", "응급환자", "의료격차", "취약지역",
]


_NANET_ROW_JS = """
    () => {
        // 검색 전=tables[1], 검색 후=tables[0] 가능 → 날짜 포함 행이 있는 테이블 탐색
        let tbl = null;
        for (const t of document.querySelectorAll('table')) {
            const firstTd = t.querySelector('tbody tr td');
            if (firstTd && /\\d{4}년/.test(firstTd.innerText || '')) {
                tbl = t; break;
            }
        }
        if (!tbl) return [];
        const out = [];
        tbl.querySelectorAll('tbody tr').forEach(tr => {
            const tds = tr.querySelectorAll('td');
            if (tds.length < 2) return;
            const dateRaw = (tds[0].innerText || '').trim();
            if (!/\\d{4}년/.test(dateRaw)) return;
            const forms = tds[1].querySelectorAll('.dayForm, .defaultLi');
            if (forms.length === 0) {
                const p = tds[1].querySelector('.right p, p');
                const title = p ? p.innerText.trim() : (tds[1].innerText || '').split('\\n')[0].trim();
                if (title) out.push({ dateRaw, title });
            } else {
                forms.forEach(f => {
                    const p = f.querySelector('.right p, p');
                    const title = p ? p.innerText.trim() : '';
                    if (title) out.push({ dateRaw, title });
                });
            }
        });
        return out;
    }
"""


async def _nanet_search_keyword(page, keyword: str, from_str: str, end_str: str) -> list[dict]:
    """nanet에서 키워드 검색 후 결과 반환 (페이지네이션 포함)."""
    items: list[dict] = []
    # 날짜 입력 및 키워드 검색 실행
    try:
        await page.evaluate(f"""
            () => {{
                document.getElementById('fromDate').value = '{from_str}';
                document.getElementById('endDate').value = '{end_str}';
                const qt = document.getElementById('queryText');
                if (qt) qt.value = '{keyword}';
                const st = document.getElementById('searchType');
                if (st) st.value = 'title';
            }}
        """)
        await page.click(".btn_green.btn_search, button.btn_search, button[class*='btn_search']")
        await asyncio.sleep(2)
    except Exception as e:
        print(f"    검색 실패 ({keyword}): {e}")
        return items

    for page_no in range(1, 10):
        rows = await page.evaluate(_NANET_ROW_JS)
        if not rows:
            break

        page_items = []
        for r in rows:
            date_raw = r.get("dateRaw", "")
            title    = r.get("title", "").strip()
            if not title or not date_raw:
                continue
            dt = parse_date(date_raw)
            if dt is None or not _is_upcoming(dt.strftime("%Y-%m-%d")):
                continue
            if not any(ev in title for ev in _NANET_EVENT_FILTER):
                continue
            date_str = dt.strftime("%Y-%m-%d")
            list_url = (
                f"{NANET_BASE}/seminarList.do"
                f"#fromDate={dt.strftime('%Y%m%d')}&endDate={dt.strftime('%Y%m%d')}&searchGubun=search"
            )
            page_items.append(_make(title, date_str, list_url, "국회도서관/세미나"))

        items.extend(page_items)

        # 다음 페이지 링크 확인
        next_no = page_no + 1
        has_next = await page.evaluate(
            f"() => Array.from(document.querySelectorAll('a')).some("
            f"  a => (a.getAttribute('href') || '').includes(\"schelist('{next_no}')\")"
            f")"
        )
        if not has_next:
            break
        try:
            await page.evaluate(f"schelist('{next_no}')")
            await asyncio.sleep(2)
        except Exception:
            break

    return items


async def _scrape_nanet_seminar(page) -> list[dict]:
    """국회도서관 세미나 목록 (ampos.nanet.go.kr) 스크래핑 — 키워드별 검색."""
    today    = datetime.now()
    end      = today + timedelta(days=UPCOMING_DAYS)
    from_str = today.strftime("%Y-%m-%d")
    end_str  = end.strftime("%Y-%m-%d")
    entry    = f"{NANET_BASE}/seminarList.do"

    print(f"\n[국회도서관/세미나] {entry} ({from_str} ~ {end_str})")
    all_items: list[dict] = []

    # 최초 접속
    try:
        await page.goto(entry, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
    except Exception as e:
        print(f"  접속 실패: {e}")
        return all_items

    # 키워드별 검색
    seen: set[tuple] = set()
    for kw in _NANET_TOPIC_KEYWORDS:
        results = await _nanet_search_keyword(page, kw, from_str, end_str)
        new_cnt = 0
        for item in results:
            key = (item["title"], item["date"])
            if key not in seen:
                seen.add(key)
                all_items.append(item)
                new_cnt += 1
        if new_cnt:
            print(f"  [{kw}] {new_cnt}건 수집")

    print(f"  수집: {len(all_items)}건")
    return all_items


# ── 6. 국회 OpenAPI ───────────────────────────────────────────────────────────

async def _fetch_open_api(page) -> list[dict]:
    today = datetime.now()
    start = (today - timedelta(days=LOOKBACK_DAYS)).strftime("%Y%m%d")
    end   = (today + timedelta(days=UPCOMING_DAYS)).strftime("%Y%m%d")
    url   = (
        "https://open.assembly.go.kr/portal/openapi/nactivityschedulelist"
        f"?Key=98e6b5a04fc54812aa78184f09d4b2ac&Type=json&pIndex=1&pSize=100"
        f"&FROM_DATE={start}&TO_DATE={end}"
    )
    print(f"\n[OpenAPI] {url}")
    results: list[dict] = []

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        body = await page.inner_text("body")
        data = json.loads(body)

        rows: list = []
        for section in (data if isinstance(data, list) else data.values()):
            if isinstance(section, dict) and "row" in section:
                rows = section["row"]; break
            if isinstance(section, list):
                for item in section:
                    if isinstance(item, dict) and "row" in item:
                        rows = item["row"]; break

        print(f"  응답: {len(rows)}행")
        for row in rows:
            title    = (row.get("TITLE") or row.get("ACTVT_NM") or "").strip()
            date_str = (row.get("ACT_DT") or row.get("DT") or "").strip()
            cmit     = (row.get("CMIT_NM") or "").strip()

            if "보건복지" not in cmit and "보건" not in title:
                continue
            if not (_hit_event(title) or _hit_topic(title)):
                continue
            if not _in_window(date_str):
                continue

            results.append(_make(title, date_str, row.get("URL") or "",
                                 f"OpenAPI/{cmit}"))
        print(f"  필터 통과: {len(results)}건")
    except json.JSONDecodeError:
        print("  JSON 파싱 실패")
    except Exception as e:
        print(f"  오류: {e}")

    return results


# ── 6. 국회 공식 OpenAPI (전체 위원회 일정) ──────────────────────────────────────

async def _scrape_assembly_gov(page) -> list[dict]:
    today = datetime.now()
    start = today.strftime("%Y%m%d")
    end   = (today + timedelta(days=UPCOMING_DAYS)).strftime("%Y%m%d")
    results: list[dict] = []

    api_url = (
        "https://open.assembly.go.kr/portal/openapi/nactivityschedulelist"
        f"?Key=98e6b5a04fc54812aa78184f09d4b2ac&Type=json&pIndex=1&pSize=200"
        f"&FROM_DATE={start}&TO_DATE={end}"
    )
    print(f"\n[국회공식/OpenAPI] {api_url}")
    try:
        await page.goto(api_url, wait_until="domcontentloaded", timeout=20000)
        body = await page.inner_text("body")
        data = json.loads(body)

        rows: list = []
        for section in (data if isinstance(data, list) else data.values()):
            if isinstance(section, dict) and "row" in section:
                rows = section["row"]; break
            if isinstance(section, list):
                for item in section:
                    if isinstance(item, dict) and "row" in item:
                        rows = item["row"]; break

        print(f"  응답: {len(rows)}행")
        for row in rows:
            title    = (row.get("TITLE") or row.get("ACTVT_NM") or "").strip()
            date_str = (row.get("ACT_DT") or row.get("DT") or "").strip()
            cmit     = (row.get("CMIT_NM") or "").strip()

            if not any(ev in title for ev in ASSEMBLY_EVENT_FILTER):
                continue
            if not any(kw in title for kw in ASSEMBLY_TOPIC_KEYWORDS):
                continue
            if _is_junk(title) or not _in_window(date_str):
                continue

            results.append(_make(title, date_str, row.get("URL") or "",
                                 f"국회공식/{cmit or '전체위원회'}"))
        print(f"  필터 통과: {len(results)}건")
    except json.JSONDecodeError:
        print("  JSON 파싱 실패")
    except Exception as e:
        print(f"  OpenAPI 오류: {e}")

    return results


# ── 저장 & 출력 ───────────────────────────────────────────────────────────────

def _dedup(results: list[dict]) -> list[dict]:
    seen, out = set(), []
    for r in results:
        key = (r["title"].strip(), r["date"])
        if key not in seen:
            seen.add(key); out.append(r)
    return out


def save_results(results: list[dict], timestamp: str) -> tuple[str, str]:
    json_path = f"schedule_results_{timestamp}.json"
    csv_path  = f"schedule_results_{timestamp}.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[저장] JSON : {json_path}")

    if results:
        fields = ["title", "date", "is_upcoming", "event_type", "topic_keyword",
                  "url", "source", "collected_at"]
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader(); w.writerows(results)
        print(f"[저장] CSV  : {csv_path}")

    return json_path, csv_path


# ── 메인 ──────────────────────────────────────────────────────────────────────

async def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    today     = datetime.now()
    deadline  = today + timedelta(days=UPCOMING_DAYS)

    print("=" * 60)
    print("응급의료 관련 국회 일정 검색")
    print(f"검색 기간: {(today - timedelta(days=LOOKBACK_DAYS)).strftime('%Y-%m-%d')}"
          f" ~ {deadline.strftime('%Y-%m-%d')}")
    print(f"수집 대상: 보건복지위원회(health.na.go.kr) + 국회공식(assembly.go.kr)")
    print("=" * 60)

    all_results: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        ctx_health = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
        )
        ctx_asm = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
        )

        page_health = await ctx_health.new_page()
        page_asm    = await ctx_asm.new_page()

        ctx_nanet = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
        )
        page_nanet = await ctx_nanet.new_page()

        # health.na.go.kr(순차) 와 assembly.go.kr, nanet을 병렬 실행
        async def _scrape_health(pg):
            result = []
            result.extend(await _scrape_calendar(pg))
            result.extend(await _scrape_board(pg))
            return result

        print("\n▶ 보건복지위원회 + 국회공식 + 국회도서관 세미나 병렬 수집")
        health_results, asm_results, nanet_results = await asyncio.gather(
            _scrape_health(page_health),
            _scrape_assembly_gov(page_asm),
            _scrape_nanet_seminar(page_nanet),
        )
        all_results.extend(health_results)
        all_results.extend(asm_results)
        all_results.extend(nanet_results)

        await ctx_health.close()
        await ctx_asm.close()
        await ctx_nanet.close()
        await browser.close()

    # 중복 제거 (제목+날짜 기준) 후 날짜순 정렬
    all_results = _dedup(all_results)
    all_results.sort(key=lambda r: parse_date(r.get("date", "")) or datetime.max)

    upcoming = [r for r in all_results if r["is_upcoming"]]
    health_up = [r for r in upcoming if "국회공식" not in r.get("source", "") and "국회도서관" not in r.get("source", "")]
    asm_up    = [r for r in upcoming if "국회공식" in r.get("source", "")]
    nanet_up  = [r for r in upcoming if "국회도서관" in r.get("source", "")]
    topic_up  = [r for r in upcoming if r["topic_keyword"]]

    print("\n" + "=" * 60)
    print("검색 결과 요약")
    print("=" * 60)
    print(f"  앞으로 {UPCOMING_DAYS}일 이내 예정 일정: {len(upcoming)}건")
    print(f"    └ 보건복지위원회: {len(health_up)}건")
    print(f"    └ 국회공식(전체위원회): {len(asm_up)}건")
    print(f"    └ 국회도서관 세미나: {len(nanet_up)}건")
    print(f"    └ 응급의료 키워드 포함: {len(topic_up)}건")

    if upcoming:
        print("\n[예정 일정]")
        for r in upcoming:
            tag = "★응급" if r["topic_keyword"] else "  "
            src = r.get("source", "")[:12]
            print(f"  {tag} [{r['date']}] {r['event_type']:6s} | {src:12s} | {r['title'][:50]}")
    else:
        print(f"\n  → 앞으로 {UPCOMING_DAYS}일 내 등록된 실제 일정 없음")

    save_results(upcoming, timestamp)
    if not upcoming:
        print("\n수집된 예정 일정 없음")
        print(f"  보건복지위: {BASE_URL}/cmmit/schl/cmitSchl/schlList.do?menuNo=2000048")
        print(f"  국회공식:   {ASSEMBLY_BASE_URL}/cmmit/schl/cmitSchl/schlList.do")

    return all_results


if __name__ == "__main__":
    asyncio.run(main())
