import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 파일 탐색 및 데이터 로드
BASE_DIR = os.path.expanduser("~")
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _latest(pattern):
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

def _load(path):
    if not path or not os.path.exists(path): return []
    with open(path, encoding="utf-8") as f: return json.load(f)

asm_data = _load(_latest(os.path.join(BASE_DIR, "assembly_results_*.json")))
sch_data = _load(_latest(os.path.join(BASE_DIR, "schedule_results_*.json")))
news_data = _load(_latest(os.path.join(BASE_DIR, "news_results_*.json")))

# 2. 요약 카드 스타일 (이미지 35c281 디자인)
def _card(icon, label, value, text_color, bg_color, border_color):
    style = (f"flex:1; background:{bg_color}; border-radius:15px; border-top:5px solid {border_color}; "
             f"padding:20px 10px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.05); -webkit-print-color-adjust: exact;")
    return f'''
    <div style="{style}">
        <div style="font-size:24px; margin-bottom:8px;">{icon}</div>
        <div style="font-size:32px; font-weight:800; color:{text_color}; margin-bottom:4px;">{value}</div>
        <div style="font-size:13px; font-weight:700; color:{text_color};">{escape(label)}</div>
    </div>'''

# 3. 사이드바 항목 선택
st.sidebar.title("NMC 보고서 항목 선택")
sel_a = [r for i, r in enumerate(asm_data) if st.sidebar.checkbox(f"의안: {r.get('bill_name', '')[:15]}", True, key=f"a{i}")]
sel_s = [r for i, r in enumerate(sch_data) if st.sidebar.checkbox(f"일정: {r.get('title', '')[:15]}", True, key=f"s{i}")]
sel_n = [r for i, r in enumerate(news_data) if st.sidebar.checkbox(f"뉴스: {r.get('title', '')[:15]}", True, key=f"n{i}")]

# 4. 보고서 발행
if st.button("✨ NMC 공식 양식 보고서 발행", use_container_width=True):
    today = datetime.now().strftime("%Y-%m-%d")
    gen_at = datetime.now().strftime("%H:%M")
    
    # 헤더
    header = f'''<div style="background:#1B3A6B; color:#fff; padding:35px 30px; border-radius:10px 10px 0 0; -webkit-print-color-adjust: exact;">
        <div style="font-size:11px; letter-spacing:2px; opacity:0.8; margin-bottom:10px;">응급의료정책팀 | 자동 모니터링 보고서</div>
        <div style="font-size:26px; font-weight:700;">의료정책 모니터링 보고서 ({today})</div>
        <div style="font-size:12px; opacity:0.7; margin-top:8px;">기준일: {today} &nbsp;·&nbsp; 생성 시각: {gen_at}</div>
    </div>'''

    # 요약 카드
    cards = f'''<div style="display:flex; gap:15px; padding:25px 0;">
        {_card("📋", "계류 의안", len(sel_a), "#1B3A6B", "#EBF1F9", "#1B3A6B")}
        {_card("📅", "예정 일정", len(sel_s), "#155724", "#E8F5E9", "#155724")}
        {_card("📰", "언론 기사", len(sel_n), "#721C24", "#F8D7DA", "#721C24")}
        {_card("📊", "전체 항목", len(sel_a)+len(sel_s)+len(sel_n), "#495057", "#F1F3F5", "#495057")}
    </div>'''

    body = ""
    # ❶ 의안 현황
    if sel_a:
        body += f'''<div style="display:flex; align-items:center; gap:10px; margin-top:30px; margin-bottom:15px;">
            <div style="background:#1B3A6B; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; -webkit-print-color-adjust: exact;">1</div>
            <div style="font-size:18px; font-weight:800; color:#1B3A6B;">의안 현황</div>
        </div>'''
        for r in sel_a:
            b_name = escape(r.get('bill_name', ''))
            prop = escape(r.get('proposer', '의원 등'))
            stat = escape(r.get('status', '소관위접수'))
            notice = escape(r.get('legislative_notice', '입법예고 정보 없음'))
            summ = escape(r.get('summary', ''))
            
            body += f'''<div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:25px; margin-bottom:20px; border-left:6px solid #3B82F6; box-shadow:0 4px 12px rgba(0,0,0,0.03); -webkit-print-color-adjust: exact;">
                <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                    <div style="font-size:16px; font-weight:800; color:#1B3A6B;">{b_name}</div>
                    <div style="font-size:12px; color:#555;">{prop}</div>
                    <div style="background:#1B3A6B; color:#fff; padding:3px 12px; border-radius:15px; font-size:11px; font-weight:700; -webkit-print-color-adjust: exact;">{stat}</div>
                </div>
                <div style="background:#FFF9E6; border:1px solid #FFD966; color:#856404; padding:5px 12px; border-radius:5px; font-size:12px; font-weight:700; margin-bottom:15px; -webkit-print-color-adjust: exact;">{notice}</div>
                <div style="font-size:13px; color:#444; line-height:1.7; border-top:1px solid #F1F3F5; padding-top:15px; text-align:justify;">{summ}</div>
            </div>'''

    # ❷ 주요 일정
    if sel_s:
        body += f'''<div style="display:flex; align-items:center; gap:10px; margin-top:40px; margin-bottom:15px;">
            <div style="background:#1B3A6B; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; -webkit-print-color-adjust: exact;">2</div>
            <div style="font-size:18px; font-weight:800; color:#1B3A6B;">주요 일정</div>
        </div>'''
        for r in sel_s:
            title = escape(r.get('title', ''))
            src = escape(r.get('source', '국회'))
            dt = escape(r.get('date', ''))
            body += f'''<div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:20px 25px; margin-bottom:15px; border-left:6px solid #28A745; display:flex; align-items:center; justify-content:space-between; -webkit-print-color-adjust: exact;">
                <div><div style="font-size:15px; font-weight:800; color:#111;">{title}</div><div style="font-size:12px; color:#777; margin-top:5px;">{src}</div></div>
                <div style="text-align:right;"><div style="background:#28A745; color:#fff; padding:3px 15px; border-radius:15px; font-size:11px; font-weight:700;">예정</div><div style="font-size:13px; font-weight:800; color:#333; margin-top:5px;">{dt}</div></div>
            </div>'''

    # ❸ 언론 모니터링
    if sel_n:
        body += f'''<div style="display:flex; align-items:center; gap:10px; margin-top:40px; margin-bottom:15px;">
            <div style="background:#1B3A6B; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; -webkit-print-color-adjust: exact;">3</div>
            <div style="font-size:18px; font-weight:800; color:#1B3A6B;">언론 모니터링</div>
        </div>'''
        for r in sel_n:
            n_title = escape(r.get('title', ''))
            n_src = escape(r.get('source', ''))
            n_dt = escape(r.get('date', ''))
            n_kw = escape(r.get('keyword', '기사'))
            body += f'''<div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:18px 25px; margin-bottom:12px; border-left:6px solid #DC3545; display:flex; align-items:center; justify-content:space-between; -webkit-print-color-adjust: exact;">
                <div><div style="font-size:14px; font-weight:700; color:#1B3A6B;">{n_title}</div><div style="font-size:12px; color:#777; margin-top:5px;">{n_src} | {n_dt}</div></div>
                <div style="background:#F8D7DA; color:#721C24; padding:4px 12px; border-radius:15px; font-size:11px; font-weight:700;">{n_kw}</div>
            </div>'''

    final_report = f'<div style="background:#FBFBFB; padding:30px; font-family:sans-serif;">{header}{cards}{body}</div>'
    st.markdown(final_report, unsafe_allow_html=True)
    st.download_button("💾 보고서 파일 저장", data=final_report, file_name=f"NMC_Report_{today}.html", mime="text/html")