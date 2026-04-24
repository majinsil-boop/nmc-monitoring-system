import streamlit as st
import glob
import json
import os
import base64
from datetime import datetime
from html import escape

# ── URL 보정 헬퍼 ──────────────────────────────────────────────────────────────
def fix_url(raw: str) -> str:
    if not raw or raw == "#":
        return "#"
    raw = raw.strip()
    if raw.startswith(("http://", "https://")):
        return raw
    return "https://" + raw

def get_link(record: dict, *keys) -> str:
    for k in keys:
        v = record.get(k, "")
        if v and v != "#":
            return fix_url(v)
    return "#"

# ── PDF HTML 빌더 ──────────────────────────────────────────────────────────────
def build_pdf_html(sel_a, sel_s, sel_n, today):
    na, ns, nn = len(sel_a), len(sel_s), len(sel_n)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'Noto Sans CJK KR', 'Noto Sans KR', sans-serif;
  background: #fff;
  font-size: 11px;
  color: #222;
  line-height: 1.6;
  padding: 20px 24px;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
a {{ color: #1B3A6B; text-decoration: none; }}

.header {{
  background: linear-gradient(135deg, #1B3A6B 0%, #2A5298 100%);
  color: #fff;
  padding: 18px 24px;
  border-radius: 10px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 16px;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
.header .team  {{ font-size: 9px; opacity: 0.8; margin-bottom: 4px; }}
.header .title {{ font-size: 20px; font-weight: 800; }}
.header .date  {{ font-size: 18px; font-weight: 800; text-align: right; }}
.header .time  {{ font-size: 10px; opacity: 0.75; margin-top: 2px; text-align: right; }}

.cards {{ display: flex; gap: 10px; margin-bottom: 16px; }}
.card {{
  flex: 1; border-radius: 10px; padding: 12px 8px;
  text-align: center;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}}
.card .icon  {{ font-size: 16px; }}
.card .label {{ font-size: 10px; font-weight: 700; margin-top: 3px; }}
.card .num   {{ font-size: 22px; font-weight: 800; margin-top: 2px; }}

.sec-title {{
  font-size: 14px; font-weight: 800; color: #1B3A6B;
  margin: 14px 0 8px;
  display: flex; justify-content: space-between; align-items: center;
}}
.sec-count {{
  background: #1B3A6B; color: #fff; font-size: 10px;
  padding: 2px 10px; border-radius: 12px; font-weight: 700;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}}

.item {{
  background: #fff; border: 1px solid #E2E8F0; border-radius: 8px;
  padding: 12px 14px; margin-bottom: 8px;
  page-break-inside: avoid;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}}
.item-blue  {{ border-left: 6px solid #1B3A6B; }}
.item-green {{ border-left: 6px solid #28A745; }}
.item-red   {{ border-left: 6px solid #DC3545; }}

.tag {{
  display: inline-block; padding: 2px 8px; border-radius: 4px;
  font-size: 9px; font-weight: 700; margin-right: 4px; margin-bottom: 4px;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}}
.tag-navy   {{ background: #1B3A6B; color: #fff; }}
.tag-yellow {{ background: #FFF9E6; border: 1px solid #FFD966; color: #856404; }}
.tag-green  {{ background: #E8F5E9; color: #1B5E20; }}

.item-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }}
.item-name   {{ font-size: 12px; font-weight: 800; color: #1B3A6B; flex: 1; padding-right: 8px; }}
.item-meta   {{ font-size: 9px; color: #777; margin-top: 3px; }}
.item-summary {{
  font-size: 10px; color: #444; line-height: 1.5;
  background: #F8F9FA; padding: 6px 8px; border-radius: 4px; margin-top: 6px;
}}

.row-flex {{ display: flex; justify-content: space-between; align-items: center; }}
.row-right {{ font-size: 11px; font-weight: 800; white-space: nowrap; margin-left: 10px; }}

.footer {{
  text-align: center; font-size: 9px; color: #aaa;
  margin-top: 24px; padding-top: 10px; border-top: 1px solid #eee;
  display: flex; justify-content: space-between;
}}
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="team">응급의료정책연구팀</div>
    <div class="title">응급의료 동향 모니터링</div>
  </div>
  <div>
    <div class="date">{today}</div>
    <div class="time">08:30 생성</div>
  </div>
</div>

<div class="cards">
  <div class="card" style="background:#EBF1F9;">
    <div class="icon">📋</div><div class="label">계류 의안</div>
    <div class="num" style="color:#1B3A6B;">{na}</div>
  </div>
  <div class="card" style="background:#E8F5E9;">
    <div class="icon">📅</div><div class="label">예정 일정</div>
    <div class="num" style="color:#28A745;">{ns}</div>
  </div>
  <div class="card" style="background:#FDECEA;">
    <div class="icon">📰</div><div class="label">언론 기사</div>
    <div class="num" style="color:#DC3545;">{nn}</div>
  </div>
  <div class="card" style="background:#F3F4F6;">
    <div class="icon">📊</div><div class="label">전체</div>
    <div class="num" style="color:#495057;">{na+ns+nn}</div>
  </div>
</div>
"""

    # ❶ 의안
    if sel_a:
        html += f'<div class="sec-title">❶ 의안 현황 <span class="sec-count">총 {na}건</span></div>'
        for r in sel_a:
            link   = get_link(r, "url", "bill_link", "link")
            name   = escape(r.get("bill_name", ""))
            summ   = escape(r.get("summary", ""))
            notice = escape(r.get("legislative_notice", ""))
            kw     = escape(r.get("keyword", ""))
            status = escape(r.get("status", "접수"))
            date   = escape(r.get("proposed_date", ""))
            html += f"""
<div class="item item-blue">
  <div class="item-header">
    <div class="item-name"><a href="{link}">{name}</a></div>
    <span class="tag tag-navy">{status}</span>
  </div>
  <div>
    <span class="tag tag-navy">{kw}</span>
    {f'<span class="tag tag-yellow">{notice}</span>' if notice else ''}
  </div>
  <div class="item-meta">발의: {date}</div>
  {f'<div class="item-summary">{summ}</div>' if summ else ''}
</div>"""

    # ❷ 일정
    if sel_s:
        html += f'<div class="sec-title">❷ 주요 일정 <span class="sec-count">총 {ns}건</span></div>'
        for r in sel_s:
            link   = get_link(r, "url", "link")
            title  = escape(r.get("title", ""))
            date   = escape(r.get("date", ""))
            etype  = escape(r.get("event_type", "토론회"))
            source = escape(r.get("source", ""))
            html += f"""
<div class="item item-green">
  <div class="row-flex">
    <div style="flex:1;">
      <div style="font-size:12px; font-weight:800; color:#333; margin-bottom:4px;">
        <a href="{link}">{title}</a>
      </div>
      <span class="tag tag-green">{etype}</span>
      <span class="tag tag-green">예정</span>
      <div class="item-meta">{source}</div>
    </div>
    <div class="row-right">{date}</div>
  </div>
</div>"""

    # ❸ 뉴스
    if sel_n:
        KW_COLOR = {"중증응급": "#800000", "중증외상": "#6F42C1", "상급종합병원": "#A52A2A"}
        html += f'<div class="sec-title">❸ 언론 모니터링 <span class="sec-count">총 {nn}건</span></div>'
        for r in sel_n:
            link   = get_link(r, "url", "link")
            title  = escape(r.get("title", ""))
            source = escape(r.get("source", ""))
            date   = escape(r.get("date", ""))
            kw     = r.get("keyword", "응급의료")
            c_hex  = KW_COLOR.get(kw, "#DC3545")
            kw_esc = escape(kw)
            html += f"""
<div class="item item-red">
  <div class="row-flex">
    <div style="flex:1;">
      <div style="font-size:12px; font-weight:800; color:#1B3A6B; margin-bottom:3px;">
        <a href="{link}">{title}</a>
      </div>
      <div class="item-meta">{source} | {date}</div>
    </div>
    <span class="tag" style="background:{c_hex}; color:#fff; margin-left:10px;">{kw_esc}</span>
  </div>
</div>"""

    html += f"""
<div class="footer">
  <span>본 보고서는 자동 수집·검토된 항목만 포함됩니다. 중요 사항은 반드시 원문을 확인하십시오.</span>
  <span>응급의료정책연구팀</span>
</div>
</body></html>"""
    return html


def generate_pdf_bytes(sel_a, sel_s, sel_n, today) -> bytes:
    from weasyprint import HTML
    html_str = build_pdf_html(sel_a, sel_s, sel_n, today)
    return HTML(string=html_str).write_pdf()


# ── 데이터 로드 ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _load_data(pattern):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files = sorted(glob.glob(os.path.join(current_dir, pattern)))
    if not files:
        return []
    try:
        with open(files[-1], encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

asm_raw  = _load_data("assembly_results_*.json")
sch_raw  = _load_data("schedule_results_*.json")
news_raw = _load_data("news_results_*.json")

# ── 세션 초기화 ────────────────────────────────────────────────────────────────
if "phase" not in st.session_state:
    st.session_state.phase = "SELECT"

# ══════════════════════════════════════════════════════════════════════════════
# [A] 선택 화면
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 정책 모니터링 보고서 생성기")

    sel_a, sel_s, sel_n = [], [], []

    st.subheader("❶ 의안 현황")
    if not asm_raw:
        st.info("의안 데이터가 없습니다.")
    for i, r in enumerate(asm_raw):
        link = get_link(r, "url", "bill_link", "link")
        col_t, col_l = st.columns([0.8, 0.2])
        with col_t:
            if st.checkbox(
                f"[{r.get('status', '접수')}] {r.get('bill_name', '')}",
                key=f"check_a_{i}"
            ):
                sel_a.append(r)
        with col_l:
            if link != "#":
                st.markdown(f"[🔗 원문보기]({link})")

    st.write("---")

    st.subheader("❷ 주요 일정")
    if not sch_raw:
        st.info("일정 데이터가 없습니다.")
    for i, r in enumerate(sch_raw):
        link = get_link(r, "url", "link")
        col_t, col_l = st.columns([0.8, 0.2])
        with col_t:
            if st.checkbox(
                f"📅 [{r.get('date', '')}] {r.get('title', '')}",
                key=f"check_s_{i}"
            ):
                sel_s.append(r)
        with col_l:
            if link != "#":
                st.markdown(f"[🔗 원문보기]({link})")

    st.write("---")

    st.subheader("❸ 언론 모니터링")
    if not news_raw:
        st.info("뉴스 데이터가 없습니다.")
    for i, r in enumerate(news_raw):
        link = get_link(r, "url", "link")
        col_t, col_l = st.columns([0.8, 0.2])
        with col_t:
            if st.checkbox(
                f"📰 [{r.get('source', '')}] {r.get('title', '')}",
                key=f"check_n_{i}"
            ):
                sel_n.append(r)
        with col_l:
            if link != "#":
                st.markdown(f"[🔗 기사보기]({link})")

    st.write("---")
    if st.button("✨ 보고서 발행 (클릭 시 화면이 바뀝니다)", use_container_width=True):
        st.session_state.sel_a = sel_a
        st.session_state.sel_s = sel_s
        st.session_state.sel_n = sel_n
        st.session_state.phase = "REPORT"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# [B] 보고서 화면
# ══════════════════════════════════════════════════════════════════════════════
else:
    today = datetime.now().strftime("%Y-%m-%d")

    # 사이드바
    if st.sidebar.button("🔙 다시 선택하기"):
        st.session_state.phase = "SELECT"
        st.rerun()

    # PDF 저장 버튼 (사이드바)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📥 PDF 저장")
    if st.sidebar.button("PDF 생성하기", use_container_width=True):
        with st.sidebar:
            with st.spinner("PDF 생성 중..."):
                try:
                    pdf_bytes = generate_pdf_bytes(
                        st.session_state.get("sel_a", []),
                        st.session_state.get("sel_s", []),
                        st.session_state.get("sel_n", []),
                        today
                    )
                    st.session_state.pdf_bytes = pdf_bytes
                    st.session_state.pdf_ready = True
                except Exception as e:
                    st.error(f"PDF 생성 실패: {e}")

    if st.session_state.get("pdf_ready"):
        filename = f"응급의료_모니터링_{today.replace('-','')}.pdf"
        st.sidebar.download_button(
            label="⬇️ PDF 다운로드",
            data=st.session_state.pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True
        )

    # 방어 로직
    if not (st.session_state.get("sel_a") or
            st.session_state.get("sel_s") or
            st.session_state.get("sel_n")):
        st.warning("선택된 항목이 없습니다. '다시 선택하기'를 눌러 항목을 체크해 주세요.")
        st.stop()

    st.markdown(
        "<style>"
        "[data-testid='stHeader'] { display: none; }"
        "@media print {"
        "  header, footer, .stButton, [data-testid='stSidebar'] { display: none !important; }"
        "  .main { padding: 0 !important; }"
        "}"
        "</style>",
        unsafe_allow_html=True
    )

    # ── 보고서 HTML 렌더링 ────────────────────────────────────────────────────
    na = len(st.session_state.get("sel_a", []))
    ns = len(st.session_state.get("sel_s", []))
    nn = len(st.session_state.get("sel_n", []))

    html = '<div style="background:#FBFBFB; padding:20px; font-family:sans-serif;">'

    # 헤더
    html += (
        f'<div style="background:#1B3A6B; color:#fff; padding:20px 30px; '
        f'display:flex; justify-content:space-between; align-items:flex-end; '
        f'-webkit-print-color-adjust:exact; border-radius:10px;">'
        f'<div>'
        f'<div style="font-size:10px; opacity:0.8;">응급의료정책연구팀</div>'
        f'<div style="font-size:22px; font-weight:800;">응급의료 동향 모니터링</div>'
        f'</div>'
        f'<div style="text-align:right;">'
        f'<div style="font-size:18px; font-weight:800;">{today}</div>'
        f'</div></div>'
    )

    # 요약 카드
    html += '<div style="display:flex; gap:10px; padding:15px 0;">'
    for icon, label, val, bg, fc in [
        ("📋", "계류 의안", na, "#EBF1F9", "#1B3A6B"),
        ("📅", "예정 일정", ns, "#E8F5E9", "#28A745"),
        ("📰", "언론 기사", nn, "#FDECEA", "#DC3545"),
        ("📊", "전체",      na+ns+nn, "#F3F4F6", "#495057"),
    ]:
        html += (
            f'<div style="flex:1; background:{bg}; border-radius:10px; padding:12px; '
            f'display:flex; flex-direction:column; align-items:center; justify-content:center; '
            f'gap:5px; -webkit-print-color-adjust:exact;">'
            f'<div style="font-size:18px;">{icon}</div>'
            f'<div style="font-size:11px; font-weight:700;">{label}</div>'
            f'<div style="font-size:24px; font-weight:800; color:{fc};">{val}</div>'
            f'</div>'
        )
    html += '</div>'

    # ❶ 의안
    if st.session_state.get("sel_a"):
        html += f'<div style="margin:10px 0; font-size:16px; font-weight:800; color:#1B3A6B; display:flex; justify-content:space-between; align-items:center;">❶ 의안 현황 <span style="background:#1B3A6B;color:#fff;font-size:11px;padding:2px 12px;border-radius:12px;">총 {na}건</span></div>'
        for r in st.session_state.sel_a:
            link   = get_link(r, "url", "bill_link", "link")
            name   = escape(r.get("bill_name", ""))
            summ   = escape(r.get("summary", ""))
            notice = escape(r.get("legislative_notice", ""))
            kw     = escape(r.get("keyword", ""))
            status = escape(r.get("status", "접수"))
            a_tag  = f'<a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration:none; font-size:14px; font-weight:800; color:#1B3A6B;">{name} 🔗</a>'
            html += (
                f'<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #1B3A6B; '
                f'padding:15px; border-radius:12px; margin-bottom:10px; -webkit-print-color-adjust:exact;">'
                f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">'
                f'{a_tag}'
                f'<div style="background:#1B3A6B; color:#fff; padding:2px 10px; border-radius:12px; font-size:10px;">{status}</div>'
                f'</div>'
                f'<div style="margin-bottom:6px;">'
                f'<span style="background:#1B3A6B;color:#fff;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;margin-right:4px;">{kw}</span>'
                + (f'<span style="background:#FFF9E6;border:1px solid #FFD966;color:#856404;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;">{notice}</span>' if notice else '')
                + f'</div>'
                f'<div style="font-size:11px; color:#444; line-height:1.5; background:#F8F9FA; padding:8px; border-radius:4px;">{summ}</div>'
                f'</div>'
            )

    # ❷ 일정
    if st.session_state.get("sel_s"):
        html += f'<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B; display:flex; justify-content:space-between; align-items:center;">❷ 주요 일정 <span style="background:#1B3A6B;color:#fff;font-size:11px;padding:2px 12px;border-radius:12px;">총 {ns}건</span></div>'
        for r in st.session_state.sel_s:
            link   = get_link(r, "url", "link")
            title  = escape(r.get("title", ""))
            date   = escape(r.get("date", ""))
            etype  = escape(r.get("event_type", "토론회"))
            source = escape(r.get("source", ""))
            a_tag  = f'<a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration:none; font-size:13px; font-weight:800; color:#333;">{title} 🔗</a>'
            html += (
                f'<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #28A745; '
                f'padding:12px 15px; margin-bottom:8px; display:flex; justify-content:space-between; '
                f'align-items:center; -webkit-print-color-adjust:exact;">'
                f'<div>{a_tag}'
                f'<div style="margin-top:4px;">'
                f'<span style="background:#E8F5E9;color:#1B5E20;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700;">{etype}</span>&nbsp;'
                f'<span style="background:#E8F5E9;color:#1B5E20;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700;">예정</span>'
                f'<div style="font-size:10px;color:#777;margin-top:2px;">{source}</div>'
                f'</div></div>'
                f'<div style="font-size:12px; font-weight:800; margin-left:12px;">{date}</div>'
                f'</div>'
            )

    # ❸ 뉴스
    if st.session_state.get("sel_n"):
        KW_COLOR = {"중증응급": "#800000", "중증외상": "#6F42C1", "상급종합병원": "#A52A2A"}
        html += f'<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B; display:flex; justify-content:space-between; align-items:center;">❸ 언론 모니터링 <span style="background:#1B3A6B;color:#fff;font-size:11px;padding:2px 12px;border-radius:12px;">총 {nn}건</span></div>'
        for r in st.session_state.sel_n:
            link   = get_link(r, "url", "link")
            title  = escape(r.get("title", ""))
            source = escape(r.get("source", ""))
            date   = escape(r.get("date", ""))
            kw     = r.get("keyword", "응급의료")
            c_hex  = KW_COLOR.get(kw, "#DC3545")
            kw_esc = escape(kw)
            a_tag  = f'<a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration:none; font-size:13px; font-weight:800; color:#1B3A6B;">{title} 🔗</a>'
            html += (
                f'<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #DC3545; '
                f'padding:12px 15px; margin-bottom:8px; display:flex; justify-content:space-between; '
                f'align-items:center; -webkit-print-color-adjust:exact;">'
                f'<div>{a_tag}'
                f'<div style="font-size:10px; color:#777; margin-top:3px;">{source} | {date}</div>'
                f'</div>'
                f'<div style="background:{c_hex}; color:#fff; padding:2px 10px; border-radius:12px; '
                f'font-size:10px; font-weight:700; white-space:nowrap; margin-left:10px;">{kw_esc}</div>'
                f'</div>'
            )

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
