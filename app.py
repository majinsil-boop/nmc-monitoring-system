import streamlit as st
import glob
import json
import os
import io
from datetime import datetime
from html import escape

# ── URL 보정 ───────────────────────────────────────────────────────────────────
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

# ── 폰트 경로 탐색 ─────────────────────────────────────────────────────────────
def _find_font(bold=False):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")
    fname = "NanumGothicBold.ttf" if bold else "NanumGothic.ttf"

    candidates = [
        os.path.join(fonts_dir, fname),
        os.path.join(base_dir,  fname),
        f"/usr/share/fonts/truetype/nanum/{fname}",
        f"/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

# ── 폰트 경로 확인용 ───────────────────────────────────────────────────────────
def _debug_font_info():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")
    reg  = _find_font(bold=False)
    bold = _find_font(bold=True)
    flist = os.listdir(fonts_dir) if os.path.exists(fonts_dir) else "폴더 없음"
    return (
        f"app.py 위치: {base_dir}\n"
        f"fonts/ 폴더: {fonts_dir}\n"
        f"fonts/ 존재: {os.path.exists(fonts_dir)}\n"
        f"fonts/ 파일 목록: {flist}\n\n"
        f"탐색된 폰트(Regular): {reg}\n"
        f"탐색된 폰트(Bold):    {bold}"
    )

# ── PDF 생성 (reportlab) ───────────────────────────────────────────────────────
def generate_pdf_bytes(sel_a, sel_s, sel_n, today) -> bytes:
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors

    FONT_REG  = _find_font(bold=False)
    FONT_BOLD = _find_font(bold=True) or FONT_REG
    if not FONT_REG:
        raise FileNotFoundError(
            "한글 폰트를 찾을 수 없습니다.\n"
            "fonts/ 폴더에 NanumGothic.ttf, NanumGothicBold.ttf 를 넣어주세요."
        )

    pdfmetrics.registerFont(TTFont("KR",   FONT_REG))
    pdfmetrics.registerFont(TTFont("KR-B", FONT_BOLD))

    W, H = A4
    M = 15*mm   # margin
    CW = W - 2*M

    NAVY  = colors.HexColor("#1B3A6B")
    GREEN = colors.HexColor("#28A745")
    RED   = colors.HexColor("#DC3545")
    WHITE = colors.white
    LGRAY = colors.HexColor("#F8F9FA")
    EGRAY = colors.HexColor("#E2E8F0")
    KW_COLOR = {
        "중증응급":    colors.HexColor("#800000"),
        "중증외상":    colors.HexColor("#6F42C1"),
        "상급종합병원": colors.HexColor("#A52A2A"),
    }

    buf = io.BytesIO()
    cv  = canvas.Canvas(buf, pagesize=A4)

    # ── 헤더 (그라데이션 효과: 두 사각형 겹치기) ──────────────────────
    cv.setFillColor(NAVY)
    cv.rect(M, H-46*mm, CW, 30*mm, fill=1, stroke=0)
    cv.setFillColor(colors.HexColor("#2A5298"))
    cv.rect(M + CW*0.5, H-46*mm, CW*0.5, 30*mm, fill=1, stroke=0)

    cv.setFillColor(colors.HexColor("#8FA8C8"))
    cv.setFont("KR", 7.5)
    cv.drawString(M+5*mm, H-22*mm, "응급의료정책연구팀")
    cv.setFillColor(WHITE)
    cv.setFont("KR-B", 16)
    cv.drawString(M+5*mm, H-33*mm, "응급의료 동향 모니터링")
    cv.setFont("KR-B", 14)
    cv.drawRightString(W-M-4*mm, H-27*mm, today)
    cv.setFont("KR", 8)
    cv.setFillColor(colors.HexColor("#8FA8C8"))
    cv.drawRightString(W-M-4*mm, H-36*mm, "08:30 생성")

    # ── 요약 카드 ────────────────────────────────────────────────────
    card_data = [
        ("계류 의안", len(sel_a), "#EBF1F9", "#1B3A6B"),
        ("예정 일정", len(sel_s), "#E8F5E9", "#28A745"),
        ("언론 기사", len(sel_n), "#FDECEA", "#DC3545"),
        ("전체",      len(sel_a)+len(sel_s)+len(sel_n), "#F3F4F6", "#495057"),
    ]
    cw4 = (CW - 9*mm) / 4
    card_y = H - 67*mm
    for i, (label, val, bg, fc) in enumerate(card_data):
        cx = M + i*(cw4+3*mm)
        cv.setFillColor(colors.HexColor(bg))
        cv.roundRect(cx, card_y, cw4, 19*mm, 3*mm, fill=1, stroke=0)
        # 상단 컬러 강조선
        cv.setFillColor(colors.HexColor(fc))
        cv.roundRect(cx, card_y+16*mm, cw4, 3*mm, 1*mm, fill=1, stroke=0)
        cv.setFont("KR-B", 18)
        cv.drawCentredString(cx+cw4/2, card_y+8*mm, str(val))
        cv.setFillColor(colors.HexColor("#555555"))
        cv.setFont("KR", 7.5)
        cv.drawCentredString(cx+cw4/2, card_y+3*mm, label)

    y = H - 75*mm

    def new_page():
        nonlocal y
        # 푸터
        cv.setStrokeColor(colors.HexColor("#DDDDDD"))
        cv.line(M, 18*mm, W-M, 18*mm)
        cv.setFillColor(colors.HexColor("#AAAAAA"))
        cv.setFont("KR", 7)
        cv.drawString(M, 13*mm, "본 보고서는 자동 수집·검토된 항목만 포함됩니다. 중요 사항은 반드시 원문을 확인하십시오.")
        cv.drawRightString(W-M, 13*mm, "응급의료정책연구팀")
        cv.showPage()
        y = H - 15*mm

    def section_title(title, count):
        nonlocal y
        y -= 8*mm
        if y < 35*mm:
            new_page()
        cv.setFillColor(NAVY)
        cv.setFont("KR-B", 11)
        cv.drawString(M, y, title)
        bw = 22*mm
        cv.setFillColor(NAVY)
        cv.roundRect(W-M-bw, y-2*mm, bw, 7*mm, 2*mm, fill=1, stroke=0)
        cv.setFillColor(WHITE)
        cv.setFont("KR", 8)
        cv.drawCentredString(W-M-bw/2, y+0.5*mm, f"총 {count}건")
        y -= 8*mm

    def draw_tag(x, ty, text, bg, fg="#ffffff"):
        tw = len(text)*3.0*mm + 6*mm
        cv.setFillColor(colors.HexColor(bg))
        cv.roundRect(x, ty-2*mm, tw, 6*mm, 2*mm, fill=1, stroke=0)
        cv.setFillColor(colors.HexColor(fg))
        cv.setFont("KR", 7.5)
        cv.drawCentredString(x+tw/2, ty+0.3*mm, text)
        return tw + 2*mm

    def card_box(bcolor, height):
        nonlocal y
        if y - height < 25*mm:
            new_page()
        cy2 = y - height
        cv.setFillColor(WHITE)
        cv.rect(M, cy2, CW, height, fill=1, stroke=0)
        cv.setFillColor(bcolor)
        cv.rect(M, cy2, 3*mm, height, fill=1, stroke=0)
        cv.setStrokeColor(colors.HexColor("#D0D7E5"))
        cv.setLineWidth(0.5)
        cv.rect(M, cy2, CW, height, fill=0, stroke=1)
        return cy2

    def add_link(x, y2, w, h2, url):
        """클릭 가능한 링크 영역 추가"""
        if url and url != "#":
            from reportlab.lib.colors import HexColor
            cv.linkURL(url, (x, y2, x+w, y2+h2), relative=0)

    # ── ❶ 의안 ──────────────────────────────────────────────────────
    if sel_a:
        section_title("❶ 의안 현황", len(sel_a))
        for r in sel_a:
            name   = r.get("bill_name", "")
            summ   = r.get("summary", "")
            notice = r.get("legislative_notice", "")
            kw     = r.get("keyword", "")
            status = r.get("status", "접수")
            date   = r.get("proposed_date", "")
            link   = get_link(r, "url", "bill_link", "link")

            summ_lines = [summ[i:i+50] for i in range(0, min(len(summ), 150), 50)]
            h = (7 + 7 + 6 + len(summ_lines)*5 + 4)*mm

            cy2 = card_box(NAVY, h)
            ty  = cy2 + h - 7*mm

            # 태그
            tx = M+5*mm
            tx += draw_tag(tx, ty, kw, "#1B3A6B")
            tx += draw_tag(tx, ty, status, "#1B3A6B")
            if notice:
                draw_tag(tx, ty, notice[:30], "#FFF9E6", "#856404")
            ty -= 7*mm

            # 법안명 (링크)
            cv.setFillColor(NAVY)
            cv.setFont("KR-B", 9.5)
            cv.drawString(M+5*mm, ty, name[:52]+("…" if len(name)>52 else ""))
            add_link(M, cy2, CW, h, link)
            ty -= 6*mm

            # 발의일
            cv.setFillColor(colors.HexColor("#888888"))
            cv.setFont("KR", 7.5)
            cv.drawString(M+5*mm, ty, f"발의: {date}")
            ty -= 6*mm

            # 요약 (배경)
            if summ_lines:
                bg_h = len(summ_lines)*5*mm + 3*mm
                cv.setFillColor(colors.HexColor("#F8F9FA"))
                cv.rect(M+4*mm, ty-bg_h+4*mm, CW-8*mm, bg_h, fill=1, stroke=0)
                cv.setFillColor(colors.HexColor("#444444"))
                cv.setFont("KR", 8)
                for line in summ_lines:
                    cv.drawString(M+6*mm, ty, line)
                    ty -= 5*mm

            y -= h + 3*mm

    # ── ❷ 일정 ──────────────────────────────────────────────────────
    if sel_s:
        section_title("❷ 주요 일정", len(sel_s))
        for r in sel_s:
            title  = r.get("title", "")
            date   = r.get("date", "")
            etype  = r.get("event_type", "토론회")
            source = r.get("source", "")
            link   = get_link(r, "url", "link")
            h = 21*mm

            cy2 = card_box(GREEN, h)
            ty  = cy2 + h - 6*mm

            tx = M+5*mm
            tx += draw_tag(tx, ty, etype, "#28A745")
            draw_tag(tx, ty, "예정", "#28A745")
            ty -= 7*mm

            cv.setFillColor(colors.HexColor("#222222"))
            cv.setFont("KR-B", 9.5)
            cv.drawString(M+5*mm, ty, title[:48]+("…" if len(title)>48 else ""))
            cv.setFillColor(NAVY)
            cv.setFont("KR-B", 10)
            cv.drawRightString(W-M-4*mm, ty, date)
            add_link(M, cy2, CW, h, link)
            ty -= 5*mm

            cv.setFillColor(colors.HexColor("#888888"))
            cv.setFont("KR", 7.5)
            cv.drawString(M+5*mm, ty, source)
            y -= h + 3*mm

    # ── ❸ 뉴스 ──────────────────────────────────────────────────────
    if sel_n:
        section_title("❸ 언론 모니터링", len(sel_n))
        for r in sel_n:
            title  = r.get("title", "")
            source = r.get("source", "")
            date   = r.get("date", "")
            kw     = r.get("keyword", "응급의료")
            kw_col = KW_COLOR.get(kw, RED)
            link   = get_link(r, "url", "link")
            h = 17*mm

            cy2 = card_box(RED, h)
            ty  = cy2 + h - 6*mm

            # 제목
            cv.setFillColor(NAVY)
            cv.setFont("KR-B", 9.5)
            cv.drawString(M+5*mm, ty, title[:48]+("…" if len(title)>48 else ""))
            add_link(M, cy2, CW, h, link)

            # 키워드 배지
            kw_w = len(kw)*3.0*mm + 6*mm
            cv.setFillColor(kw_col)
            cv.roundRect(W-M-kw_w-3*mm, ty-2*mm, kw_w, 6*mm, 2*mm, fill=1, stroke=0)
            cv.setFillColor(WHITE)
            cv.setFont("KR", 7.5)
            cv.drawCentredString(W-M-kw_w/2-3*mm, ty+0.3*mm, kw)
            ty -= 6*mm

            cv.setFillColor(colors.HexColor("#888888"))
            cv.setFont("KR", 7.5)
            cv.drawString(M+5*mm, ty, f"{source} | {date}")
            y -= h + 3*mm

    # ── 푸터 ────────────────────────────────────────────────────────
    cv.setStrokeColor(colors.HexColor("#DDDDDD"))
    cv.line(M, 18*mm, W-M, 18*mm)
    cv.setFillColor(colors.HexColor("#AAAAAA"))
    cv.setFont("KR", 7)
    cv.drawString(M, 13*mm, "본 보고서는 자동 수집·검토된 항목만 포함됩니다. 중요 사항은 반드시 원문을 확인하십시오.")
    cv.drawRightString(W-M, 13*mm, "응급의료정책연구팀")

    cv.save()
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

    st.subheader("❶ 의안 현황")
    if not asm_raw:
        st.info("의안 데이터가 없습니다.")
    for i, r in enumerate(asm_raw):
        link = get_link(r, "url", "bill_link", "link")
        col_chk, col_link = st.columns([0.82, 0.18])
        with col_chk:
            if st.checkbox(f"[{r.get('status','접수')}] {r.get('bill_name','')}", key=f"check_a_{i}"):
                sel_a.append(r)
        with col_link:
            if link != "#":
                st.markdown(f'<a href="{link}" target="_blank" style="font-size:13px;color:#1B3A6B;text-decoration:none;">🔗 원문보기</a>', unsafe_allow_html=True)

    st.write("---")
    st.subheader("❷ 주요 일정")
    if not sch_raw:
        st.info("일정 데이터가 없습니다.")
    for i, r in enumerate(sch_raw):
        link = get_link(r, "url", "link")
        col_chk, col_link = st.columns([0.82, 0.18])
        with col_chk:
            if st.checkbox(f"📅 [{r.get('date','')}] {r.get('title','')}", key=f"check_s_{i}"):
                sel_s.append(r)
        with col_link:
            if link != "#":
                st.markdown(f'<a href="{link}" target="_blank" style="font-size:13px;color:#1B3A6B;text-decoration:none;">🔗 원문보기</a>', unsafe_allow_html=True)

    st.write("---")
    st.subheader("❸ 언론 모니터링")
    if not news_raw:
        st.info("뉴스 데이터가 없습니다.")
    for i, r in enumerate(news_raw):
        link = get_link(r, "url", "link")
        col_chk, col_link = st.columns([0.82, 0.18])
        with col_chk:
            if st.checkbox(f"📰 [{r.get('source','')}] {r.get('title','')}", key=f"check_n_{i}"):
                sel_n.append(r)
        with col_link:
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

    if st.sidebar.button("🔍 폰트 경로 확인", use_container_width=True):
        st.sidebar.code(_debug_font_info())

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

    if not (st.session_state.get("sel_a") or st.session_state.get("sel_s") or st.session_state.get("sel_n")):
        st.warning("선택된 항목이 없습니다. '다시 선택하기'를 눌러 항목을 체크해 주세요.")
        st.stop()

    st.markdown(
        "<style>[data-testid='stHeader']{display:none}"
        "@media print{header,footer,.stButton,[data-testid='stSidebar']{display:none!important}"
        ".main{padding:0!important}}</style>",
        unsafe_allow_html=True,
    )

    # ── 화면 렌더링 ────────────────────────────────────────────────────────────
    na = len(st.session_state.get("sel_a", []))
    ns = len(st.session_state.get("sel_s", []))
    nn = len(st.session_state.get("sel_n", []))

    html = '<div style="background:#FBFBFB;padding:20px;font-family:sans-serif;">'
    html += (
        f'<div style="background:#1B3A6B;color:#fff;padding:20px 30px;'
        f'display:flex;justify-content:space-between;align-items:flex-end;border-radius:10px;">'
        f'<div><div style="font-size:10px;opacity:.8;">응급의료정책연구팀</div>'
        f'<div style="font-size:22px;font-weight:800;">응급의료 동향 모니터링</div></div>'
        f'<div style="text-align:right;"><div style="font-size:18px;font-weight:800;">{today}</div></div>'
        f'</div>'
    )
    html += '<div style="display:flex;gap:10px;padding:15px 0;">'
    for icon, label, val, bg, fc in [
        ("📋","계류 의안",na,"#EBF1F9","#1B3A6B"),
        ("📅","예정 일정",ns,"#E8F5E9","#28A745"),
        ("📰","언론 기사",nn,"#FDECEA","#DC3545"),
        ("📊","전체",na+ns+nn,"#F3F4F6","#495057"),
    ]:
        html += (f'<div style="flex:1;background:{bg};border-radius:10px;padding:12px;text-align:center;">'
                 f'<div style="font-size:18px;">{icon}</div>'
                 f'<div style="font-size:11px;font-weight:700;">{label}</div>'
                 f'<div style="font-size:24px;font-weight:800;color:{fc};">{val}</div></div>')
    html += '</div>'

    def sec_title(text, count):
        return (f'<div style="font-size:16px;font-weight:800;color:#1B3A6B;'
                f'display:flex;justify-content:space-between;align-items:center;margin:14px 0 8px;">'
                f'{text}<span style="background:#1B3A6B;color:#fff;font-size:11px;'
                f'padding:2px 12px;border-radius:12px;">총 {count}건</span></div>')

    if st.session_state.get("sel_a"):
        html += sec_title("❶ 의안 현황", na)
        for r in st.session_state.sel_a:
            link   = get_link(r, "url", "bill_link", "link")
            name   = escape(r.get("bill_name",""))
            summ   = escape(r.get("summary",""))
            notice = escape(r.get("legislative_notice",""))
            kw     = escape(r.get("keyword",""))
            status = escape(r.get("status","접수"))
            a_tag  = f'<a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;font-size:14px;font-weight:800;color:#1B3A6B;">{name} 🔗</a>'
            html += (f'<div style="background:#fff;border:1px solid #E2E8F0;border-left:6px solid #1B3A6B;padding:15px;border-radius:12px;margin-bottom:10px;">'
                     f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">{a_tag}'
                     f'<span style="background:#1B3A6B;color:#fff;padding:2px 10px;border-radius:12px;font-size:10px;">{status}</span></div>'
                     f'<div style="margin-bottom:6px;"><span style="background:#1B3A6B;color:#fff;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;margin-right:4px;">{kw}</span>'
                     + (f'<span style="background:#FFF9E6;border:1px solid #FFD966;color:#856404;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;">{notice}</span>' if notice else '')
                     + f'</div><div style="font-size:11px;color:#444;line-height:1.5;background:#F8F9FA;padding:8px;border-radius:4px;">{summ}</div></div>')

    if st.session_state.get("sel_s"):
        html += sec_title("❷ 주요 일정", ns)
        for r in st.session_state.sel_s:
            link   = get_link(r, "url", "link")
            title  = escape(r.get("title",""))
            date   = escape(r.get("date",""))
            etype  = escape(r.get("event_type","토론회"))
            source = escape(r.get("source",""))
            a_tag  = f'<a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;font-size:13px;font-weight:800;color:#333;">{title} 🔗</a>'
            html += (f'<div style="background:#fff;border:1px solid #E2E8F0;border-left:6px solid #28A745;padding:12px 15px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">'
                     f'<div>{a_tag}<div style="margin-top:4px;"><span style="background:#E8F5E9;color:#1B5E20;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700;">{etype}</span>&nbsp;'
                     f'<span style="background:#E8F5E9;color:#1B5E20;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700;">예정</span>'
                     f'<div style="font-size:10px;color:#777;margin-top:2px;">{source}</div></div></div>'
                     f'<div style="font-size:12px;font-weight:800;margin-left:12px;">{date}</div></div>')

    if st.session_state.get("sel_n"):
        KW_COLOR = {"중증응급":"#800000","중증외상":"#6F42C1","상급종합병원":"#A52A2A"}
        html += sec_title("❸ 언론 모니터링", nn)
        for r in st.session_state.sel_n:
            link   = get_link(r, "url", "link")
            title  = escape(r.get("title",""))
            source = escape(r.get("source",""))
            date   = escape(r.get("date",""))
            kw     = r.get("keyword","응급의료")
            c_hex  = KW_COLOR.get(kw, "#DC3545")
            kw_esc = escape(kw)
            a_tag  = f'<a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;font-size:13px;font-weight:800;color:#1B3A6B;">{title} 🔗</a>'
            html += (f'<div style="background:#fff;border:1px solid #E2E8F0;border-left:6px solid #DC3545;padding:12px 15px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">'
                     f'<div>{a_tag}<div style="font-size:10px;color:#777;margin-top:3px;">{source} | {date}</div></div>'
                     f'<div style="background:{c_hex};color:#fff;padding:2px 10px;border-radius:12px;font-size:10px;font-weight:700;white-space:nowrap;margin-left:10px;">{kw_esc}</div></div>')

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
