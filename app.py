import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 데이터 로드 로직
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

# 2. 키워드별 배지 색상
def get_badge_style(kw):
    styles = {
        "중증응급": "background:#800000; color:#fff;",
        "중증외상": "background:#6F42C1; color:#fff;",
        "상급종합병원": "background:#A52A2A; color:#fff;",
        "응급의료": "background:#DC3545; color:#fff;",
        "필수의료": "background:#E07B00; color:#fff;",
        "토론회": "background:#28A745; color:#fff;"
    }
    return styles.get(kw, "background:#6C757D; color:#fff;")

# 3. 화면 제어
if "show_report" not in st.session_state:
    st.session_state.show_report = False

# [A] 항목 선택 화면
if not st.session_state.show_report:
    st.title("🚑 NMC 정책 모니터링 보고서 생성기")
    st.info("각 섹션에서 발행할 항목을 체크한 후 하단의 버튼을 눌러주세요.")

    st.subheader("❶ 의안 현황 선택")
    sel_a = [r for i, r in enumerate(asm_raw) if st.checkbox(f"[{r.get('status','접수')}] {r.get('bill_name','')}", True, key=f"ma{i}")]
    
    st.subheader("❷ 주요 일정 선택")
    sel_s = [r for i, r in enumerate(sch_raw) if st.checkbox(f"[{r.get('date','')}] {r.get('title','')}", True, key=f"ms{i}")]
    
    st.subheader("❸ 언론 모니터링 선택")
    sel_n = [r for i, r in enumerate(news_raw) if st.checkbox(f"[{r.get('source','')}] {r.get('title','')}", True, key=f"mn{i}")]

    if st.button("✨ 선택한 항목으로 보고서 최종 발행", use_container_width=True):
        st.session_state.update({"sel_a": sel_a, "sel_s": sel_s, "sel_n": sel_n, "show_report": True})
        st.rerun()

# [B] 보고서 출력 화면 (인쇄용)
else:
    if st.sidebar.button("🔙 다시 선택하기"):
        st.session_state.show_report = False
        st.rerun()

    today = datetime.now().strftime("%Y-%m-%d")
    st.markdown("<style>@media print { header, footer, .stButton, .stInfo, [data-testid='stSidebar'] { display: none !important; } .main { padding: 0 !important; } }</style>", unsafe_allow_html=True)

    # 보고서 조립용 리스트
    res = []
    res.append('<div style="background:#FBFBFB;padding:30px;font-family:sans-serif;">')
    
    # 헤더
    h = '<div style="background:#1B3A6B;color:#fff;padding:35px 30px;border-radius:10px 10px 0 0;-webkit-print-color-adjust:exact;">'
    h += '<div style="font-size:11px;letter-spacing:2px;opacity:0.8;margin-bottom:10px;">응급의료정책팀 | 자동 모니터링 보고서</div>'
    h += '<div style="font-size:26px;font-weight:700;">의료정책 모니터링 보고서 (' + today + ')</div></div>'
    res.append(h)

    # 요약카드
    def card(icon, label, val, color):
        s = 'flex:1;background:#fff;border-radius:15px;border-top:5px solid '+color+';padding:20px 10px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.05);-webkit-print-color-adjust:exact;'
        return '<div style="'+s+'"><div style="font-size:22px;margin-bottom:8px;">'+icon+'</div><div style="font-size:32px;font-weight:800;color:'+color+';margin-bottom:4px;">'+str(val)+'</div><div style="font-size:12px;font-weight:700;color:#666;">'+label+'</div></div>'

    cards = '<div style="display:flex;gap:12px;padding:20px 0;">'
    cards += card("📋", "계류의안", len(st.session_state.sel_a), "#1B3A6B")
    cards += card("📅", "예정일정", len(st.session_state.sel_s), "#28A745")
    cards += card("📰", "언론기사", len(st.session_state.sel_n), "#DC3545")
    cards += '</div>'
    res.append(cards)

    # 1. 의안
    if st.session_state.sel_a:
        res.append('<div style="margin-top:30px;margin-bottom:15px;font-size:18px;font-weight:800;color:#1B3A6B;">1. 의안 현황</div>')
        for r in st.session_state.sel_a:
            box = '<div style="background:#fff;border-radius:20px;border:1px solid #E2E8F0;padding:25px;margin-bottom:20px;border-left:6px solid #3B82F6;-webkit-print-color-adjust:exact;">'
            box += '<div style="display:flex;justify-content:space-between;margin-bottom:12px;"><div style="font-size:16px;font-weight:800;">' + escape(r.get("bill_name","")) + '</div>'
            box += '<div style="background:#1B3A6B;color:#fff;padding:3px 12px;border-radius:15px;font-size:11px;">' + escape(r.get("status","접수")) + '</div></div>'
            box += '<div style="background:#FFF9E6;border:1px solid #FFD966;color:#856404;padding:5px 12px;border-radius:5px;font-size:12px;margin-bottom:15px;">' + escape(r.get("legislative_notice","입법예고")) + '</div>'
            box += '<div style="font-size:13px;color:#444;line-height:1.7;border-top:1px solid #F1F3F5;padding-top:15px;">' + escape(r.get("summary","")) + '</div></div>'
            res.append(box)

    # 2. 일정
    if st.session_state.sel_s:
        res.append('<div style="margin-top:40px;margin-bottom:15px;font-size:18px;font-weight:800;color:#1B3A6B;">2. 주요 일정</div>')
        for r in st.session_state.sel_s:
            box = '<div style="background:#fff;border-radius:20px;border:1px solid #E2E8F0;padding:20px 25px;margin-bottom:15px;border-left:6px solid #28A745;display:flex;justify-content:space-between;align-items:center;-webkit-print-color-adjust:exact;">'
            box += '<div><div style="font-size:15px;font-weight:800;">' + escape(r.get("title","")) + '</div><div style="font-size:12px;color:#777;">' + escape(r.get("source","국회")) + '</div></div>'
            box += '<div style="text-align:right;"><div style="font-size:13px;font-weight:800;">' + escape(r.get("date","")) + '</div></div></div>'
            res.append(box)

    # 3. 뉴스
    if st.session_state.sel_n:
        res.append('<div style="margin-top:40px;margin-bottom:15px;font-size:18px;font-weight:800;color:#1B3A6B;">3. 언론 모니터링</div>')
        for r in st.session_state.sel_n:
            kw = r.get('keyword','응급의료')
            style = get_badge_style(kw)
            box = '<div style="background:#fff;border-radius:20px;border:1px solid #E2E8F0;padding:18px 25px;margin-bottom:12px;border-left:6px solid #DC3545;display:flex;justify-content:space-between;align-items:center;-webkit-print-color-adjust:exact;">'
            box += '<div><div style="font-size:14px;font-weight:700;">' + escape(r.get("title","")) + '</div><div style="font-size:12px;color:#777;">' + escape(r.get("source","")) + ' | ' + escape(r.get("date","")) + '</div></div>'
            box += '<div style="' + style + 'padding:4px 15px;border-radius:15px;font-size:11px;font-weight:700;">' + escape(kw) + '</div></div>'
            res.append(box)

    res.append('</div>')
    st.markdown("".join(res), unsafe_allow_html=True)
    st.info("💡 **Ctrl+P**를 눌러 PDF로 저장하세요. 깔끔한 보고서만 인쇄됩니다.")