"""
통합 모니터링 보고서 생성기
1. assembly_search.py → schedule_search.py → news_monitor.py 순서대로 실행
2. 각 결과 JSON을 읽어 네이비 공문서 스타일 HTML 보고서 생성
3. 보고서_YYYYMMDD.html 저장 후 브라우저 자동 오픈

사용법:
  python generate_report.py            # 세 스크립트 실행 후 보고서 생성
  python generate_report.py --no-run   # 기존 최신 결과 파일로 보고서만 생성
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from html import escape

BASE_DIR = os.path.expanduser("~")

# ── 스크립트 실행 ─────────────────────────────────────────────────────────────

def _run_script(name: str) -> bool:
    path = os.path.join(BASE_DIR, name)
    print(f"\n{'='*60}")
    print(f"▶ {name} 실행 중...")
    print(f"{'='*60}")
    result = subprocess.run(
        [sys.executable, path],
        cwd=BASE_DIR,
    )
    ok = result.returncode == 0
    status = "완료" if ok else f"오류 (종료코드 {result.returncode})"
    print(f"[{status}] {name}")
    return ok


def run_all_scripts():
    for script in ["assembly_search.py", "schedule_search.py", "news_monitor.py"]:
        _run_script(script)


# ── 파일 탐색 & 로드 ──────────────────────────────────────────────────────────

def _latest(pattern: str) -> str | None:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def _load(path: str | None) -> list[dict]:
    if not path or not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _find_files() -> tuple[str | None, str | None, str | None]:
    asm  = _latest(os.path.join(BASE_DIR, "assembly_results_*.json"))
    sch  = _latest(os.path.join(BASE_DIR, "schedule_results_*.json"))
    news = _latest(os.path.join(BASE_DIR, "news_results_*.json"))
    return asm, sch, news


# ── 중요도 판단 ───────────────────────────────────────────────────────────────

_URGENT_NEWS_KW = {"응급의료", "응급실", "닥터헬기", "중증외상", "구급", "응급실 뺑뺑이"}
_NORMAL_NEWS_KW = {"필수의료", "공공보건의료법", "구조", "외상"}


def _is_notice_active(notice: str) -> bool:
    """입법예고 종료일이 오늘 이후(당일 포함)이면 True. 날짜 파싱 실패 시 True(안전 포함)."""
    if not notice:
        return False
    m = re.search(r"~\s*(\d{4}-\d{2}-\d{2})", notice)
    if not m:
        return True
    try:
        end_date = datetime.strptime(m.group(1), "%Y-%m-%d")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return end_date >= today
    except ValueError:
        return True


def _importance_assembly(item: dict) -> str:
    # 입법예고 기간 중인 경우만 중요
    if item.get("legislative_notice") and _is_notice_active(item["legislative_notice"]):
        return "중요"
    status = item.get("status", "")
    if any(s in status for s in ("위원회심사", "본회의", "공포")):
        return "중요"
    return "보통"


def _importance_schedule(item: dict) -> str:
    if item.get("is_upcoming"):
        return "중요" if item.get("topic_keyword") else "보통"
    return "참고"


def _importance_news(item: dict) -> str:
    kw = item.get("keyword", "")
    if kw in _URGENT_NEWS_KW:
        return "중요"
    if kw in _NORMAL_NEWS_KW:
        return "보통"
    return "참고"


# ── 의안 중복 제거 ────────────────────────────────────────────────────────────

def _dedup_assembly(items: list[dict]) -> list[dict]:
    seen, out = set(), []
    for r in items:
        key = r.get("bill_no") or r.get("bill_name", "")
        if key and key not in seen:
            seen.add(key)
            out.append(r)
    return out


# ── HTML 헬퍼 ─────────────────────────────────────────────────────────────────

_BADGE_STYLE = {
    "중요": "background:#DC3545;color:#fff;",
    "보통": "background:#E07B00;color:#fff;",
    "참고": "background:#6C757D;color:#fff;",
}
_BAR_COLOR = {
    "중요": "#DC3545",
    "보통": "#E07B00",
    "참고": "#ADB5BD",
}


def _badge(level: str) -> str:
    style = _BADGE_STYLE.get(level, "background:#6C757D;color:#fff;")
    return (f'<span style="{style}padding:2px 9px;border-radius:3px;'
            f'font-size:11px;font-weight:700;letter-spacing:.5px;white-space:nowrap;">'
            f'{escape(level)}</span>')


def _tag(text: str, bg: str, fg: str) -> str:
    return (f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:3px;font-size:11px;white-space:nowrap;">'
            f'{escape(text)}</span>')


def _bar_style(level: str) -> str:
    color = _BAR_COLOR.get(level, "#ADB5BD")
    return (f'border-left:5px solid {color};padding:11px 14px;margin-bottom:8px;'
            f'background:#fff;border-radius:0 4px 4px 0;'
            f'box-shadow:0 1px 3px rgba(0,0,0,.07);')


def _link(url: str, text: str) -> str:
    t = escape(text or "")
    if url:
        return (f'<a href="{escape(url)}" target="_blank" '
                f'style="color:#1B3A6B;text-decoration:none;font-weight:600;">{t}</a>')
    return f'<span style="font-weight:600;">{t}</span>'


def _section_header(title: str, count: int, icon: str = "") -> str:
    return (
        f'<div style="background:#1B3A6B;color:#fff;padding:10px 18px;'
        f'border-radius:5px 5px 0 0;margin-top:28px;'
        f'display:flex;align-items:center;justify-content:space-between;">'
        f'<span style="font-size:15px;font-weight:700;">{icon}&nbsp;{escape(title)}</span>'
        f'<span style="background:rgba(255,255,255,.2);padding:2px 12px;'
        f'border-radius:20px;font-size:12px;">총 {count}건</span>'
        f'</div>'
        f'<div style="border:1px solid #D0D7E5;border-top:none;'
        f'border-radius:0 0 5px 5px;padding:14px 14px 6px;">'
    )


def _section_footer() -> str:
    return "</div>"


def _empty(msg: str = "해당 기간 내 수집된 항목이 없습니다.") -> str:
    return f'<p style="color:#999;font-size:13px;padding:8px 0;margin:0;">{escape(msg)}</p>'


# ── 섹션 빌더 ─────────────────────────────────────────────────────────────────

def _assembly_still_valid(item: dict) -> bool:
    """
    보고서 표시 시점에서도 유효한 의안인지 확인.
    파일 생성 이후 기준일이 지난 항목을 걸러낸다.
    """
    if _is_notice_active(item.get("legislative_notice", "")):
        return True
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if (item.get("proposed_date") or "") >= cutoff:
        return True
    if (item.get("status_changed_date") or "") >= cutoff:
        return True
    return False


def _build_assembly_section(items: list[dict]) -> str:
    items = [r for r in items if _assembly_still_valid(r)]
    items = _dedup_assembly(items)
    html  = _section_header("의안 현황 (국회의안정보시스템)", len(items), "📋")

    if not items:
        html += _empty()
    else:
        order = {"중요": 0, "보통": 1, "참고": 2}
        items.sort(key=lambda r: (
            order.get(_importance_assembly(r), 9),
            "0" if r.get("legislative_notice") else "1",
            r.get("proposed_date", "") or "0000-00-00",
        ))

        for r in items:
            lvl    = _importance_assembly(r)
            name   = r.get("bill_name", "").replace(" (새창 열림)", "").strip()
            date   = r.get("proposed_date", "") or r.get("vote_date", "")
            status = r.get("status", "")
            chg    = r.get("status_changed_date", "")
            notice = r.get("legislative_notice", "")
            summary= r.get("summary", "")
            kw     = r.get("keyword", "")
            url    = r.get("url", "")

            html += f'<div style="{_bar_style(lvl)}">'

            # 배지 행
            html += '<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px;">'
            html += _badge(lvl)
            html += _tag(kw, "#EAF0FB", "#1B3A6B")
            html += _tag(status, "#F1F3F5", "#555")
            if notice and _is_notice_active(notice):
                html += _tag(notice, "#FFF3CD", "#856404")
            html += '</div>'

            # 의안명 링크
            html += f'<div style="font-size:14px;margin-bottom:5px;">{_link(url, name)}</div>'

            # 요약
            if summary:
                html += (f'<div style="font-size:12px;color:#555;line-height:1.5;'
                         f'margin-bottom:5px;padding:6px 8px;background:#F8F9FA;'
                         f'border-radius:3px;">'
                         f'{escape(summary[:200])}{"…" if len(summary) > 200 else ""}</div>')

            # 메타
            meta = f'발의: {escape(date)}'
            if chg and chg != date:
                meta += f' &nbsp;·&nbsp; 심사변경: {escape(chg)}'
            html += f'<div style="font-size:11px;color:#888;">{meta}</div>'
            html += '</div>'

    html += _section_footer()
    return html


def _build_schedule_section(items: list[dict]) -> str:
    html = _section_header("일정 현황 (보건복지위원회)", len(items), "📅")

    if not items:
        html += _empty("앞으로 14일 내 등록된 회의·공청회·토론회가 없습니다.")
    else:
        order = {"중요": 0, "보통": 1, "참고": 2}
        items.sort(key=lambda r: (
            order.get(_importance_schedule(r), 9),
            r.get("date", ""),
        ))

        for r in items:
            lvl    = _importance_schedule(r)
            title  = r.get("title", "")
            date   = r.get("date", "")
            etype  = r.get("event_type", "")
            topic  = r.get("topic_keyword", "")
            source = r.get("source", "")
            url    = r.get("url", "")

            html += f'<div style="{_bar_style(lvl)}">'
            html += '<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px;">'
            html += _badge(lvl)
            html += _tag(etype, "#EAF0FB", "#1B3A6B")
            html += _tag("예정", "#D4EDDA", "#155724")
            if topic:
                html += _tag(f"★ {topic}", "#FFF3CD", "#856404")
            html += '</div>'
            html += f'<div style="font-size:14px;margin-bottom:5px;">{_link(url, title)}</div>'
            html += f'<div style="font-size:11px;color:#888;">{escape(date)} &nbsp;·&nbsp; {escape(source)}</div>'
            html += '</div>'

    html += _section_footer()
    return html


def _build_news_section(items: list[dict]) -> str:
    html = _section_header("언론 모니터링 (전일 기사)", len(items), "📰")

    if not items:
        html += _empty("전일 수집된 관련 기사가 없습니다.")
    else:
        order = {"중요": 0, "보통": 1, "참고": 2}
        items.sort(key=lambda r: (
            order.get(_importance_news(r), 9),
            r.get("date", ""),
        ))

        for r in items:
            lvl    = _importance_news(r)
            title  = r.get("title", "")
            kw     = r.get("keyword", "")
            source = r.get("source", "")
            date   = r.get("date", "")[:10]
            url    = r.get("url", "")
            summary= r.get("summary", "")

            html += f'<div style="{_bar_style(lvl)}">'
            html += '<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px;">'
            html += _badge(lvl)
            html += _tag(kw, "#EAF0FB", "#1B3A6B")
            html += _tag(source, "#F8F9FA", "#555")
            html += '</div>'
            html += f'<div style="font-size:14px;margin-bottom:5px;">{_link(url, title)}</div>'
            if summary:
                html += (f'<div style="font-size:12px;color:#555;margin-bottom:4px;">'
                         f'{escape(summary[:150])}{"…" if len(summary) > 150 else ""}</div>')
            html += f'<div style="font-size:11px;color:#888;">{escape(date)}</div>'
            html += '</div>'

    html += _section_footer()
    return html


# ── 요약 카드 ─────────────────────────────────────────────────────────────────

def _card(label: str, value: int, sub: str = "", color: str = "#1B3A6B") -> str:
    return (
        f'<div style="flex:1;min-width:130px;background:#fff;border-radius:6px;'
        f'border-top:4px solid {color};padding:14px 16px;'
        f'box-shadow:0 1px 4px rgba(0,0,0,.1);text-align:center;">'
        f'<div style="font-size:28px;font-weight:700;color:{color};">{value}</div>'
        f'<div style="font-size:12px;color:#444;margin-top:3px;">{escape(label)}</div>'
        + (f'<div style="font-size:11px;color:#999;margin-top:2px;">{escape(sub)}</div>' if sub else "")
        + '</div>'
    )


# ── HTML 템플릿 ───────────────────────────────────────────────────────────────

_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"Malgun Gothic","Apple SD Gothic Neo","Noto Sans KR",sans-serif;
     background:#EEF2F9;color:#222;font-size:13px;line-height:1.65}}
.wrap{{max-width:920px;margin:0 auto;padding-bottom:48px}}
a{{color:#1B3A6B;text-decoration:none}}
a:hover{{text-decoration:underline}}
@media print{{
  body{{background:#fff}}
  .wrap{{max-width:100%}}
  .noprint{{display:none}}
}}
</style>
</head>
<body>
<div class="wrap">

<!-- 헤더 -->
<div style="background:linear-gradient(135deg,#1B3A6B 0%,#2A5298 100%);
            color:#fff;padding:30px 28px 22px;border-radius:0 0 10px 10px;
            margin-bottom:22px;">
  <div style="font-size:11px;letter-spacing:2.5px;opacity:.7;margin-bottom:8px;">
    응급의료정책팀 &nbsp;|&nbsp; 자동 모니터링 보고서
  </div>
  <div style="font-size:23px;font-weight:700;margin-bottom:6px;">{title}</div>
  <div style="font-size:12px;opacity:.75;">
    기준일: {base_date} &nbsp;·&nbsp; 생성: {generated_at}
  </div>
</div>

<!-- 요약 카드 -->
<div style="display:flex;gap:12px;flex-wrap:wrap;padding:0 16px;margin-bottom:8px;">
  {cards}
</div>

<!-- 범례 -->
<div class="noprint"
     style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;
            padding:10px 18px;margin:14px 16px 4px;background:#fff;
            border-radius:5px;border:1px solid #D0D7E5;font-size:12px;color:#555;">
  <span style="font-weight:700;color:#1B3A6B;">중요도</span>
  <span><span style="display:inline-block;width:9px;height:9px;border-radius:50%;
        background:#DC3545;vertical-align:middle;margin-right:4px;"></span>
        중요 — 응급의료 직접 관련 / 입법예고 중</span>
  <span><span style="display:inline-block;width:9px;height:9px;border-radius:50%;
        background:#E07B00;vertical-align:middle;margin-right:4px;"></span>
        보통 — 예정 일정 / 관련 키워드</span>
  <span><span style="display:inline-block;width:9px;height:9px;border-radius:50%;
        background:#ADB5BD;vertical-align:middle;margin-right:4px;"></span>
        참고 — 기타</span>
</div>

<!-- 본문 -->
<div style="padding:0 16px;">
  {sections}
</div>

<!-- 푸터 -->
<div style="text-align:center;font-size:11px;color:#bbb;margin-top:36px;padding:0 16px;">
  본 보고서는 자동 수집 결과입니다. 중요 사항은 반드시 원문 링크로 확인하십시오.
</div>

</div>
</body>
</html>
"""


# ── HTML 조립 ─────────────────────────────────────────────────────────────────

def generate_html(asm_path, sch_path, news_path) -> tuple[str, str]:
    assembly_items = _load(asm_path)
    schedule_items = _load(sch_path)
    news_items     = _load(news_path)

    today     = datetime.now().strftime("%Y-%m-%d")
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    title     = f"의료정책 모니터링 보고서 ({today})"

    # 통계
    asm_dedup  = _dedup_assembly(assembly_items)
    asm_cnt    = len(asm_dedup)
    asm_urgent = sum(1 for r in asm_dedup if _importance_assembly(r) == "중요")
    sch_cnt    = len(schedule_items)
    news_cnt   = len(news_items)
    news_urg   = sum(1 for r in news_items if _importance_news(r) == "중요")
    total      = asm_cnt + sch_cnt + news_cnt

    cards = "".join([
        _card("계류 의안",  asm_cnt,  f"중요 {asm_urgent}건", "#1B3A6B"),
        _card("예정 일정",  sch_cnt,  "14일 이내",            "#2A5298"),
        _card("언론 기사",  news_cnt, f"중요 {news_urg}건",   "#1B3A6B"),
        _card("전체 항목",  total,    "중복 제거",             "#495057"),
    ])

    sections = (
        _build_assembly_section(assembly_items)
        + _build_schedule_section(schedule_items)
        + _build_news_section(news_items)
    )

    html = _TEMPLATE.format(
        title      = escape(title),
        base_date  = escape(today),
        generated_at = escape(generated),
        cards      = cards,
        sections   = sections,
    )
    return html, title


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="통합 모니터링 보고서 생성")
    parser.add_argument("--no-run", action="store_true",
                        help="스크립트 실행 없이 기존 최신 파일로 보고서만 생성")
    parser.add_argument("--out", help="출력 파일 경로 직접 지정")
    args = parser.parse_args()

    # 1. 스크립트 실행
    if not args.no_run:
        run_all_scripts()

    # 2. 최신 결과 파일 탐색
    asm_path, sch_path, news_path = _find_files()

    print(f"\n{'='*60}")
    print("보고서 생성")
    print(f"{'='*60}")
    print(f"  의안 파일 : {os.path.basename(asm_path)  if asm_path  else '없음'}")
    print(f"  일정 파일 : {os.path.basename(sch_path)  if sch_path  else '없음'}")
    print(f"  뉴스 파일 : {os.path.basename(news_path) if news_path else '없음'}")

    # 3. HTML 생성
    html, title = generate_html(asm_path, sch_path, news_path)

    # 4. 저장
    today    = datetime.now().strftime("%Y%m%d")
    out_path = args.out or os.path.join(BASE_DIR, f"보고서_{today}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  → 저장 완료: {out_path}")

    # 5. 브라우저 오픈 (Windows)
    try:
        os.startfile(out_path)
    except Exception:
        pass


if __name__ == "__main__":
    main()
