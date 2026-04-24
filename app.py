import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 파일 탐색 및 데이터 로드 (원본 데이터 필드 보존)
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

# 2. [핵심] 메인 화면 체크박스 영역 (이 부분이 누락되었었습니다)
st.title("🚑 NMC 정책 모니터링 보고서 생성기")
st.write("---")

st.subheader("📋 발행할 항목을 선택해주세요")
tab1, tab2, tab3 = st.tabs(["의안 현황", "주요 일정", "언론 모니터링"])

with tab1:
    sel_a = [r for i, r in enumerate(asm_raw) if st.checkbox(f"[의안] {r.get('bill_name', '')}", True, key=f"ma{i}")]
with tab2:
    sel_s = [r for i, r in enumerate(sch_raw) if st.checkbox(f"[일정] {r.get('title', '')}", True, key=f"ms{i}")]
with tab3:
    sel_n = [r for i, r in enumerate(news_raw) if st.checkbox(f"[뉴스] {r.get('title', '')}", True, key=f"mn{i}")]

# 3. 요약 카드 렌더링 함수
def render_card(icon, label, value, text_color, bg_color, border_color):
    style = (f"flex:1; background:{bg_color}; border-radius:15px; border-top:5px solid {border_color}; "
             f"padding:20px 10px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.05); -webkit-print-color-adjust: exact;")
    return f'''<div style="{style}"><div style="font-size:22px; margin-bottom:8px;">{icon}</div><div style="font-size:32px; font-weight:800; color:{text_color}; margin-bottom:4px;">{value}</div><div style="font-size:12px; font-weight:700; color:{text_color}; opacity:0.8;">{label}</div></div>'''

# 4. 보고서 발행 버튼 및 결과 출력
if st.button("✨ 선택한 항목으로 보고서 발행", use_container_width=True):
    today = datetime.now().strftime("%Y-%m-%d")
    gen_at = datetime.now().strftime("%H:%M")
    
    header_html = f'''<div style="background:#1B3A6B; color:#fff; padding:35px 30px; border-radius:10px 10px 0 0; -webkit-print-color-adjust: exact;"><div style="font-size:11px; letter-spacing:2px; opacity:0.8; margin-bottom:10px;">응급의료정책팀 | 자동 모니터링 보고서</div><div style="font-size:26px; font-weight:700;">의료정책 모니터링 보고서 ({today})</div></div>'''
    cards_html = f'''<div style="display:flex; gap:12px; padding:20px 0;">{render_card("📋", "계류 의안", len(sel_a), "#1B3A6B", "#EBF1F9", "#1B3A6B")}{render_card("📅", "예정 일정", len(sel_s), "#155724", "#E8F5E9", "#155724")}{render_card("📰", "언론 기사", len(sel_n), "#721C24", "#F8D7DA", "#721C24")}{render_card("📊", "전체 항목", len(sel_a)+len(sel_s)+len(sel_n), "#495057", "#F1F3F5", "#495057")}</div>'''

    body_html = ""
    # ❶ 의안 섹션 리스트 표출
    if sel_a:
        body_html += '<div style="display:flex; align-items:center; gap:10px; margin-top:30px; margin-bottom:15px;"><div style="background:#1B3A6B; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700;">1</div><div style="font-size:18px; font-weight:800; color:#1B3A6B;">의안 현황</div></div>'
        for r in sel_a:
            body_html += f'''<div style="background:#fff; border-radius:20px; border:1px solid #E2E8F0; padding:25px; margin-bottom:20px; border-left:6px solid #3B82F6; box-shadow:0 4px 12px rgba(0,0,0,0.03);"><div style="display:flex; justify-content:space-between; margin-bottom:12px;"><div style="font-size:16px; font-weight:800; color:#1B3A6B;">{escape(r.get('bill_name',''))}</div><div style="background:#1B3A6B; color:#fff; padding:3px 12px; border-radius:15px; font-size:11px; font-weight:700;">{escape(r.get('status','접수'))}</div></div><div style="background:#FFF9E6; border:1px solid #FFD966; color:#856404; padding:5px 12px; border-radius:5px; font-size:12px; font-weight:700; margin-bottom:15px;">{escape(r.get('legislative_notice','입법예고'))}</div><div style="font-size:13px; color:#444; line-height:1.7; border-top:1px solid #F1F3F5; padding-top:15px;">{escape(r.get('summary',''))}</div></div>'''

    # ❷ 주요 일정 섹션 리스트 표출
    if sel_s:
        body_html += '<div style="display:flex; align-items:center; gap:10px; margin-top:40px; margin-bottom:15px;"><div style="background:#1B3A6B; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700;">2</div><div style="font-size:18px; font-weight:800; color:#1B3A6B;">주요 일정</div></div>'
        for r in sel_s:
            body_html += f'''<div style="background:#fff; border-radius:20px; border:1px solid #E2E8F0; padding:20px 25px; margin-bottom:15px; border-left:6px solid #28A745; display:flex; align-items:center; justify-content:space-between;"><div><div style="font-size:15px; font-weight:800; color:#111; margin-bottom:8px;">{escape(r.get('title',''))}</div><div style="font-size:12px; color:#777;">{escape(r.get('source','국회'))}</div></div><div style="text-align:right;"><div style="background:#28A745; color:#fff; padding:3px 15px; border-radius:15px; font-size:11px; font-weight:700;">예정</div><div style="font-size:13px; font-weight:800; color:#333; margin-top:5px;">{escape(r.get('date',''))}</div></div></div>'''

    # ❸ 언론 모니터링 섹션 리스트 표출
    if sel_n:
        body_html += '<div style="display:flex; align-items:center; gap:10px; margin-top:40px; margin-bottom:15px;"><div style="background:#1B3A6B; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight: