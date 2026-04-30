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

# ── 폰트 탐색 ──────────────────────────────────────────────────────────────────
def _find_font(bold=False):
    base_dir  = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")
    fname     = "NanumGothicBold.ttf" if bold else "NanumGothic.ttf"
    for p in [
        os.path.join(fonts_dir, fname),
        os.path.join(base_dir,  fname),
        f"/usr/share/fonts/truetype/nanum/{fname}",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    ]:
        if os.path.exists(p):
            return p
    return None

def _debug_font_info():
    base_dir  = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")
    flist = os.listdir(fonts_dir) if os.path.exists(fonts_dir) else "폴더 없음"
    return (
        f"app.py 위치: {base_dir}\n"
        f"fonts/ 존재: {os.path.exists(fonts_dir)}\n"
        f"fonts/ 파일: {flist}\n"
        f"Regular: {_find_font(False)}\n"
        f"Bold:    {_find_font(True)}"
    )

# ── PDF 생성 ───────────────────────────────────────────────────────────────────
def generate_pdf_bytes(sel_a, sel_s, sel_n, today) -> bytes:
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors

    FONT_REG  = _find_font(False)
    FONT_BOLD = _find_font(True) or FONT_REG
    if not FONT_REG:
        raise FileNotFoundError("fonts/ 폴더에 NanumGothic.ttf, NanumGothicBold.ttf 를 넣어주세요.")

    pdfmetrics.registerFont(TTFont("KR",   FONT_REG))
    pdfmetrics.registerFont(TTFont("KR-B", FONT_BOLD))

    W, H = A4
    M    = 14*mm
    CW   = W - 2*M

    NAVY  = colors.HexColor("#1B3A6B")
    GREEN = colors.HexColor("#28A745")
    RED   = colors.HexColor("#DC3545")
    WHITE = colors.white
    EGRAY = colors.HexColor("#D0D7E5")
    KW_COLOR = {
        "중증응급":    colors.HexColor("#800000"),
        "중증외상":    colors.HexColor("#6F42C1"),
        "상급종합병원": colors.HexColor("#A52A2A"),
    }

    buf = io.BytesIO()
    cv  = canvas.Canvas(buf, pagesize=A4)

    # 헤더
    cv.setFillColor(NAVY)
    cv.rect(M, H-42*mm, CW, 26*mm, fill=1, stroke=0)
    cv.setFillColor(colors.HexColor("#2A5298"))
    cv.rect(M+CW*0.55, H-42*mm, CW*0.45, 26*mm, fill=1, stroke=0)
    cv.setFillColor(colors.HexColor("#8FA8C8"))
    cv.setFont("KR", 7)
    cv.drawString(M+4*mm, H-20*mm, "응급의료정책연구팀")
    cv.setFillColor(WHITE)
    cv.setFont("KR-B", 15)
    cv.drawString(M+4*mm, H-31*mm, "응급의료 동향 모니터링")
    cv.setFont("KR-B", 13)
    cv.drawRightString(W-M-4*mm, H-25*mm, today)
    cv.setFont("KR", 7.5)
    cv.setFillColor(colors.HexColor("#8FA8C8"))
    cv.drawRightString(W-M-4*mm, H-33*mm, "08:30 생성")

    # 요약 카드
    card_items = [
        ("계류 의안", len(sel_a), "#EBF1F9", "#1B3A6B"),
        ("예정 일정", len(sel_s), "#E8F5E9", "#28A745"),
        ("언론 기사", len(sel_n), "#FDECEA", "#DC3545"),
        ("전체",      len(sel_a)+len(sel_s)+len(sel_n), "#F3F4F6", "#495057"),
    ]
    cw4    = (CW - 9*mm) / 4
    card_y = H - 60*mm
    for i, (label, val, bg, fc) in enumerate(card_items):
        cx = M + i*(cw4+3*mm)
        cv.setFillColor(colors.HexColor(bg))
        cv.roundRect(cx, card_y, cw4, 16*mm, 2*mm, fill=1, stroke=0)
        cv.setFillColor(colors.HexColor(fc))
        cv.setFont("KR-B", 16)
        cv.drawCentredString(cx+cw4/2, card_y+8*mm, str(val))
        cv.setFillColor(colors.HexColor("#555"))
        cv.setFont("KR", 7)
        cv.drawCentredString(cx+cw4/2, card_y+3.5*mm, label)

    y = [H - 65*mm]

    def _footer():
        cv.setStrokeColor(colors.HexColor("#DDDDDD"))
        cv.line(M, 17*mm, W-M, 17*mm)
        cv.setFillColor(colors.HexColor("#AAAAAA"))
        cv.setFont("KR", 6.5)
        cv.drawString(M, 12*mm, "본 보고서는 자동 수집·검토된 항목만 포함됩니다. 중요 사항은 반드시 원문을 확인하십시오.")
        cv.drawRightString(W-M, 12*mm, "응급의료정책연구팀")

    def chk(need):
        if y[0] - need < 22*mm:
            _footer()
            cv.showPage()
            y[0] = H - 15*mm

    def sec_title(title, count):
        chk(18*mm)
        y[0] -= 7*mm
        cv.setFillColor(NAVY); cv.setFont("KR-B", 10.5)
        cv.drawString(M, y[0], title)
        bw = 20*mm
        cv.setFillColor(NAVY)
        cv.roundRect(W-M-bw, y[0]-1.5*mm, bw, 6*mm, 2*mm, fill=1, stroke=0)
        cv.setFillColor(WHITE); cv.setFont("KR", 7.5)
        cv.drawCentredString(W-M-bw/2, y[0]+0.5*mm, f"총 {count}건")
        y[0] -= 7*mm

    def draw_tag(x, ty, text, bg, fg="#fff"):
        tw = len(text)*2.8*mm + 5*mm
        cv.setFillColor(colors.HexColor(bg))
        cv.roundRect(x, ty-1.8*mm, tw, 5.5*mm, 1.5*mm, fill=1, stroke=0)
        cv.setFillColor(colors.HexColor(fg))
        cv.setFont("KR", 7)
        cv.drawCentredString(x+tw/2, ty+0.2*mm, text)
        return tw + 1.5*mm

    def card(bcolor, h, link, draw_fn):
        chk(h)
        cy2 = y[0] - h
        cv.setFillColor(WHITE)
        cv.rect(M, cy2, CW, h, fill=1, stroke=0)
        cv.setFillColor(bcolor)
        cv.rect(M, cy2, 3*mm, h, fill=1, stroke=0)
        cv.setStrokeColor(EGRAY); cv.setLineWidth(0.4)
        cv.rect(M, cy2, CW, h, fill=0, stroke=1)
        if link and link != "#":
            cv.linkURL(link, (M, cy2, M+CW, cy2+h))
        draw_fn(cy2, h)
        y[0] -= h + 2.5*mm

    # ❶ 의안
    if sel_a:
        sec_title("❶ 의안 현황", len(sel_a))
        for r in sel_a:
            name   = r.get("bill_name", "")
            summ   = r.get("summary", "")[:140]
            notice = r.get("legislative_notice", "")
            kw     = r.get("keyword", "")
            status = r.get("status", "접수")
            date   = r.get("proposed_date", "")
            link   = get_link(r, "url", "bill_link", "link")
            sl     = [summ[i:i+46] for i in range(0, len(summ), 46)]
            h      = (6 + 6.5 + 5 + len(sl)*4.8 + 3)*mm

            def draw_a(cy2, h, n=name, s=sl, no=notice, k=kw, st=status, d=date):
                ty = cy2 + h - 6*mm
                tx = M+4*mm
                tx += draw_tag(tx, ty, k,  "#1B3A6B")
                tx += draw_tag(tx, ty, st, "#1B3A6B")
                if no:
                    draw_tag(tx, ty, no[:30], "#FFF9E6", "#856404")
                ty -= 6.5*mm
                cv.setFillColor(NAVY); cv.setFont("KR-B", 9)
                cv.drawString(M+4*mm, ty, n[:52]+("…" if len(n)>52 else ""))
                ty -= 5*mm
                cv.setFillColor(colors.HexColor("#888")); cv.setFont("KR", 7)
                cv.drawString(M+4*mm, ty, f"발의: {d}")
                ty -= 5*mm
                if s:
                    bg_h = len(s)*4.8*mm + 2*mm
                    cv.setFillColor(colors.HexColor("#F8F9FA"))
                    cv.rect(M+3.5*mm, ty - bg_h + 5*mm, CW-7*mm, bg_h, fill=1, stroke=0)
                    cv.setFillColor(colors.HexColor("#444")); cv.setFont("KR", 7.5)
                    for line in s:
                        cv.drawString(M+5*mm, ty, line); ty -= 4.8*mm

            card(NAVY, h, link, draw_a)

    # ❷ 일정
    if sel_s:
        sec_title("❷ 주요 일정", len(sel_s))
        for r in sel_s:
            title  = r.get("title", "")
            date   = r.get("date", "")
            etype  = r.get("event_type", "토론회")
            source = r.get("source", "")
            link   = get_link(r, "url", "link")
            h      = 19*mm

            def draw_s(cy2, h, t=title, d=date, et=etype, src=source):
                ty = cy2 + h - 5.5*mm
                tx = M+4*mm
                tx += draw_tag(tx, ty, et,    "#28A745")
                draw_tag(tx, ty, "예정", "#28A745")
                ty -= 6.5*mm
                cv.setFillColor(colors.HexColor("#222")); cv.setFont("KR-B", 9)
                cv.drawString(M+4*mm, ty, t[:48]+("…" if len(t)>48 else ""))
                cv.setFillColor(NAVY); cv.setFont("KR-B", 9)
                cv.drawRightString(W-M-3*mm, ty, d)
                ty -= 5*mm
                cv.setFillColor(colors.HexColor("#888")); cv.setFont("KR", 7)
                cv.drawString(M+4*mm, ty, src)

            card(GREEN, h, link, draw_s)

    # ❸ 뉴스
    if sel_n:
        sec_title("❸ 언론 모니터링", len(sel_n))
        for r in sel_n:
            title  = r.get("title", "")
            source = r.get("source", "")
            date   = r.get("date", "")
            kw     = r.get("keyword", "응급의료")
            kc     = KW_COLOR.get(kw, RED)
            link   = get_link(r, "url", "link")
            h      = 15*mm

            def draw_n(cy2, h, t=title, s=source, d=date, k=kw, kc=kc):
                ty = cy2 + h - 5.5*mm
                cv.setFillColor(NAVY); cv.setFont("KR-B", 9)
                cv.drawString(M+4*mm, ty, t[:50]+("…" if len(t)>50 else ""))
                kw_w = len(k)*2.8*mm + 6*mm
                cv.setFillColor(kc)
                cv.roundRect(W-M-kw_w-2*mm, ty-2*mm, kw_w, 6*mm, 2*mm, fill=1, stroke=0)
                cv.setFillColor(WHITE); cv.setFont("KR", 7)
                cv.drawCentredString(W-M-kw_w/2-2*mm, ty+0.3*mm, k)
                ty -= 5.5*mm
                cv.setFillColor(colors.HexColor("#888")); cv.setFont("KR", 7)
                cv.drawString(M+4*mm, ty, f"{s} | {d}")

            card(RED, h, link, draw_n)

    _footer()
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
        c1, c2 = st.columns([0.82, 0.18])
        with c1:
            if st.checkbox(f"[{r.get('status','접수')}] {r.get('bill_name','')}", key=f"a{i}"):
                sel_a.append(r)
        with c2:
            if link != "#":
                st.markdown(f'<a href="{link}" target="_blank" style="font-size:13px;color:#1B3A6B;text-decoration:none;">🔗 원문보기</a>', unsafe_allow_html=True)

    st.write("---")
    st.subheader("❷ 주요 일정")
    if not sch_raw:
        st.info("일정 데이터가 없습니다.")
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
    if not news_raw:
        st.info("뉴스 데이터가 없습니다.")
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
                st.session_state.pdf_bytes  = pdf_bytes
                st.session_state.pdf_ready  = True
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
    na = len(st.session_state.get("sel_a", []))
    ns = len(st.session_state.get("sel_s", []))
    nn = len(st.session_state.get("sel_n", []))

    html = '<div style="background:#FBFBFB;padding:20px;font-family:sans-serif;">'
    html += (
        f'<div style="background:#1B3A6B;color:#fff;padding:20px 30px;'
        f'display:flex;justify-content:space-between;align-items:flex-end;border-radius:10px;">'
        f'<div><div style="font-size:10px;opacity:.8;">응급의료정책연구팀</div>'
        f'<div style="font-size:22px;font-weight:800;">응급의료 동향 모니터링</div></div>'
        f'<div style="text-align:right;"><div style="font-size:18px;font-weight:800;">{today}</div></div></div>'
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
