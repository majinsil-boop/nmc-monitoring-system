import asyncio
import json
import csv
import os
import re
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import subprocess

# [기존 설정 및 헬퍼 함수들은 유지하되 핵심 로직만 최적화]
# ... (상단 생략: summarize_with_claude, _load_history 등은 동일)

async def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_results = []
    history = _load_history()
    print(f"[이력 DB] 기존 이력 {len(history)}건 로드")

    async with async_playwright() as p:
        # 1. 속도 최적화: headless=True로 변경 (화면 안 띄움)
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR")
        page = await context.new_page()

        # 2. 검색 효율화: 모든 키워드를 다 검색창에 넣지 않고 핵심만 검색
        # (연구원님의 키워드 리스트를 효율적으로 순회)
        for keyword in KEYWORDS:
            try:
                results = await search_bills(page, keyword)
                all_results.extend(results)
            except Exception as e:
                print(f"  '{keyword}' 검색 오류: {e}")

        # 3. 중복 제거
        seen_no = set()
        unique = []
        for r in all_results:
            key = r.get("bill_no")
            if key and key not in seen_no:
                seen_no.add(key)
                unique.append(r)
        all_results = unique

        # 4. [핵심] 상세 페이지 진입 전 '선별 필터링'
        # 목록에서 이미 '가결, 폐기'된 것들은 상세 페이지(Claude 요약)를 가지 않습니다.
        filtered_for_detail = []
        print(f"\n[선별] {len(all_results)}건 중 상세 수집 대상을 골라냅니다...")
        
        for bill in all_results:
            # 상태가 종료된 것(공포, 가결 등)은 요약하지 않고 패스!
            if not _is_active(bill.get("status", "")):
                continue
            
            # 7일 이내 발의/변동 건이거나 입법예고 중인 것만 상세 수집
            if _is_recent(bill) or _is_notice_active(bill.get("legislative_notice", "")):
                filtered_for_detail.append(bill)

        print(f"🔎 최종 {len(filtered_for_detail)}건에 대해서만 상세 요약을 진행합니다. (시간 단축)")

        # 5. 선별된 의안만 상세 페이지 수집 및 Claude 요약
        for i, bill in enumerate(filtered_for_detail, 1):
            url = bill.get("url", "")
            print(f"  [{i}/{len(filtered_for_detail)}] {bill.get('bill_name','')[:30]}...")
            raw_summary, status_date, notice = await _fetch_bill_detail(page, url)
            
            if raw_summary:
                bill["summary"] = _summarize_with_claude(raw_summary, bill.get("bill_name", ""))
            bill["status_changed_date"] = status_date
            bill["legislative_notice"] = notice
            
            # 상태 변경 감지
            _apply_status_change_label(bill, history)

        await browser.close()

    # 6. 결과 저장 및 정렬 (기존 로직 유지)
    # ... (중략)
    save_results(filtered_for_detail, timestamp)
    _save_history(filtered_for_detail, history)

if __name__ == "__main__":
    asyncio.run(main())