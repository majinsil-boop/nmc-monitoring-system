"""
report_server.py — 보고서 생성 Flask 서버 (포트 5000)

엔드포인트:
  GET  /             → 최신 JSON 자동 로드 후 review_news.html 서빙
  POST /save-report  → HTML 저장 + Playwright A4 PDF 변환
"""

import glob
import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, Response
from playwright.sync_api import sync_playwright

BASE     = os.path.expanduser("~")
PORT     = 5000
MARKER   = "null; // __PRELOAD_MARKER__"
app      = Flask(__name__)


def _load_latest(pattern: str) -> list:
    """패턴에 맞는 가장 최신 JSON 파일을 읽어 반환. 없으면 빈 리스트."""
    files = sorted(glob.glob(os.path.join(BASE, pattern)))
    if not files:
        return []
    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


def _html_to_pdf(html_path: str, pdf_path: str):
    """Playwright 동기 API로 A4 PDF 변환 (링크 클릭 가능)."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page    = browser.new_page()
        # screen 미디어 사용 → 링크 어노테이션 보존 + 색상 유지
        page.emulate_media(media="screen")
        page.goto(
            Path(html_path).as_uri(),
            wait_until="networkidle",
            timeout=30_000,
        )
        page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            scale=0.82,          # A4 한 장 자동 축소
            margin={"top": "8mm", "right": "10mm",
                    "bottom": "8mm", "left": "10mm"},
        )
        browser.close()


@app.route("/")
def index():
    template = os.path.join(BASE, "review_news.html")
    if not os.path.exists(template):
        return "review_news.html 파일이 없습니다.", 404

    with open(template, encoding="utf-8") as f:
        html = f.read()

    # 최신 JSON 자동 로드
    asm_data  = _load_latest("assembly_results_*.json")
    sch_data  = _load_latest("schedule_results_*.json")
    news_data = _load_latest("news_results_*.json")

    print(f"  [자동 로드] 의안 {len(asm_data)}건 / 일정 {len(sch_data)}건 / 뉴스 {len(news_data)}건")

    preload = json.dumps(
        {"assembly": asm_data, "schedule": sch_data, "news": news_data},
        ensure_ascii=False,
    )

    if MARKER in html:
        html = html.replace(MARKER, preload + "; // auto-loaded")

    return Response(html, content_type="text/html; charset=utf-8",
                    headers={"Cache-Control": "no-store, no-cache, must-revalidate",
                             "Pragma": "no-cache"})


@app.route("/save-report", methods=["POST"])
def save_report():
    data     = request.get_json(force=True)
    html_str = data.get("html", "")
    filename = data.get("filename") or f"보고서_{datetime.now().strftime('%Y%m%d')}.html"

    html_path = os.path.join(BASE, filename)
    pdf_path  = html_path.replace(".html", ".pdf")

    # HTML 저장
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_str)
    print(f"  [저장] HTML : {html_path}")

    # PDF 변환
    _html_to_pdf(html_path, pdf_path)
    print(f"  [저장] PDF  : {pdf_path}")

    return jsonify({
        "ok":        True,
        "html_path": html_path,
        "pdf_path":  pdf_path,
    })


if __name__ == "__main__":
    print(f"{'='*50}")
    print(f"  보고서 서버 시작  →  http://127.0.0.1:{PORT}")
    print(f"  종료: Ctrl+C")
    print(f"{'='*50}")
    app.run(host="127.0.0.1", port=PORT, debug=False)
