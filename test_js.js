
const _els = {};
function makeEl(id) {
  return { id, textContent:'', innerHTML:'', className:'', value:'',
    style:{transition:'',opacity:''},
    classList:{ toggle:()=>{}, add:()=>{}, remove:()=>{}, contains:()=>false },
    remove:()=>{} };
}
const document = {
  getElementById: (id) => (_els[id] = _els[id] || makeEl(id)),
  querySelectorAll: () => [],
  createElement: () => makeEl('_tmp'),
  body: { appendChild: ()=>{} }
};
const window = {};
const fetch = () => Promise.resolve({ok:true, json:()=>Promise.resolve({})});
const alert = m => console.log('ALERT:', m);
const setTimeout = (fn, ms) => {};  // no-op

// ── 데이터 저장소 ─────────────────────────────────────────────────────────────
const store = { assembly: [], schedule: [], news: [] };
// checked: 'assembly-0', 'schedule-2', 'news-5' 형태
const checked = new Set();

// run_all.py가 데이터를 임베드할 때 이 줄을 교체합니다
const __PRELOADED__ = {"assembly": [{"bill_no": "2218323", "bill_name": "공공보건의료에 관한 법률 일부개정법률안 (소병훈의원 등 10인) (새창 열림)", "proposer": "의원", "proposed_date": "2026-04-14", "vote_date": "", "status": "접수", "url": "https://likms.assembly.go.kr/bill/bi/billDetailPage.do?billId=PRC_X2V6U0U4T0T8P1Q1O0O9N3L7M9T3V9", "keyword": "공공보건의료법", "summary": "및 주요내용 제안이유 및 주요내용 현행법은 지역 간 의료 격차 해소를 위하여 지역별 인구 분포, 의료인력 및 의료기관의 수 등을 평가ㆍ분석하여 의료서비스의 공급이 현저하게 부족한 지역을 의료취약지로 지정하도록 규정하고 있으나, 지역별ㆍ전문과목별 의사 수급의 적정성을 판단할 수 있는 객관적인 지표를 활용하도록 하는 규정은 부재한 실정임. 이에 따라 의료취약지", "status_changed_date": "2026-04-15", "legislative_notice": ""}], "schedule": [], "news": [{"keyword": "응급의료", "source": "view", "title": "\"응급실 뺑뺑이로 사망 4살 아이\"…'병원 과실' 인정 4억 배상 판결", "url": "https://view.asiae.co.kr/article/2026041520490014392", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:34"}, {"keyword": "응급의료", "source": "ulsanpress", "title": "다음 달부터 응급의료기관 재지정 평가", "url": "https://www.ulsanpress.net/news/articleView.html?idxno=573367", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:30"}, {"keyword": "응급의료", "source": "seoul", "title": "응급실 뺑뺑이에 숨진 4살…법원, 병원들 4억 배상 판결", "url": "https://www.seoul.co.kr/news/society/2026/04/15/20260415500273?wlog_tag3=naver", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:38"}, {"keyword": "응급의료", "source": "news1", "title": "'응급실 뺑뺑이' 돌다 하늘나라 간 4살 동희…'4억 배상' 판결", "url": "https://www.news1.kr/local/busan-gyeongnam/6137954", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:38"}, {"keyword": "응급의료", "source": "kookje", "title": "'응급실 뺑뺑이' 4살 아이 사망…\"병원, 유족에 4억 배상\" 판결", "url": "http://www.kookje.co.kr/news2011/asp/newsbody.asp?code=0300&key=20260415.99099004517", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:09"}, {"keyword": "응급의료", "source": "khan", "title": "응급실 뺑뺑이 끝에 아동 사망 사건…법원, 병원 2곳에 “4억원 공동 배...", "url": "https://www.khan.co.kr/article/202604152038005", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:38"}, {"keyword": "응급의료", "source": "joongang", "title": "4살 ‘응급실 뺑뺑이’ 돌게 한 병원…법원 “4억 배상하라”", "url": "https://www.joongang.co.kr/article/25420467", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:41"}, {"keyword": "응급의료", "source": "ikbc", "title": "\"응급환자 있다\" 거짓말에 '뺑뺑이'…아이 사망, 4억 배상", "url": "https://www.ikbc.co.kr/article/view/kbc202604150074", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:09"}, {"keyword": "응급의료", "source": "hankyung", "title": "응급실 뺑뺑이로 사망한 4살 아이…'병원 과실' 4억 배상", "url": "https://www.hankyung.com/article/2026041538287", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:30"}, {"keyword": "응급의료", "source": "hankookilbo", "title": "'응급실 뺑뺑이' 겪다 숨진 네 살 동희…법원, 4억 배상 판결", "url": "https://www.hankookilbo.com/news/article/A2026041522150003648?did=NA", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:09"}, {"keyword": "응급의료", "source": "hani", "title": "법원 “사망 초래한 응급환자 뺑뺑이, 거부한 병원들 책임”", "url": "https://www.hani.co.kr/arti/area/yeongnam/1254424.html", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:38"}, {"keyword": "응급의료", "source": "dt", "title": "‘응급실 뺑뺑이 사망’ 원인제공 병원…법원 “4억원 배상하라”", "url": "https://www.dt.co.kr/article/12057686?ref=naver", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:30"}, {"keyword": "응급의료", "source": "donga", "title": "‘응급실 뺑뺑이’로 숨진 아이…병원 2곳에 4억 배상 판결", "url": "https://www.donga.com/news/Society/article/all/20260415/133748578/1", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:09"}, {"keyword": "응급의료", "source": "dailian", "title": "‘응급실 뺑뺑이’로 4살 아이 사망…법원, 4억 배상 판결", "url": "https://www.dailian.co.kr/news/view/1634078/?sc=Naver", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:41"}, {"keyword": "응급의료", "source": "chosun", "title": "응급실 뺑뺑이로 사망... 병원에 4억 배상 판결", "url": "https://www.chosun.com/national/regional/2026/04/15/QEBWQKNHOVFZNLUOASNQHJBVU4/?utm_source=naver&utm_medium=referral&utm_campaign=naver-news", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:41"}, {"keyword": "응급실 뺑뺑이", "source": "yna", "title": "응급실 '뺑뺑이' 사망 원인제공 병원에 4억원 배상 판결", "url": "https://www.yna.co.kr/view/AKR20260415167500051?input=1195m", "date": "2026-04-15", "collected_at": "2026-04-16 08:34:32"}, {"keyword": "응급실 뺑뺑이", "source": "seoul", "title": "응급실 뺑뺑이 끊는다…최종 치료 못 하면 응급센터 퇴출", "url": "https://www.seoul.co.kr/news/society/2026/04/15/20260415500218?wlog_tag3=naver", "date": "2026-04-15", "collected_at": "2026-04-16 08:34:32"}, {"keyword": "응급실 뺑뺑이", "source": "mt", "title": "'응급실 뺑뺑이'에 숨진 네 살 동희…법원, 병원에 '4억 배상' 판결", "url": "https://www.mt.co.kr/thebio/2026/04/15/2026041517562951836", "date": "2026-04-15", "collected_at": "2026-04-16 08:34:32"}, {"keyword": "응급실 뺑뺑이", "source": "docdocdoc", "title": "'응급실 뺑뺑이' 소아 사망 사건에 양산부산대병원 등 4억 배상 판결", "url": "http://www.docdocdoc.co.kr/news/articleView.html?idxno=3038335", "date": "2026-04-15", "collected_at": "2026-04-16 08:34:32"}, {"keyword": "응급실", "source": "wowtv", "title": "'응급실 뺑뺑이' 끝 숨진 4살…法 \"4억 배상하라\"", "url": "http://www.wowtv.co.kr/NewsCenter/News/Read?articleId=A202604150512&t=NN", "date": "2026-04-15", "collected_at": "2026-04-16 08:34:06"}, {"keyword": "응급실", "source": "news", "title": "'응급실 뺑뺑이'로 끝내 사망…병원에 4억 원 배상 판결", "url": "https://news.tvchosun.com/site/data/html_dir/2026/04/15/2026041590275.html", "date": "2026-04-15", "collected_at": "2026-04-16 08:34:01"}, {"keyword": "응급실", "source": "news", "title": "응급실 '뺑뺑이' 사망 원인 제공 병원에 4억 원 배상 판결", "url": "https://news.sbs.co.kr/news/endPage.do?news_id=N1008519749&plink=ORI&cooper=NAVER", "date": "2026-04-15", "collected_at": "2026-04-16 08:34:06"}, {"keyword": "응급실", "source": "mk", "title": "‘응급실 뺑뺑이’ 아이 사망…법원 “거부·방치한 병원, 4억 배상하라...", "url": "https://www.mk.co.kr/article/12018118", "date": "2026-04-15", "collected_at": "2026-04-16 08:34:01"}, {"keyword": "응급실", "source": "kyeonggi", "title": "[단독] 의왕의 한 고교서 아드레날린 마신 학생들 응급실 이송", "url": "https://www.kyeonggi.com/article/20260415580556", "date": "2026-04-15", "collected_at": "2026-04-16 08:34:06"}, {"keyword": "응급실", "source": "khan", "title": "6년전 ‘응급실 뺑뺑이’로 숨진 김동희군 유족 손배소 일부 승소···4...", "url": "https://www.khan.co.kr/article/202604151917001", "date": "2026-04-15", "collected_at": "2026-04-16 08:34:01"}, {"keyword": "응급실", "source": "ggilbo", "title": "권역응급의료센터 최대 60곳으로 확대", "url": "https://www.ggilbo.com/news/articleView.html?idxno=1153013", "date": "2026-04-15", "collected_at": "2026-04-16 08:34:06"}, {"keyword": "응급실", "source": "edaily", "title": "4살 '응급실 뺑뺑이' 돌게 한 병원, 유족에 4억 배상 판결", "url": "http://www.edaily.co.kr/news/newspath.asp?newsid=05172566645416448", "date": "2026-04-15", "collected_at": "2026-04-16 08:34:06"}, {"keyword": "닥터헬기", "source": "metroseoul", "title": "영양군, \"골든타임 사수할 수 있나\"… 영양군 응급의료 체계, 공론화가...", "url": "http://www.metroseoul.co.kr/article/20260415500031", "date": "2026-04-15", "collected_at": "2026-04-16 08:33:45"}]}; // auto-loaded

// ── UI 갱신 ──────────────────────────────────────────────────────────────────
function refresh() {
  renderAll();
}

function renderAll() {
  const q = document.getElementById('qInput')?.value.trim().toLowerCase() || '';
  const out = [];

  if (store.assembly.length) out.push(renderAssembly(q));
  if (store.schedule.length) out.push(renderSchedule(q));
  if (store.news.length)     out.push(renderNews(q));

  document.getElementById('mainList').innerHTML = out.join('');
  updateStats();
}

// ── 의안 섹션 ────────────────────────────────────────────────────────────────
function importanceAsm(item) {
  if (item.legislative_notice && isNoticeActive(item.legislative_notice)) return '중요';
  const s = item.status || '';
  if (['위원회심사','본회의','공포'].some(x => s.includes(x))) return '중요';
  return '보통';
}
function isNoticeActive(notice) {
  const m = (notice||'').match(/~\s*(\d{4}-\d{2}-\d{2})/);
  if (!m) return !!notice;
  return new Date(m[1]) >= new Date(new Date().toDateString());
}

function renderAssembly(q) {
  const items = store.assembly.map((a, i) => ({...a, _k:'assembly-'+i}))
    .filter(a => !q || (a.bill_name||'').toLowerCase().includes(q));

  const sel = items.filter(a => checked.has(a._k)).length;
  const rows = items.length ? items.map(a => {
    const lvl   = importanceAsm(a);
    const on    = checked.has(a._k);
    const name  = (a.bill_name||'').replace(' (새창 열림)','').trim();
    const tagC  = lvl==='중요' ? 'tag-red' : 'tag-orange';
    const notice = a.legislative_notice && isNoticeActive(a.legislative_notice) ? a.legislative_notice : '';
    return `
    <div class="item ${on?'':'off'}" id="item-${a._k}">
      <input type="checkbox" ${on?'checked':''} onchange="toggle('${a._k}',this.checked)">
      <div class="item-body">
        <div class="item-title">
          ${a.url ? `<a href="${esc(a.url)}" target="_blank">${esc(name)}</a>` : esc(name)}
        </div>
        <div class="item-meta">
          <span class="tag ${tagC}">${lvl}</span>
          <span class="tag tag-blue">${esc(a.keyword||'')}</span>
          <span class="tag tag-gray">${esc(a.status||'')}</span>
          ${notice ? `<span class="tag tag-orange">${esc(notice)}</span>` : ''}
          <span>발의: ${esc(a.proposed_date||'')}</span>
        </div>
        ${a.summary ? `<div class="item-summary">${esc((a.summary||'').substring(0,180))}${a.summary.length>180?'…':''}</div>` : ''}
      </div>
    </div>`;
  }).join('') : '<div class="empty">해당 항목이 없습니다.</div>';

  return `
  <div class="section">
    <div class="sec-head assembly" onclick="toggleSec('sb-assembly')">
      <span class="sec-icon">📋</span>
      <span class="sec-title">의안 현황 (국회의안정보시스템)</span>
      <span class="sec-badge" id="badge-assembly">${sel} / ${items.length}건 선택</span>
      <span style="font-size:11px;opacity:.7">▼</span>
    </div>
    <div class="sec-body" id="sb-assembly">
      <div class="sec-ctrl">
        <a onclick="setSection('assembly',true)">전체 선택</a>
        <a onclick="setSection('assembly',false)">전체 해제</a>
      </div>
      ${rows}
    </div>
  </div>`;
}

// ── 일정 섹션 ────────────────────────────────────────────────────────────────
function renderSchedule(q) {
  const items = store.schedule.map((a, i) => ({...a, _k:'schedule-'+i}))
    .filter(a => !q || (a.title||'').toLowerCase().includes(q));

  const sel = items.filter(a => checked.has(a._k)).length;
  const rows = items.length ? items.map(a => {
    const on      = checked.has(a._k);
    const upcoming = a.is_upcoming;
    return `
    <div class="item ${on?'':'off'}" id="item-${a._k}">
      <input type="checkbox" ${on?'checked':''} onchange="toggle('${a._k}',this.checked)">
      <div class="item-body">
        <div class="item-title">
          ${a.url ? `<a href="${esc(a.url)}" target="_blank">${esc(a.title||'')}</a>` : esc(a.title||'')}
        </div>
        <div class="item-meta">
          <span class="tag ${upcoming?'tag-red':'tag-gray'}">${upcoming?'예정':'과거'}</span>
          <span class="tag tag-blue">${esc(a.event_type||'')}</span>
          ${a.topic_keyword ? `<span class="tag tag-orange">★ ${esc(a.topic_keyword)}</span>` : ''}
          <span>${esc(a.date||'')}</span>
          <span>${esc(a.source||'')}</span>
        </div>
      </div>
    </div>`;
  }).join('') : '<div class="empty">해당 항목이 없습니다.</div>';

  return `
  <div class="section">
    <div class="sec-head schedule" onclick="toggleSec('sb-schedule')">
      <span class="sec-icon">📅</span>
      <span class="sec-title">일정 현황 (보건복지위원회)</span>
      <span class="sec-badge" id="badge-schedule">${sel} / ${items.length}건 선택</span>
      <span style="font-size:11px;opacity:.7">▼</span>
    </div>
    <div class="sec-body" id="sb-schedule">
      <div class="sec-ctrl">
        <a onclick="setSection('schedule',true)">전체 선택</a>
        <a onclick="setSection('schedule',false)">전체 해제</a>
      </div>
      ${rows}
    </div>
  </div>`;
}

// ── 뉴스 섹션 ────────────────────────────────────────────────────────────────
function renderNews(q) {
  const items = store.news.map((a, i) => ({...a, _k:'news-'+i}))
    .filter(a => !q || (a.title||'').toLowerCase().includes(q)
                    || (a.source||'').toLowerCase().includes(q));

  // 키워드별 그룹
  const groups = {};
  for (const a of items) (groups[a.keyword] = groups[a.keyword]||[]).push(a);

  const totalSel = items.filter(a => checked.has(a._k)).length;

  const groupHTML = Object.entries(groups).map(([kw, grpItems]) => {
    const gSel = grpItems.filter(a => checked.has(a._k)).length;
    const rows  = grpItems.map(a => {
      const on = checked.has(a._k);
      return `
      <div class="item ${on?'':'off'}" id="item-${a._k}" style="padding-left:28px;">
        <input type="checkbox" ${on?'checked':''} onchange="toggle('${a._k}',this.checked)">
        <div class="item-body">
          <div class="item-title">
            ${a.url ? `<a href="${esc(a.url)}" target="_blank">${esc(a.title||'')}</a>` : esc(a.title||'')}
          </div>
          <div class="item-meta">
            <span class="tag tag-gray">${esc(a.source||'출처미상')}</span>
            <span>${esc((a.date||'').substring(0,10))}</span>
          </div>
        </div>
      </div>`;
    }).join('');

    return `
    <div style="border-bottom:1px solid #EEF2F9;">
      <div style="padding:7px 14px;background:#F4F7FC;display:flex;align-items:center;gap:8px;cursor:pointer;"
           onclick="toggleSec('ng-${esc(kw)}')">
        <span style="font-size:12px;font-weight:700;color:#1B3A6B;flex:1;">${esc(kw)}</span>
        <span style="font-size:11px;color:#888;" id="ng-badge-${esc(kw)}">${gSel}/${grpItems.length}건</span>
        <a style="font-size:11px;color:#2A5298;margin-left:8px;" onclick="setKw('${esc(kw)}',true,event)">전체선택</a>
        <a style="font-size:11px;color:#2A5298;margin-left:4px;" onclick="setKw('${esc(kw)}',false,event)">전체해제</a>
      </div>
      <div id="ng-${esc(kw)}">${rows}</div>
    </div>`;
  }).join('');

  return `
  <div class="section">
    <div class="sec-head news" onclick="toggleSec('sb-news')">
      <span class="sec-icon">📰</span>
      <span class="sec-title">언론 모니터링 (전일 기사)</span>
      <span class="sec-badge" id="badge-news">${totalSel} / ${items.length}건 선택</span>
      <span style="font-size:11px;opacity:.7">▼</span>
    </div>
    <div class="sec-body" id="sb-news">
      <div class="sec-ctrl">
        <a onclick="setSection('news',true)">전체 선택</a>
        <a onclick="setSection('news',false)">전체 해제</a>
      </div>
      ${groupHTML || '<div class="empty">해당 항목이 없습니다.</div>'}
    </div>
  </div>`;
}

// ── 체크박스 제어 ─────────────────────────────────────────────────────────────
function toggle(key, val) {
  val ? checked.add(key) : checked.delete(key);
  const el = document.getElementById('item-'+key);
  if (el) el.className = 'item ' + (val ? '' : 'off');
  updateStats();
  updateBadges();
}

function setAll(val) {
  ['assembly','schedule','news'].forEach(type =>
    store[type].forEach((_, i) => val ? checked.add(type+'-'+i) : checked.delete(type+'-'+i))
  );
  renderAll();
}

function setSection(type, val) {
  store[type].forEach((_, i) => val ? checked.add(type+'-'+i) : checked.delete(type+'-'+i));
  renderAll();
}

function setKw(kw, val, e) {
  e.stopPropagation();
  store.news.forEach((a, i) => { if (a.keyword === kw) val ? checked.add('news-'+i) : checked.delete('news-'+i); });
  renderAll();
}

function toggleSec(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('collapsed');
}

function updateStats() {
  const asmSel  = store.assembly.filter((_,i) => checked.has('assembly-'+i)).length;
  const schSel  = store.schedule.filter((_,i) => checked.has('schedule-'+i)).length;
  const newsSel = store.news.filter((_,i) => checked.has('news-'+i)).length;
  document.getElementById('cAsm').textContent   = asmSel;
  document.getElementById('cSch').textContent   = schSel;
  document.getElementById('cNews').textContent  = newsSel;
  document.getElementById('cTotal').textContent = asmSel + schSel + newsSel;
  document.getElementById('selInfo').textContent = `의안 ${asmSel}건 · 일정 ${schSel}건 · 기사 ${newsSel}건 선택`;
}

function updateBadges() {
  const types = ['assembly','schedule','news'];
  types.forEach(type => {
    const badge = document.getElementById('badge-'+type);
    if (!badge) return;
    const total = store[type].length;
    const sel   = store[type].filter((_,i) => checked.has(type+'-'+i)).length;
    badge.textContent = `${sel} / ${total}건 선택`;
  });
  // 뉴스 키워드 배지
  const kwGroups = {};
  store.news.forEach((a, i) => (kwGroups[a.keyword] = kwGroups[a.keyword]||[]).push(i));
  Object.entries(kwGroups).forEach(([kw, idxs]) => {
    const b = document.getElementById('ng-badge-'+kw);
    if (b) b.textContent = idxs.filter(i => checked.has('news-'+i)).length + '/' + idxs.length + '건';
  });
}

// ── 보고서 생성 ───────────────────────────────────────────────────────────────
function makeReport() {
  const selAsm  = store.assembly.filter((_,i) => checked.has('assembly-'+i));
  const selSch  = store.schedule.filter((_,i) => checked.has('schedule-'+i));
  const selNews = store.news.filter((_,i) => checked.has('news-'+i));
  const total   = selAsm.length + selSch.length + selNews.length;
  if (!total) { alert('선택된 항목이 없습니다.'); return; }

  const d = new Date();
  const pad = n => String(n).padStart(2,'0');
  const today    = `${d.getFullYear()}.${pad(d.getMonth()+1)}.${pad(d.getDate())}`;
  const fileDate = `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}`;
  const now      = d.toLocaleString('ko-KR');

  // ── 의안 섹션 (테이블 형식) ───────────────────────────────────────────────
  let asmHTML = '';
  if (selAsm.length === 0) {
    asmHTML = rptEmptyLine(1, '의안 현황', '해당 기간 내 수집된 의안이 없습니다.');
  } else {
    const rows = selAsm.map(a => {
      const name   = (a.bill_name||'').replace(' (새창 열림)','').trim();
      const lvl    = importanceAsm(a);
      const lvlStyle = lvl === '중요'
        ? 'background:#DC3545;color:#fff;padding:1px 5px;border-radius:2px;font-size:9px;font-weight:700'
        : 'background:#E07B00;color:#fff;padding:1px 5px;border-radius:2px;font-size:9px;font-weight:700';
      const notice = a.legislative_notice && isNoticeActive(a.legislative_notice)
        ? `<div style="font-size:9px;color:#856404;margin-top:1px">★ ${esc(a.legislative_notice)}</div>` : '';
      return `<tr>
        <td style="padding:5px 7px;border-bottom:1px solid #F0F2F5;vertical-align:top;font-size:10px;font-weight:600;color:#1B3A6B;line-height:1.4;min-width:90px">
          ${a.url?`<a href="${esc(a.url)}" style="color:#1B3A6B;text-decoration:none">${esc(name)}</a>`:esc(name)}
          ${notice}
        </td>
        <td style="padding:5px 7px;border-bottom:1px solid #F0F2F5;vertical-align:top;font-size:10px;color:#555;white-space:nowrap">${esc(a.proposer||a.proposed_by||'')}</td>
        <td style="padding:5px 7px;border-bottom:1px solid #F0F2F5;vertical-align:top;font-size:10px;color:#555;white-space:nowrap">${esc(a.status||'')}</td>
        <td style="padding:5px 7px;border-bottom:1px solid #F0F2F5;vertical-align:top;font-size:10px;color:#666;line-height:1.4">${esc((a.summary||'').substring(0,80))}${(a.summary||'').length>80?'…':''}</td>
        <td style="padding:5px 7px;border-bottom:1px solid #F0F2F5;vertical-align:top;text-align:center"><span style="${lvlStyle}">${lvl}</span></td>
      </tr>`;
    }).join('');
    const table = `
      <table style="width:100%;border-collapse:collapse;background:#fff">
        <thead>
          <tr style="background:#EEF2F9">
            <th style="padding:5px 7px;font-size:10px;font-weight:700;color:#1B3A6B;border-bottom:2px solid #1B3A6B;text-align:left">법안명</th>
            <th style="padding:5px 7px;font-size:10px;font-weight:700;color:#1B3A6B;border-bottom:2px solid #1B3A6B;text-align:left;white-space:nowrap">발의자</th>
            <th style="padding:5px 7px;font-size:10px;font-weight:700;color:#1B3A6B;border-bottom:2px solid #1B3A6B;text-align:left;white-space:nowrap">진행상태</th>
            <th style="padding:5px 7px;font-size:10px;font-weight:700;color:#1B3A6B;border-bottom:2px solid #1B3A6B;text-align:left">주요내용</th>
            <th style="padding:5px 7px;font-size:10px;font-weight:700;color:#1B3A6B;border-bottom:2px solid #1B3A6B;text-align:center;white-space:nowrap">구분</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>`;
    asmHTML = rptSection(1, '의안 현황', selAsm.length, table);
  }

  // ── 일정 섹션 (카드형, 날짜 우측) ─────────────────────────────────────────
  let schHTML = '';
  if (selSch.length === 0) {
    schHTML = rptEmptyLine(2, '일정 현황', '앞으로 14일 내 등록된 회의·공청회·토론회가 없습니다.');
  } else {
    const cards = selSch.map(a => {
      const bar      = a.is_upcoming ? '#DC3545' : '#ADB5BD';
      const badgeBg  = a.is_upcoming ? '#DC3545' : '#6C757D';
      return `
      <div style="border-left:4px solid ${bar};padding:7px 10px;margin-bottom:4px;background:#fff;border-radius:0 3px 3px 0;box-shadow:0 1px 2px rgba(0,0,0,.06);display:flex;align-items:flex-start;gap:8px">
        <div style="flex:1;min-width:0">
          <div style="font-size:11px;font-weight:600;color:#1B3A6B;line-height:1.4;margin-bottom:3px">
            ${a.url?`<a href="${esc(a.url)}" style="color:#1B3A6B;text-decoration:none">${esc(a.title||'')}</a>`:esc(a.title||'')}
          </div>
          <div style="font-size:10px;color:#888;display:flex;align-items:center;gap:6px;flex-wrap:wrap">
            <span style="background:#EAF0FB;color:#1B3A6B;padding:1px 5px;border-radius:2px">${esc(a.event_type||'')}</span>
            ${a.topic_keyword?`<span style="color:#856404">★ ${esc(a.topic_keyword)}</span>`:''}
            <span style="background:#F1F3F5;color:#555;padding:1px 5px;border-radius:2px">${esc(a.source||'')}</span>
            ${a.url?`<a href="${esc(a.url)}" style="color:#2A5298;font-size:9px">원문</a>`:''}
          </div>
        </div>
        <div style="flex-shrink:0;text-align:right">
          <div style="background:${badgeBg};color:#fff;font-size:9px;font-weight:700;padding:2px 7px;border-radius:10px;margin-bottom:3px">${a.is_upcoming?'예정':'참고'}</div>
          <div style="font-size:10px;font-weight:600;color:#555">${esc((a.date||'').substring(0,10))}</div>
        </div>
      </div>`;
    }).join('');
    schHTML = rptSection(2, '일정 현황', selSch.length, cards);
  }

  // ── 뉴스 섹션 (테이블 형식) ──────────────────────────────────────────────
  let newsHTML = '';
  if (selNews.length === 0) {
    newsHTML = rptEmptyLine(3, '언론 모니터링', '선택된 기사가 없습니다.');
  } else {
    const rows = selNews.map(a => {
      const kwColor = {'응급의료':'#1B3A6B','응급실':'#C0392B','닥터헬기':'#17599A','중증외상':'#7D3C98','응급실 뺑뺑이':'#B35900'};
      const kw = a.keyword||'';
      const kwBg = kwColor[kw] || '#495057';
      return `<tr>
        <td style="padding:5px 7px;border-bottom:1px solid #F0F2F5;vertical-align:top;font-size:10px;font-weight:600;color:#1B3A6B;line-height:1.4">${esc(a.title||'')}</td>
        <td style="padding:5px 7px;border-bottom:1px solid #F0F2F5;vertical-align:top;font-size:10px;color:#555;white-space:nowrap">${esc(a.source||'')}</td>
        <td style="padding:5px 7px;border-bottom:1px solid #F0F2F5;vertical-align:top;font-size:10px;color:#666;line-height:1.4">${esc((a.summary||'').substring(0,80))}${(a.summary||'').length>80?'…':''}</td>
        <td style="padding:5px 7px;border-bottom:1px solid #F0F2F5;vertical-align:top;font-size:10px;text-align:center;white-space:nowrap">
          ${a.url?`<a href="${esc(a.url)}" style="color:#2A5298;text-decoration:underline;font-size:9px">원문</a>`:'-'}
        </td>
        <td style="padding:5px 7px;border-bottom:1px solid #F0F2F5;vertical-align:top;text-align:center">
          <span style="background:${kwBg};color:#fff;padding:1px 5px;border-radius:2px;font-size:9px;font-weight:700;white-space:nowrap">${esc(kw)}</span>
        </td>
      </tr>`;
    }).join('');
    const table = `
      <table style="width:100%;border-collapse:collapse;background:#fff">
        <thead>
          <tr style="background:#EEF2F9">
            <th style="padding:5px 7px;font-size:10px;font-weight:700;color:#1B3A6B;border-bottom:2px solid #1B3A6B;text-align:left">기사제목</th>
            <th style="padding:5px 7px;font-size:10px;font-weight:700;color:#1B3A6B;border-bottom:2px solid #1B3A6B;text-align:left;white-space:nowrap">언론사</th>
            <th style="padding:5px 7px;font-size:10px;font-weight:700;color:#1B3A6B;border-bottom:2px solid #1B3A6B;text-align:left">핵심내용</th>
            <th style="padding:5px 7px;font-size:10px;font-weight:700;color:#1B3A6B;border-bottom:2px solid #1B3A6B;text-align:center;white-space:nowrap">링크</th>
            <th style="padding:5px 7px;font-size:10px;font-weight:700;color:#1B3A6B;border-bottom:2px solid #1B3A6B;text-align:center;white-space:nowrap">구분</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>`;
    newsHTML = rptSection(3, '언론 모니터링', selNews.length, table);
  }

  const html = `<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>응급의료 동향 모니터링 (${today})</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Malgun Gothic","Apple SD Gothic Neo",sans-serif;color:#1a1a1a;font-size:11px;line-height:1.55;background:#fff}
a{color:#1B3A6B;text-decoration:none}
table{border-collapse:collapse;width:100%}
th,td{text-align:left;vertical-align:top}
@page{size:A4 portrait;margin:12mm 14mm}
@media print{
  *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  html{zoom:0.87}
}
</style>
</head>
<body>
<div style="max-width:186mm;margin:0 auto">

  <!-- 헤더 -->
  <div style="background:#1B3A6B;color:#fff;padding:10px 16px 10px;border-radius:4px 4px 0 0;display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <div style="font-size:9px;letter-spacing:1.5px;opacity:.65;margin-bottom:4px">응급의료정책연구팀</div>
      <div style="font-size:17px;font-weight:700;letter-spacing:.4px;line-height:1.2">응급의료 동향 모니터링</div>
    </div>
    <div style="text-align:right;padding-top:2px">
      <div style="font-size:14px;font-weight:700">${today}</div>
      <div style="font-size:9px;opacity:.55;margin-top:2px">생성: ${now}</div>
    </div>
  </div>
  <div style="height:2px;background:#2A5298;margin-bottom:10px"></div>

  <!-- 요약 카드 -->
  <div style="display:flex;gap:6px;margin-bottom:10px">
    ${[['계류 의안',selAsm.length,'#1B3A6B'],['예정 일정',selSch.length,'#17599A'],['언론 기사',selNews.length,'#1D6E9E'],['전체',total,'#333']].map(([l,n,c])=>`
    <div style="flex:1;padding:7px 12px;background:#F8F9FC;border-top:3px solid ${c};border:1px solid #E0E5EF;border-top:3px solid ${c}">
      <div style="font-size:22px;font-weight:700;color:${c};line-height:1.1">${n}</div>
      <div style="font-size:9px;color:#666;margin-top:3px;letter-spacing:.3px">${l}</div>
    </div>`).join('')}
  </div>

  ${asmHTML}
  ${schHTML}
  ${newsHTML}

  <!-- 푸터 -->
  <div style="margin-top:10px;padding-top:6px;border-top:2px solid #1B3A6B;display:flex;justify-content:space-between;align-items:center">
    <span style="font-size:9px;color:#888">본 보고서는 자동 수집·검토된 항목만 포함됩니다. 중요 사항은 반드시 원문을 확인하십시오.</span>
    <span style="font-size:9px;color:#888">응급의료정책연구팀</span>
  </div>
</div>
</body></html>`;

  // ── Flask 서버로 전송 → HTML+PDF 동시 생성 ───────────────────────────────
  const btns = document.querySelectorAll('.btn-green');
  btns.forEach(b => { b._orig = b.textContent; b.textContent = '⏳ 생성 중...'; b.disabled = true; });
  const restoreBtns = () => btns.forEach(b => { b.textContent = b._orig; b.disabled = false; });

  const ctrl   = new AbortController();
  const tid    = setTimeout(() => ctrl.abort(), 90_000);

  fetch('/save-report', {
    method:  'POST',
    headers: {'Content-Type': 'application/json'},
    body:    JSON.stringify({html, filename: `보고서_${fileDate}.html`}),
    signal:  ctrl.signal,
  })
  .then(r => { clearTimeout(tid); if (!r.ok) throw new Error('server'); return r.json(); })
  .then(res => {
    restoreBtns();
    showToast(`✅ 보고서 생성 완료\nHTML : ${res.html_path}\nPDF  : ${res.pdf_path}`, 'ok');
  })
  .catch(() => {
    clearTimeout(tid);
    restoreBtns();
    // 폴백: 파일 다운로드 + 인쇄 대화상자
    const blob  = new Blob([html], {type:'text/html;charset=utf-8'});
    const dlUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = dlUrl; a.download = `보고서_${fileDate}.html`; a.click();
    const win = window.open(dlUrl, '_blank');
    if (win) win.onload = () => setTimeout(() => win.print(), 400);
    showToast('⚠️ 서버 미연결\nHTML 다운로드 + 인쇄 대화상자로 대체됩니다.\n(run_all.py 실행 시 자동 연결됩니다)', 'warn');
  });
}

const CIRCLE_NUMS = ['','①','②','③','④','⑤'];

function rptSection(num, title, count, inner) {
  const circle = CIRCLE_NUMS[num] || '';
  return `<div style="margin-bottom:8px">
    <div style="background:#1B3A6B;color:#fff;padding:5px 10px;border-radius:3px 3px 0 0;display:flex;align-items:center;gap:7px">
      <span style="font-size:13px;font-weight:700;line-height:1">${circle}</span>
      <span style="font-size:11px;font-weight:700;flex:1">${title}</span>
      <span style="background:rgba(255,255,255,.2);padding:1px 8px;border-radius:10px;font-size:9px;font-weight:700">총 ${count}건</span>
    </div>
    <div style="border:1px solid #D0D7E5;border-top:none;border-radius:0 0 3px 3px;padding:4px 6px;background:#fff">
      ${inner}
    </div>
  </div>`;
}

function rptEmptyLine(num, title, msg) {
  const circle = CIRCLE_NUMS[num] || '';
  return `<div style="margin-bottom:8px;padding:6px 10px;background:#F8F9FA;border-radius:3px;border-left:3px solid #CBD3E0;display:flex;align-items:center;gap:8px">
    <span style="font-size:13px;color:#1B3A6B;font-weight:700">${circle}</span>
    <span style="font-size:11px;font-weight:700;color:#1B3A6B">${title}</span>
    <span style="font-size:10px;color:#aaa">${msg}</span>
  </div>`;
}

function showToast(msg, type = '') {
  const t = document.createElement('div');
  t.className = 'toast' + (type ? ' ' + type : '');
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => { t.style.transition = 'opacity .4s'; t.style.opacity = '0'; }, 4000);
  setTimeout(() => t.remove(), 4500);
}

function esc(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── 초기화 ──────────────────────────────────────────────────────────────────
(function init() {
  if (__PRELOADED__) {
    ['assembly','schedule','news'].forEach(type => {
      const data = __PRELOADED__[type] || [];
      store[type] = data;
      data.forEach((_, i) => checked.add(type+'-'+i));
    });
    refresh();
  } else {
    // Flask 서버 없이 직접 열었을 때 안내 표시
    const banner = document.getElementById('infoBanner');
    banner.classList.remove('hidden');
    banner.textContent = '데이터를 불러오지 못했습니다. run_all.py를 실행하거나 python report_server.py를 먼저 실행한 후 http://127.0.0.1:5000 에 접속하세요.';
    banner.classList.add('error');
    renderAll();
  }
})()

try {
  console.log('=== 초기화 후 결과 ===');
  console.log('store.assembly:', store.assembly.length);
  console.log('store.schedule:', store.schedule.length);
  console.log('store.news:', store.news.length);
  console.log('mainList innerHTML:', _els['mainList'] ? _els['mainList'].innerHTML.length + ' chars' : 'NOT SET');
} catch(e2) {
  console.error('POST-INIT ERROR:', e2.message);
}
