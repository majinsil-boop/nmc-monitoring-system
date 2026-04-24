"""
언론 모니터링 스크립트 (네이버 뉴스 검색 기반)
키워드: 응급의료, 닥터헬기, 응급실, 중증외상, 응급실 뺑뺑이
수집 범위: 전일(어제) 기사
언론사: 제한 없음 (네이버 뉴스 검색 결과 전체)
"""

import asyncio
import json
import csv
import re
import sys
import urllib.parse
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Windows 콘솔 UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── 상수 ──────────────────────────────────────────────────────────────────────

KEYWORDS  = [
    "응급의료", "닥터헬기", "응급실", "중증외상", "응급실 뺑뺑이",
    "중증응급", "응급의료 취약지역", "미수용", "상급종합병원",
    "중앙응급의료센터", "중앙응급",
    "필수의료", "심뇌센터", "모자보건", "모자의료",
]

_NOW      = datetime.now()
YESTERDAY = _NOW - timedelta(days=1)

# 수집 시간 창: 전일 18:00(석간) ~ 당일 06:00(조간)
# 월요일 실행 시 주말(금 18:00 ~) 포함
_days_back = 3 if _NOW.weekday() == 0 else 1   # 0=월요일
DATE_FROM  = (_NOW - timedelta(days=_days_back)).replace(
                 hour=18, minute=0, second=0, microsecond=0)
DATE_TO    = _NOW.replace(hour=6,  minute=0, second=0, microsecond=0)

MAX_PAGES = 5   # 키워드당 최대 페이지 (10건/페이지)

# ── 필터 설정 ─────────────────────────────────────────────────────────────────

# 제목에 반드시 포함되어야 할 키워드 (하나라도 없으면 제외)
TITLE_KEYWORDS: list[str] = [
    "응급의료", "응급실", "닥터헬기", "중증외상", "응급실 뺑뺑이",
    "구급차", "응급환자", "권역외상", "응급의학",
    "중증응급", "응급의료 취약지역", "취약지역", "미수용", "상급종합병원",
    "중앙응급의료센터", "중앙응급",
    "필수의료", "심뇌센터", "모자보건", "모자의료",
]

# 제외할 연예/엔터 매체 도메인
_EXCLUDE_DOMAINS: set[str] = {
    "tenasia", "starnews", "mydaily", "xportsnews", "insight",
    "wikitree", "dispatch", "startoday", "joynews24", "tvreport",
    "newsen", "sportsdonga", "osen", "topstarnews",
    "heraldpop", "mtstarnews", "spotvnews", "imbc",
}

# 제외할 제목 키워드 (연예·스포츠·지역행사)
_EXCLUDE_TITLE_KW: list[str] = [
    # 연예·방송
    "드라마", "영화", "예능", "배우", "아이돌", "가수", "공연", "시상식",
    "콘서트", "뮤지컬", "오디션", "앨범", "컴백", "데뷔", "티저",
    "OST", "MV", "팬미팅", "팬사인회", "굿즈", "직캠",
    "백상예술대상", "청룡영화상", "대종상", "골든디스크",
    "등장 비화", "애드리브", "비하인드", "촬영 현장",
    "넷플릭스", "왓챠", "티빙", "웨이브", "쿠팡플레이", "시청률",
    # 스포츠
    "야구", "축구", "농구", "배구", "골프", "테니스", "수영", "격투기",
    "올림픽", "월드컵", "챔피언스리그", "선수권대회",
    # 지역행사·기타
    "수여식", "시상식", "경연대회", "축제", "공모전",
    "주가", "코스피", "코스닥", "환율", "증시", "펀드",
]


def _is_relevant(title: str) -> bool:
    """제목에 TITLE_KEYWORDS 중 하나라도 포함되면 True."""
    return any(kw in title for kw in TITLE_KEYWORDS)


def _is_excluded(title: str, press: str) -> bool:
    """연예/엔터 매체이거나 제목에 무관 키워드가 있으면 True."""
    domain_key = press.lower().replace("www.", "").replace("m.", "").split(".")[0]
    if domain_key in _EXCLUDE_DOMAINS:
        return True
    if any(kw in title for kw in _EXCLUDE_TITLE_KW):
        return True
    return False

# ── 날짜 파싱 ─────────────────────────────────────────────────────────────────

_DATE_FMTS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%Y.%m.%d %H:%M:%S",
    "%Y.%m.%d %H:%M",
    "%Y.%m.%d",
    "%Y/%m/%d %H:%M",
    "%Y/%m/%d",
]
_DATE_RE = re.compile(
    r"\d{4}[-./]\d{1,2}[-./]\d{1,2}"
    r"(?:[T\s]+\d{1,2}:\d{2}(?::\d{2})?)?"
)
_REL_RE = re.compile(r"(\d+)\s*(초|분|시간)\s*전|(어제)|(오늘)")


def _parse_date(raw: str) -> datetime | None:
    if not raw:
        return None
    raw = raw.strip()

    # 상대 시간
    m = _REL_RE.search(raw)
    if m:
        if m.group(3):   return YESTERDAY
        if m.group(4):   return _NOW
        n, unit = int(m.group(1)), m.group(2)
        return _NOW - {"초": timedelta(seconds=n),
                       "분": timedelta(minutes=n),
                       "시간": timedelta(hours=n)}[unit]

    # 절대 날짜
    found = _DATE_RE.search(raw)
    if found:
        s = (found.group()
             .replace(".", "-").replace("/", "-").replace("T", " ").strip())
        for fmt in _DATE_FMTS:
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
    return None


def _is_target_date(raw: str) -> bool:
    """어제 00:00 ~ 오늘 06:00 이내이면 True."""
    dt = _parse_date(raw)
    if dt is None:
        return False
    return DATE_FROM <= dt <= DATE_TO


# ── 네이버 뉴스 스크래퍼 ──────────────────────────────────────────────────────

async def _scrape_naver_news(page, keyword: str) -> list[dict]:
    """
    네이버 뉴스 검색으로 어제 기사를 수집한다.
    - sort=1: 최신순
    - pd=3 + ds/de: 날짜 범위 지정 (어제 하루)
    """
    enc      = urllib.parse.quote(keyword)
    from_dot = DATE_FROM.strftime("%Y.%m.%d")
    to_dot   = _NOW.strftime("%Y.%m.%d")
    base_url = (
        f"https://search.naver.com/search.naver"
        f"?where=news&query={enc}&sort=1&pd=3&ds={from_dot}&de={to_dot}"
    )

    results: list[dict] = []
    seen:    set[str]   = set()

    for pg in range(MAX_PAGES):
        start = pg * 10 + 1
        url   = base_url + (f"&start={start}" if start > 1 else "")

        try:
            await page.goto(url, wait_until="networkidle", timeout=25000)
            await asyncio.sleep(1.5)
        except (PlaywrightTimeout, Exception):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(2.0)
            except Exception as e:
                print(f"    오류: {e}"); break

        # 기사 목록 파싱 (네이버 SDS 컴포넌트 구조 대응)
        items = await page.evaluate("""
            () => {
                // 네이버 뉴스 결과 컨테이너 (fds-news-item-list-tab: 안정적 시멘틱 클래스)
                const container = document.querySelector('div.fds-news-item-list-tab');
                if (!container) return [];

                const results = [];
                const seenHrefs = new Set();
                const seenTitles = new Set();

                // 외부 기사 링크 수집
                const extLinks = Array.from(container.querySelectorAll('a[href]'))
                    .filter(a => {
                        const href = a.getAttribute('href') || '';
                        const txt  = (a.innerText || '').trim();
                        return href.startsWith('http')
                            && href.indexOf('naver.com') === -1
                            && txt.length >= 8 && txt.length <= 150;
                    });

                for (const a of extLinks) {
                    const href  = a.getAttribute('href') || '';
                    const title = (a.innerText || '').trim();
                    if (!href || !title) continue;
                    if (seenHrefs.has(href) || seenTitles.has(title)) continue;
                    seenHrefs.add(href);
                    seenTitles.add(title);

                    // 카드 경계 탐색: 제목보다 충분히 많은 텍스트를 가진 조상
                    let card = a.parentElement;
                    for (let i = 0; i < 7; i++) {
                        if (!card) break;
                        if ((card.innerText || '').length > title.length + 10) break;
                        card = card.parentElement;
                    }

                    let press = '';
                    let dateStr = '';
                    let snippet = '';
                    if (card) {
                        const spans = Array.from(card.querySelectorAll('span, a'));
                        for (const el of spans) {
                            const t = (el.innerText || '').trim();
                            if (!t || t === title) continue;
                            // 날짜 패턴
                            if (!dateStr && t.length <= 40 && (
                                /[0-9]{4}[.][0-9]{1,2}[.][0-9]{1,2}/.test(t) ||
                                /[0-9]+(분|시간)/.test(t.replace(/ /g,'')) ||
                                t === '어제' || t === '오늘'
                            )) {
                                dateStr = t;
                                continue;
                            }
                            // 언론사: 숫자 없고 2~20자
                            if (!press && t.length >= 2 && t.length <= 20
                                && !/[0-9]/.test(t) && el.getAttribute('href') !== href) {
                                press = t;
                                continue;
                            }
                            // 스니펫: 30자 이상의 긴 텍스트
                            if (!snippet && t.length >= 30 && t !== press) {
                                snippet = t.substring(0, 200);
                            }
                        }
                        // 스니펫 폴백: 카드 전체 텍스트에서 제목 제거 후 추출
                        if (!snippet) {
                            const cardText = (card.innerText || '').replace(title, '').trim();
                            if (cardText.length > 20) snippet = cardText.substring(0, 200);
                        }
                    }

                    results.push({ title, href, press, dateStr, snippet });
                }
                return results;
            }
        """)

        if not items:
            print(f"    p{pg+1}: 결과 없음 → 종료")
            break

        page_count = 0
        for item in items:
            title    = item.get("title", "").strip()
            href     = item.get("href", "").strip()
            press    = item.get("press", "").strip()
            date_raw = item.get("dateStr", "").strip()
            snippet  = item.get("snippet", "").strip()

            if not title or not href or href in seen:
                continue
            seen.add(href)

            # 날짜 처리:
            #   네이버가 ds/de 파라미터로 이미 날짜 필터링했으므로
            #   파싱 성공 시 검증, 실패/미확인 시 어제 날짜로 기본값 설정
            dt = _parse_date(date_raw)
            if dt:
                if dt > DATE_TO:       # 오늘 기사가 섞인 경우 제외
                    continue
                if dt < DATE_FROM:     # 명백히 오래된 기사 제외
                    continue
                date_str = dt.strftime("%Y-%m-%d")
            else:
                date_str = YESTERDAY.strftime("%Y-%m-%d")   # 날짜 미확인 → 어제로 처리

            # 언론사 폴백: 도메인에서 추출
            if not press and href.startswith("http"):
                try:
                    domain = urllib.parse.urlparse(href).netloc
                    domain = domain.replace("www.", "").replace("m.", "")
                    press  = domain.split(".")[0]
                except Exception:
                    pass

            # 제목 필수 키워드 필터 (우선 적용)
            if not _is_relevant(title):
                continue

            # 연예/스포츠/지역행사 제외 필터
            if _is_excluded(title, press):
                continue

            results.append({
                "keyword":      keyword,
                "source":       press,
                "title":        title,
                "url":          href,
                "date":         date_str,
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            page_count += 1

        print(f"    p{pg+1}: {page_count}건 수집 (총 {len(items)}건 중)")

    return results


# ── 의료전문 언론 직접 수집 (봇차단 없는 사이트만) ──────────────────────────────

_DIRECT_MEDIA: list[tuple[str, str]] = [
    ("청년의사", "https://www.docdocdoc.co.kr/news/articleList.html?view_type=sm"),
]

# 봇차단으로 직접 수집 불가 → 네이버 검색으로 대체
# (표시이름, 네이버 검색어, URL 도메인 식별자)
_NAVER_PRESS_SUPPLEMENT: list[tuple[str, str, str]] = [
    ("메디칼타임즈", "메디칼타임즈", "medicaltimes"),
    ("법률신문",    "법률신문",    "lawtimes"),
]
_SUPPLEMENT_KEYWORDS: list[str] = [
    "응급의료", "응급실", "중증외상", "응급실 뺑뺑이", "상급종합병원", "중증응급",
]


async def _scrape_media_direct(page, site_name: str, url: str) -> list[dict]:
    """청년의사·메디칼타임즈·법률신문 기사 목록 직접 수집."""
    results: list[dict] = []
    print(f"\n[{site_name}] {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(1.5)

        items = await page.evaluate("""
            () => {
                const out = [];
                // 뉴스판 계열 (type2), 일반 list, article 태그 순으로 시도
                const lists = [
                    ...document.querySelectorAll('ul.type2 li'),
                    ...document.querySelectorAll('ul.article-list li'),
                    ...document.querySelectorAll('.news-list li, .list-news li'),
                    ...document.querySelectorAll('article'),
                ];
                for (const item of lists) {
                    const a = item.querySelector(
                        'h4 a, h3 a, h2 a, .title a, .heading a, a[href]'
                    );
                    if (!a) continue;
                    const title = (a.innerText || '').trim();
                    if (!title || title.length < 5 || title.length > 200) continue;
                    const href = a.getAttribute('href') || '';

                    let dateStr = '';
                    for (const el of item.querySelectorAll(
                        'em, .date, .time, .byline, span[class*="date"], span[class*="time"]'
                    )) {
                        const t = (el.innerText || '').trim();
                        if (/\\d{4}[.\\-\\/]\\d{1,2}/.test(t) ||
                            /\\d+(분|시간)전/.test(t.replace(/ /g,''))) {
                            dateStr = t; break;
                        }
                    }

                    let snippet = '';
                    const desc = item.querySelector('.lead, .summary, p');
                    if (desc) snippet = (desc.innerText || '').trim().slice(0, 200);

                    out.push({ title, href, dateStr, snippet });
                }
                return out;
            }
        """)

        base = "/".join(url.split("/")[:3])  # https://www.site.com
        for item in items:
            title    = item.get("title", "").strip()
            href     = item.get("href", "").strip()
            date_raw = item.get("dateStr", "").strip()
            snippet  = item.get("snippet", "").strip()

            if not title or not href:
                continue
            link = href if href.startswith("http") else base + ("" if href.startswith("/") else "/") + href.lstrip("/")

            # 날짜 필터 — 직접수집 사이트는 시간 무관 날짜(date)만 비교
            # (의료 전문지는 주로 업무시간 발행 → 18:00~06:00 시간창 적용 시 전량 탈락)
            dt = _parse_date(date_raw)
            if dt:
                if not (DATE_FROM.date() <= dt.date() <= DATE_TO.date()):
                    continue
                date_str = dt.strftime("%Y-%m-%d")
            else:
                date_str = DATE_FROM.strftime("%Y-%m-%d")

            # 제목 또는 본문 요약에 키워드 포함 여부
            combined = title + " " + snippet
            if not _is_relevant(combined):
                continue
            if _is_excluded(title, site_name):
                continue

            results.append({
                "keyword":      next((kw for kw in TITLE_KEYWORDS if kw in combined), "기타"),
                "source":       site_name,
                "title":        title,
                "url":          link,
                "date":         date_str,
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

    except Exception as e:
        print(f"  오류: {e}")

    print(f"  수집: {len(results)}건")
    return results


# ── 봇차단 언론사 네이버 검색 대체 수집 ──────────────────────────────────────────

async def _scrape_naver_press(page, press_name: str, press_query: str, press_domain: str) -> list[dict]:
    """메디칼타임즈·법률신문 등 봇차단 사이트를 네이버 검색으로 대체 수집.
    'press_query keyword' 로 검색 후 URL에 press_domain이 포함된 기사만 채택."""
    results: list[dict] = []
    seen:    set[str]   = set()
    print(f"\n[{press_name}] 네이버 검색 대체 수집")
    for kw in _SUPPLEMENT_KEYWORDS:
        articles = await _scrape_naver_news(page, f"{press_query} {kw}")
        for a in articles:
            url = a.get("url", "")
            if press_domain not in url.lower():
                continue
            if url in seen:
                continue
            seen.add(url)
            a["keyword"] = kw
            a["source"]  = press_name
            results.append(a)
    print(f"  수집: {len(results)}건")
    return results


# ── 보건복지부 보도자료 수집 ──────────────────────────────────────────────────────

_MOHW_URL = "https://www.mohw.go.kr/board.es?mid=a10503010100&bid=0027"


async def _scrape_mohw_press(page) -> list[dict]:
    """보건복지부 알림 > 보도자료 수집. 제목·내용에 키워드 포함 시 통과."""
    results: list[dict] = []
    print(f"\n[보건복지부] {_MOHW_URL}")
    try:
        await page.goto(_MOHW_URL, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(1.5)

        items = await page.evaluate("""
            () => {
                const out = [];
                const rows = document.querySelectorAll('table tbody tr');
                for (const row of rows) {
                    const tds = row.querySelectorAll('td');
                    if (tds.length < 3) continue;
                    // 제목 링크 탐색 (일반적으로 두 번째 td)
                    let titleEl = null;
                    for (const td of tds) {
                        const a = td.querySelector('a');
                        if (a && (a.innerText || '').trim().length > 5) {
                            titleEl = a; break;
                        }
                    }
                    if (!titleEl) continue;
                    const title = (titleEl.innerText || '').trim();
                    const href  = titleEl.getAttribute('href') || '';
                    // 날짜: 마지막 td 중 날짜 패턴 탐색
                    let dateStr = '';
                    for (const td of [...tds].reverse()) {
                        const t = (td.innerText || '').trim();
                        if (/\\d{4}[.\\-\\/]\\d{1,2}[.\\-\\/]\\d{1,2}/.test(t)) {
                            dateStr = t; break;
                        }
                    }
                    // 내용 요약 (있으면)
                    const snippet = row.querySelector('.board_text, .summary, p');
                    const snippetText = snippet ? (snippet.innerText || '').trim().slice(0, 200) : '';
                    out.push({ title, href, dateStr, snippet: snippetText });
                }
                return out;
            }
        """)

        for item in items:
            title    = item.get("title", "").strip()
            href     = item.get("href", "").strip()
            date_raw = item.get("dateStr", "").strip()
            snippet  = item.get("snippet", "").strip()

            if not title:
                continue
            link = href if href.startswith("http") else "https://www.mohw.go.kr" + (
                "" if href.startswith("/") else "/") + href.lstrip("/")

            dt = _parse_date(date_raw)
            if dt:
                if not (DATE_FROM <= dt <= DATE_TO):
                    continue
                date_str = dt.strftime("%Y-%m-%d")
            else:
                date_str = DATE_FROM.strftime("%Y-%m-%d")

            combined = title + " " + snippet
            if not _is_relevant(combined):
                continue

            results.append({
                "keyword":      next((kw for kw in TITLE_KEYWORDS if kw in combined), "기타"),
                "source":       "보건복지부",
                "title":        title,
                "url":          link,
                "date":         date_str,
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

    except Exception as e:
        print(f"  오류: {e}")

    print(f"  수집: {len(results)}건")
    return results


# ── 전체 수집 흐름 ────────────────────────────────────────────────────────────

async def collect_all(context) -> list[dict]:
    all_results: list[dict] = []

    # ── 네이버 뉴스 키워드 검색 ──────────────────────────────
    for keyword in KEYWORDS:
        print(f"\n{'='*55}")
        print(f"[키워드] {keyword}")
        print(f"{'='*55}")

        page = await context.new_page()
        try:
            articles = await _scrape_naver_news(page, keyword)
            print(f"  -> {len(articles)}건 수집")
            all_results.extend(articles)
        except Exception as e:
            print(f"  오류: {e}")
        finally:
            try:
                await page.close()
            except Exception:
                pass

        await asyncio.sleep(0.5)

    # ── 의료전문 언론 직접 수집 (청년의사) ──────────────────
    print(f"\n{'='*55}")
    print("[직접수집] 청년의사")
    print(f"{'='*55}")

    for site_name, site_url in _DIRECT_MEDIA:
        page = await context.new_page()
        try:
            articles = await _scrape_media_direct(page, site_name, site_url)
            all_results.extend(articles)
        except Exception as e:
            print(f"  [{site_name}] 오류: {e}")
        finally:
            try:
                await page.close()
            except Exception:
                pass
        await asyncio.sleep(0.5)

    # ── 봇차단 언론사 네이버 검색 대체 (메디칼타임즈·법률신문) ──
    print(f"\n{'='*55}")
    print("[네이버 대체] 메디칼타임즈 · 법률신문")
    print(f"{'='*55}")

    for press_name, press_query, press_domain in _NAVER_PRESS_SUPPLEMENT:
        page = await context.new_page()
        try:
            articles = await _scrape_naver_press(page, press_name, press_query, press_domain)
            all_results.extend(articles)
        except Exception as e:
            print(f"  [{press_name}] 오류: {e}")
        finally:
            try:
                await page.close()
            except Exception:
                pass
        await asyncio.sleep(0.5)

    # ── 보건복지부 보도자료 ──────────────────────────────────
    page = await context.new_page()
    try:
        articles = await _scrape_mohw_press(page)
        all_results.extend(articles)
    except Exception as e:
        print(f"  [보건복지부] 오류: {e}")
    finally:
        try:
            await page.close()
        except Exception:
            pass

    return all_results


# ── 중복 제거 & 저장 ──────────────────────────────────────────────────────────

def _dedup(results: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out:  list[dict] = []
    for r in results:
        key = r.get("url") or f"{r['title']}|{r['source']}"
        if key and key not in seen:
            seen.add(key)
            out.append(r)
    return out


def save_results(results: list[dict], date_str: str) -> tuple[str, str]:
    json_path = f"news_results_{date_str}.json"
    csv_path  = f"news_results_{date_str}.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[저장] JSON : {json_path}")

    fields = ["keyword", "source", "title", "date", "url", "collected_at"]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"[저장] CSV  : {csv_path}")

    return json_path, csv_path


# ── 메인 ──────────────────────────────────────────────────────────────────────

async def main():
    date_str = YESTERDAY.strftime("%Y%m%d")

    print("=" * 60)
    print("언론 모니터링 - 전일 기사 수집 (네이버 뉴스 검색)")
    print(f"수집 대상일: {YESTERDAY.strftime('%Y-%m-%d')} (어제)")
    print(f"키워드: {', '.join(KEYWORDS)}")
    print(f"언론사: 제한 없음")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=100,
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"},
        )
        all_results = await collect_all(context)
        await browser.close()

    all_results = _dedup(all_results)
    all_results.sort(
        key=lambda r: (r.get("date", ""), r["keyword"], r.get("source", "")),
        reverse=True,
    )

    print("\n" + "=" * 60)
    print("수집 결과 요약")
    print("=" * 60)
    for kw in KEYWORDS:
        kw_items = [r for r in all_results if r["keyword"] == kw]
        if not kw_items:
            print(f"  {kw}: 0건")
            continue
        print(f"  {kw}: {len(kw_items)}건")
        # 언론사별 카운트
        sources: dict[str, int] = {}
        for r in kw_items:
            sources[r.get("source", "기타")] = sources.get(r.get("source", "기타"), 0) + 1
        for src, cnt in sorted(sources.items(), key=lambda x: -x[1])[:5]:
            print(f"    └ {src}: {cnt}건")
    print(f"  전체 (중복 제거): {len(all_results)}건")

    # 0건이어도 반드시 저장 (generate_report.py가 오래된 파일을 재사용하지 않도록)
    save_results(all_results, date_str)

    if all_results:
        print("\n[미리보기] 최신 10건")
        for r in all_results[:10]:
            print(f"  [{r['date']}] [{r.get('source','')}] {r['keyword']} | {r['title'][:50]}")
    else:
        print("\n수집된 기사가 없습니다.")

    return all_results


if __name__ == "__main__":
    asyncio.run(main())
