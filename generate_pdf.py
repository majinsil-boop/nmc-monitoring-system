"""
generate_pdf.py — 최신 보고서 HTML을 Playwright로 A4 PDF 변환

사용법:
  python generate_pdf.py                     # 최신 보고서_*.html 자동 선택
  python generate_pdf.py 보고서_20260414.html  # 파일 직접 지정
"""

import asyncio
import glob
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright

BASE = os.path.expanduser("~")


async def html_to_pdf(html_path: str) -> str:
    pdf_path = str(Path(html_path).with_suffix(".pdf"))
    file_url = Path(html_path).as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page    = await browser.new_page()
        # screen 미디어 사용 → 링크 어노테이션 보존 + 색상 유지
        await page.emulate_media(media="screen")
        await page.goto(file_url, wait_until="networkidle", timeout=30000)
        await page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            scale=0.82,          # A4 한 장 자동 축소
            margin={"top": "8mm", "right": "10mm", "bottom": "8mm", "left": "10mm"},
        )
        await browser.close()

    return pdf_path


def main():
    if len(sys.argv) > 1:
        html_path = os.path.join(BASE, sys.argv[1]) if not os.path.isabs(sys.argv[1]) else sys.argv[1]
    else:
        files = sorted(glob.glob(os.path.join(BASE, "보고서_*.html")))
        if not files:
            print("[오류] 보고서 HTML 파일이 없습니다.")
            print("  먼저 review_*.html 앱에서 '보고서 생성' 버튼을 눌러 HTML을 저장하세요.")
            sys.exit(1)
        html_path = files[-1]

    if not os.path.exists(html_path):
        print(f"[오류] 파일을 찾을 수 없습니다: {html_path}")
        sys.exit(1)

    print(f"  HTML : {html_path}")
    pdf_path = asyncio.run(html_to_pdf(html_path))
    print(f"  PDF  : {pdf_path}")
    os.startfile(pdf_path)


if __name__ == "__main__":
    main()
