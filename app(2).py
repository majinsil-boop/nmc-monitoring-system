import streamlit as st
import glob
import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from html import escape

# playwright 브라우저 자동 설치
@st.cache_resource
def _install_playwright():
    subprocess.run(["playwright", "install", "chromium"], check=False)

_install_playwright()

# ══════════════════════════════════════════════════════════════════════════════
# URL 보정
# ══════════════════════════════════════════════════════════════════════════════
def fix_url(raw: str) -> str:
    if not raw or raw == "#": return "#"
    raw = raw.strip()
    if raw.startswith(("http://", "https://")): return raw
    return "https://" + raw

def get_link(record: dict, *keys) -> str:
    for k in keys:
        v = record.get(k, "")
        if v and v != "#": return fix_url(v)
    return "#"

# ══════════════════════════════════════════════════════════════════════════════
# 중요도 판단
# ══════════════════════════════════════════════════════════════════════════════
_URGENT_NEWS_KW = {"응급의료", "응급실", "닥터헬기", "중증외상", "구급", "응급실 뺑뺑이", "중증응급"}
_NORMAL_NEWS_KW = {"필수의료", "공공보건의료법", "구조", "외상", "상급종합병원"}

def _is_notice_active(notice: str) -> bool:
    if not notice: return False
    m = re.search(r"~\s*(\d{4}-\d{2}-\d{2})", notice)
    if not m: return True
    try:
        end_date = datetime.strptime(m.group(1), "%Y-%m-%d")
        return end_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    except: return True

def _importance_assembly(item):
    if item.get("legislative_notice") and _is_notice_active(item["legislative_notice"]): return "중요"
    if any(s in item.get("status","") for s in ("위원회심사","본회의","공포")): return "중요"
    return "보통"

def _importance_news(item):
    kw = item.get("keyword","")
    if kw in _URGENT_NEWS_KW: return "중요"
    if kw in _NORMAL_NEWS_KW: return "보통"
    return "참고"

def _dedup_assembly(items):
    seen, out = set(), []
    for r in items:
        key = r.get("bill_no") or r.get("bill_name","")
        if key and key not in seen:
            seen.add(key); out.append(r)
    return out

# ══════════════════════════════════════════════════════════════════════════════
# HTML 빌더 (보고서_20260430.html 디자인 그대로)
# ══════════════════════════════════════════════════════════════════════════════
# 키워드별 보더 색상
_KW_BORDER = {
    "중증응급":    "#f4a8a8",
    "중증외상":    "#f0b8b0",
    "응급의료":    "#f0aaaa",
    "응급실":      "#f4a8a8",
    "응급실 뺑뺑이": "#f4a8a8",
    "닥터헬기":    "#f0b8b0",
    "상급종합병원": "#ecc0b8",
    "필수의료":    "#f0b8b0",
}
_KW_BADGE_BG = {
    "중증응급":    "#8B0000",
    "중증외상":    "#6C3483",
    "응급의료":    "#1B3A6B",
    "응급실":      "#C0392B",
    "응급실 뺑뺑이": "#C0392B",
    "닥터헬기":    "#1B3A6B",
    "상급종합병원": "#A52A2A",
    "필수의료":    "#1B3A6B",
}

def _importance_badge_color(lvl):
    return {"중요":"#DC3545","보통":"#E07B00","참고":"#6C757D"}.get(lvl,"#6C757D")

def build_html(sel_a, sel_s, sel_n, today) -> str:
    generated = datetime.now().strftime("%H:%M")
    today_fmt  = today.replace("-",".")

    na = len(_dedup_assembly(sel_a))
    ns = len(sel_s)
    nn = len(sel_n)
    total = na + ns + nn

    # ── 카드 섹션 ──────────────────────────────────────────────────────────
    cards_html = f"""
    <div style="flex:1;background:#e8edf8;border-radius:10px;padding:10px 14px;border-top:3px solid #1B3A6B;box-shadow:0 1px 5px rgba(0,0,0,.07);text-align:center">
      <div style="font-size:15px;margin-bottom:3px">📋</div>
      <div style="font-size:24px;font-weight:900;color:#0d2a5e;line-height:1.1">{na}</div>
      <div style="font-size:9.5px;color:#0d2a5e;opacity:.7;margin-top:3px;font-weight:600">계류 의안</div>
    </div>
    <div style="flex:1;background:#e8f5ee;border-radius:10px;padding:10px 14px;border-top:3px solid #1a6e35;box-shadow:0 1px 5px rgba(0,0,0,.07);text-align:center">
      <div style="font-size:15px;margin-bottom:3px">📅</div>
      <div style="font-size:24px;font-weight:900;color:#0d4a22;line-height:1.1">{ns}</div>
      <div style="font-size:9.5px;color:#0d4a22;opacity:.7;margin-top:3px;font-weight:600">예정 일정</div>
    </div>
    <div style="flex:1;background:#fdeaea;border-radius:10px;padding:10px 14px;border-top:3px solid #C0392B;box-shadow:0 1px 5px rgba(0,0,0,.07);text-align:center">
      <div style="font-size:15px;margin-bottom:3px">📰</div>
      <div style="font-size:24px;font-weight:900;color:#6b0000;line-height:1.1">{nn}</div>
      <div style="font-size:9.5px;color:#6b0000;opacity:.7;margin-top:3px;font-weight:600">언론 기사</div>
    </div>
    <div style="flex:1;background:#f0ede8;border-radius:10px;padding:10px 14px;border-top:3px solid #888;box-shadow:0 1px 5px rgba(0,0,0,.07);text-align:center">
      <div style="font-size:15px;margin-bottom:3px">📊</div>
      <div style="font-size:24px;font-weight:900;color:#2a2a2a;line-height:1.1">{total}</div>
      <div style="font-size:9.5px;color:#2a2a2a;opacity:.7;margin-top:3px;font-weight:600">전체</div>
    </div>"""

    def sec_header(num, title, count):
        return f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;background:#0d2a5e;color:#fff;border-radius:50%;font-size:13px;font-weight:900;flex-shrink:0;line-height:1">{num}</span>
      <span style="font-size:13px;font-weight:800;color:#0d2a5e;flex:1;letter-spacing:.1px">{title}</span>
      <span style="background:#0d2a5e;color:#fff;padding:2px 11px;border-radius:20px;font-size:9px;font-weight:700">총 {count}건</span>
    </div>"""

    # ── 의안 섹션 ──────────────────────────────────────────────────────────
    asm_items = _dedup_assembly(sel_a)
    asm_html  = f'<div style="margin-bottom:16px;padding:0 8px">{sec_header(1,"의안 현황",len(asm_items))}'
    if not asm_items:
        asm_html += '<p style="padding:14px;text-align:center;color:#aaa;font-size:11px">해당 기간 내 수집된 의안이 없습니다.</p>'
    else:
        for r in asm_items:
            name   = r.get("bill_name","").replace(" (새창 열림)","").strip()
            summ   = r.get("summary","")
            notice = r.get("legislative_notice","")
            kw     = r.get("keyword","")
            status = r.get("status","")
            date   = r.get("proposed_date","")
            url    = fix_url(r.get("url",""))
            lvl    = _importance_assembly(r)
            bc     = _importance_badge_color(lvl)

            tags = ""
            if kw:   tags += f'<span style="background:#dce4f5;color:#1B3A6B;padding:1px 7px;border-radius:4px;font-size:9px;font-weight:600">{escape(kw)}</span> '
            if status: tags += f'<span style="background:#f0f0f0;color:#555;padding:1px 7px;border-radius:4px;font-size:9px;font-weight:600">{escape(status)}</span> '
            if notice and _is_notice_active(notice):
                tags += f'<span style="background:#fff3cd;color:#856404;padding:1px 7px;border-radius:4px;font-size:9px;font-weight:600">{escape(notice)}</span>'

            summ_html = ""
            if summ:
                summ_html = f'<div style="font-size:10px;color:#555;line-height:1.5;margin-top:5px;padding:5px 8px;background:#f8f9fa;border-radius:4px">{escape(summ[:200])}{"…" if len(summ)>200 else ""}</div>'

            asm_html += f"""
    <div style="background:#fff;border-radius:10px;border-left:5px solid #7a9fd4;box-shadow:0 1px 6px rgba(0,0,0,.07);padding:10px 14px;margin-bottom:8px;page-break-inside:avoid">
      <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:5px">
        <span style="background:{bc};color:#fff;padding:1px 7px;border-radius:20px;font-size:9px;font-weight:700;flex-shrink:0">{lvl}</span>
        <div style="flex:1;font-size:11px;font-weight:700;color:#0d2a5e;line-height:1.4">
          <a href="{escape(url)}" style="color:#0d2a5e;text-decoration:none">{escape(name)}</a>
        </div>
      </div>
      <div style="margin-bottom:4px">{tags}</div>
      {summ_html}
      <div style="font-size:9.5px;color:#888;margin-top:5px">발의: {escape(date)}</div>
    </div>"""
    asm_html += "</div>"

    # ── 일정 섹션 ──────────────────────────────────────────────────────────
    sch_html = f'<div style="margin-bottom:16px;padding:0 8px">{sec_header(2,"주요 일정",len(sel_s))}'
    if not sel_s:
        sch_html += '<p style="padding:14px;text-align:center;color:#aaa;font-size:11px">예정된 일정이 없습니다.</p>'
    else:
        for r in sel_s:
            title  = r.get("title","")
            date   = r.get("date","")
            etype  = r.get("event_type","토론회")
            source = r.get("source","")
            url    = fix_url(r.get("url",""))
            sch_html += f"""
    <div style="background:#fff;border-radius:10px;border-left:5px solid #98d4a8;box-shadow:0 1px 6px rgba(0,0,0,.07);padding:10px 14px;margin-bottom:8px;display:flex;align-items:flex-start;gap:10px;page-break-inside:avoid">
      <div style="flex:1;min-width:0">
        <div style="font-size:11px;font-weight:700;color:#0d3a1e;line-height:1.45;margin-bottom:4px">
          <a href="{escape(url)}" style="color:#0d3a1e;text-decoration:none">{escape(title)}</a>
        </div>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <span style="background:#d4f0dd;color:#155724;padding:1px 7px;border-radius:4px;font-size:9px;font-weight:600">{escape(etype)}</span>
          <span style="font-size:9.5px;color:#666">{escape(source)}</span>
        </div>
      </div>
      <div style="flex-shrink:0;text-align:right">
        <div style="background:#1a7a3c;color:#fff;font-size:9px;font-weight:700;padding:2px 9px;border-radius:20px;margin-bottom:4px">예정</div>
        <div style="font-size:10.5px;font-weight:700;color:#1a4a2a">{escape(date)}</div>
      </div>
    </div>"""
    sch_html += "</div>"

    # ── 뉴스 섹션 ──────────────────────────────────────────────────────────
    # 키워드 태그 모음
    kw_set = list(dict.fromkeys(r.get("keyword","") for r in sel_n if r.get("keyword","")))
    kw_tags = " ".join(f'<span style="display:inline-block;background:#e8e4dc;color:#555;padding:1px 9px;border-radius:20px;font-size:9px;font-weight:600">{escape(k)}</span>' for k in kw_set)

    news_html = f'<div style="margin-bottom:16px;padding:0 8px">{sec_header(3,"언론 모니터링",len(sel_n))}'
    if kw_tags:
        news_html += f'<div style="margin-bottom:8px;display:flex;gap:5px;flex-wrap:wrap">{kw_tags}</div>'
    if not sel_n:
        news_html += '<p style="padding:14px;text-align:center;color:#aaa;font-size:11px">수집된 기사가 없습니다.</p>'
    else:
        for r in sel_n:
            title  = r.get("title","")
            source = r.get("source","")
            date   = r.get("date","")[:10]
            kw     = r.get("keyword","응급의료")
            url    = fix_url(r.get("url",""))
            border = _KW_BORDER.get(kw, "#f0aaaa")
            badge_bg = _KW_BADGE_BG.get(kw, "#1B3A6B")
            news_html += f"""
    <a href="{escape(url)}" style="display:block;color:inherit;text-decoration:none;background:#fff;border-radius:10px;border-left:5px solid {border};box-shadow:0 1px 6px rgba(0,0,0,.07);padding:9px 14px;margin-bottom:8px;page-break-inside:avoid">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">
        <div style="flex:1;min-width:0">
          <div style="font-size:11px;font-weight:700;color:#6b0000;line-height:1.45;margin-bottom:3px">{escape(title)}</div>
          <div style="font-size:9.5px;color:#888">
            <span style="font-weight:600;color:#555">{escape(source)}</span><span style="margin-left:6px">{escape(date)}</span>
          </div>
        </div>
        <span style="flex-shrink:0;background:{badge_bg};color:#fff;padding:2px 9px;border-radius:20px;font-size:9px;font-weight:700;white-space:nowrap;margin-top:2px">{escape(kw)}</span>
      </div>
    </a>"""
    news_html += "</div>"

    # ── 전체 조립 ──────────────────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a1a;font-size:11px;line-height:1.6;background:#fdfcf9}}
a{{text-decoration:none;color:inherit}}
@page{{size:A4 portrait;margin:6mm 6mm}}
@media print{{
  *{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
  html{{zoom:0.86}}
  body{{background:#fdfcf9;margin:0;padding:0}}
  a[href]:after{{content:none !important}}
}}
</style>
</head>
<body>
<div style="width:100%;margin:0 auto;padding:0">

  <div style="background:linear-gradient(135deg,#0d2a5e 0%,#1B3A6B 60%,#2A5298 100%);color:#fff;padding:14px 20px;border-radius:0;display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;box-shadow:0 3px 12px rgba(13,42,94,.22)">
    <div>
      <div style="font-size:9px;letter-spacing:2px;opacity:.6;margin-bottom:5px">응급의료정책연구팀</div>
      <div style="font-size:19px;font-weight:900;letter-spacing:-.3px;line-height:1.2">응급의료 동향 모니터링</div>
    </div>
    <div style="text-align:right">
      <div style="font-size:18px;font-weight:700;letter-spacing:.5px">{today_fmt}</div>
      <div style="font-size:9px;opacity:.55;margin-top:3px">{generated} 생성</div>
    </div>
  </div>

  <div style="padding:0 8px">
    <div style="display:flex;gap:8px;margin-bottom:14px">{cards_html}</div>
    {asm_html}
    {sch_html}
    {news_html}
    <div style="margin-top:12px;padding-top:8px;border-top:1px solid #ddd;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:9px;color:#999">본 보고서는 자동 수집·검토된 항목만 포함됩니다. 중요 사항은 반드시 원문을 확인하십시오.</span>
      <span style="font-size:9px;color:#999;font-weight:600">응급의료정책연구팀</span>
    </div>
  </div>
</div>
</body></html>"""

# ══════════════════════════════════════════════════════════════════════════════
# PDF 생성 (playwright)
# ══════════════════════════════════════════════════════════════════════════════
def generate_pdf_bytes(sel_a, sel_s, sel_n, today) -> bytes:
    from playwright.sync_api import sync_playwright
    html_str = build_html(sel_a, sel_s, sel_n, today)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.emulate_media(media="screen")
        page.set_content(html_str, wait_until="networkidle")
        pdf_bytes = page.pdf(
            format="A4",
            print_background=True,
            scale=0.82,
            margin={"top":"8mm","right":"10mm","bottom":"8mm","left":"10mm"},
        )
        browser.close()
    return pdf_bytes

# ══════════════════════════════════════════════════════════════════════════════
# 데이터 로드
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _load_data(pattern):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files = sorted(glob.glob(os.path.join(current_dir, pattern)))
    if not files: return []
    try:
        with open(files[-1], encoding="utf-8") as f:
            return json.load(f)
    except: return []

asm_raw  = _load_data("assembly_results_*.json")
sch_raw  = _load_data("schedule_results_*.json")
news_raw = _load_data("news_results_*.json")

if "phase" not in st.session_state:
    st.session_state.phase = "SELECT"

# ══════════════════════════════════════════════════════════════════════════════
# [A] 선택 화면
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.phase == "SELECT":
    st.title("🚑 NMC 정책 모니터링 보고서 생성기")
    sel_a, sel_s, sel_n = [], [], []

    st.subheader("❶ 의안 현황")
    if not asm_raw: st.info("의안 데이터가 없습니다.")
    for i, r in enumerate(asm_raw):
        link = get_link(r, "url", "bill_link", "link")
        c1, c2 = st.columns([0.82, 0.18])
        with c1:
            if st.checkbox(f"[{r.get('status','접수')}] {r.get('bill_name','')}", key=f"a{i}"):
                sel_a.append(r)
        with c2:
            if link != "#":
                st.markdown(f'<a href="{link}" target="_blank" style="font-size:13px;color:#1B3A6B;text-decoration:none;">🔗 원문보기</a>', unsafe_allow_html=True)

    st.write("---")
    st.subheader("❷ 주요 일정")
    if not sch_raw: st.info("일정 데이터가 없습니다.")
    for i, r in enumerate(sch_raw):
        link = get_link(r, "url", "link")
        c1, c2 = st.columns([0.82, 0.18])
        with c1:
            if st.checkbox(f"📅 [{r.get('date','')}] {r.get('title','')}", key=f"s{i}"):
                sel_s.append(r)
        with c2:
            if link != "#":
                st.markdown(f'<a href="{link}" target="_blank" style="font-size:13px;color:#1B3A6B;text-decoration:none;">🔗 원문보기</a>', unsafe_allow_html=True)

    st.write("---")
    st.subheader("❸ 언론 모니터링")
    if not news_raw: st.info("뉴스 데이터가 없습니다.")
    for i, r in enumerate(news_raw):
        link = get_link(r, "url", "link")
        c1, c2 = st.columns([0.82, 0.18])
        with c1:
            if st.checkbox(f"📰 [{r.get('source','')}] {r.get('title','')}", key=f"n{i}"):
                sel_n.append(r)
        with c2:
            if link != "#":
                st.markdown(f'<a href="{link}" target="_blank" style="font-size:13px;color:#1B3A6B;text-decoration:none;">🔗 기사보기</a>', unsafe_allow_html=True)

    st.write("---")
    if st.button("✨ 보고서 발행", use_container_width=True):
        st.session_state.sel_a = sel_a
        st.session_state.sel_s = sel_s
        st.session_state.sel_n = sel_n
        st.session_state.pdf_ready = False
        st.session_state.phase = "REPORT"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# [B] 보고서 화면
# ══════════════════════════════════════════════════════════════════════════════
else:
    today = datetime.now().strftime("%Y-%m-%d")

    if st.sidebar.button("🔙 다시 선택하기"):
        st.session_state.phase = "SELECT"
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📥 PDF 저장")

    if st.sidebar.button("📄 PDF 생성하기", use_container_width=True):
        with st.spinner("PDF 생성 중..."):
            try:
                pdf_bytes = generate_pdf_bytes(
                    st.session_state.get("sel_a", []),
                    st.session_state.get("sel_s", []),
                    st.session_state.get("sel_n", []),
                    today,
                )
                st.session_state.pdf_bytes = pdf_bytes
                st.session_state.pdf_ready = True
            except Exception as e:
                st.sidebar.error(f"PDF 생성 실패: {e}")

    if st.session_state.get("pdf_ready"):
        st.sidebar.download_button(
            label="⬇️ PDF 다운로드",
            data=st.session_state.pdf_bytes,
            file_name=f"응급의료_모니터링_{today.replace('-','')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    if not (st.session_state.get("sel_a") or st.session_state.get("sel_s") or st.session_state.get("sel_n")):
        st.warning("선택된 항목이 없습니다. '다시 선택하기'를 눌러 항목을 체크해 주세요.")
        st.stop()

    st.markdown(
        "<style>[data-testid='stHeader']{display:none}"
        "@media print{header,footer,.stButton,[data-testid='stSidebar']{display:none!important}"
        ".main{padding:0!important}}</style>",
        unsafe_allow_html=True,
    )

    # 화면 렌더링
    html = build_html(
        st.session_state.get("sel_a", []),
        st.session_state.get("sel_s", []),
        st.session_state.get("sel_n", []),
        today,
    )
    st.markdown(html, unsafe_allow_html=True)
