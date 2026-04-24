import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 환경 설정 및 데이터 로드
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

# 2. 키워드별 배지 색상 로직 (연구원님 원본 스타일)
def get_badge_style(kw):
    styles = {
        "중중응급": "background:#800000; color:#fff;",
        "중중외상": "background:#6F42C1; color:#fff;",
        "상급종합병원": "background:#A52A2A; color:#fff;",
        "응급의료": "background:#DC3545; color:#fff;",
        "필수의료": "background:#E07B00; color:#fff;",
        "토론회": "background:#28A745; color:#fff;"
    }
    return styles.get(kw, "background:#6C757D; color:#fff;")

# 3. 메인 선택 화면 (보고서 발행 전까지만 보임)
if "show_report" not in st.session_state:
    st.session_state.show_report = False

if not st.session_state.show_report:
    st.title("🚑 NMC 정책 모니터링 보고서 생성기")
    st.info("아래 각 섹션에서 발행할 항목을 체크한 후, 하단의 [보고서 발행] 버튼을 눌러주세요.")

    st.subheader("❶ 의안 현황 선택")
    sel_a = [r for i, r in enumerate(asm_raw) if st.checkbox(f"[{r.get('status','접수')}] {r.get('bill_name','')}", True, key=f"ma{i}")]

    st.subheader("❷ 주요 일정 선택")
    sel_s = [r for i, r in enumerate(sch_raw) if st.checkbox(f"[{r.get('date','')}] {r.get('title','')}", True, key=f"ms{i}")]

    st.subheader("❸ 언론 모니터링 선택")
    sel_n = [r for i, r in enumerate(news_raw) if st.checkbox(f"[{r.get('source','')}] {r.get('title','')}", True, key=f"mn{i}")]

    if st.button("✨ 선택한 항목으로 보고서 최종 발행", use_container_width=True):
        st.session_state.sel_a = sel_a
        st.session_state.sel_s = sel_s
        st.session_state.sel_n = sel_n
        st.session_state.show_report = True
        st.rerun()

# 4. 실제 보고서 출력 화면 (발행 버튼 클릭 후 인쇄용 디자인)
else:
    if st.button("🔙 다시 선택하기"):
        st.session_state.show_report = False
        st.rerun()

    today = datetime.now().strftime("%Y-%m-%d")
    
    # [인쇄용 CSS] 인쇄 시 버튼 등 불필요한 요소 제거
    st.markdown("""
        <style>
        @media print {
            header, footer, .stButton, .stInfo { display: none !important; }
            .main { padding: 0 !important; }
        }
        </style>
    """, unsafe_allow_html=True)

    # 보고서 조립
    header = f'<div style="background:#1B3A6B;color:#fff;padding:35px 30px;border-radius:10px 10px 0 0;-webkit-print-color-adjust:exact;"><div style="font-size:11px;letter-spacing:2px;opacity:0.8;margin-bottom:10px;">응급의료정책팀 | 자동 모니터링 보고서</div><div style="font-size:26px;font-weight:700;">의료정책 모니터링 보고서 ({today})</div></div>'
    
    # 요약 카드 (안전한 조립)
    def c_html(icon, label, val, t_c, b_c, br_c):
        return f'<div style="flex:1;background:{b_c};border-radius:15px;border-top:5px solid {br_c};padding:20px 10px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.05);-webkit-print-color-adjust:exact;"><div style="font-size:22px;margin-bottom:8px;">{icon}</div><div style="font-size:32px;font-weight:800;color:{t_c};margin-bottom:4px;">{val}</div><div style="font-size:12px;font-weight:700;color:{t_c};opacity:0.8;">{label}</div></div>'
    
    cards = f'<div style="display:flex;gap:12px;padding:20px 0;">{c_html("📋","계류의안",len(st.session_state.sel_a),"#1B3A6B","#EBF1F9","#1B3A6B")}{c_html("📅","예정일정",len(st.session_state.sel_s),"#155724","#E8F5E9","#155724")}{c_html("📰","언론기사",len(st.session_state.sel_n),"#721C24","#F8D7DA","#721C24")}{c_html("📊","전체",len(st.session_state.sel_a)+len(st.session_state.sel_s)+len(st.session_state.sel_n),"#495057","#F1F3F5","#495057")}</div>'

    body = ""
    # 섹션 1: 의안
    if st.session_state.sel_a:
        body += '<div style="display:flex;align-items:center;gap:10px;margin-top:30px;margin-bottom:15px;"><div style="background:#1B3A6B;color:#fff;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;-webkit-print-color-adjust:exact;">1</div><div style="font-size:18px;font-weight:800;color:#1B3A6B;">의안 현황</div></div>'
        for r in st.session_state.sel_a:
            body += f'<div style="background:#fff;border-radius:20px;border:1px solid #E2E8F0;padding:25px;margin-bottom:20px;border-left:6px solid #3B82F6;-webkit-print-color-adjust:exact;"><div style="display:flex;justify-content:space-between;margin-bottom:12px;"><div style="font-size:16px;font-weight:800;color:#1B3A6B;">{escape(r.get("bill_name",""))}</div><div style="background:#1B3A6B;color:#fff;padding:3px 12px;border-radius:15px;font-size:11px;font-weight:700;-webkit-print-color-adjust:exact;">{escape(r.get("status","접수"))}</div></div><div style="background:#FFF9E6;border:1px solid #FFD966;color:#856404;padding:5px 12px;border-radius:5px;font-size:12px;font-weight:700;margin-bottom:15px;-webkit-print-color-adjust:exact;">{escape(r.get("legislative_notice","입법예고"))}</div><div style="font-size:13px;color:#444;line-height:1.7;border-top:1px solid #F1F3F5;padding-top:15px;">{escape(r.get("summary",""))}</div></div>'

    # 섹션 2: 일정
    if st.session_state.sel_s:
        body += '<div style="display:flex;align-items:center;gap:10px;margin-top:40px;margin-bottom:15px;"><div style="background:#1B3A6B;color:#fff;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;-webkit-print-color-adjust:exact;">2</div><div style="font-size:18px;font-weight:800;color:#1B3A6B;">주요 일정</div></div>'
        for r in st.session_state.sel_s:
            body += f'<div style="background:#fff;border-radius:20px;border:1px solid #E2E8F0;padding:20px 25px;margin-bottom:15px;border-left:6px solid #28A745;display:flex;justify-content:space-between;align-items:center;-webkit-print-color-adjust:exact;"><div><div style="font-size:15px;font-weight:800;color:#111;margin-bottom:8px;">{escape(r.get("title",""))}</div><div style="font-size:12px;color:#777;">{escape(r.get("source","국회"))}</div></div><div style="text-align:right;"><div style="background:#28A745;color:#fff;padding:3px 15px;border-radius:15px;font-size:11px;font-weight:700;-webkit-print-color-adjust:exact;">예정</div><div style="font-size:13px;font-weight:800;color:#333;margin-top:5px;">{escape(r.get("date",""))}</div></div></div>'

    # 섹션 3: 뉴스 (배지 색상 적용)
    if st.session_state.sel_n:
        body += '<div style="display:flex;align-items:center;gap:10px;margin-top:40px;margin-bottom:15px;"><div style="background:#1B3A6B;color:#fff;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;-webkit-print-color-adjust:exact;">3</div><div style="font-size:18px;font-weight:800;color:#1B3A6B;">언론 모니터링</div></div>'
        for r in st.session_state.sel_n:
            kw = r.get('keyword','응급의료')
            style = get_badge_style(kw)
            body += f'<div style="background:#fff;border-radius:20px;border:1px solid #E2E8F0;padding:18px 25px;margin-bottom:12px;border-left:6px solid #DC3545;display:flex;justify-content:space-between;align-items:center;-webkit-print-color-adjust:exact;"><div><div style="font-size:14px;font-weight:700;color:#1B3A6B;">{escape(r.get("title",""))}</div><div style="font-size:12