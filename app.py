import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# ── URL 보정 헬퍼 ──────────────────────────────────────────────
def fix_url(raw: str) -> str:
    """프로토콜이 없는 URL에 https:// 를 강제 추가"""
    if not raw or raw == "#":
        return "#"
    raw = raw.strip()
    if raw.startswith(("http://", "https://")):
        return raw
    return "https://" + raw

def get_link(record: dict, *keys) -> str:
    """여러 후보 키를 순서대로 탐색해 첫 번째 유효한 URL 반환"""
    for k in keys:
        v = record.get(k, "")
        if v and v != "#":
            return fix_url(v)
    return "#"

# ── 데이터 로드 ────────────────────────────────────────────────
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

# ── 세션 초기화 ────────────────────────────────────────────────
if "phase" not in st.session_state:
    st.session_state.phase = "SELECT"

# ══════════════════════════════════════════════════════════════
# [A] 선택 화면
# ══════════════════════════════════════════════════════════════
if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 정책 모니터링 보고서 생성기")

    sel_a, sel_s, sel_n = [], [], []

    # ── ❶ 의안 ──────────────────────────────────────────────
    st.subheader("❶ 의안 현황")
    if not asm_raw:
        st.info("의안 데이터가 없습니다.")
    for i, r in enumerate(asm_raw):
        # url → bill_link → link 순으로 탐색
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

    # ── ❷ 일정 ──────────────────────────────────────────────
    st.subheader("❷ 주요 일정")
    if not sch_raw:
        st.info("일정 데이터가 없습니다.")
    for i, r in enumerate(sch_raw):
        # url → link 순으로 탐색
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

    # ── ❸ 뉴스 ──────────────────────────────────────────────
    st.subheader("❸ 언론 모니터링")
    if not news_raw:
        st.info("뉴스 데이터가 없습니다.")
    for i, r in enumerate(news_raw):
        # url → link 순으로 탐색
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

# ══════════════════════════════════════════════════════════════
# [B] 보고서 화면
# ══════════════════════════════════════════════════════════════
else:
    today = datetime.now().strftime("%Y-%m-%d")
    if st.sidebar.button("🔙 다시 선택하기"):
        st.session_state.phase = "SELECT"
        st.rerun()

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
        "  .report-container { transform: scale(0.96); transform-origin: top center; }"
        "}"
        "</style>",
        unsafe_allow_html=True
    )

    html = '<div class="report-container" style="background:#FBFBFB; padding:20px; font-family:sans-serif;">'

    # ── 헤더 ────────────────────────────────────────────────
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

    # ── 요약 카드 ────────────────────────────────────────────
    na = len(st.session_state.sel_a)
    ns = len(st.session_state.sel_s)
    nn = len(st.session_state.sel_n)
    html += '<div style="display:flex; gap:10px; padding:15px 0;">'
    for icon, label, val, bg in [
        ("📋", "의안",  na,        "#EBF1F9"),
        ("📅", "일정",  ns,        "#E8F5E9"),
        ("📰", "뉴스",  nn,        "#FDECEA"),
        ("📊", "전체",  na+ns+nn,  "#F3F4F6"),
    ]:
        html += (
            f'<div style="flex:1; background:{bg}; border-radius:10px; padding:12px; '
            f'display:flex; flex-direction:column; align-items:center; justify-content:center; '
            f'gap:5px; -webkit-print-color-adjust:exact;">'
            f'<div style="font-size:18px;">{icon}</div>'
            f'<div style="font-size:11px; font-weight:700;">{label}</div>'
            f'<div style="font-size:24px; font-weight:800;">{val}</div>'
            f'</div>'
        )
    html += '</div>'

    # ── ❶ 의안 ──────────────────────────────────────────────
    if st.session_state.sel_a:
        html += '<div style="margin:10px 0; font-size:16px; font-weight:800; color:#1B3A6B;">❶ 의안 현황</div>'
        for r in st.session_state.sel_a:
            link = get_link(r, "url", "bill_link", "link")
            name = escape(r.get("bill_name", ""))
            summ = escape(r.get("summary", ""))
            # href 와 내부 속성을 따옴표 충돌 없이 구성
            a_tag = f'<a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration:none; font-size:14px; font-weight:800; color:#1B3A6B;">{name} 🔗</a>'
            html += (
                f'<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #1B3A6B; '
                f'padding:15px; border-radius:12px; margin-bottom:10px; -webkit-print-color-adjust:exact;">'
                f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">'
                f'{a_tag}'
                f'<div style="background:#1B3A6B; color:#fff; padding:2px 10px; border-radius:12px; '
                f'font-size:10px; -webkit-print-color-adjust:exact;">접수</div>'
                f'</div>'
                f'<div style="background:#FFF9E6; border:1px solid #FFD966; color:#856404; padding:3px 10px; '
                f'border-radius:5px; font-size:11px; font-weight:700; margin-bottom:8px; display:inline-block; '
                f'-webkit-print-color-adjust:exact;">입법예고 진행중</div>'
                f'<div style="font-size:11px; color:#444; line-height:1.5;">{summ}</div>'
                f'</div>'
            )

    # ── ❷ 일정 ──────────────────────────────────────────────
    if st.session_state.sel_s:
        html += '<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">❷ 주요 일정</div>'
        for r in st.session_state.sel_s:
            link  = get_link(r, "url", "link")
            title = escape(r.get("title", ""))
            date  = escape(r.get("date", ""))
            a_tag = f'<a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration:none; font-size:13px; font-weight:800; color:#333;">{title} 🔗</a>'
            html += (
                f'<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #28A745; '
                f'padding:12px 15px; margin-bottom:8px; display:flex; justify-content:space-between; '
                f'align-items:center; -webkit-print-color-adjust:exact;">'
                f'<div>{a_tag}'
                f'<div style="margin-top:3px;">'
                f'<span style="background:#E8F5E9; color:#1B5E20; padding:1px 6px; border-radius:4px; '
                f'font-size:10px; font-weight:700; -webkit-print-color-adjust:exact;">토론회</span>'
                f'</div></div>'
                f'<div style="font-size:12px; font-weight:800;">{date}</div>'
                f'</div>'
            )

    # ── ❸ 뉴스 ──────────────────────────────────────────────
    if st.session_state.sel_n:
        html += '<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">❸ 언론 모니터링</div>'
        KW_COLOR = {
            "중증응급":    "#800000",
            "중증외상":    "#6F42C1",
            "상급종합병원": "#A52A2A",
        }
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
                f'font-size:10px; font-weight:700; -webkit-print-color-adjust:exact;">{kw_esc}</div>'
                f'</div>'
            )

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
