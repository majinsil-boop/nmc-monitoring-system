import streamlit as st
import pandas as pd
import glob
import os
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="NMC 응급의료 모니터링 시스템", layout="wide")

def get_latest_file(pattern):
    files = glob.glob(pattern)
    return sorted(files)[-1] if files else None

# 데이터 로드
df_a = pd.read_json(get_latest_file('assembly_results_*.json')) if get_latest_file('assembly_results_*.json') else pd.DataFrame()
df_s = pd.read_json(get_latest_file('schedule_results_*.json')) if get_latest_file('schedule_results_*.json') else pd.DataFrame()
df_n = pd.read_json(get_latest_file('news_results_*.json')) if get_latest_file('news_results_*.json') else pd.DataFrame()

# 2. 디자인 스타일 (NMC 공식 양식 완벽 재현)
STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    .report-wrap { font-family: 'Noto Sans KR', sans-serif; background-color: #F8F9FB; padding: 40px; }
    .header { background: linear-gradient(135deg, #1B3A6B 0%, #2A5298 100%); color: white; padding: 40px 30px; border-radius: 12px; margin-bottom: 30px; }
    .header-title { font-size: 30px; font-weight: 700; margin: 0; }
    .card-box { display: flex; gap: 15px; margin-bottom: 40px; }
    .card { flex: 1; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; border-top: 5px solid #1B3A6B; }
    .card-val { font-size: 32px; font-weight: 700; color: #1B3A6B; }
    .sec-header { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid #1B3A6B; padding-bottom: 10px; margin-top: 45px; margin-bottom: 20px; }
    .sec-title-text { font-size: 22px; font-weight: 800; color: #1B3A6B; border-left: 6px solid #1B3A6B; padding-left: 15px; line-height: 1; }
    .time-stamp { font-size: 12px; color: #A0AEC0; margin-left: 12px; font-weight: normal; }
    .item-card { background: white; padding: 30px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); position: relative; overflow: hidden; }
    .point-bar { position: absolute; left: 0; top: 0; bottom: 0; width: 8px; }
    .keyword-tag { display: inline-block; background-color: #E9EFF6; color: #1B3A6B; padding: 4px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; margin-right: 8px; margin-bottom: 12px; }
    .badge { padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 700; color: white; vertical-align: middle; margin-right: 8px; }
    .meta-box { background: #F1F3F7; padding: 15px; border-radius: 8px; font-size: 14px; color: #4A5568; margin: 15px 0; display: flex; gap: 20px; }
    .summary-box { font-size: 15px; line-height: 1.8; color: #333; text-align: justify; margin-top: 15px; }
    .link-btn { display: inline-block; margin-top: 20px; font-size: 13px; font-weight: 700; color: #1B3A6B; text-decoration: none; border: 1.5px solid #1B3A6B; padding: 6px 15px; border-radius: 5px; }
</style>
"""

st.title("🚑 NMC 정책 모니터링 시스템")

# 3. 항목 선택 UI (들여쓰기 수정 완료)
selected = {'a': [], 's': [], 'n': []}
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("📋 의안 선택")
    if not df_a.empty:
        for i, r in df_a.iterrows():
            if st.checkbox(f"{r.get('bill_name')}", key=f"a{i}"):
                selected['a'].append(r.to_dict())

with c2:
    st.subheader("📅 일정 선택")
    if not df_s.empty:
        for i, r in df_s.iterrows():
            if st.checkbox(f"{r.get('title')}", key=f"s{i}"):
                selected['s'].append(r.to_dict())

with c3:
    st.subheader("📰 뉴스 선택")
    if not df_n.empty:
        for i, r in df_n.iterrows():
            if st.checkbox(f"{r.get('title', '제목 없음')}", key=f"n{i}"):
                selected['n'].append(r.to_dict())

# 4. 보고서 발행 로직
if st.button("✨ NMC 공식 양식으로 보고서 발행", use_container_width=True):
    total = len(selected['a']) + len(selected['s']) + len(selected['n'])
    now_time = datetime.now().strftime('%H:%M')
    
    html = f"""
    {STYLE}
    <div class="report-wrap">
        <div class="header">
            <div style="font-size:13px; opacity:0.8; margin-bottom:8px;">의료정책연구 | 응급의료정책팀</div>
            <div class="header-title">응급의료 동향 모니터링 보고서</div>
            <div style="margin-top:15px; font-size:15px; opacity:0.9;">{datetime.now().strftime('%Y.%m.%d')}</div>
        </div>

        <div class="card-box">
            <div class="card"><div class="card-val">{len(selected['a'])}</div><div style="font-size:13px; color:#666;">계류 의안</div></div>
            <div class="card"><div class="card-val">{len(selected['s'])}</div><div style="font-size:13px; color:#666;">예정 일정</div></div>
            <div class="card"><div class="card-val">{len(selected['n'])}</div><div style="font-size:13px; color:#666;">언론 기사</div></div>
            <div class="card" style="background:#E9ECEF;"><div class="card-val">{total}</div><div style="font-size:13px; color:#666;">전체</div></div>
        </div>
    """

    if selected['a']:
        html += f'<div class="sec-header"><div class="sec-title-text">1. 의안 현황 <span class="time-stamp">{now_time} 생성</span></div><div style="font-size:14px; color:#888;">총 {len(selected["a"])}건</div></div>'
        for item in selected['a']:
            html += f"""
            <div class="item-card">
                <div class="point-bar" style="background:#E63946;"></div>
                <div class="keyword-tag">의료법</div>
                <div style="font-size:19px; font-weight:700; color:#111; margin:12px 0;"><span class="badge" style="background:#E63946;">중요</span> {item.get('bill_name')}</div>
                <div class="meta-box">
                    <span><b>제안자:</b> {item.get('proposer', '의원')}</span>
                    <span><b>상태:</b> {item.get('status', '소관위접수')}</span>
                </div>
                <div class="summary-box">{item.get('summary', '요약 정보가 없습니다.')}</div>
                <a href="{item.get('url')}" class="link-btn" target="_blank">🔗 상세 정보 원문 링크</a>
            </div>
            """

    if selected['n']:
        html += f'<div class="sec-header"><div class="sec-title-text">3. 언론 모니터링 <span class="time-stamp">{now_time} 생성</span></div><div style="font-size:14px; color:#888;">총 {len(selected["n"])}건</div></div>'
        for item in selected['n']:
            kws = str(item.get('keywords', '중증응급')).split(',')
            tag_html = "".join([f'<span class="keyword-tag">{k.strip()}</span>' for k in kws])
            html += f"""
            <div class="item-card">
                <div class="point-bar" style="background:#8E9AAF;"></div>
                <div class="keyword-area">{tag_html}</div>
                <div style="font-size:19px; font-weight:700; color:#111; margin:12px 0;"><span class="badge" style="background:#8E9AAF;">참고</span> {item.get('title')}</div>
                <div style="font-size:14px; color:#718096;">{item.get('source')} | {item.get('date', '')}</div>
                <a href="{item.get('url')}" class="link-btn" target="_blank">🔗 기사 원문 보기</a>
            </div>
            """

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    st.download_button("💾 보고서 파일(.html) 다운로드", data=html, file_name=f"NMC_Report_{datetime.now().strftime('%m%d')}.html", mime="text/html")