import streamlit as st
import pandas as pd
import glob
import os
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def get_latest_file(pattern):
    files = glob.glob(pattern)
    return sorted(files)[-1] if files else None

# 데이터 로드
df_a = pd.read_json(get_latest_file('assembly_results_*.json')) if get_latest_file('assembly_results_*.json') else pd.DataFrame()
df_s = pd.read_json(get_latest_file('schedule_results_*.json')) if get_latest_file('schedule_results_*.json') else pd.DataFrame()
df_n = pd.read_json(get_latest_file('news_results_*.json')) if get_latest_file('news_results_*.json') else pd.DataFrame()

# 샘플 보고서의 디자인 요소를 CSS로 100% 구현
STYLE = """
<style>
    .report-wrap { font-family: 'Malgun Gothic', sans-serif; background-color: #F4F7FA; padding: 30px; }
    .header { background: linear-gradient(135deg, #1B3A6B 0%, #2A5298 100%); color: white; padding: 40px 30px; border-radius: 10px; position: relative; }
    
    /* 요약 카드 레이아웃 */
    .card-box { display: flex; gap: 15px; margin: 25px 0; }
    .card { flex: 1; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; }
    .card-val { font-size: 28px; font-weight: bold; color: #1B3A6B; margin-bottom: 5px; }
    .card-lbl { font-size: 13px; color: #666; font-weight: 600; }

    /* 섹션 타이틀 */
    .sec-title { background: #1B3A6B; color: white; padding: 12px 20px; border-radius: 6px; font-weight: bold; font-size: 18px; margin-top: 40px; display: flex; justify-content: space-between; align-items: center; }
    
    /* 개별 카드형 항목 (왼쪽 포인트 컬러) */
    .item-card { background: white; padding: 25px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); position: relative; }
    .item-a { border-left: 8px solid #E63946; } /* 의안: 빨간색 */
    .item-s { border-left: 8px solid #FFB703; } /* 일정: 노란색 */
    .item-n { border-left: 8px solid #8E9AAF; } /* 뉴스: 회색 */

    /* 키워드 및 배지 스타일 */
    .keyword-tag { font-size: 11px; font-weight: bold; color: #1B3A6B; margin-bottom: 8px; display: block; }
    .badge { padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; color: white; margin-right: 8px; vertical-align: middle; }
    
    /* 상세 정보 텍스트 */
    .bill-meta { background: #F8F9FA; padding: 12px; border-radius: 6px; font-size: 13px; color: #555; margin: 12px 0; }
    .summary-text { font-size: 14.5px; line-height: 1.7; color: #333; text-align: justify; margin-top: 15px; }
    
    /* 링크 버튼 */
    .btn-link { display: inline-block; margin-top: 15px; font-size: 13px; font-weight: bold; color: #1B3A6B; text-decoration: none; border: 1.5px solid #1B3A6B; padding: 5px 12px; border-radius: 5px; transition: 0.3s; }
    .btn-link:hover { background: #1B3A6B; color: white; }
</style>
"""

st.title("🚑 NMC 공식 보고서 자동 생성 시스템")

# 선택 UI (기존과 동일)
selected = {'a': [], 's': [], 'n': []}
c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("📋 의안 선택")
    for i, r in df_a.iterrows():
        if st.checkbox(f"{r.get('bill_name')}", key=f"a{i}"): selected['a'].append(r.to_dict())
with c2:
    st.subheader("📅 일정 선택")
    for i, r in df_s.iterrows():
        if st.checkbox(f"{r.get('title')}", key=f"s{i}"): selected['s'].append(r.to_dict())
with c3:
    st.subheader("📰 뉴스 선택")
    for i, r in df_n.iterrows():
        if st.checkbox(f"{r.get('title')}", key=f"n{i}"): selected['n'].append(r.to_dict())

if st.button("✨ NMC 공식 양식으로 보고서 발행", use_container_width=True):
    total_cnt = len(selected['a']) + len(selected['s']) + len(selected['n'])
    
    html_content = f"""
    {STYLE}
    <div class="report-wrap">
        <div class="header">
            <div style="font-size:13px; opacity:0.8; margin-bottom:5px;">의료정책연구 | 응급의료정책팀</div>
            <div style="font-size:28px; font-weight:bold;">응급의료 동향 모니터링 보고서</div>
            <div style="margin-top:10px; font-size:14px;">{datetime.now().strftime('%Y.%m.%d')}</div>
        </div>

        <div class="card-box">
            <div class="card"><div class="card-val">{len(selected['a'])}</div><div class="card-lbl">계류 의안</div></div>
            <div class="card"><div class="card-val">{len(selected['s'])}</div><div class="card-lbl">예정 일정</div></div>
            <div class="card"><div class="card-val">{len(selected['n'])}</div><div class="card-lbl">언론 기사</div></div>
            <div class="card" style="background:#F1F3F5;"><div class="card-val">{total_cnt}</div><div class="card-lbl">전체 항목</div></div>
        </div>
    """

    # 1. 의안 섹션
    if selected['a']:
        html_content += f'<div class="sec-title"><span>📋 1. 의안 현황</span><span style="font-size:13px;">총 {len(selected["a"])}건</span></div>'
        for item in selected['a']:
            html_content += f"""
            <div class="item-card item-a">
                <span class="keyword-tag">의료법</span>
                <div style="margin-bottom:10px;">
                    <span class="badge" style="background:#E63946;">중요</span>
                    <b style="font-size:18px;">{item.get('bill_name')}</b>
                </div>
                <div class="bill-meta">
                    <b>제안자:</b> {item.get('proposer', '정보없음')} | <b>상태:</b> {item.get('status', '접수')} | <b>입법예고:</b> {item.get('period', '-')}
                </div>
                <div class="summary-text">{item.get('summary', '요약 정보가 없습니다.')}</div>
                <a href="{item.get('url')}" class="btn-link" target="_blank">🔗 상세 정보 원문 링크</a>
            </div>
            """

    # 2. 일정 섹션
    if selected['s']:
        html_content += f'<div class="sec-title"><span>📅 2. 주요 일정</span><span style="font-size:13px;">총 {len(selected["s"])}건</span></div>'
        for item in selected['s']:
            html_content += f"""
            <div class="item-card item-s">
                <span class="keyword-tag">{item.get('category', '토론회/세미나')}</span>
                <span class="badge" style="background:#FFB703; color:black;">일정</span>
                <b style="font-size:17px;">{item.get('title')}</b>
                <div style="margin-top:12px; font-size:14px; color:#444;">📍 일시 및 장소: <b>{item.get('date', '-')}</b></div>
            </div>
            """

    # 3. 뉴스 섹션 (키워드 표시 추가)
    if selected['n']:
        html_content += f'<div class="sec-title"><span>📰 3. 언론 모니터링</span><span style="font-size:13px;">총 {len(selected["n"])}건</span></div>'
        for item in selected['n']:
            # 뉴스 검색에 사용된 키워드 (예: 중증응급, 상급종합병원 등) 추출
            keywords = item.get('keywords', '중증응급, 응급의료') 
            html_content += f"""
            <div class="item-card item-n">
                <span class="keyword-tag">{keywords}</span>
                <div style="margin-bottom:10px;">
                    <span class="badge" style="background:#8E9AAF;">참고</span>
                    <b style="font-size:16px;">{item.get('title')}</b>
                </div>
                <div style="font-size:13px; color:#777; margin-bottom:10px;">{item.get('source')} | {item.get('date', '')}</div>
                <a href="{item.get('url')}" class="btn-link" target="_blank">🔗 기사 원문 보기</a>
            </div>
            """

    html_content += "</div>"
    
    st.markdown(html_content, unsafe_allow_html=True)
    st.download_button("💾 NMC 최종 보고서(.html) 다운로드", data=html_content, file_name=f"NMC_Report_Final_{datetime.now().strftime('%m%d')}.html", mime="text/html")
    st.success("🎉 이미지 샘플과 동일한 디자인으로 보고서가 생성되었습니다!")