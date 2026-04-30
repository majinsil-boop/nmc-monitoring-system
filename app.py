import streamlit as st
import glob
import json
import os
import re
import tempfile
from datetime import datetime, timedelta
from html import escape

# ══════════════════════════════════════════════════════════════════════════════
# URL 보정
# ══════════════════════════════════════════════════════════════════════════════
def fix_url(raw: str) -> str:
    if not raw or raw == "#": return "#"
    raw = raw.strip()
    if raw.startswith(("http://", "https://")): return raw
    return "https://" + raw

def get_link(record: dict, *keys) -> str:
    for k in keys:
        v = record.get(k, "")
        if v and v != "#": return fix_url(v)
    return "#"

# ══════════════════════════════════════════════════════════════════════════════
# gerate_report 의 HTML 빌더 (그대로 가져옴)
# ══════════════════════════════════════════════════════════════════════════════
_URGENT_NEWS_KW = {"응급의료", "응급실", "닥터헬기", "중증외상", "구급", "응급실 뺑뺑이"}
_NORMAL_NEWS_KW = {"필수의료", "공공보건의료법", "구조", "외상"}

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

def _is_notice_active(notice: str) -> bool:
    if not notice: return False
    m = re.search(r"~\s*(\d{4}-\d{2}-\d{2})", notice)
    if not m: return True
    try:
        end_date = datetime.strptime(m.group(1), "%Y-%m-%d")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return end_date >= today
    except ValueError:
        return True

def _importance_assembly(item: dict) -> str:
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
    if kw in _URGENT_NEWS_KW: return "중요"
    if kw in _NORMAL_NEWS_KW: return "보통"
    return "참고"

def _dedup_assembly(items):
    seen, out = set(), []
    for r in items:
        key = r.get("bill_no") or r.get("bill_name", "")
        if key and key not in seen:
            seen.add(key); out.append(r)
    return out

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

def _assembly_still_valid(item: dict) -> bool:
    if _is_notice_active(item.get("legislative_notice", "")): return True
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if (item.get("proposed_date") or "") >= cutoff: return True
    if (item.get("status_changed_date") or "") >= cutoff: return True
    return False

def _build_assembly_section(items) -> str:
    items = [r for r in items if _assembly_still_valid(r)]
    items = _dedup_assembly(items)
    html  = _section_header("의안 현황", len(items), "📋")
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
            lvl     = _importance_assembly(r)
            name    = r.get("bill_name", "").replace(" (새창 열림)", "").strip()
            date    = r.get("proposed_date", "") or r.get("vote_date", "")
            status  = r.get("status", "")
            notice  = r.get("legislative_notice", "")
            summary = r.get("summary", "")
            kw      = r.get("keyword", "")
            url     = fix_url(r.get("url", ""))
            html += f'<div style="{_bar_style(lvl)}">'
            html += '<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px;">'
            html += _badge(lvl)
            html += _tag(kw, "#EAF0FB", "#1B3A6B")
            html += _tag(status, "#F1F3F5", "#555")
            if notice and _is_notice_active(notice):
                html += _tag(notice, "#FFF3CD", "#856404")
            html += '</div>'
            html += f'<div style="font-size:14px;margin-bottom:5px;">{_link(url, name)}</div>'
            if summary:
                html += (f'<div style="font-size:12px;color:#555;line-height:1.5;'
                         f'margin-bottom:5px;padding:6px 8px;background:#F8F9FA;border-radius:3px;">'
                         f'{escape(summary[:200])}{"…" if len(summary) > 200 else ""}</div>')
            html += f'<div style="font-size:11px;color:#888;">발의: {escape(date)}</div>'
            html += '</div>'
    html += _section_footer()
    return html

def _build_schedule_section(items) -> str:
    html = _section_header("주요 일정", len(items), "📅")
    if not items:
        html += _empty("앞으로 14일 내 등록된 회의·공청회·토론회가 없습니다.")
    else:
        for r in items:
            lvl    = _importance_schedule(r)
            title  = r.get("title", "")
            date   = r.get("date", "")
            etype  = r.get("event_type", "")
            source = r.get("source", "")
            url    = fix_url(r.get("url", ""))
            html += f'<div style="{_bar_style(lvl)}">'
            html += '<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px;">'
            html += _badge(lvl)
            html += _tag(etype, "#EAF0FB", "#1B3A6B")
            html += _tag("예정", "#D4EDDA", "#155724")
            html += '</div>'
            html += f'<div style="font-size:14px;margin-bottom:5px;">{_link(url, title)}</div>'
            html += f'<div style="font-size:11px;color:#888;">{escape(date)} &nbsp;·&nbsp; {escape(source)}</div>'
            html += '</div>'
    html += _section_footer()
    return html

def _build_news_section(items) -> str:
    html = _section_header("언론 모니터링", len(items), "📰")
    if not items:
        html += _empty("수집된 관련 기사가 없습니다.")
    else:
        order = {"중요": 0, "보통": 1, "참고": 2}
        items.sort(key=lambda r: (order.get(_importance_news(r), 9), r.get("date", "")))
        for r in items:
            lvl    = _importance_news(r)
            title  = r.get("title", "")
            kw     = r.get("keyword", "")
            source = r.get("source", "")
            date   = r.get("date", "")[:10]
            url    = fix_url(r.get("url", ""))
            html += f'<div style="{_bar_style(lvl)}">'
            html += '<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px;">'
            html += _badge(lvl)
            html += _tag(kw, "#EAF0FB", "#1B3A6B")
            html += _tag(source, "#F8F9FA", "#555")
            html += '</div>'
            html += f'<div style="font-size:14px;margin-bottom:5px;">{_link(url, title)}</div>'
            html += f'<div style="font-size:11px;color:#888;">{escape(date)}</div>'
            html += '</div>'
    html += _section_footer()
    return html

_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"Malgun Gothic","Apple SD Gothic Neo","Noto Sans KR",sans-serif;
     background:#EEF2F9;color:#222;font-size:13px;line-height:1.65}}
.wrap{{max-width:920px;margin:0 auto;padding-bottom:48px}}
a{{color:#1B3A6B;text-decoration:none}}
</style>
</head>
<body>
<div class="wrap">
<div style="background:linear-gradient(135deg,#1B3A6B 0%,#2A5298 100%);
            color:#fff;padding:30px 28px 22px;border-radius:0 0 10px 10px;margin-bottom:22px;">
  <div style="font-size:11px;letter-spacing:2.5px;opacity:.7;margin-bottom:8px;">
    응급의료정책팀 &nbsp;|&nbsp; 자동 모니터링 보고서
  </div>
  <div style="font-size:23px;font-weight:700;margin-bottom:6px;">{title}</div>
  <div style="font-size:12px;opacity:.75;">기준일: {base_date} &nbsp;·&nbsp; 생성: {generated_at}</div>
</div>
<div style="display:flex;gap:12px;flex-wrap:wrap;padding:0 16px;margin-bottom:8px;">
  {cards}
</div>
<div style="padding:0 16px;">
  {sections}
</div>
<div style="text-align:center;font-size:11px;color:#bbb;margin-top:36px;padding:0 16px;">
  본 보고서는 자동 수집 결과입니다. 중요 사항은 반드시 원문 링크로 확인하십시오.
</div>
</div>
</body>
</html>
"""

def build_html(sel_a, sel_s, sel_n, today) -> str:
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    title     = f"의료정책 모니터링 보고서 ({today})"
    asm_dedup = _dedup_assembly(sel_a)
    asm_urgent = sum(1 for r in asm_dedup if _importance_assembly(r) == "중요")
    news_urg   = sum(1 for r in sel_n if _importance_news(r) == "중요")
    total      = len(asm_dedup) + len(sel_s) + len(sel_n)
    cards = "".join([
        _card("계류 의안", len(asm_dedup), f"중요 {asm_urgent}건", "#1B3A6B"),
        _card("예정 일정", len(sel_s),     "14일 이내",            "#2A5298"),
        _card("언론 기사", len(sel_n),     f"중요 {news_urg}건",   "#1B3A6B"),
        _card("전체 항목", total,           "중복 제거",            "#495057"),
    ])
    sections = (
        _build_assembly_section(sel_a)
        + _build_schedule_section(sel_s)
        + _build_news_section(sel_n)
    )
    return _TEMPLATE.format(
        title        = escape(title),
        base_date    = escape(today),
        generated_at = escape(generated),
        cards        = cards,
        sections     = sections,
    )

# ══════════════════════════════════════════════════════════════════════════════
# PDF 생성 (pdfkit + wkhtmltopdf)
# ══════════════════════════════════════════════════════════════════════════════
def generate_pdf_bytes(sel_a, sel_s, sel_n, today) -> bytes:
    import pdfkit
    html_str = build_html(sel_a, sel_s, sel_n, today)
    options = {
        "encoding": "UTF-8",
        "quiet": "",
        "page-size": "A4",
        "margin-top":    "10mm",
        "margin-bottom": "10mm",
        "margin-left":   "12mm",
        "margin-right":  "12mm",
        "enable-local-file-access": "",
    }
    # wkhtmltopdf 경로
    wk_path = None
    for p in ["/usr/bin/wkhtmltopdf", "/usr/local/bin/wkhtmltopdf"]:
        if os.path.exists(p):
            wk_path = p; break

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        tmp_path = f.name

    try:
        if wk_path:
            config = pdfkit.configuration(wkhtmltopdf=wk_path)
            pdfkit.from_string(html_str, tmp_path, configuration=config, options=options)
        else:
            pdfkit.from_string(html_str, tmp_path, options=options)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ══════════════════════════════════════════════════════════════════════════════
# 데이터 로드
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _load_data(pattern):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files = sorted(glob.glob(os.path.join(current_dir, pattern)))
    if not files: return []
    try:
        with open(files[-1], encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

asm_raw  = _load_data("assembly_results_*.json")
sch_raw  = _load_data("schedule_results_*.json")
news_raw = _load_data("news_results_*.json")

if "phase" not in st.session_state:
    st.session_state.phase = "SELECT"

# ══════════════════════════════════════════════════════════════════════════════
# [A] 선택 화면
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 정책 모니터링 보고서 생성기")
    sel_a, sel_s, sel_n = [], [], []

    st.subheader("❶ 의안 현황")
    if not asm_raw: st.info("의안 데이터가 없습니다.")
    for i, r in enumerate(asm_raw):
        link = get_link(r, "url", "bill_link", "link")
        c1, c2 = st.columns([0.82, 0.18])
        with c1:
            if st.checkbox(f"[{r.get('status','접수')}] {r.get('bill_name','')}", key=f"a{i}"):
                sel_a.append(r)
        with c2:
            if link != "#":
                st.markdown(f'<a href="{link}" target="_blank" style="font-size:13px;color:#1B3A6B;text-decoration:none;">🔗 원문보기</a>', unsafe_allow_html=True)

    st.write("---")
    st.subheader("❷ 주요 일정")
    if not sch_raw: st.info("일정 데이터가 없습니다.")
    for i, r in enumerate(sch_raw):
        link = get_link(r, "url", "link")
        c1, c2 = st.columns([0.82, 0.18])
        with c1:
            if st.checkbox(f"📅 [{r.get('date','')}] {r.get('title','')}", key=f"s{i}"):
                sel_s.append(r)
        with c2:
            if link != "#":
                st.markdown(f'<a href="{link}" target="_blank" style="font-size:13px;color:#1B3A6B;text-decoration:none;">🔗 원문보기</a>', unsafe_allow_html=True)

    st.write("---")
    st.subheader("❸ 언론 모니터링")
    if not news_raw: st.info("뉴스 데이터가 없습니다.")
    for i, r in enumerate(news_raw):
        link = get_link(r, "url", "link")
        c1, c2 = st.columns([0.82, 0.18])
        with c1:
            if st.checkbox(f"📰 [{r.get('source','')}] {r.get('title','')}", key=f"n{i}"):
                sel_n.append(r)
        with c2:
            if link != "#":
                st.markdown(f'<a href="{link}" target="_blank" style="font-size:13px;color:#1B3A6B;text-decoration:none;">🔗 기사보기</a>', unsafe_allow_html=True)

    st.write("---")
    if st.button("✨ 보고서 발행", use_container_width=True):
        st.session_state.sel_a = sel_a
        st.session_state.sel_s = sel_s
        st.session_state.sel_n = sel_n
        st.session_state.pdf_ready = False
        st.session_state.phase = "REPORT"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# [B] 보고서 화면
# ══════════════════════════════════════════════════════════════════════════════
else:
    today = datetime.now().strftime("%Y-%m-%d")

    if st.sidebar.button("🔙 다시 선택하기"):
        st.session_state.phase = "SELECT"
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📥 PDF 저장")

    if st.sidebar.button("📄 PDF 생성하기", use_container_width=True):
        with st.spinner("PDF 생성 중..."):
            try:
                pdf_bytes = generate_pdf_bytes(
                    st.session_state.get("sel_a", []),
                    st.session_state.get("sel_s", []),
                    st.session_state.get("sel_n", []),
                    today,
                )
                st.session_state.pdf_bytes = pdf_bytes
                st.session_state.pdf_ready = True
            except Exception as e:
                st.sidebar.error(f"PDF 생성 실패: {e}")

    if st.session_state.get("pdf_ready"):
        st.sidebar.download_button(
            label="⬇️ PDF 다운로드",
            data=st.session_state.pdf_bytes,
            file_name=f"응급의료_모니터링_{today.replace('-','')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    if not (st.session_state.get("sel_a") or st.session_state.get("sel_s") or st.session_state.get("sel_n")):
        st.warning("선택된 항목이 없습니다. '다시 선택하기'를 눌러 항목을 체크해 주세요.")
        st.stop()

    st.markdown(
        "<style>[data-testid='stHeader']{display:none}"
        "@media print{header,footer,.stButton,[data-testid='stSidebar']{display:none!important}"
        ".main{padding:0!important}}</style>",
        unsafe_allow_html=True,
    )

    # 화면 렌더링 (HTML 그대로)
    sel_a = st.session_state.get("sel_a", [])
    sel_s = st.session_state.get("sel_s", [])
    sel_n = st.session_state.get("sel_n", [])
    html  = build_html(sel_a, sel_s, sel_n, today)
    st.markdown(html, unsafe_allow_html=True)
