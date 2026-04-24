import streamlit as st
import glob
import json
import os
from datetime import datetime
from html import escape

st.set_page_config(page_title="NMC 보고서", layout="wide")

def _load_data(pattern):
    curr = os.path.dirname(os.path.abspath(__file__))
    f_path = os.path.join(curr, pattern)
    fs = sorted(glob.glob(f_path))
    if not fs: return []
    try:
        with open(fs[-1], encoding="utf-8") as f:
            return json.load(f)
    except: return []

# [가장 단순한 주소 처리]
def get_url(r, keys):
    for k in keys:
        u = r.get(k)
        if u and u != "#":
            u = str(u).strip()
            # 주소가 likms... 처럼 시작하면 앞에 https:// 강제 삽입
            if not u.startswith("http"):
                return "https://" + u
            return u
    return "#"

a_raw = _load_data("assembly_results_*.json")
s_raw = _load_data("schedule_results_*.json")
n_raw = _load_data("news_results_*.json")

if "phase" not in st.session_state:
    st.session_state.phase = "SELECT"

if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 정책 보고서 생성기")
    sa, ss, sn = [], [], []

    st.subheader("❶ 의안")
    for i, r in enumerate(a_raw):
        lk = get_url(r, ["link", "bill_link"])
        st.write(f"🔗 **{r.get('bill_name','')}**")
        st.markdown(f'<a href="{lk}" target="_blank">👉 [원문 확인]</a>', unsafe_allow_html=True)
        if st.checkbox("선택", key=f"ca{i}"): sa.append(r)
        st.write("---")

    st.subheader("❷ 일정")
    for i, r in enumerate(s_raw):
        lk = get_url(r, ["link"])
        st.write(f"📅 **{r.get('title','')}**")
        st.markdown(f'<a href="{lk}" target="_blank">👉 [원문 확인]</a>', unsafe_allow_html=True)
        if st.checkbox("선택", key=f"cs{i}"): ss.append(r)
        st.write("---")

    st.subheader("❸ 뉴스")
    for i, r in enumerate(n_raw):
        lk = get_url(r, ["link", "url"])
        st.write(f"📰 **{r.get('title','')}**")
        st.markdown(f'<a href="{lk}" target="_blank">👉 [기사 보기]</a>', unsafe_allow_html=True)
        if st.checkbox("선택", key=f"cn{i}"): sn.append(r)
        st.write("---")

    if st.button("✨ 보고서 발행"):
        st.session_state.sel_a, st.session_state.sel_s, st.session_state.sel_n = sa, ss, sn
        st.session_state.phase = "REPORT"; st.rerun()

else:
    # [보고서 화면 디자인 복구]
    t = datetime.now().strftime("%Y-%m-%d")
    st.sidebar.button("🔙 다시 선택", on_click=lambda: st.session_state.update({"phase":"SELECT"}))
    
    h = '<div style="background:#FBFBFB; padding:20px; font-family:sans-serif;">'
    h += '<div style="background:#1B3A6B; color:#fff; padding:20px 30px; display:flex; justify-content:space-between; align-items:flex-end; border-radius:10px; -webkit-print-color-adjust:exact;">'
    h += '<div><div style="font-size:10px; opacity:0.8;">응급의료정책연구팀</div><div style="font-size:22px; font-weight:800;">응급의료 동향 모니터링</div></div>'
    h += f'<div><div style="font-size:18px; font-weight:800;">{t}</div></div></div>'
    
    # ❶ 의안 (파란 선)
    if st.session_state.sel_a:
        h += '<div style="margin:20px 0 10px; font-size:16px; font-weight:800; color:#1B3A6B;">❶ 의안 현황</div>'
        for r in st.session_state.sel_a:
            l = get_url(r, ["link", "bill_link"])
            h += f'<div style="background:#fff; border:1px solid #E2E8F0; border-left:6px solid #1B3A6B; padding:15px; border-radius:12px; margin-bottom:10px;">'
            h += f'<div style="display:flex; justify-content:space-between; align-items:center;">'
            h += f'<div style="font-size:14px; font-weight:800; color:#1B3A6B;">{escape(str(r.get("bill_name","")))}</div>'
            h += f'<a href="{l}" target="_blank" style="background:#1B3A6B; color:#fff; padding:4px 10px; border-radius:5px; font-size:10px; text-decoration:none;">원문보기 🔗</a></div>'
            h += f'<div style="font-size:11px; color:#444; margin-top:8px;">{escape(str(r.get("summary","")))}</div></div>'

    # [중략 - ❷ 일정, ❸ 뉴스 로직도 동일하게 적용]
    h += '</div>'
    st.markdown(h, unsafe_allow_html=True)