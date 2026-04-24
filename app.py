import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

# 1. 설정 및 데이터 로드
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")
BASE_DIR = os.getcwd()

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

def get_badge_style(kw):
    styles = {
        "중증응급": "background:#800000; color:#fff;",
        "응급의료": "background:#DC3545; color:#fff;",
        "필수의료": "background:#E07B00; color:#fff;",
        "소아응급": "background:#28A745; color:#fff;"
    }
    return styles.get(kw, "background:#1B3A6B; color:#fff;")

if "report_done" not in st.session_state:
    st.session_state.report_done = False

# [A] 선택 화면
if not st.session_state.report_done:
    st.title("🚑 NMC 정책 모니터링 보고서 생성기")
    st.info("💡 팁: 한 페이지에 담기 위해 섹션별로 꼭 필요한 항목만 체크해주세요.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("❶ 의안")
        sel_a = [r for i, r in enumerate(asm_raw) if st.checkbox(f"{r.get('bill_name','')[:15]}", True, key=f"ma{i}")]
    with col2:
        st.subheader("❷ 일정")
        sel_s = [r for i, r in enumerate(sch_raw) if st.checkbox(f"{r.get('title','')[:15]}", True, key=f"ms{i}")]
    with col3:
        st.subheader("❸ 뉴스")
        sel_n = [r for i, r in enumerate(news_raw) if st.checkbox(f"{r.get('title','')[:15]}", True, key=f"mn{i}")]

    if st.button("✨ 선택한 항목으로 보고서 발행", use_container_width=True):
        st.session_state.update({"a_list": sel_a, "s_list": sel_s, "n_list": sel_n, "report_done": True})
        st.rerun()

# [B] 보고서 결과 화면 (한 페이지 압축 최적화)
else:
    if st.button("🔙 항목 다시 선택"):
        st.session_state.report_done = False
        st.rerun()

    today = datetime.now().strftime("%Y-%m-%d")
    
    # [핵심] PDF 한 페이지용 CSS 최적화
    st.markdown("""
        <style>
        @media print {
            header, footer, .stButton, [data-testid='stSidebar'] { display: none !important; }
            .main { padding: 0 !important; }
            #printable { width: 100%; height: auto; overflow: visible; }
            /* 폰트 및 여백 압축 */
            body { font-size: 11pt; }
            h2 { font-size: 14pt; margin-top: 15px !important; }
            .card-val { font-size: 24pt !important; }
            .item-box { page-break-inside: avoid; margin-bottom: 10px !important; padding: 15px !important; }
        }
        </style>
    """, unsafe_allow_html=True)

    # 1) 헤더 (높이 축소)
    header = f'<div style="background:#1B3A6B;color:#fff;padding:25px 30px;border-radius:10px 10px 0 0;-webkit-print-color-adjust:exact;"><div style="font-size:10px;opacity:0.8;margin-bottom:5px;">응급의료정책팀 모니터링</div><div style="font-size:22px;font-weight:700;">의료정책 모니터링 보고서 ({today})</div></div>'

    # 2) 요약 카드 (크기 축소)
    def c(icon, label, val, color):
        return f'<div style="flex:1;background:#fff;border-radius:12px;border-top:4px solid {color};padding:15px 5px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,0.05);-webkit-print-color-adjust:exact;"><div style="font-size:18px;margin-bottom:5px;">{icon}</div><div class="card-val" style="font-size:28px;font-weight:800;color:{color};">{val}</div><div style="font-size:11px;color:#666;">{label}</div></div>'

    cards = f'<div style="display:flex;gap:10px;padding:15px 0;">{c("📋","의안",len(st.session_state.a_list),"#1B3A6B")}{c("📅","일정",len(st.session_state.s_list),"#28A745")}{c("📰","뉴스",len(st.session_state.n_list),"#DC3545")}</div>'

    body = ""
    # 의안 (요약문 길이 제한 등 압축)
    if st.session_state.a_list:
        body += '<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">1. 의안 현황</div>'
        for r in st.session_state.a_list:
            body += f'<div class="item-box" style="background:#fff;border-radius:15px;border:1px solid #E2E8F0;padding:15px;margin-bottom:12px;border-left:6px solid #3B82F6;-webkit-print-color-adjust:exact;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;"><div style="font-size:14px;font-weight:800;">{escape(r.get("bill_name","")[:40])}</div><div style="background:#1B3A6B;color:#fff;padding:2px 10px;border-radius:12px;font-size:10px;">{escape(r.get("status","접수"))}</div></div><div style="font-size:12px;color:#555;line-height:1.5;border-top:1px solid #F1F3F5;padding-top:10px;">{escape(r.get("summary","")[:200])}...</div></div>'

    # 일정 및 뉴스 (한 줄씩 콤팩트하게)
    if st.session_state.s_list:
        body += '<div style="margin:25px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">2. 주요 일정</div>'
        for r in st.session_state.s_list:
            body += f'<div class="item-box" style="background:#fff;border-radius:12px;border:1px solid #E2E8F0;padding:12px 20px;margin-bottom:8px;border-left:6px solid #28A745;display:flex;justify-content:space-between;align-items:center;-webkit-print-color-adjust:exact;"><div style="font-size:13px;font-weight:700;">{escape(r.get("title",""))}</div><div style="font-size:12px;color:#333;">{escape(r.get("date",""))}</div></div>'

    if st.session_state.n_list:
        body += '<div style="margin:25px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">3. 언론 모니터링</div>'
        for r in st.session_state.n_list:
            kw = r.get('keyword','응급의료')
            style = get_badge_style(kw)
            body += f'<div class="item-box" style="background:#fff;border-radius:12px;border:1px solid #E2E8F0;padding:12px 20px;margin-bottom:8px;border-left:6px solid #DC3545;display:flex;justify-content:space-between;align-items:center;-webkit-print-color-adjust:exact;"><div style="font-size:13px;font-weight:700;">{escape(r.get("title","")[:45])}</div><div style="{style}padding:3px 12px;border-radius:12px;font-size:10px;font-weight:700;">{escape(kw)}</div></div>'

    st.markdown(f'<div id="printable" style="background:#FBFBFB;padding:30px;font-family:sans-serif;max-width:800px;margin:auto;">{header}{cards}{body}</div>', unsafe_allow_html=True)
    st.info("💡 **Ctrl+P**를 누른 후, 설정에서 **[페이지에 맞춤]** 또는 **[배율: 80~90%]**로 조정하면 한 페이지에 완벽하게 들어옵니다.")