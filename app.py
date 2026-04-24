import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 연구원님 원본 데이터 로딩 로직 (모든 필드 보존)
BASE_DIR = os.path.expanduser("~")
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _latest(pattern):
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

def _load(path):
    if not path or not os.path.exists(path): return []
    with open(path, encoding="utf-8") as f: return json.load(f)

# 원본 데이터 파일들 로드
asm_data = _load(_latest(os.path.join(BASE_DIR, "assembly_results_*.json")))
sch_data = _load(_latest(os.path.join(BASE_DIR, "schedule_results_*.json")))
news_data = _load(_latest(os.path.join(BASE_DIR, "news_results_*.json")))

# 2. 요약 카드 스타일 (image_35c281 디자인 100% 이식)
def _card(icon, label, value, text_color, bg_color, border_color):
    return f'''
    <div style="flex:1; background:{bg_color}; border-radius:15px; border-top:5px solid {border_color}; 
                padding:20px 10px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.05); -webkit-print-color-adjust: exact;">
        <div style="font-size:24px; margin-bottom:8px;">{icon}</div>
        <div style="font-size:32px; font-weight:800; color:{text_color}; margin-bottom:5px;">{value}</div>
        <div style="font-size:13px; font-weight:700; color:{text_color};">{label}</div>
    </div>'''

# 3. 사이드바 항목 선택
st.sidebar.title("NMC 보고서 항목 선택")
sel_a = [r for i, r in enumerate(asm_data) if st.sidebar.checkbox(f"의안: {r.get('bill_name', '의안')[:15]}", True, key=f"a{i}")]
sel_s = [r for i, r in enumerate(sch_data) if st.sidebar.checkbox(f"일정: {r.get('title', '일정')[:15]}", True, key=f"s{i}")]
sel_n = [r for i, r in enumerate(news_data) if st.sidebar.checkbox(f"뉴스: {r.get('title', '뉴스')[:15]}", True, key=f"n{i}")]

# 4. 보고서 생성 (데이터 누락 방지 및 PDF 최적화)
if st.button("✨ NMC 공식 양식 보고서 발행", use_container_width=True):
    today = datetime.now().strftime("%Y-%m-%d")
    gen_at = datetime.now().strftime("%H:%M")
    
    # [헤더 섹션]
    header = f'''<div style="background:#1B3A6B; color:#fff; padding:35px 30px; border-radius:10px 10px 0 0; -webkit-print-color-adjust: exact;">
        <div style="font-size:11px; letter-spacing:2px; opacity:0.8; margin-bottom:10px;">응급의료정책팀 | 자동 모니터링 보고서</div>
        <div style="font-size:26px; font-weight:700;">의료정책 모니터링 보고서 ({today})</div>
        <div style="font-size:12px; opacity:0.7; margin-top:8px;">기준일: {today} &nbsp;·&nbsp; 생성 시각: {gen_at}</div>
    </div>'''

    # [요약 카드 섹션]
    cards = f'''<div style="display:flex; gap:15px; padding:25px 0;">
        {_card("📋", "계류 의안", len(sel_a), "#1B3A6B", "#EBF1F9", "#1B3A6B")}
        {_card("📅", "예정 일정", len(sel_s), "#155724", "#E8F5E9", "#155724")}
        {_card("📰", "언론 기사", len(sel_n), "#721C24", "#F8D7DA", "#721C24")}
        {_card("📊", "전체 항목", len(sel_a)+len(sel_s)+len(sel_n), "#495057", "#F1F3F5", "#495057")}
    </div>'''

    body = ""
    # ❶ 의안 현황 (image_35c69a 디테일 반영)
    if sel_a:
        body += f'''<div style="display:flex; align-items:center; gap:10px; margin-top:30px; margin-bottom:15px;">
            <div style="background:#1B3A6B; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; -webkit-print-color-adjust: exact;">1</div>
            <div style="font-size:18px; font-weight:800; color:#1B3A6B;">의안 현황</div>
        </div>'''
        for r in sel_a:
            body += f'''<div style="background:#fff; border-radius:15px; border:1px solid #E2E8F0; padding:25px; margin-bottom:20px; border-left:6px solid #3B82F6; -webkit-print-color-adjust: exact;">
                <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                    <div style="font-size:16px; font-weight:800; color:#1B3A6B;">{escape(r.get('bill_name', ''))}</div>
                    <div style="font-size:12px; color:#555;">{r.get('proposer', '의원 등')}</div>
                    <div style="background:#1B3A6B; color:#fff; padding:3px 12px; border-radius:15px; font-size:11px; font-weight:700; -webkit-print-color-adjust: exact;">{r.get('status', '소관위접수')}</div>
                </div>
                <div style="background:#FFF9E6; border:1px solid #FFD966; color:#856404; padding:5px 12px; border-radius:5px; font-size:12px; font-weight:700; margin-bottom:15px; -webkit-print-color-adjust: exact;">입법예고 진행중</div>
                <div style="font-size:13px; color:#444; line-height:1.7; border-top:1px solid #F1F3F5; padding-top:15px;">{escape(r.get('summary', '내용 요약 정보가 없습니다.'))}</div>
            </div>'''

    # ❷ 주요 일정 (image_35c61e 디테일 반영)
    if sel_s:
        body += f'''<div style="display:flex; align-items:center; gap:10px; margin-top:40px; margin-bottom:15px;">
            <div style="background:#1B3A6B; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:7