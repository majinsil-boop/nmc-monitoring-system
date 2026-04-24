import streamlit as st
import pandas as pd
import glob
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def get_latest_file(pattern):
    files = glob.glob(pattern)
    return sorted(files)[-1] if files else None

# 데이터 로드
df_a = pd.read_json(get_latest_file('assembly_results_*.json')) if get_latest_file('assembly_results_*.json') else pd.DataFrame()
df_s = pd.read_json(get_latest_file('schedule_results_*.json')) if get_latest_file('schedule_results_*.json') else pd.DataFrame()
df_n = pd.read_json(get_latest_file('news_results_*.json')) if get_latest_file('news_results_*.json') else pd.DataFrame()

# 2. 이미지 속 디자인을 그대로 옮긴 CSS
STYLE = """
<style>
    .report-wrap { font-family: 'Malgun Gothic', sans-serif; background-color: #EEF2F9; padding: 20px; }
    .header { background: linear-gradient(135deg, #1B3A6B 0%, #2A5298 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }
    .card-box { display: flex; gap: 10px; margin-bottom: 20px; }
    .card { flex: 1; background: white; padding: 15px; border-radius: 8px; border-top: 4px solid #1B3A6B; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }
    .card-val { font-size: 24px; font-weight: bold; color: #1B3A6B; }
    .sec-title { background: #1B3A6B; color: white; padding: 10px 15px; border-radius: 5px; font-weight: bold; margin-top: 20px; display: flex; justify-content: space-between; }
    .item { background: white; padding: 15px; border-left: 5px solid #DC3545; margin: 10px 0; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .badge { background: #DC3545; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; margin-right: 10px; }
    .link { color: #1B3A6B; text-decoration: none; font-weight: bold; font-size: 13px; border: 1px solid #1B3A6B; padding: 3px 8px; border-radius: 4px; }
</style>
"""

st.title("🚑 NMC 고퀄리티 보고서 생성기")

# 체크박스 선택 UI
selected = {'a': [], 's': [], 'n': []}
c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("📋 의안")
    for i, r in df_a.iterrows():
        if st.checkbox(f"{r.get('bill_name')}", key=f"a{i}"): selected['a'].append(r.to_dict())
with c2:
    st.subheader("📅 일정")
    for i, r in df_s.iterrows():
        if st.checkbox(f"{r.get('title')}", key=f"s{i}"): selected['s'].append(r.to_dict())
with c3:
    st.subheader("📰 뉴스")
    for i, r in df_n.iterrows():
        if st.checkbox(f"{r.get('title')}", key=f"n{i}"): selected['n'].append(r.to_dict())

# 보고서 발행 버튼
if st.button("✨ 기존 보고서 디자인으로 발행", use_container_width=True):
    total = len(selected['a']) + len(selected['s']) + len(selected['n'])
    
    # HTML 조립
    html = f"""
    {STYLE}
    <div class="report-wrap">
        <div class="header">
            <div style="font-size:12px; opacity:0.8;">응급의료정책팀 | 자동 모니터링</div>
            <div style="font-size:24px; font-weight:bold;">의료정책 모니터링 보고서 ({datetime.now().strftime('%Y-%m-%d')})</div>
        </div>
        <div class="card-box">
            <div class="card"><div class="card-val">{len(selected['a'])}</div><div style="font-size:12px;">계류 의안</div></div>
            <div class="card"><div class="card-val">{len(selected['s'])}</div><div style="font-size:12px;">예정 일정</div></div>
            <div class="card"><div class="card-val">{len(selected['n'])}</div><div style="font-size:12px;">언론 기사</div></div>
            <div class="card" style="background:#f8f9fa;"><div class="card-val">{total}</div><div style="font-size:12px;">전체 항목</div></div>
        </div>
    """
    
    if selected['a']:
        html += f'<div class="sec-title"><span>📋 1. 의안 현황</span><span>{len(selected["a"])}건</span></div>'
        for item in selected['a']:
            html += f'<div class="item"><span class="badge">중요</span><b>{item.get("bill_name")}</b><br><br><a href="{item.get("url")}" class="link" target="_blank">🔗 원문 링크 클릭</a></div>'

    if selected['n']:
        html += f'<div class="sec-title"><span>📰 3. 언론 모니터링</span><span>{len(selected["n"])}건</span></div>'
        for item in selected['n']:
            html += f'<div class="item" style="border-left-color:#6c757d;"><span class="badge" style="background:#6c757d;">참고</span><b>{item.get("title")}</b><br><br><a href="{item.get("url")}" class="link" target="_blank">🔗 기사 보기</a></div>'

    html += "</div>"
    
    # 웹 화면에 즉시 보여주기
    st.markdown(html, unsafe_allow_html=True)
    
    # 파일로 저장할 수 있게 제공
    st.download_button("💾 보고서 파일(.html) 다운로드", data=html, file_name=f"NMC_보고서_{datetime.now().strftime('%m%d')}.html", mime="text/html")
    st.success("드디어 디자인이 적용되었습니다! 파일을 다운로드해 브라우저에서 열어보세요.")