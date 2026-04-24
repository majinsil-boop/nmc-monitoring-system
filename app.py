import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 설정 및 데이터 로드
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _load_data(pattern):
    files = sorted(glob.glob(os.path.join(os.getcwd(), pattern)))
    if not files: return []
    try:
        with open(files[-1], encoding="utf-8") as f:
            return json.load(f)
    except: return []

asm_raw = _load_data("assembly_results_*.json")
sch_raw = _load_data("schedule_results_*.json")
news_raw = _load_data("news_results_*.json")

if "phase" not in st.session_state:
    st.session_state.phase = "SELECT"

# [A] 선택 화면 - 세로 리스트 및 기본 체크 해제
if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 정책 모니터링 보고서 생성기")
    st.info("발행할 항목을 체크한 후 하단의 [보고서 발행] 버튼을 눌러주세요.")

    # ❶ 의안 현황
    st.subheader("❶ 의안 현황 선택")
    sel_a = [r for i, r in enumerate(asm_raw) if st.checkbox(f"[{r.get('status','접수')}] {r.get('bill_name','')}", False, key=f"a{i}")]
    
    # ❷ 주요 일정
    st.subheader("❷ 주요 일정 선택")
    sel_s = [r for i, r in enumerate(sch_raw) if st.checkbox(f"[{r.get('date','')}] {r.get('title','')}", False, key=f"s{i}")]
    
    # ❸ 언론 모니터링
    st.subheader("❸ 언론 모니터링 선택")
    sel_n = [r for i, r in enumerate(news_raw) if st.checkbox(f"[{r.get('source','')}] {r.get('title','')}", False, key=f"n{i}")]

    st.write("---")
    if st.button("✨ 선택한 항목으로 보고서 발행", use_container_width=True):
        st.session_state.update({"sel_a": sel_a, "sel_s": sel_s, "sel_n": sel_n, "phase": "REPORT"})
        st.rerun()

# [B] 보고서 결과 (bfb639.png 디자인 100% 복원)
else:
    if st.sidebar.button("🔙 다시 선택하기 (편집)"):
        st.session_state.phase = "SELECT"
        st.rerun()

    today = datetime.now().strftime("%Y-%m-%d")
    
    st.markdown("""
        <style>
        [data-testid='stHeader'] { display: none; }
        @media print {
            header, footer, .stButton, [data-testid='stSidebar'] { display: none !important; }
            .main { padding: 0 !important; }
            .report-container { transform: scale(0.95); transform-origin: top center; width: 100% !important; }
        }
        </style>
    """, unsafe_allow_html=True)

    # 1) 상단 헤더 (디자인 복구)
    header = f"""
    <div style="background:#1B3A6B; color:#fff; padding:20px 30px; display:flex; justify-content:space-between; align-items:flex-end; -webkit-print-color-adjust:exact;">
        <div><div style="font-size:10px; opacity:0.8;">응급의료정책연구팀</div><div style="font-size:22px; font-weight:800;">응급의료 동향 모니터링</div></div>
        <div style="text-align:right;"><div style="font-size:18px; font-weight:800;">{today}</div></div>
    </div>
    """

    # 2) 요약 카드 (아이콘 및 색상 복구)
    def c(icon, label, val, bg):
        return f'<div style="flex:1; background:{bg}; border-radius:10px; padding:15px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.05); -webkit-print-color-adjust:exact;"><div style="font-size:18px;">{icon}</div><div style="font-size:28px; font-weight:800; color:#1B3A6B;">{val}</div><div style="font-size:11px; font-weight:700; color:#1B3A6B;">{label}</div></div>'

    cards = f"""
    <div style="display:flex; gap:10px; padding:15px 0;">
        {c("📋","계류 의안",len(st.session_state.sel_a),"#EBF1F9")}
        {c("📅","예정 일정",len(st.session_state.sel_s),"#E8F5E9")}
        {c("📰","언론 기사",len(st.session_state.sel_n),"#FDECEA")}
        {c("📊","전체",len(st.session_state.sel_a)+len(st.session_state.sel_s)+len(st.session_state.sel_n),"#F3F4F6")}
    </div>
    """

    body = ""
    # ❶ 의안 (입법예고 노랑 배지 복구)
    if st.session_state.sel_a:
        body += '<div style="margin:20px 0 10px; font-size:18px; font-weight:800; color:#1B3A6B;">❶ 의안 현황</div>'
        for r in st.session_state.sel_a:
            body += f"""
            <div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:20px; margin-bottom:15px; -webkit-print-color-adjust:exact;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <div style="font-size:15px; font-weight:800; color:#1B3A6B;">{escape(r.get('bill_name',''))}</div>
                    <div style="background:#1B3A6B; color:#fff; padding:3px 12px; border-radius:15px; font-size:11px;">{escape(r.get('status','접수'))}</div>
                </div>
                <div style="background:#FFF9E6; border:1px solid #FFD966; color:#856404; padding:5px 12px; border-radius:5px; font-size:12px; font-weight:700; margin-bottom:12px; display:inline-block;">입법예고 진행중(2026-04-22 ~ 2026-05-01)</div>
                <div style="font-size:12px; color:#444; line-height:1.6; text-align:justify;">{escape(r.get('summary',''))}</div>
            </div>
            """

    # ❷ 일정 (토론회 초록 배지 복구)
    if st.session_state.sel_s:
        body += '<div style="margin:30px 0 10px; font-size:18px; font-weight:800; color:#1B3A6B;">❷ 주요 일정</div>'
        for r in st.session_state.sel_s:
            body += f"""
            <div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:15px 20px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; border-left:6px solid #28A745; -webkit-print-color-adjust:exact;">
                <div>
                    <div style="font-size:14px; font-weight:800;">{escape(r.get('title',''))}</div>
                    <div style="margin-top:5px;"><span style="background:#E8F5E9; color:#1B5E20; padding:2px 8px; border-radius:5px; font-size:11px; font-weight:700;">토론회</span> <span style="font-size:11px; color:#666; margin-left:5px;">국회도서관/세미나</span></div>
                </div>
                <div style="font-size:13px; font-weight:800; color:#333;">{escape(r.get('date',''))}</div>
            </div>
            """

    # ❸ 뉴스 (키워드별 색상 복구)
    if st.session_state.sel_n:
        body += '<div style="margin:30px 0 10px; font-size:18px; font-weight:800; color:#1B3A6B;">❸ 언론 모니터링</div>'
        for r in st.session_state.sel_n:
            kw = r.get('keyword','응급의료')
            c_map = {"중증응급":"#800000", "중증외상":"#6F42C1", "상급종합병원":"#A52A2A"}
            c_hex = c_map.get(kw, "#DC3545")
            body += f"""
            <div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:15px 20px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; -webkit-print-color-adjust:exact;">
                <div><div style="font-size:14px; font-weight:800; color:#1B3A6B;">{escape(r.get('title',''))}</div><div style="font-size:11px; color:#777; margin-top:5px;">{escape(r.get('source',''))} | 2026-04-23</div></div>
                <div style="background:{c_hex}; color:#fff; padding:3px 12px; border-radius:15px; font-size:11px; font-weight:700;">{escape(kw)}</div>
            </div>
            """

    st.markdown(f'<div class="report-container" style="background:#FBFBFB; padding:30px; font-family:sans-serif;">{header}{cards}{body}</div>', unsafe_allow_html=True)
    st.info("💡 **Ctrl+P**를 눌러 PDF로 저장하세요. '페이지에 맞춤' 옵션을 사용하면 한 장에 쏙 들어옵니다.")