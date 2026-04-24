import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 파일 및 데이터 로딩
BASE_DIR = os.getcwd()
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _load_data(pattern):
    files = sorted(glob.glob(os.path.join(BASE_DIR, pattern)))
    if not files: return []
    try:
        with open(files[-1], encoding="utf-8") as f:
            return json.load(f)
    except: return []

asm_raw = _load_data("assembly_results_*.json")
sch_raw = _load_data("schedule_results_*.json")
news_raw = _load_data("news_results_*.json")

# 2. 키워드별 배지 색상 스타일
def get_badge_style(kw):
    styles = {
        "중증응급": "background:#800000; color:#fff;",
        "중증외상": "background:#6F42C1; color:#fff;",
        "상급종합병원": "background:#A52A2A; color:#fff;",
        "응급의료": "background:#DC3545; color:#fff;",
        "필수의료": "background:#E07B00; color:#fff;",
        "토론회": "background:#28A745; color:#fff;"
    }
    return styles.get(kw, "background:#6C757D; color:#fff;")

# 3. 화면 모드 제어
if "show_report" not in st.session_state:
    st.session_state.show_report = False

# [A] 항목 선택 화면 (한 페이지에 ❶❷❸ 모두 노출)
if not st.session_state.show_report:
    st.title("🚑 NMC 정책 모니터링 보고서 생성기")
    st.info("아래 각 섹션에서 발행할 항목을 체크한 후, 최하단의 [보고서 최종 발행] 버튼을 눌러주세요.")

    st.subheader("❶ 의안 현황 선택")
    sel_a = [r for i, r in enumerate(asm_raw) if st.checkbox(f"[{r.get('status','접수')}] {r.get('bill_name','')}", True, key=f"ma{i}")]

    st.subheader("❷ 주요 일정 선택")
    sel_s = [r for i, r in enumerate(sch_raw) if st.checkbox(f"[{r.get('date','')}] {r.get('title','')}", True, key=f"ms{i}")]

    st.subheader("❸ 언론 모니터링 선택")
    sel_n = [r for i, r in enumerate(news_raw) if st.checkbox(f"[{r.get('source','')}] {r.get('title','')}", True, key=f"mn{i}")]

    st.write("---")
    if st.button("✨ 선택한 항목으로 보고서 최종 발행", use_container_width=True):
        st.session_state.update({"sel_a": sel_a, "sel_s": sel_s, "sel_n": sel_n, "show_report": True})
        st.rerun()

# [B] 실제 보고서 출력 화면 (인쇄 시 이 화면만 보임)
else:
    if st.sidebar.button("🔙 다시 선택하기 (편집)"):
        st.session_state.show_report = False
        st.rerun()

    today = datetime.now().strftime("%Y-%m-%d")
    st.markdown("<style>@media print { header, footer, .stButton, .stInfo, [data-testid='stSidebar'] { display: none !important; } .main { padding: 0 !important; } }</style>", unsafe_allow_html=True)

    def render_card(icon, label, val, t_c, b_c, br_c):
        style = f"flex:1;background:{b_c};border-radius:15px;border-top:5px solid {br_c};padding:20px 10px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.05);-webkit-print-color-adjust:exact;"
        return f'<div style="{style}"><div style="font-size:22px;margin-bottom:8px;">{icon}</div><div style="font-size:32px;font-weight:800;color:{t_c};margin-bottom:4px;">{val}</div><div style="font-size:12px;font-weight:700;color:{t_c};opacity:0.8;">{label}</div></div>'

    report_parts = []
    
    # 1) 헤더 및 카드
    report_parts.append(f'<div style="background:#1B3A6B;color:#fff;padding:35px 30px;border-radius:10px 10px 0 0;-webkit-print-color-adjust:exact;"><div style="font-size:11px;letter-spacing:2px;opacity:0.8;margin-bottom:10px;">응급의료정책팀 | 자동 모니터링 보고서</div><div style="font-size:26px;font-weight:700;">의료정책 모니터링 보고서 ({today})</div></div>')
    
    cards_html = '<div style="display:flex;gap:12px;padding:20px 0;">'
    cards_html += render_card("📋","계류의안",len(st.session_state.sel_a),"#1B3A6B","#EBF1F9","#1B3A6B")
    cards_html += render_card("📅","예정일정",len(st.session_state.sel_s),"#155724","#E8F5E9","#