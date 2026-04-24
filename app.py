import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 파일 및 데이터 로딩
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

# 2. 키워드별 배지 색상 (이미지 35c6da/c0409c 스타일)
def get_badge_style(kw):
    styles = {
        "응급의료": "background:#DC3545; color:#fff;",
        "필수의료": "background:#E07B00; color:#fff;",
        "소아응급": "background:#28A745; color:#fff;",
        "중증외상": "background:#6F42C1; color:#fff;",
        "뉴스": "background:#1B3A6B; color:#fff;"
    }
    return styles.get(kw, "background:#6C757D; color:#fff;")

# 3. 화면 모드 제어 (세션 상태 활용)
if "report_generated" not in st.session_state:
    st.session_state.report_generated = False

# [A] 항목 선택 화면 (이미지 c09e96 스타일)
if not st.session_state.report_generated:
    st.title("🚑 NMC 정책 모니터링 보고서 생성기")
    st.write("아래 각 섹션에서 발행할 항목을 체크한 후, 하단의 [보고서 발행] 버튼을 눌러주세요.")

    st.subheader("❶ 의안 현황 선택")
    sel_a = [r for i, r in enumerate(asm_raw) if st.checkbox(f"[{r.get('status','접수')}] {r.get('bill_name','')}", True, key=f"ma{i}")]

    st.subheader("❷ 주요 일정 선택")
    sel_s = [r for i, r in enumerate(sch_raw) if st.checkbox(f"[{r.get('date','')}] {r.get('title','')}", True, key=f"ms{i}")]

    st.subheader("❸ 언론 모니터링 선택")
    sel_n = [r for i, r in enumerate(news_raw) if st.checkbox(f"[{r.get('source','')}] {r.get('title','')}", True, key=f"mn{i}")]

    st.write("---")
    if st.button("✨ 선택한 항목으로 보고서 발행", use_container_width=True):
        st.session_state.update({"sel_a": sel_a, "sel_s": sel_s, "sel_n": sel_n, "report_generated": True})
        st.rerun()

# [B] 보고서 출력 전용 화면 (이미지 c0409c 스타일)
else:
    if st.button("🔙 항목 다시 선택하기"):
        st.session_state.report_generated = False
        st.rerun()

    today = datetime.now().strftime("%Y-%m-%d")
    
    # 인쇄 시 불필요한 Streamlit UI 숨기기
    st.markdown("<style>@media print { header, footer, .stButton, [data-testid='stSidebar'] { display: none !important; } .main { padding: 0 !important; } }</style>", unsafe_allow_html=True)

    # 보고서 조립
    parts = []
    # 헤더
    parts.append('<div style="background:#1B3A6B;color:#fff;padding:40px 30px;border-radius:10px 10px 0 0;-webkit-print-color-adjust:exact;"><div style="font-size:12px;opacity:0.8;margin-bottom:10px;">응급의료정책팀 | 자동 모니터링 보고서</div><div style="font-size:28px;font-weight:700;">의료정책 모니터링 보고서 (' + today + ')</div></div>')
    
    # 요약 카드
    def card(icon, label, val, color):
        return '<div style="flex:1;background:#fff;border-radius:15px;border-top:5px solid ' + color + ';padding:20px;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,0.05);-webkit-print-color-adjust:exact;"><div style="font-size:24px;margin-bottom:10px;">' + icon + '</div><div style="font-size:36px;font-weight:800;color:' + color + ';">' + str(val) + '</div><div style="font-size:13px;color:#666;font-weight:700;">' + label + '</div></div>'

    parts.append('<div style="display:flex;gap:15px;padding:20px 0;">')
    parts.append(card("📋", "계류의안", len(st.session_state.sel_a), "#1B3A6B"))
    parts.append(card("📅", "예정일정", len(st.session_state.sel_s), "#28A745"))
    parts.append(card("📰", "언론기사", len(st.session_state.sel_n), "#DC3545"))
    parts.append('</div>')

    # 1. 의안 현황
    if st.session_state.sel_a:
        parts.append('<div style="margin-top:30px;margin-bottom:20px;font-size:20px;font-weight:800;color:#1B3A6B;">1. 의안 현황</div>')
        for r in st.session_state.sel_a:
            box = '<div style="background:#fff;border-radius:20px;border:1px solid #E2E8F0;padding:25px;margin-bottom:20px;border-left:8px solid #3B82F6;-webkit-print-color-adjust:exact;">'
            box += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;"><div style="font-size:17px;font-weight:800;">' + escape(r.get("bill_name","")) + '</div><div style="background:#1B3A6B;color:#fff;padding:4px 15px;border-radius:20px;font-size:12px;font-weight:700;">' + escape(r.get("status","접수")) + '</div></div>'
            box += '<div style="background:#FFF9E6;border:1px solid #FFD966;color:#856404;padding:8px 15px;border-radius:8px;font-size:13px;font-weight:700;margin-bottom:15px;">' + escape(r.get("legislative_notice","입법예고중")) + '</div>'
            box += '<div style="font-size:14px;color:#444;line-height:1.8;border-top:1px solid #F1F3F5;padding-top:15px;text-align:justify;">' + escape(r.get("summary","")) + '</div></div>'
            parts.append(box)

    # 2. 주요 일정
    if st.session_state.sel_s:
        parts.append('<div style="margin-top:40px;margin-bottom:20px;font-size:20px;font-weight:800;color:#1B3A6B;">2. 주요 일정</div>')
        for r in st.session_state.sel_s:
            box = '<div style="background:#fff;border-radius:20px;border:1px solid #E2E8F0;padding:25px;margin-bottom:15px;border-left:8px solid #28A745;display:flex;justify-content:space-between;align-items:center;-webkit-print-color-adjust:exact;">'
            box += '<div><div style="font-size:16px;font-weight:800;">' + escape(r.get("title","")) + '</div><div style="font-size:13px;color:#777;margin-top:5px;">' + escape(r.get("source","국회")) + '</div></div>'
            box += '<div style="font-size:14px;font-weight:800;color:#333;">' + escape(r.get("date","")) + '</div></div>'
            parts.append(box)

    # 3. 언론 모니터링
    if st.session_state.sel_n:
        parts.append('<div style="margin-top:40px;margin-bottom:20px;font-size:20px;font-weight:800;color:#1B3A6B;">3. 언론 모니터링</div>')
        for r in st.session_state.sel_n:
            kw = r.get('keyword','뉴스')
            style = get_badge_style(kw)
            box = '<div style="background:#fff;border-radius:20px;border:1px solid #E2E8F0;padding:20px 25px;margin-bottom:12px;border-left:8px solid #DC3545;display:flex;justify-content:space-between;align-items:center;-webkit-print-color-adjust:exact;">'
            box += '<div><div style="font-size:15px;font-weight:800;">' + escape(r.get("title","")) + '</div><div style="font-size:13px;color:#777;margin-top:5px;">' + escape(r.get("source","")) + ' | ' + escape(r.get("date","")) + '</div></div>'
            box += '<div style="' + style + 'padding:5px 15px;border-radius:20px;font-size:11px;font-weight:700;">' + escape(kw) + '</div></div>'
            parts.append(box)

    # 최종 출력
    st.markdown('<div style="background:#FBFBFB;padding:40px;font-family:sans-serif;">' + "".join(parts) + '</div>', unsafe_allow_html=True)
    st.info("💡 **Ctrl+P (인쇄)**를 눌러 PDF로 저장하세요. 선택창 없이 보고서만 깔끔하게 출력됩니다.")