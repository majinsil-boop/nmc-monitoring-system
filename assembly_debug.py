"""
국회의안정보시스템 HTML 구조 진단 스크립트 v2
"""

import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://likms.assembly.go.kr/bill/bi/main/mainPage.do"
SEARCH_KEYWORD = "응급의료"


async def main():
    requests_log = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
        )
        page = await context.new_page()

        # 네트워크 요청 캡처
        def on_request(req):
            if any(k in req.url for k in ["search", "bill", "sch", "list", "List"]):
                requests_log.append(f"{req.method} {req.url}")

        page.on("request", on_request)

        print("1) 메인 페이지 접속...")
        await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)
        print(f"   현재 URL: {page.url}")

        # 검색 입력
        print(f"\n2) '{SEARCH_KEYWORD}' 검색 입력...")
        search_input = await page.query_selector("#first__input_keyword_pc")
        if search_input:
            await search_input.click()
            await search_input.fill(SEARCH_KEYWORD)
            print("   입력 완료")
        else:
            print("   #first__input_keyword_pc 없음, 대체 시도...")
            for sel in ["input[placeholder*='의안명']", ".search_input", "input[type='search']"]:
                el = await page.query_selector(sel)
                if el:
                    await el.click()
                    await el.fill(SEARCH_KEYWORD)
                    print(f"   {sel} 입력 완료")
                    break

        # 검색 버튼 클릭 또는 Enter
        print("\n3) 검색 실행...")
        search_btn = await page.query_selector("#first__search_form button[type='submit'], #first__search_form .btn_search, button.btn_search")
        if search_btn:
            await search_btn.click()
            print("   버튼 클릭")
        else:
            await page.keyboard.press("Enter")
            print("   Enter 키")

        await page.wait_for_load_state("networkidle", timeout=20000)
        await asyncio.sleep(3)
        print(f"   검색 후 URL: {page.url}")

        # 현재 HTML 저장
        html = await page.content()
        with open("html_dump_search.txt", "w", encoding="utf-8") as f:
            f.write(html)
        print("   html_dump_search.txt 저장")

        # 테이블 구조 분석
        print("\n4) 테이블 구조:")
        tables = await page.query_selector_all("table")
        print(f"   table {len(tables)}개")
        for i, tbl in enumerate(tables):
            id_ = await tbl.get_attribute("id") or ""
            cls = await tbl.get_attribute("class") or ""
            rows = await tbl.query_selector_all("tbody tr")
            ths = await tbl.query_selector_all("th")
            th_texts = [await th.inner_text() for th in ths]
            print(f"   [{i}] id={id_!r} class={cls!r} rows={len(rows)} ths={th_texts}")
            if rows:
                first_row = rows[0]
                cols = await first_row.query_selector_all("td")
                col_texts = []
                for c in cols[:8]:
                    t = (await c.inner_text()).strip().replace("\n", " ")[:30]
                    col_texts.append(t)
                print(f"       첫 행: {col_texts}")
                # 링크 확인
                link = await first_row.query_selector("a")
                if link:
                    href = await link.get_attribute("href") or ""
                    onclick = await link.get_attribute("onclick") or ""
                    print(f"       링크 href={href!r} onclick={onclick!r}")

        # 결과 없음 요소 확인
        print("\n5) 결과없음 요소 확인:")
        for sel in ["td.noList", ".no_data", ".no_result", ".empty", "td:has-text('없습니다')", ".list_none", ".nodata"]:
            el = await page.query_selector(sel)
            if el:
                t = await el.inner_text()
                print(f"   발견: {sel} → {t[:50]!r}")

        # 페이지네이션 확인
        print("\n6) 페이지네이션:")
        for sel in ["a.next", "a[title='다음']", "img[alt='다음']", ".paging a", ".pagination a", ".page_nav a"]:
            els = await page.query_selector_all(sel)
            if els:
                print(f"   {sel}: {len(els)}개")
                for el in els[:3]:
                    href = await el.get_attribute("href") or ""
                    onclick = await el.get_attribute("onclick") or ""
                    text = (await el.inner_text()).strip()
                    print(f"     text={text!r} href={href!r} onclick={onclick!r}")

        # div/ul 기반 결과 목록 확인 (테이블이 아닌 경우)
        print("\n7) 리스트형 결과 (li/div):")
        for sel in [".bill_list li", ".search_result li", ".result_list li", ".list_wrap li", "ul.list li"]:
            els = await page.query_selector_all(sel)
            if els:
                print(f"   {sel}: {len(els)}개")
                if els:
                    t = (await els[0].inner_text()).strip().replace("\n", " ")[:80]
                    print(f"     첫 번째: {t!r}")

        print("\n8) 캡처된 네트워크 요청:")
        for r in sorted(set(requests_log)):
            print(f"   {r}")

        await asyncio.sleep(3)
        await browser.close()

    print("\n완료! html_dump_search.txt 확인하세요.")


if __name__ == "__main__":
    asyncio.run(main())
