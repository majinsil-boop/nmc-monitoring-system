"""
news_monitor.py 디버그 스크립트
각 언론사별로 실제 접속 URL, 발견된 기사, 날짜 파싱 결과를 상세 출력
"""
import asyncio
import re
import sys
import io
import urllib.parse
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

KEYWORD   = "응급의료"
_NOW      = datetime.now()
YESTERDAY = _NOW - timedelta(days=1)
DATE_FROM = YESTERDAY.replace(hour=0, minute=0, second=0, microsecond=0)
DATE_TO   = _NOW.replace(hour=6, minute=0, second=0, microsecond=0)

print(f"기준 시간: {_NOW.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"수집 범위: {DATE_FROM}  ~  {DATE_TO}")
print(f"검색 키워드: {KEYWORD}\n")

_ISO_RE  = re.compile(r"(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})")
_DATE_RE = re.compile(r"\d{4}[-./]\d{1,2}[-./]\d{1,2}")

def parse_date(raw):
    if not raw: return None
    iso = _ISO_RE.search(raw)
    if iso:
        try: return datetime.strptime(f"{iso.group(1)} {iso.group(2)}", "%Y-%m-%d %H:%M:%S")
        except: pass
    m = _DATE_RE.search(raw)
    if m:
        s = m.group().replace(".", "-").replace("/", "-")
        try: return datetime.strptime(s, "%Y-%m-%d")
        except: pass
    return None

def in_range(raw):
    dt = parse_date(raw)
    if not dt: return False
    return DATE_FROM <= dt <= DATE_TO

SEP = "-" * 70

async def debug_dailymedi(page):
    print(f"\n{'='*70}")
    print("[ 1. 데일리메디 ]")
    print(f"{'='*70}")
    base = "https://www.dailymedi.com"
    enc  = urllib.parse.quote(KEYWORD)
    url  = f"{base}/news/search.php?stx={enc}"
    print(f"접속 URL: {url}")

    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    await asyncio.sleep(1)
    print(f"실제 URL: {page.url}")

    anchors = await page.query_selector_all("a[href*='news_view.php']")
    print(f"news_view.php 링크 수: {len(anchors)}")

    found = 0
    for i, a in enumerate(anchors[:15]):
        title = (await a.inner_text()).strip()
        href  = (await a.get_attribute("href")) or ""
        if len(title) < 5 or len(title) > 120:
            continue
        date_raw = await page.evaluate("""
            (el) => {
                let node = el.parentElement;
                for (let i = 0; i < 6; i++) {
                    if (!node) break;
                    const t = node.innerText || '';
                    const m = t.match(/\\d{4}-\\d{2}-\\d{2}[\\s\\d:]*/) ||
                              t.match(/\\d{4}\\.\\d{2}\\.\\d{2}/);
                    if (m) return m[0].trim();
                    node = node.parentElement;
                }
                return '';
            }
        """, a)
        dt     = parse_date(date_raw)
        ok     = in_range(date_raw)
        print(f"  [{i+1:2d}] 날짜={date_raw or '없음':25s} | in_range={str(ok):5s} | {title[:45]}")
        if ok: found += 1
    print(f"  → 날짜 범위 내 기사: {found}건")

    # 페이지 전체 날짜 패턴 샘플
    body = await page.inner_text("body")
    dates = _DATE_RE.findall(body)
    uniq  = sorted(set(dates), reverse=True)[:10]
    print(f"  페이지 내 날짜 패턴 (최신 10개): {uniq}")


async def debug_doctorsnews(page):
    print(f"\n{'='*70}")
    print("[ 2. 의협신문 ]")
    print(f"{'='*70}")
    base = "https://www.doctorsnews.co.kr"
    enc  = urllib.parse.quote(KEYWORD)
    url  = f"{base}/news/articleList.html?sc_word={enc}&view_type=sm&sc_order=d"
    print(f"접속 URL: {url}")

    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    await asyncio.sleep(1)
    print(f"실제 URL: {page.url}")

    # 제목 링크 탐색
    sels = [
        "div.list-titles a[href*='articleView']",
        "div.list-block a[href*='articleView']",
        "strong.titles a[href*='articleView']",
        "a[href*='articleView']",
    ]
    links = []
    for sel in sels:
        links = await page.query_selector_all(sel)
        if links:
            print(f"  선택자 '{sel}' → {len(links)}개 링크")
            break

    if not links:
        print("  제목 링크를 찾을 수 없음")
        body = await page.inner_text("body")
        print(f"  본문 앞 500자:\n{body[:500]}")
        return

    print(f"\n  상위 5개 기사 → 상세 페이지에서 날짜 확인:")
    for i, a in enumerate(links[:5]):
        title = (await a.inner_text()).strip()
        href  = (await a.get_attribute("href")) or ""
        if not href.startswith("http"):
            href = base + href
        print(f"\n  [{i+1}] {title[:50]}")
        print(f"       URL: {href}")
        try:
            await page.goto(href, wait_until="domcontentloaded", timeout=15000)
            date_raw = await page.evaluate("""
                () => {
                    const m = document.querySelector(
                        'meta[property="article:published_time"],'
                        'meta[name="pubdate"],meta[name="date"]'
                    );
                    if (m) return m.getAttribute('content') || '';
                    const el = document.querySelector('.byline,.article-date,time,.date');
                    return el ? el.getAttribute('datetime') || el.innerText || '' : '';
                }
            """)
            dt = parse_date(date_raw)
            ok = in_range(date_raw)
            print(f"       메타 날짜: {date_raw or '없음'}")
            print(f"       파싱 결과: {dt}  →  in_range={ok}")
        except Exception as e:
            print(f"       오류: {e}")
        await page.go_back()
        await asyncio.sleep(0.5)


async def debug_docdocdoc(page):
    print(f"\n{'='*70}")
    print("[ 3. 청년의사 ]")
    print(f"{'='*70}")
    base = "https://www.docdocdoc.co.kr"
    enc  = urllib.parse.quote(KEYWORD)
    url  = f"{base}/news/articleList.html?sc_word={enc}&view_type=sm&sc_order=d"
    print(f"접속 URL: {url}")

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except PlaywrightTimeout:
        await asyncio.sleep(3)
    await asyncio.sleep(1)
    print(f"실제 URL: {page.url}")

    links = await page.query_selector_all("a[href*='articleView']")
    title_links = [a for a in links]
    print(f"  articleView 링크 수: {len(title_links)}")

    titles_found = []
    for a in title_links[:20]:
        txt = (await a.inner_text()).strip()
        if 5 <= len(txt) <= 120:
            titles_found.append((txt, (await a.get_attribute("href")) or ""))

    print(f"  제목 길이(5~120) 링크: {len(titles_found)}개")
    for i, (t, h) in enumerate(titles_found[:5]):
        print(f"  [{i+1}] {t[:55]}")
        print(f"       href: {h[:80]}")

    if titles_found:
        print(f"\n  첫 번째 기사 상세 페이지 날짜 확인:")
        href = titles_found[0][1]
        if not href.startswith("http"): href = base + href
        await page.goto(href, wait_until="domcontentloaded", timeout=15000)
        date_raw = await page.evaluate("""
            () => {
                const m = document.querySelector(
                    'meta[property="article:published_time"],'
                    'meta[name="pubdate"],meta[name="date"]'
                );
                if (m) return m.getAttribute('content') || '';
                const el = document.querySelector('.byline,.article-date,time,.date,.view-date');
                return el ? el.getAttribute('datetime') || el.innerText || '' : '';
            }
        """)
        dt = parse_date(date_raw)
        ok = in_range(date_raw)
        print(f"  메타 날짜: {date_raw or '없음'}")
        print(f"  파싱 결과: {dt}  →  in_range={ok}")

    # 페이지 날짜 패턴
    await page.go_back()
    await asyncio.sleep(0.5)
    body = await page.inner_text("body")
    dates = _DATE_RE.findall(body)
    uniq  = sorted(set(dates), reverse=True)[:10]
    print(f"  목록 페이지 날짜 패턴: {uniq}")


async def debug_korea_kr(page):
    print(f"\n{'='*70}")
    print("[ 4. 정책브리핑 ]")
    print(f"{'='*70}")
    base   = "https://www.korea.kr"
    yd_str = YESTERDAY.strftime("%Y-%m-%d")
    url    = f"{base}/news/pressReleaseList.do?startDate={yd_str}&endDate={yd_str}"
    print(f"접속 URL: {url}")
    print(f"날짜 파라미터: startDate={yd_str}, endDate={yd_str}")

    try:
        await page.goto(url, wait_until="networkidle", timeout=25000)
        await asyncio.sleep(2)
    except PlaywrightTimeout:
        await asyncio.sleep(3)
    print(f"실제 URL: {page.url}")

    links = await page.query_selector_all("a[href*='pressReleaseView']")
    print(f"  pressReleaseView 링크 수: {len(links)}")

    kw_hits = 0
    for i, a in enumerate(links[:20]):
        title = (await a.inner_text()).strip()
        parent_text = await page.evaluate("""
            (el) => {
                const node = el.closest('li, article, div');
                return node ? (node.innerText || '') : '';
            }
        """, a)
        hit = KEYWORD in title or KEYWORD in parent_text
        print(f"  [{i+1:2d}] {'[HIT]' if hit else '     '} {title[:50]}")
        if hit: kw_hits += 1

    print(f"  → '{KEYWORD}' 키워드 매칭: {kw_hits}건")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
        )

        page = await context.new_page()

        await debug_dailymedi(page)
        await debug_doctorsnews(page)
        await debug_docdocdoc(page)
        await debug_korea_kr(page)

        print(f"\n{'='*70}")
        print("진단 완료")
        print(f"{'='*70}")
        print(f"\n날짜 범위 재확인:")
        print(f"  DATE_FROM : {DATE_FROM}")
        print(f"  DATE_TO   : {DATE_TO}")
        print(f"  어제       : {YESTERDAY.strftime('%Y-%m-%d')}")
        print(f"  오늘       : {_NOW.strftime('%Y-%m-%d')}")

        await browser.close()

asyncio.run(main())
