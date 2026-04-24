import streamlit as st

# 1. 페이지 설정
st.set_page_config(page_title="NMC 응급의료 모니터링", page_icon="🚑", layout="wide")

st.title("🚑 응급의료 정책 모니터링 대시보드")
st.info("국회 의안 및 정책 동향을 실시간으로 확인하세요.")

# 2. 샘플 데이터 (나중에 실제 수집 코드와 연결될 부분)
items = [
    {"type": "국회", "title": "응급의료법 일부개정안", "link": "https://likms.assembly.go.kr"},
    {"type": "뉴스", "title": "4월 응급의료 정책 간담회 개최", "link": "https://news.naver.com"},
    {"type": "일정", "title": "중앙응급의료센터 정기 회의", "link": "https://www.nmc.or.kr"}
]

# 3. 화면 구성 (카드 스타일)
st.subheader("📝 오늘 업데이트된 항목")

for item in items:
    # 카드 전체를 클릭 가능하게 만드는 HTML 트릭
    card_html = f"""
    <div onclick="window.open('{item['link']}', '_blank')" style="
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ddd;
        background-color: #ffffff;
        margin-bottom: 15px;
        cursor: pointer;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    ">
        <span style="color: #ff4b4b; font-weight: bold;">[{item['type']}]</span>
        <span style="margin-left: 10px; font-size: 1.1rem;">{item['title']}</span>
        <div style="font-size: 0.8rem; color: #888; margin-top: 8px;">클릭 시 상세 페이지로 이동합니다.</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

# 4. 발행 버튼
if st.button("🚀 팀 카톡방에 리포트 공유하기"):
    st.success("리포트 생성을 시작합니다!")