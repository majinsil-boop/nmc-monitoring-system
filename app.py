import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. [핵심 수정] 데이터 파일 경로 설정
# 연구원님의 환경에 맞춰 파일이 위치한 경로를 수동으로 지정하거나 현재 폴더(.)로 설정하세요.
BASE_DIR = os.getcwd() # 현재 app.py가 있는 폴더 기준

st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _load_data(pattern):
    files = sorted(glob.glob(os.path.join(BASE_DIR, pattern)))
    if not files:
        return []
    try:
        with open(files[-1], encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# 파일명 패턴은 연구원님이 사용하시는 형식(results_*.json 등)에 맞췄습니다.
asm_raw = _load_data("assembly_results_*.json")
sch_raw = _load_data("schedule_results_*.json")
news_raw = _load_data("news_results_*.json")

# 2. 체크박스 영역 (데이터가 없을 때 경고 표시)
st.sidebar.title("NMC 보고서 항목 선택")

if not any([asm_raw, sch_raw, news_raw]):
    st.sidebar.error("⚠️ JSON 데이터를 찾을 수 없습니다. 파일이 app.py와 같은 폴더에 있는지 확인해주세요.")
else:
    st.sidebar.success(f"의안 {len(asm_raw)}건, 일정 {len(sch_raw)}건, 뉴스 {len(news_raw)}건 로드됨")

# 체크박스 생성
sel_a = [r for i, r in enumerate(asm_raw) if st.sidebar.checkbox(f"의안: {r.get('bill_name', '제목없음')[:15]}", True, key=f"a{i}")]
sel_s = [r for i, r in enumerate(sch_raw) if st.sidebar.checkbox(f"일정: {r.get('title', '제목없음')[:15]}", True, key=f"s{i}")]
sel_n = [r for i, r in enumerate(news_raw) if st.sidebar.checkbox(f"뉴스: {r.get('title', '제목없음')[:15]}", True, key=f"n{i}")]

# 3. 요약 카드 렌더링 함수 (디자인 100% 동일)
def render_card(icon, label, value, text_color, bg_color, border_color):
    style = (f"flex:1; background:{bg_color}; border-radius:15px; border-top:5px solid {border_color}; "
             f"padding:20px 10px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.05); -webkit-print-color-adjust: exact;")
    return f'<div style="{style}"><div style="font-size:24px; margin-bottom:8px;">{icon}</div><div style="font-size:32px; font-weight:800; color:{text_color}; margin-bottom:4px;">{value}</div><div style="font-size:12px; font-weight:700; color:{text_color}; opacity:0.8;">{escape(label)}</div></div>'

# 4. 보고서 발행 버튼
if st.button("✨ NMC 공식 양식 보고서 발행", use_container_width=True):
    today = datetime.now().strftime("%Y-%m-%d")
    
    # [헤더 및 요약카드]
    header_html = f'<div style="background:#1B3A6B; color:#fff; padding:35px 30px; border-radius:10px 10px 0 0; -webkit-print-color-adjust: exact;"><div style="font-size:11px; letter-spacing:2px; opacity:0.8; margin-bottom:10px;">응급의료정책팀 | 자동 모니터링 보고서</div><div style="font-size:26px; font-weight:700;">의료정책 모니터링 보고서 ({today})</div></div>'
    cards_html = f'<div style="display:flex; gap:12px; padding:20px 0;">{render_card("📋", "계류 의안", len(sel_a), "#1B3A6B", "#EBF1F9", "#1B3A6B")}{render_card("📅", "예정 일정", len(sel_s), "#155724", "#E8F5E9", "#155724")}{render_card("📰", "언론 기사", len(sel_n), "#721C24", "#F8D7DA", "#721C24")}{render_card("📊", "전체 항목", len(sel_a)+len(sel_s)+len(sel_n), "#495057", "#F1F3F5", "#495057")}</div>'

    body_html = ""
    # ❶ 의안 섹션 리스트 (image_35c69a 디테일)
    if sel_a:
        body_html += '<div style="display:flex; align-items:center; gap:10px; margin-top:30px; margin-bottom:15px;"><div style="background:#1B3A6B; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700;">1</div><div style="font-size:18px; font-weight:800; color:#1B3A6B;">의안 현황</div></div>'
        for r in sel_a:
            body_html += f'''<div style="background:#fff; border-radius:20px; border:1px solid #E2E8F0; padding:25px; margin-bottom:20px; border-left:6px solid #3B82F6; box-shadow:0 4px 12px rgba(0,0,0,0.03);"><div style="display:flex; justify-content:space-between; margin-bottom:12px;"><div style="font-size:16px; font-weight:800; color:#1B3A6B;">{escape(r.get('bill_name',''))}</div><div style="background:#1B3A6B; color:#fff; padding:3px 12px; border-radius:15px; font-size:11px; font-weight:700;">{escape(r.get('status','접수'))}</div></div><div style="background:#FFF9E6; border:1px solid #FFD966; color:#856404; padding:5px 12px; border-radius:5px; font-size:12px; font-weight:700; margin-bottom:15px;">{escape(r.get('legislative_notice','입법예고'))}</div><div style="font-size:13px; color:#444; line-height:1.7; border-top:1px solid #F1F3F5; padding-top:15px;">{escape(r.get('summary',''))}</div></div>'''

    # ❷ 주요 일정 섹션 리스트 (image_35c61e 디테일)
    if sel_s:
        body_html += '<div style="display:flex; align-items:center; gap:10px; margin-top:40px; margin-bottom:15px;"><div style="background:#1B3A6B; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700;">2</div><div style="font-size:18px; font-weight:800; color:#1B3A6B;">주요 일정</div></div>'
        for r in sel_s:
            body_html += f'''<div style="background:#fff; border-radius:20px; border:1px solid #E2E8F0; padding:20px 25px; margin-bottom:15px; border-left:6px solid #28A745; display:flex; align-items:center; justify-content:space-between;"><div><div style="font-size:15px; font-weight:800; color:#111; margin-bottom:8px;">{escape(r.get('title',''))}</div><div style="font-size:12px; color:#777;">{escape(r.get('source','국회'))}</div></div><div style="text-align:right;"><div style="background:#28A745; color:#fff; padding:3px 15px; border-radius:15px; font-size:11px; font-weight:700;">예정</div><div style="font-size:13px; font-weight:800; color:#333; margin-top:5px;">{escape(r.get('date',''))}</div></div></div>'''

    # ❸ 언론 모니터링 섹션 리스트 (image_35c6da 디테일)
    if sel_n:
        body_html += '<div style="display:flex; align-items:center; gap:10px; margin-top:40px; margin-bottom:15px;"><div style="background:#1B3A6B; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700;">3</div><div style="font-size:18px; font-weight:800; color:#1B3A6B;">언론 모니터링</div></div>'
        for r in sel_n:
            body_html += f'''<div style="background:#fff; border-radius:20px; border:1px solid #E2E8F0; padding:18px 25px; margin-bottom:12px; border-left:6px solid #DC3545; display:flex; align-items:center; justify-content:space-between;"><div><div style="font-size:14px; font-weight:700; color:#1B3A6B;">{escape(r.get('title',''))}</div><div style="font-size:12px; color:#777; margin-top:5px;">{escape(r.get('source',''))} | {escape(r.get('date',''))}</div></div><div style="background:#F8D7DA; color:#721C24; padding:4px 15px; border-radius:15px; font-size:11px; font-weight:700;">{escape(r.get('keyword','기사'))}</div></div>'''

    final_report = f'<div style="background:#FBFBFB; padding:30px; font-family:sans-serif;">{header_html}{cards_html}{body_html}</div>'
    st.markdown(final_report, unsafe_allow_html=True)
    st.download_button("💾 보고서 파일 저장", data=final_report, file_name=f"NMC_Report_{today}.html", mime="text/html")