import streamlit as st
import glob
import json
import os
import io
from datetime import datetime
from html import escape

# ── URL 보정 헬퍼 ──────────────────────────────────────────────────────────────
def fix_url(raw: str) -> str:
    if not raw or raw == "#":
        return "#"
    raw = raw.strip()
    if raw.startswith(("http://", "https://")):
        return raw
    return "https://" + raw

def get_link(record: dict, *keys) -> str:
    for k in keys:
        v = record.get(k, "")
        if v and v != "#":
            return fix_url(v)
    return "#"

# ── 한글 폰트 탐색 (repo 내장 → 시스템 순서로 탐색) ──────────────────────────
def _find_korean_font(bold=False):
    """
    1순위: repo 내 fonts/ 폴더 (가장 확실)
    2순위: 시스템 설치 경로 (로컬 개발 환경 대응)
    """
    keyword = "Bold" if bold else "Regular"

    # app.py 기준 상대 경로로 fonts/ 폴더 탐색
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")

    repo_candidates = [
        os.path.join(fonts_dir, f"NotoSansCJKkr-{keyword}.otf"),
        os.path.join(fonts_dir, f"NotoSansCJK-{keyword}.otf"),
        os.path.join(fonts_dir, f"NotoSansCJKkr-{keyword}.ttf"),
        os.path.join(fonts_dir, f"NotoSansCJK-{keyword}.ttf"),
        # bold 요청인데 없으면 Regular로 폴백
        os.path.join(fonts_dir, "NotoSansCJKkr-Regular.otf"),
        os.path.join(fonts_dir, "NotoSansCJK-Regular.otf"),
        os.path.join(fonts_dir, "NotoSansCJKkr-Regular.ttf"),
    ]

    for p in repo_candidates:
        if os.path.exists(p):
            return p

    # 시스템 경로 폴백 (로컬 개발 환경)
    system_candidates = [
        f"/usr/share/fonts/opentype/noto/NotoSansCJK-{keyword}.ttc",
        f"/usr/share/fonts/truetype/noto/NotoSansCJK-{keyword}.ttc",
        f"/usr/share/fonts/noto/NotoSansCJK-{keyword}.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in system_candidates:
        if os.path.exists(p):
            return p

    return None

# ── fpdf2 PDF 생성 ─────────────────────────────────────────────────────────────
def generate_pdf_bytes(sel_a, sel_s, sel_n, today) -> bytes:
    from fpdf import FPDF

    FONT_REG  = _find_korean_font(bold=False)
    FONT_BOLD = _find_korean_font(bold=True) or FONT_REG

    if not FONT_REG:
        raise FileNotFoundError(
            "한글 폰트를 찾을 수 없습니다.\n"
            "packages.txt에 다음을 추가하고 재배포하세요:\n"
            "fonts-noto-cjk"
        )

    KW_COLOR = {"중증응급": "#800000", "중증외상": "#6F42C1", "상급종합병원": "#A52A2A"}

    def hex2rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    class ReportPDF(FPDF):
        def __init__(self):
            super().__init__(orientation="P", unit="mm", format="A4")
            self.add_font("Noto", "",  FONT_REG)
            self.add_font("Noto", "B", FONT_BOLD)
            self.set_margins(15, 15, 15)
            self.set_auto_page_break(True, 18)

        def header_block(self, today_str):
            self.set_fill_color(*hex2rgb("#1B3A6B"))
            self.rect(15, 15, 180, 23, "F")
            self.set_xy(19, 17)
            self.set_font("Noto", size=7)
            self.set_text_color(180, 200, 230)
            self.cell(0, 5, "응급의료정책연구팀")
            self.set_xy(19, 22)
            self.set_font("Noto", "B", 14)
            self.set_text_color(255, 255, 255)
            self.cell(0, 8, "응급의료 동향 모니터링")
            self.set_xy(140, 19)
            self.set_font("Noto", "B", 13)
            self.set_text_color(255, 255, 255)
            self.cell(50, 7, today_str, align="R")
            self.set_xy(140, 28)
            self.set_font("Noto", size=7)
            self.set_text_color(180, 200, 230)
            self.cell(50, 5, "08:30 생성", align="R")

        def summary_cards(self, na, ns, nn):
            cards = [
                ("계류 의안", na,       "#EBF1F9", "#1B3A6B"),
                ("예정 일정", ns,       "#E8F5E9", "#28A745"),
                ("언론 기사", nn,       "#FDECEA", "#DC3545"),
                ("전체",      na+ns+nn, "#F3F4F6", "#495057"),
            ]
            x0, y0, w, h, gap = 15, 41, 43, 18, 2
            for i, (label, val, bg, fc) in enumerate(cards):
                x = x0 + i * (w + gap)
                self.set_fill_color(*hex2rgb(bg))
                self.rect(x, y0, w, h, "F")
                self.set_xy(x, y0 + 2)
                self.set_font("Noto", "B", 15)
                self.set_text_color(*hex2rgb(fc))
                self.cell(w, 7, str(val), align="C")
                self.set_xy(x, y0 + 10)
                self.set_font("Noto", size=7)
                self.set_text_color(60, 60, 60)
                self.cell(w, 5, label, align="C")

        def section_title(self, text, count):
            self.ln(4)
            self.set_font("Noto", "B", 11)
            self.set_text_color(*hex2rgb("#1B3A6B"))
            self.cell(145, 7, text)
            self.set_fill_color(*hex2rgb("#1B3A6B"))
            self.set_text_color(255, 255, 255)
            self.set_font("Noto", size=8)
            self.cell(35, 7, f"총 {count}건", fill=True, align="C")
            self.ln(9)

        def tag(self, text, bg="#1B3A6B", fg="#ffffff"):
            self.set_fill_color(*hex2rgb(bg))
            self.set_text_color(*hex2rgb(fg))
            self.set_font("Noto", size=7)
            w = self.get_string_width(text) + 5
            self.cell(w, 5, text, fill=True)
            self.cell(2, 5, "")

        def card(self, border_color, draw_fn):
            y_start = self.get_y()
            self.set_x(19)
            draw_fn()
            y_end = self.get_y()
            card_h = y_end - y_start + 2
            self.set_fill_color(*hex2rgb(border_color))
            self.rect(15, y_start - 1, 2.5, card_h, "F")
            self.set_draw_color(210, 218, 230)
            self.rect(15, y_start - 1, 180, card_h)
            self.ln(4)

    pdf = ReportPDF()
    pdf.add_page()
    pdf.header_block(today)
    pdf.summary_cards(len(sel_a), len(sel_s), len(sel_n))
    pdf.set_xy(15, 63)

    # ❶ 의안
    if sel_a:
        pdf.section_title("❶ 의안 현황", len(sel_a))
        for r in sel_a:
            name   = r.get("bill_name", "")
            summ   = r.get("summary", "")
            notice = r.get("legislative_notice", "")
            kw     = r.get("keyword", "")
            status = r.get("status", "접수")
            date   = r.get("proposed_date", "")

            def draw_assembly(n=name, s=summ, no=notice, k=kw, st=status, d=date):
                pdf.set_x(19)
                pdf.tag(k, "#1B3A6B")
                pdf.tag(st, "#1B3A6B")
                if no:
                    pdf.tag(no, "#FFF9E6", "#856404")
                pdf.ln(6)
                pdf.set_x(19)
                pdf.set_font("Noto", "B", 9)
                pdf.set_text_color(*hex2rgb("#1B3A6B"))
                pdf.multi_cell(170, 5, n)
                pdf.set_x(19)
                pdf.set_font("Noto", size=7)
                pdf.set_text_color(120, 120, 120)
                pdf.cell(0, 5, f"발의: {d}")
                pdf.ln(6)
                if s:
                    pdf.set_x(19)
                    pdf.set_fill_color(248, 249, 250)
                    pdf.set_font("Noto", size=7.5)
                    pdf.set_text_color(60, 60, 60)
                    pdf.multi_cell(170, 5, s[:200] + ("…" if len(s) > 200 else ""))
                pdf.ln(2)

            pdf.card("#1B3A6B", draw_assembly)

    # ❷ 일정
    if sel_s:
        pdf.section_title("❷ 주요 일정", len(sel_s))
        for r in sel_s:
            title  = r.get("title", "")
            date   = r.get("date", "")
            etype  = r.get("event_type", "토론회")
            source = r.get("source", "")

            def draw_schedule(t=title, d=date, et=etype, src=source):
                pdf.set_x(19)
                pdf.tag(et, "#28A745")
                pdf.tag("예정", "#28A745")
                pdf.ln(6)
                pdf.set_x(19)
                pdf.set_font("Noto", "B", 9)
                pdf.set_text_color(40, 40, 40)
                pdf.cell(140, 5, t[:55] + ("…" if len(t) > 55 else ""))
                pdf.set_font("Noto", "B", 9)
                pdf.set_text_color(*hex2rgb("#1B3A6B"))
                pdf.cell(30, 5, d, align="R")
                pdf.ln(6)
                pdf.set_x(19)
                pdf.set_font("Noto", size=7)
                pdf.set_text_color(130, 130, 130)
                pdf.cell(0, 4, src)
                pdf.ln(5)

            pdf.card("#28A745", draw_schedule)

    # ❸ 뉴스
    if sel_n:
        pdf.section_title("❸ 언론 모니터링", len(sel_n))
        for r in sel_n:
            title  = r.get("title", "")
            source = r.get("source", "")
            date   = r.get("date", "")
            kw     = r.get("keyword", "응급의료")
            c_hex  = KW_COLOR.get(kw, "#DC3545")

            def draw_news(t=title, s=source, d=date, k=kw, c=c_hex):
                pdf.set_x(19)
                pdf.set_font("Noto", "B", 9)
                pdf.set_text_color(*hex2rgb("#1B3A6B"))
                kw_w = pdf.get_string_width(k) + 7
                pdf.cell(180 - kw_w, 5, t[:54] + ("…" if len(t) > 54 else ""))
                pdf.set_fill_color(*hex2rgb(c))
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Noto", size=7)
                pdf.cell(kw_w, 5, k, fill=True, align="C")
                pdf.ln(6)
                pdf.set_x(19)
                pdf.set_font("Noto", size=7)
                pdf.set_text_color(130, 130, 130)
                pdf.cell(0, 4, f"{s} | {d}")
                pdf.ln(5)

            pdf.card("#DC3545", draw_news)

    # 푸터
    pdf.set_y(-18)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Noto", size=7)
    pdf.set_text_color(170, 170, 170)
    pdf.cell(130, 5, "본 보고서는 자동 수집·검토된 항목만 포함됩니다. 중요 사항은 반드시 원문을 확인하십시오.")
    pdf.cell(50, 5, "응급의료정책연구팀", align="R")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ── 데이터 로드 ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="NMC 응급의료 모니터링", layout="wide")

def _load_data(pattern):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files = sorted(glob.glob(os.path.join(current_dir, pattern)))
    if not files:
        return []
    try:
        with open(files[-1], encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

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

    # ── ❶ 의안 ──────────────────────────────────────────────────────────────
    st.subheader("❶ 의안 현황")
    if not asm_raw:
        st.info("의안 데이터가 없습니다.")
    for i, r in enumerate(asm_raw):
        link = get_link(r, "url", "bill_link", "link")
        col_chk, col_link = st.columns([0.82, 0.18])
        with col_chk:
            checked = st.checkbox(
                f"[{r.get('status','접수')}] {r.get('bill_name','')}",
                key=f"check_a_{i}"
            )
            if checked:
                sel_a.append(r)
        with col_link:
            if link != "#":
                st.markdown(
                    f'<a href="{link}" target="_blank" '
                    f'style="font-size:13px;color:#1B3A6B;text-decoration:none;">'
                    f'🔗 원문보기</a>',
                    unsafe_allow_html=True
                )

    st.write("---")

    # ── ❷ 일정 ──────────────────────────────────────────────────────────────
    st.subheader("❷ 주요 일정")
    if not sch_raw:
        st.info("일정 데이터가 없습니다.")
    for i, r in enumerate(sch_raw):
        link = get_link(r, "url", "link")
        col_chk, col_link = st.columns([0.82, 0.18])
        with col_chk:
            checked = st.checkbox(
                f"📅 [{r.get('date','')}] {r.get('title','')}",
                key=f"check_s_{i}"
            )
            if checked:
                sel_s.append(r)
        with col_link:
            if link != "#":
                st.markdown(
                    f'<a href="{link}" target="_blank" '
                    f'style="font-size:13px;color:#1B3A6B;text-decoration:none;">'
                    f'🔗 원문보기</a>',
                    unsafe_allow_html=True
                )

    st.write("---")

    # ── ❸ 뉴스 ──────────────────────────────────────────────────────────────
    st.subheader("❸ 언론 모니터링")
    if not news_raw:
        st.info("뉴스 데이터가 없습니다.")
    for i, r in enumerate(news_raw):
        link = get_link(r, "url", "link")
        col_chk, col_link = st.columns([0.82, 0.18])
        with col_chk:
            checked = st.checkbox(
                f"📰 [{r.get('source','')}] {r.get('title','')}",
                key=f"check_n_{i}"
            )
            if checked:
                sel_n.append(r)
        with col_link:
            if link != "#":
                st.markdown(
                    f'<a href="{link}" target="_blank" '
                    f'style="font-size:13px;color:#1B3A6B;text-decoration:none;">'
                    f'🔗 기사보기</a>',
                    unsafe_allow_html=True
                )

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

    # 사이드바
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
        filename = f"응급의료_모니터링_{today.replace('-','')}.pdf"
        st.sidebar.download_button(
            label="⬇️ PDF 다운로드",
            data=st.session_state.pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
        )

    if not (st.session_state.get("sel_a") or
            st.session_state.get("sel_s") or
            st.session_state.get("sel_n")):
        st.warning("선택된 항목이 없습니다. '다시 선택하기'를 눌러 항목을 체크해 주세요.")
        st.stop()

    st.markdown(
        "<style>[data-testid='stHeader']{display:none}"
        "@media print{header,footer,.stButton,[data-testid='stSidebar']{display:none!important}"
        ".main{padding:0!important}}</style>",
        unsafe_allow_html=True,
    )

    # ── 화면용 보고서 렌더링 ──────────────────────────────────────────────────
    na = len(st.session_state.get("sel_a", []))
    ns = len(st.session_state.get("sel_s", []))
    nn = len(st.session_state.get("sel_n", []))

    html = '<div style="background:#FBFBFB;padding:20px;font-family:sans-serif;">'

    html += (
        f'<div style="background:#1B3A6B;color:#fff;padding:20px 30px;'
        f'display:flex;justify-content:space-between;align-items:flex-end;'
        f'border-radius:10px;-webkit-print-color-adjust:exact;">'
        f'<div><div style="font-size:10px;opacity:.8;">응급의료정책연구팀</div>'
        f'<div style="font-size:22px;font-weight:800;">응급의료 동향 모니터링</div></div>'
        f'<div style="text-align:right;">'
        f'<div style="font-size:18px;font-weight:800;">{today}</div>'
        f'</div></div>'
    )

    html += '<div style="display:flex;gap:10px;padding:15px 0;">'
    for icon, label, val, bg, fc in [
        ("📋","계류 의안", na,       "#EBF1F9","#1B3A6B"),
        ("📅","예정 일정", ns,       "#E8F5E9","#28A745"),
        ("📰","언론 기사", nn,       "#FDECEA","#DC3545"),
        ("📊","전체",      na+ns+nn, "#F3F4F6","#495057"),
    ]:
        html += (
            f'<div style="flex:1;background:{bg};border-radius:10px;padding:12px;'
            f'text-align:center;-webkit-print-color-adjust:exact;">'
            f'<div style="font-size:18px;">{icon}</div>'
            f'<div style="font-size:11px;font-weight:700;">{label}</div>'
            f'<div style="font-size:24px;font-weight:800;color:{fc};">{val}</div>'
            f'</div>'
        )
    html += '</div>'

    def sec_title(text, count):
        return (
            f'<div style="font-size:16px;font-weight:800;color:#1B3A6B;'
            f'display:flex;justify-content:space-between;align-items:center;margin:14px 0 8px;">'
            f'{text}'
            f'<span style="background:#1B3A6B;color:#fff;font-size:11px;'
            f'padding:2px 12px;border-radius:12px;">총 {count}건</span></div>'
        )

    if st.session_state.get("sel_a"):
        html += sec_title("❶ 의안 현황", na)
        for r in st.session_state.sel_a:
            link   = get_link(r, "url", "bill_link", "link")
            name   = escape(r.get("bill_name", ""))
            summ   = escape(r.get("summary", ""))
            notice = escape(r.get("legislative_notice", ""))
            kw     = escape(r.get("keyword", ""))
            status = escape(r.get("status", "접수"))
            a_tag  = f'<a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;font-size:14px;font-weight:800;color:#1B3A6B;">{name} 🔗</a>'
            html += (
                f'<div style="background:#fff;border:1px solid #E2E8F0;border-left:6px solid #1B3A6B;'
                f'padding:15px;border-radius:12px;margin-bottom:10px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
                f'{a_tag}'
                f'<span style="background:#1B3A6B;color:#fff;padding:2px 10px;border-radius:12px;font-size:10px;">{status}</span>'
                f'</div>'
                f'<div style="margin-bottom:6px;">'
                f'<span style="background:#1B3A6B;color:#fff;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;margin-right:4px;">{kw}</span>'
                + (f'<span style="background:#FFF9E6;border:1px solid #FFD966;color:#856404;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;">{notice}</span>' if notice else '')
                + f'</div>'
                f'<div style="font-size:11px;color:#444;line-height:1.5;background:#F8F9FA;padding:8px;border-radius:4px;">{summ}</div>'
                f'</div>'
            )

    if st.session_state.get("sel_s"):
        html += sec_title("❷ 주요 일정", ns)
        for r in st.session_state.sel_s:
            link   = get_link(r, "url", "link")
            title  = escape(r.get("title", ""))
            date   = escape(r.get("date", ""))
            etype  = escape(r.get("event_type", "토론회"))
            source = escape(r.get("source", ""))
            a_tag  = f'<a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;font-size:13px;font-weight:800;color:#333;">{title} 🔗</a>'
            html += (
                f'<div style="background:#fff;border:1px solid #E2E8F0;border-left:6px solid #28A745;'
                f'padding:12px 15px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">'
                f'<div>{a_tag}'
                f'<div style="margin-top:4px;">'
                f'<span style="background:#E8F5E9;color:#1B5E20;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700;">{etype}</span>&nbsp;'
                f'<span style="background:#E8F5E9;color:#1B5E20;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700;">예정</span>'
                f'<div style="font-size:10px;color:#777;margin-top:2px;">{source}</div>'
                f'</div></div>'
                f'<div style="font-size:12px;font-weight:800;margin-left:12px;">{date}</div>'
                f'</div>'
            )

    if st.session_state.get("sel_n"):
        KW_COLOR = {"중증응급":"#800000","중증외상":"#6F42C1","상급종합병원":"#A52A2A"}
        html += sec_title("❸ 언론 모니터링", nn)
        for r in st.session_state.sel_n:
            link   = get_link(r, "url", "link")
            title  = escape(r.get("title", ""))
            source = escape(r.get("source", ""))
            date   = escape(r.get("date", ""))
            kw     = r.get("keyword", "응급의료")
            c_hex  = KW_COLOR.get(kw, "#DC3545")
            kw_esc = escape(kw)
            a_tag  = f'<a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;font-size:13px;font-weight:800;color:#1B3A6B;">{title} 🔗</a>'
            html += (
                f'<div style="background:#fff;border:1px solid #E2E8F0;border-left:6px solid #DC3545;'
                f'padding:12px 15px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">'
                f'<div>{a_tag}'
                f'<div style="font-size:10px;color:#777;margin-top:3px;">{source} | {date}</div>'
                f'</div>'
                f'<div style="background:{c_hex};color:#fff;padding:2px 10px;border-radius:12px;'
                f'font-size:10px;font-weight:700;white-space:nowrap;margin-left:10px;">{kw_esc}</div>'
                f'</div>'
            )

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
