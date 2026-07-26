"use strict";

const INDUSTRY_JA = {
  "Advertising Agencies": "広告代理店", "Aerospace & Defense": "航空宇宙・防衛",
  "Agricultural Inputs": "農業資材", "Airlines": "航空", "Airports & Air Services": "空港・航空サービス",
  "Apparel Manufacturing": "アパレル製造", "Apparel Retail": "アパレル小売", "Asset Management": "資産運用",
  "Auto & Truck Dealerships": "自動車・トラック販売", "Auto Manufacturers": "自動車メーカー", "Auto Parts": "自動車部品",
  "Banks - Diversified": "銀行（総合）", "Banks - Regional": "地方銀行",
  "Beverages - Brewers": "飲料（ビール）", "Beverages - Non-Alcoholic": "飲料（ノンアルコール）",
  "Beverages - Wineries & Distilleries": "飲料（ワイン・蒸留酒）", "Biotechnology": "バイオテクノロジー",
  "Broadcasting": "放送", "Building Materials": "建材", "Building Products & Equipment": "建築製品・設備",
  "Business Equipment & Supplies": "事務機器・用品", "Capital Markets": "資本市場", "Chemicals": "化学",
  "Closed-End Fund - Debt": "クローズドエンド型ファンド（債券）", "Closed-End Fund - Equity": "クローズドエンド型ファンド（株式）",
  "Closed-End Fund - Foreign": "クローズドエンド型ファンド（海外）", "Coking Coal": "原料炭",
  "Communication Equipment": "通信機器", "Computer Hardware": "コンピュータハードウェア", "Confectioners": "製菓",
  "Conglomerates": "コングロマリット", "Consulting Services": "コンサルティング", "Consumer Electronics": "民生用電子機器",
  "Copper": "銅", "Credit Services": "信用・金融サービス", "Diagnostics & Research": "診断・研究",
  "Discount Stores": "ディスカウントストア", "Drug Manufacturers - General": "医薬品（大手）",
  "Drug Manufacturers - Specialty & Generic": "医薬品（専門・ジェネリック）", "Education & Training Services": "教育・研修サービス",
  "Electrical Equipment & Parts": "電気機器・部品", "Electronic Components": "電子部品",
  "Electronic Gaming & Multimedia": "電子ゲーム・マルチメディア", "Electronics & Computer Distribution": "電子・コンピュータ流通",
  "Engineering & Construction": "エンジニアリング・建設", "Entertainment": "エンターテインメント", "Exchange Traded Fund": "ETF",
  "Farm & Heavy Construction Machinery": "農業・建設機械", "Farm Products": "農産物",
  "Financial Conglomerates": "金融コングロマリット", "Financial Data & Stock Exchanges": "金融データ・取引所",
  "Food Distribution": "食品流通", "Footwear & Accessories": "履物・アクセサリー",
  "Furnishings, Fixtures & Appliances": "家具・什器・家電", "Gambling": "ギャンブル", "Gold": "金",
  "Grocery Stores": "食料品店", "Health Information Services": "医療情報サービス", "Healthcare Plans": "医療保険",
  "Home Improvement Retail": "ホームセンター", "Household & Personal Products": "家庭用品・パーソナルケア",
  "Industrial Distribution": "産業用流通", "Information Technology Services": "ITサービス",
  "Insurance - Diversified": "保険（総合）", "Insurance - Life": "生命保険",
  "Insurance - Property & Casualty": "損害保険", "Insurance - Reinsurance": "再保険",
  "Insurance - Specialty": "専門保険", "Insurance Brokers": "保険ブローカー",
  "Integrated Freight & Logistics": "総合貨物・物流", "Internet Content & Information": "インターネットコンテンツ・情報",
  "Internet Retail": "インターネット小売", "Leisure": "レジャー", "Lodging": "宿泊",
  "Lumber & Wood Production": "木材・製材", "Luxury Goods": "高級品", "Marine Shipping": "海運",
  "Medical Care Facilities": "医療施設", "Medical Devices": "医療機器", "Medical Distribution": "医薬・医療流通",
  "Medical Instruments & Supplies": "医療器具・用品", "Metal Fabrication": "金属加工", "Mortgage Finance": "住宅ローン金融",
  "Oil & Gas Drilling": "石油・ガス掘削", "Oil & Gas E&P": "石油・ガス開発（E&P）",
  "Oil & Gas Equipment & Services": "石油・ガス機器・サービス", "Oil & Gas Integrated": "石油・ガス（統合）",
  "Oil & Gas Midstream": "石油・ガス中流", "Oil & Gas Refining & Marketing": "石油・ガス精製・販売",
  "Other Industrial Metals & Mining": "その他産業用金属・鉱業", "Other Precious Metals & Mining": "その他貴金属・鉱業",
  "Packaged Foods": "加工食品", "Packaging & Containers": "包装・容器", "Paper & Paper Products": "紙・紙製品",
  "Personal Services": "個人向けサービス", "Pharmaceutical Retailers": "医薬品小売",
  "Pollution & Treatment Controls": "環境・浄化設備", "Publishing": "出版",
  "REIT - Diversified": "REIT（総合）", "REIT - Healthcare Facilities": "REIT（ヘルスケア施設）",
  "REIT - Hotel & Motel": "REIT（ホテル・モーテル）", "REIT - Industrial": "REIT（産業用）",
  "REIT - Mortgage": "REIT（モーゲージ）", "REIT - Office": "REIT（オフィス）",
  "REIT - Residential": "REIT（住宅）", "REIT - Retail": "REIT（商業）", "REIT - Specialty": "REIT（特殊）",
  "Railroads": "鉄道", "Real Estate - Development": "不動産開発", "Real Estate Services": "不動産サービス",
  "Recreational Vehicles": "レジャー車両（RV）", "Rental & Leasing Services": "レンタル・リース",
  "Residential Construction": "住宅建設", "Resorts & Casinos": "リゾート・カジノ", "Restaurants": "レストラン",
  "Scientific & Technical Instruments": "科学・技術機器", "Security & Protection Services": "セキュリティ・警備",
  "Semiconductor Equipment & Materials": "半導体製造装置・材料", "Semiconductors": "半導体", "Shell Companies": "シェルカンパニー",
  "Silver": "銀", "Software - Application": "ソフトウェア（アプリケーション）", "Software - Infrastructure": "ソフトウェア（インフラ）",
  "Solar": "太陽光", "Specialty Business Services": "専門ビジネスサービス", "Specialty Chemicals": "特殊化学",
  "Specialty Industrial Machinery": "特殊産業機械", "Specialty Retail": "専門小売",
  "Staffing & Employment Services": "人材・雇用サービス", "Steel": "鉄鋼", "Telecom Services": "通信サービス",
  "Thermal Coal": "一般炭", "Tobacco": "タバコ", "Tools & Accessories": "工具・アクセサリー",
  "Travel Services": "旅行サービス", "Trucking": "トラック輸送", "Uranium": "ウラン",
  "Utilities - Diversified": "公益（総合）", "Utilities - Independent Power Producers": "公益（独立系発電）",
  "Utilities - Regulated Electric": "公益（規制電力）", "Utilities - Regulated Gas": "公益（規制ガス）",
  "Utilities - Regulated Water": "公益（規制水道）", "Utilities - Renewable": "公益（再生可能エネルギー）",
  "Waste Management": "廃棄物処理",
};
const SECTOR_JA = {
  "Basic Materials": "素材", "Communication Services": "コミュニケーションサービス", "Consumer Cyclical": "一般消費財",
  "Consumer Defensive": "生活必需品", "Energy": "エネルギー", "Financial": "金融", "Healthcare": "ヘルスケア",
  "Industrials": "資本財・サービス", "Real Estate": "不動産", "Technology": "テクノロジー", "Utilities": "公益",
};
function indJa(name) { return INDUSTRY_JA[name] || name || ""; }
function secJa(name) { return SECTOR_JA[name] || name || ""; }

const DEFAULT_COLS = [
  "Ticker", "Company", "Change", "RS Rating", "Industry RS", "EPS加速", "売上加速", "HV", "Industry", "Country",
  "Price", "Rel Volume", "Avg Volume", "Market Cap", "Float Short",
  "Perf Month", "Perf Quart", "SMA20", "SMA50", "52W Low", "Earnings",
];

const TEXT_COLS = new Set(["Ticker", "Company", "Sector", "Industry", "Country", "Earnings", "IPO Date", "HV", "EPS加速", "売上加速"]);

const state = {
  data: null,
  day: null,
  visibleCols: [],
  sortCol: "RS Rating",
  sortDir: -1,
  filterText: "",
  rsMin: 0,
  trend: null,
  trendSort: "latest",
  trendSortDir: -1,
  hvSort: "date",
  hvSortDir: -1,
};

function parseNum(val) {
  if (val == null) return NaN;
  let s = String(val).replace(/[%$,]/g, "").trim().toUpperCase();
  if (s === "" || s === "-") return NaN;
  const mult = { B: 1e9, M: 1e6, K: 1e3 };
  const suf = s.slice(-1);
  if (mult[suf]) {
    const n = parseFloat(s.slice(0, -1));
    return isNaN(n) ? NaN : n * mult[suf];
  }
  const n = parseFloat(s);
  return isNaN(n) ? NaN : n;
}

function gradeFromRS(rs) {
  if (rs == null || isNaN(rs)) return "NA";
  if (rs >= 80) return "A";
  if (rs >= 60) return "B";
  if (rs >= 40) return "C";
  if (rs >= 20) return "D";
  return "E";
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (v != null) node.setAttribute(k, v);
  }
  for (const c of children) {
    if (c == null) continue;
    node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return node;
}

function svgEl(tag, attrs = {}, ...children) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v != null) node.setAttribute(k, v);
  }
  for (const c of children) {
    if (c == null) continue;
    node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return node;
}

async function init() {
  let resp;
  try {
    resp = await fetch("data.json", { cache: "no-store" });
    if (!resp.ok) throw new Error(resp.status);
    state.data = await resp.json();
  } catch (e) {
    document.querySelector("main").innerHTML =
      '<p class="empty">data.json を読み込めませんでした。サーバー経由で開いているか確認してください（file:// 直開きは不可）。</p>';
    return;
  }

  document.getElementById("screening-summary").textContent =
    "条件: " + (state.data.screening_summary || "");
  document.getElementById("generated-at").textContent =
    "生成: " + (state.data.generated_at || "");

  const days = state.data.days || [];
  const sel = document.getElementById("day-select");
  days.forEach((d, i) => {
    sel.appendChild(el("option", { value: String(i) },
      `${d.date}（${d.count}銘柄）`));
  });
  sel.addEventListener("change", () => selectDay(Number(sel.value)));

  bindControls();

  if (days.length === 0) {
    document.querySelector("main").innerHTML = '<p class="empty">データがまだありません。</p>';
    return;
  }
  selectDay(0);

  initWeeklySelect(days);
  renderHighVolume();
  state.trend = buildIndustryTrend();
  renderTrend();
}

function bindControls() {
  const filter = document.getElementById("filter");
  filter.addEventListener("input", () => {
    state.filterText = filter.value.trim().toLowerCase();
    renderTable();
  });
  const rsMin = document.getElementById("rs-min");
  rsMin.addEventListener("input", () => {
    state.rsMin = Number(rsMin.value) || 0;
    renderTable();
  });
  document.getElementById("copy-tv").addEventListener("click", copyTradingView);

  const myRun = document.getElementById("mylist-run");
  if (myRun) myRun.addEventListener("click", runMyList);
  const myCopy = document.getElementById("mylist-copy");
  if (myCopy) myCopy.addEventListener("click", copyMyList);

  const weekSel = document.getElementById("week-select");
  if (weekSel) weekSel.addEventListener("change", () => renderWeekly(weekSel.value));
  const weekCopy = document.getElementById("weekly-copy");
  if (weekCopy) weekCopy.addEventListener("click", copyWeekly);

  const hvf = document.getElementById("hv-filter");
  if (hvf) hvf.addEventListener("input", renderHighVolume);

  const tf = document.getElementById("trend-filter");
  tf.addEventListener("input", renderTrend);
  document.getElementById("trend-gran").addEventListener("change", renderTrend);
  document.getElementById("trend-mode").addEventListener("change", renderTrend);
  document.getElementById("trend-limit").addEventListener("change", renderTrend);
}

function selectDay(index) {
  const day = state.data.days[index];
  state.day = day;
  document.getElementById("screen-meta").textContent = `${day.date}・${day.count}銘柄`;

  const present = new Set(day.columns);
  const keep = state.visibleCols.filter((c) => present.has(c));
  state.visibleCols = keep.length
    ? keep
    : DEFAULT_COLS.filter((c) => present.has(c));

  if (!day.columns.includes(state.sortCol)) {
    state.sortCol = day.columns.includes("RS Rating") ? "RS Rating" : day.columns[0];
    state.sortDir = -1;
  }

  buildColMenu();
  updateLinks();
  renderInsights();
  renderTable();
}

function orderCols(cols) {
  const rank = new Map(DEFAULT_COLS.map((c, i) => [c, i]));
  return cols.slice().sort((a, b) => {
    const ra = rank.has(a) ? rank.get(a) : Infinity;
    const rb = rank.has(b) ? rank.get(b) : Infinity;
    if (ra !== rb) return ra - rb;
    return state.day.columns.indexOf(a) - state.day.columns.indexOf(b);
  });
}

function buildColMenu() {
  const box = document.getElementById("col-checkboxes");
  box.innerHTML = "";
  for (const col of state.day.columns) {
    const cb = el("input", { type: "checkbox" });
    cb.checked = state.visibleCols.includes(col);
    cb.addEventListener("change", () => {
      if (cb.checked) {
        state.visibleCols = orderCols([...state.visibleCols, col]);
      } else {
        state.visibleCols = state.visibleCols.filter((c) => c !== col);
      }
      renderTable();
    });
    box.appendChild(el("label", {}, cb, col));
  }
}

function renderInsights() {
  const root = document.getElementById("insights");
  root.innerHTML = "";
  const ins = state.day.insights || {};

  root.appendChild(el("div", { class: "card" },
    el("h3", {}, "銘柄RS 高位"),
    el("div", { class: "big" }, String(ins.rs_ge_80 ?? 0)),
    el("div", { class: "sub" }, `RS≥80（うち RS≥90: ${ins.rs_ge_90 ?? 0}）`),
  ));

  const topCard = el("div", { class: "card" },
    el("h3", { title: "抽出銘柄が属するIndustryをIndustry RS順位の上位5つまで表示。" }, "🏆 Top Industry"));
  const tops = ins.top_industries || [];
  if (tops.length) {
    const ul = el("ul");
    for (const t of tops) {
      ul.appendChild(el("li", {},
        el("span", {}, indJa(t.name)), el("span", { class: "v" }, `${t.rank}位`)));
    }
    topCard.appendChild(ul);
    if (ins.total_industries) topCard.appendChild(el("div", { class: "sub" }, `全${ins.total_industries} Industry中`));
  } else {
    topCard.appendChild(el("div", { class: "sub" }, "—"));
  }
  root.appendChild(topCard);

  const concCard = el("div", { class: "card" }, el("h3", {}, "🔥 集中Industry（3銘柄以上）"));
  const concList = el("ul");
  (ins.concentrated || []).forEach(([ind, c]) => {
    concList.appendChild(el("li", {}, el("span", {}, indJa(ind)), el("span", { class: "v" }, `${c}`)));
  });
  concCard.appendChild((ins.concentrated && ins.concentrated.length) ? concList : el("div", { class: "sub" }, "—"));
  root.appendChild(concCard);

  root.appendChild(buildSentimentCard());

  const divCard = el("div", { class: "card" }, el("h3", {}, "💎 乖離（強い銘柄×弱いIndustry）"));
  const divList = el("ul");
  (ins.divergent || []).forEach((d) => {
    divList.appendChild(el("li", {},
      el("span", {}, d.ticker),
      el("span", { class: "v" }, `RS${d.rs} / Industry${d.ind_rank}位`)));
  });
  divCard.appendChild((ins.divergent && ins.divergent.length) ? divList : el("div", { class: "sub" }, "—"));
  root.appendChild(divCard);
}

function rowObj(row) {
  const o = {};
  state.day.columns.forEach((c, i) => { o[c] = row[i]; });
  return o;
}

function filteredSortedRows() {
  const cols = state.day.columns;
  const iRS = cols.indexOf("RS Rating");
  let rows = state.day.rows;

  if (state.filterText) {
    const q = state.filterText;
    const idxs = ["Ticker", "Company", "Sector", "Industry"]
      .map((c) => cols.indexOf(c)).filter((i) => i >= 0);
    const ii = cols.indexOf("Industry"), si = cols.indexOf("Sector");
    rows = rows.filter((r) =>
      idxs.some((i) => String(r[i]).toLowerCase().includes(q))
      || (ii >= 0 && indJa(r[ii]).toLowerCase().includes(q))
      || (si >= 0 && secJa(r[si]).toLowerCase().includes(q)));
  }
  if (state.rsMin > 0 && iRS >= 0) {
    rows = rows.filter((r) => {
      const v = parseNum(r[iRS]);
      return !isNaN(v) && v >= state.rsMin;
    });
  }

  const sc = cols.indexOf(state.sortCol);
  if (sc >= 0) {
    const numeric = !TEXT_COLS.has(state.sortCol);
    rows = rows.slice().sort((a, b) => {
      let av = a[sc], bv = b[sc];
      if (numeric) {
        av = parseNum(av); bv = parseNum(bv);
        const aNan = isNaN(av), bNan = isNaN(bv);
        if (aNan && bNan) return 0;
        if (aNan) return 1;
        if (bNan) return -1;
        return (av - bv) * state.sortDir;
      }
      return String(av).localeCompare(String(bv)) * state.sortDir;
    });
  }
  return rows;
}

function renderTable() {
  const cols = state.visibleCols;
  const headRow = document.getElementById("screen-head");
  const body = document.getElementById("screen-body");
  headRow.innerHTML = "";
  body.innerHTML = "";

  for (const col of cols) {
    const isNum = !TEXT_COLS.has(col);
    const th = el("th", { class: isNum ? "num" : "" });
    th.appendChild(document.createTextNode(col));
    if (col === state.sortCol) {
      th.appendChild(el("span", { class: "arrow" }, state.sortDir === 1 ? " ▲" : " ▼"));
    }
    th.addEventListener("click", () => {
      if (state.sortCol === col) state.sortDir *= -1;
      else { state.sortCol = col; state.sortDir = isNum ? -1 : 1; }
      renderTable();
    });
    headRow.appendChild(th);
  }

  const rows = filteredSortedRows();
  document.getElementById("table-empty").hidden = rows.length > 0;

  const allCols = state.day.columns;
  const frag = document.createDocumentFragment();
  for (const row of rows) {
    const tr = el("tr");
    for (const col of cols) {
      const idx = allCols.indexOf(col);
      const raw = idx >= 0 ? row[idx] : "";
      tr.appendChild(renderCell(col, raw, row));
    }
    frag.appendChild(tr);
  }
  body.appendChild(frag);
}

function accelCell(ticker, isEps) {
  const td = el("td", { class: "accel-cell" });
  const map = (state.data.earnings_accel && state.data.earnings_accel.map) || {};
  const a = map[String(ticker || "").toUpperCase()];
  const flag = a ? (isEps ? a.eps_accel : a.rev_accel) : "";
  if (flag !== "Y" && flag !== "N") return td;
  const q0 = isEps ? a.eps_yoy_q0 : a.rev_yoy_q0;
  const q1 = isEps ? a.eps_yoy_q1 : a.rev_yoy_q1;
  const pct = (v) => (v == null ? "—" : (v > 0 ? "+" : "") + Number(v).toFixed(1) + "%");
  const title = `今期YoY ${pct(q0)} / 前期YoY ${pct(q1)}`;
  if (flag === "Y") td.appendChild(el("span", { class: "accel-badge accel-up", title }, "▲加速"));
  else td.appendChild(el("span", { class: "accel-flat", title }, "—"));
  return td;
}

function renderCell(col, raw, row) {
  if (col === "Ticker") {
    const td = el("td", { class: "ticker" });
    td.appendChild(el("a", {
      href: `https://finviz.com/quote.ashx?t=${encodeURIComponent(raw)}`,
      target: "_blank", rel: "noopener",
    }, raw));
    return td;
  }
  if (col === "RS Rating" || col === "Industry RS") {
    const v = parseNum(raw);
    const td = el("td", { class: "num" });
    if (isNaN(v)) { td.textContent = raw || "—"; return td; }
    td.appendChild(el("span", { class: `grade grade-${gradeFromRS(v)}` }, String(Math.round(v))));
    return td;
  }
  if (col === "Change" || col === "from Open" || col === "Gap") {
    const v = parseNum(raw);
    const td = el("td", { class: "num " + (v > 0 ? "up" : v < 0 ? "down" : "") });
    td.textContent = raw || "—";
    return td;
  }
  if (col === "HV") {
    const td = el("td", { class: "hv-cell" });
    if (raw) td.appendChild(hvBadge(raw));
    return td;
  }
  if (col === "EPS加速" || col === "売上加速") {
    const ti = state.day.columns.indexOf("Ticker");
    return accelCell(row && ti >= 0 ? row[ti] : "", col === "EPS加速");
  }
  if (col === "Company" || col === "Industry" || col === "Country") {
    const empty = (raw === "" || raw == null);
    const disp = empty ? "—" : (col === "Industry" ? indJa(raw) : raw);
    const td = el("td", { class: "col-narrow" });
    td.appendChild(el("span", { class: "trunc", title: empty ? "" : raw }, disp));
    return td;
  }
  const isNum = !TEXT_COLS.has(col);
  const td = el("td", { class: isNum ? "num" : "" });
  td.textContent = (raw === "" || raw == null) ? "—" : raw;
  return td;
}

function allTickers() {
  const i = state.day.columns.indexOf("Ticker");
  return i >= 0 ? state.day.rows.map((r) => r[i]).filter(Boolean) : [];
}

function updateLinks() {
  const tickers = allTickers();
  const maps = document.getElementById("finviz-maps");
  maps.href = `https://finviz.com/screener.ashx?v=711&t=${tickers.join(",")}&show_etf=true`;
}

function buildTradingViewText() {
  const cols = state.day.columns;
  const iT = cols.indexOf("Ticker");
  const iIRS = cols.indexOf("Industry RS");
  const iRS = cols.indexOf("RS Rating");
  if (iT < 0) return "";

  const sections = [
    ["Ind Grade A", new Set(["A"])],
    ["Ind Grade B", new Set(["B"])],
    ["Ind Grade C", new Set(["C"])],
    ["Ind Grade D/E/NA", new Set(["D", "E", "NA"])],
  ];
  const items = state.day.rows.map((r) => ({
    ticker: r[iT],
    irs: iIRS >= 0 ? parseNum(r[iIRS]) : NaN,
    rs: iRS >= 0 ? parseNum(r[iRS]) : NaN,
    grade: gradeFromRS(iIRS >= 0 ? parseNum(r[iIRS]) : NaN),
  }));

  const parts = [];
  for (const [name, keys] of sections) {
    const group = items.filter((it) => keys.has(it.grade));
    if (!group.length) continue;
    group.sort((a, b) =>
      (isNaN(b.irs) ? -1 : b.irs) - (isNaN(a.irs) ? -1 : a.irs) ||
      (isNaN(b.rs) ? -1 : b.rs) - (isNaN(a.rs) ? -1 : a.rs) ||
      a.ticker.localeCompare(b.ticker));
    parts.push("###" + name, ...group.map((it) => it.ticker));
  }
  return parts.join(",");
}

async function copyTradingView() {
  const text = buildTradingViewText();
  const btn = document.getElementById("copy-tv");
  try {
    await navigator.clipboard.writeText(text);
    const orig = btn.textContent;
    btn.textContent = "コピーしました ✓";
    setTimeout(() => { btn.textContent = orig; }, 1500);
  } catch (e) {
    window.prompt("コピーできませんでした。手動でコピーしてください:", text);
  }
}

let universeCache = null;

async function ensureUniverse() {
  if (universeCache && universeCache !== "error") return universeCache;
  try {
    const resp = await fetch("universe.json", { cache: "no-store" });
    if (!resp.ok) throw new Error(resp.status);
    universeCache = await resp.json();
  } catch (e) {
    universeCache = "error";
  }
  return universeCache;
}

function parseMyTickers(text) {
  const seen = new Set();
  const out = [];
  for (let tok of String(text).split(/[\s,;]+/)) {
    tok = tok.trim().toUpperCase();
    if (!tok) continue;
    const c = tok.indexOf(":");
    if (c >= 0) tok = tok.slice(c + 1);
    if (!tok || seen.has(tok)) continue;
    seen.add(tok);
    out.push(tok);
  }
  return out;
}

async function runMyList() {
  const input = document.getElementById("mylist-input");
  const output = document.getElementById("mylist-output");
  const status = document.getElementById("mylist-status");
  const unmatchedEl = document.getElementById("mylist-unmatched");
  const copyBtn = document.getElementById("mylist-copy");

  const tickers = parseMyTickers(input.value);
  if (!tickers.length) {
    status.textContent = "ティッカーを入力してください";
    output.value = "";
    copyBtn.disabled = true;
    unmatchedEl.hidden = true;
    return;
  }

  status.textContent = "RSデータを読み込み中…";
  const uni = await ensureUniverse();
  if (uni === "error" || !uni || !uni.tickers) {
    status.textContent = "universe.json を読み込めませんでした（サーバー経由で開いているか確認）";
    return;
  }

  const sections = [
    ["Ind Grade A", new Set(["A"])],
    ["Ind Grade B", new Set(["B"])],
    ["Ind Grade C", new Set(["C"])],
    ["Ind Grade D/E/NA", new Set(["D", "E", "NA"])],
  ];

  const items = [];
  const unmatched = [];
  for (const t of tickers) {
    const rec = uni.tickers[t];
    if (!rec) unmatched.push(t);
    const rs = rec ? rec[0] : null;
    const irs = rec ? rec[1] : null;
    items.push({
      ticker: t,
      rs: rs == null ? NaN : rs,
      irs: irs == null ? NaN : irs,
      grade: gradeFromRS(irs == null ? NaN : irs),
    });
  }

  const sortRows = (a, b) =>
    (isNaN(b.rs) ? -1 : b.rs) - (isNaN(a.rs) ? -1 : a.rs) ||
    (isNaN(b.irs) ? -1 : b.irs) - (isNaN(a.irs) ? -1 : a.irs) ||
    a.ticker.localeCompare(b.ticker);

  const weak = items.filter((it) => !isNaN(it.rs) && it.rs < 60);
  const weakSet = new Set(weak);

  const parts = [];
  for (const [name, keys] of sections) {
    const group = items.filter((it) => keys.has(it.grade) && !weakSet.has(it));
    if (!group.length) continue;
    group.sort(sortRows);
    parts.push("###" + name, ...group.map((it) => it.ticker));
  }
  if (weak.length) {
    weak.sort(sortRows);
    parts.push("###Stock RS<60", ...weak.map((it) => it.ticker));
  }

  output.value = parts.join(",");
  copyBtn.disabled = parts.length === 0;

  const matched = tickers.length - unmatched.length;
  status.textContent =
    `${tickers.length}銘柄を変換（ヒット ${matched} / 未ヒット ${unmatched.length}）｜RS基準日 ${uni.date || "—"}`;
  if (unmatched.length) {
    unmatchedEl.hidden = false;
    unmatchedEl.textContent =
      `未ヒット（RSデータ無し→D/E/NAブロックに収容）: ${unmatched.join(", ")}`;
  } else {
    unmatchedEl.hidden = true;
  }
}

async function copyMyList() {
  const output = document.getElementById("mylist-output");
  const btn = document.getElementById("mylist-copy");
  const text = output.value;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    const orig = btn.textContent;
    btn.textContent = "コピーしました ✓";
    setTimeout(() => { btn.textContent = orig; }, 1500);
  } catch (e) {
    output.select();
    window.prompt("コピーできませんでした。手動でコピーしてください:", text);
  }
}

function isoWeekKey(dateStr) {
  const d = new Date(dateStr + "T00:00:00Z");
  const day = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() - day + 1);
  return d.toISOString().slice(0, 10);
}

function initWeeklySelect(days) {
  const sel = document.getElementById("week-select");
  if (!sel || !days || !days.length) return;

  const weekMap = new Map();
  days.forEach((d, i) => {
    const wk = isoWeekKey(d.date);
    if (!weekMap.has(wk)) weekMap.set(wk, []);
    weekMap.get(wk).push(i);
  });

  const weekKeys = Array.from(weekMap.keys()).sort((a, b) => b.localeCompare(a));

  sel.innerHTML = "";
  weekKeys.forEach((wk) => {
    const idxs = weekMap.get(wk);
    const dates = idxs.map((i) => days[i].date).sort();
    const startStr = dates[0].slice(5).replace("-", "/");
    const endStr = dates[dates.length - 1].slice(5).replace("-", "/");
    const totalRaw = idxs.reduce((s, i) => s + (days[i].count || 0), 0);
    const label = dates.length === 1
      ? `${startStr}（1日・${totalRaw}銘柄延べ）`
      : `${startStr}〜${endStr}（${dates.length}日・${totalRaw}銘柄延べ）`;
    sel.appendChild(el("option", { value: wk }, label));
  });

  state.weekMap = weekMap;

  if (weekKeys.length) {
    sel.value = weekKeys[0];
    renderWeekly(weekKeys[0]);
  }
}

async function renderWeekly(weekKey) {
  const sel = document.getElementById("week-select");
  const output = document.getElementById("weekly-output");
  const status = document.getElementById("weekly-status");
  const copyBtn = document.getElementById("weekly-copy");
  if (!sel || !output || !status) return;

  const wk = typeof weekKey === "string" && state.weekMap && state.weekMap.has(weekKey)
    ? weekKey
    : sel.value;

  const weekMap = state.weekMap;
  if (!weekMap || !weekMap.has(wk)) return;

  status.textContent = "RSデータを読み込み中…";
  const uni = await ensureUniverse();
  if (uni === "error" || !uni || !uni.tickers) {
    status.textContent = "universe.json を読み込めませんでした（サーバー経由で開いているか確認）";
    return;
  }

  const days = state.data.days || [];
  const idxs = weekMap.get(wk);
  const dateList = idxs.map((i) => days[i].date).sort();

  const seen = new Map();
  for (const i of idxs) {
    const day = days[i];
    const tIdx = day.columns.indexOf("Ticker");
    if (tIdx === -1) continue;
    for (const row of day.rows) {
      const t = row[tIdx];
      if (t && !seen.has(t)) seen.set(t, true);
    }
  }
  const tickers = Array.from(seen.keys());

  if (!tickers.length) {
    output.value = "";
    copyBtn.disabled = true;
    status.textContent = `対象 ${dateList.length}日（${dateList.join(", ")}）・該当銘柄なし`;
    return;
  }

  const sections = [
    ["Ind Grade A", new Set(["A"])],
    ["Ind Grade B", new Set(["B"])],
    ["Ind Grade C", new Set(["C"])],
    ["Ind Grade D/E/NA", new Set(["D", "E", "NA"])],
  ];

  const items = tickers.map((t) => {
    const rec = uni.tickers[t];
    const rs = rec ? rec[0] : null;
    const irs = rec ? rec[1] : null;
    return {
      ticker: t,
      rs: rs == null ? NaN : rs,
      irs: irs == null ? NaN : irs,
      grade: gradeFromRS(irs == null ? NaN : irs),
    };
  });

  const sortRows = (a, b) =>
    (isNaN(b.rs) ? -1 : b.rs) - (isNaN(a.rs) ? -1 : a.rs) ||
    (isNaN(b.irs) ? -1 : b.irs) - (isNaN(a.irs) ? -1 : a.irs) ||
    a.ticker.localeCompare(b.ticker);

  const weak = items.filter((it) => !isNaN(it.rs) && it.rs < 60);
  const weakSet = new Set(weak);

  const parts = [];
  for (const [name, keys] of sections) {
    const group = items.filter((it) => keys.has(it.grade) && !weakSet.has(it));
    if (!group.length) continue;
    group.sort(sortRows);
    parts.push("###" + name, ...group.map((it) => it.ticker));
  }
  if (weak.length) {
    weak.sort(sortRows);
    parts.push("###Stock RS<60", ...weak.map((it) => it.ticker));
  }

  output.value = parts.join(",");
  copyBtn.disabled = parts.length === 0;
  status.textContent =
    `対象 ${dateList.length}日（${dateList.join(", ")}）・重複なし ${tickers.length}銘柄｜RS基準日 ${uni.date || "—"}`;
}

async function copyWeekly() {
  const output = document.getElementById("weekly-output");
  const btn = document.getElementById("weekly-copy");
  const text = output.value;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    const orig = btn.textContent;
    btn.textContent = "コピーしました ✓";
    setTimeout(() => { btn.textContent = orig; }, 1500);
  } catch (e) {
    output.select();
    window.prompt("コピーできませんでした。手動でコピーしてください:", text);
  }
}

function hvBadge(label) {
  if (!label) return document.createTextNode("");
  const cls = /x$/.test(label) ? "hv-broad" : `hv-${label}`;
  return el("span", { class: `hv-badge ${cls}` }, label);
}
function hvFmt(v, nd) {
  return (v == null || isNaN(v)) ? "—" : Number(v).toFixed(nd);
}

const hvTier = (t) => (t === "HVE" ? 0 : t === "HV1" ? 1 : /x$/.test(t) ? 2 : 3);
function hvAccelRank(ticker) {
  const map = (state.data && state.data.earnings_accel && state.data.earnings_accel.map) || {};
  const a = map[String(ticker || "").toUpperCase()];
  if (!a) return null;
  return a.eps_accel === "Y" ? 2 : a.eps_accel === "N" ? 1 : null;
}
const HV_COLS = [
  { label: "Ticker",      cls: "",    key: "ticker",   type: "text", dir: 1,  get: (r) => r.ticker || "" },
  { label: "種別",        cls: "",    key: "type",     type: "num",  dir: 1,  get: (r) => hvTier(r.type) },
  { label: "EPS加速",     cls: "",    key: "eps",      type: "num",  dir: -1, get: (r) => hvAccelRank(r.ticker) },
  { label: "HV日",        cls: "",    key: "date",     type: "text", dir: -1, get: (r) => r.date || "" },
  { label: "Gap%",        cls: "num", key: "gap",      type: "num",  dir: -1, get: (r) => r.gap },
  { label: "Range%",      cls: "num", key: "range",    type: "num",  dir: -1, get: (r) => r.close_range },
  { label: "RelVol",      cls: "num", key: "relvol",   type: "num",  dir: -1, get: (r) => r.relvol },
  { label: "Since%",      cls: "num", key: "since",    type: "num",  dir: -1, get: (r) => r.since },
  { label: "Industry",    cls: "",    key: "industry", type: "text", dir: 1,  get: (r) => indJa(r.industry) },
  { label: "時価総額(M)", cls: "num", key: "mcap",     type: "num",  dir: -1, get: (r) => r.market_cap },
];

function renderHighVolume() {
  const panel = document.getElementById("hv-panel");
  if (!panel) return;
  const hv = state.data.high_volume;
  if (!hv || !hv.rows || !hv.rows.length) { panel.hidden = true; return; }
  panel.hidden = false;

  const meta = hv.meta || {};
  const parts = [];
  if (meta.window_start && meta.window_end) parts.push(`${meta.window_start}〜${meta.window_end}`);
  parts.push(`${hv.rows.length}銘柄`);
  if (meta.generated_at) parts.push(`更新 ${String(meta.generated_at).slice(0, 10)}`);
  document.getElementById("hv-meta").textContent = parts.join(" / ");

  const q = (document.getElementById("hv-filter").value || "").trim().toLowerCase();

  let rows = hv.rows.slice();
  if (q) rows = rows.filter((r) =>
    r.ticker.toLowerCase().includes(q) || (r.industry || "").toLowerCase().includes(q)
    || indJa(r.industry).toLowerCase().includes(q));

  const spec = HV_COLS.find((c) => c.key === state.hvSort) || HV_COLS.find((c) => c.key === "date");
  const dir = state.hvSortDir;
  const byDateDesc = (a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0);
  rows.sort((a, b) => {
    const av = spec.get(a), bv = spec.get(b);
    let r;
    if (spec.type === "num") {
      const an = av == null || isNaN(av), bn = bv == null || isNaN(bv);
      if (an && bn) r = 0;
      else if (an) return 1;
      else if (bn) return -1;
      else r = (av - bv) * dir;
    } else {
      r = String(av).localeCompare(String(bv)) * dir;
    }
    return r || (spec.key === "date" ? 0 : byDateDesc(a, b));
  });

  const head = document.getElementById("hv-head");
  const body = document.getElementById("hv-body");
  head.innerHTML = ""; body.innerHTML = "";

  const htr = el("tr");
  for (const c of HV_COLS) {
    const th = el("th", { class: (c.cls ? c.cls + " " : "") + "hv-sortable", title: "クリックで昇順/降順" }, c.label);
    if (c.key === state.hvSort) th.appendChild(el("span", { class: "arrow" }, dir === 1 ? " ▲" : " ▼"));
    th.addEventListener("click", () => {
      if (state.hvSort === c.key) state.hvSortDir *= -1;
      else { state.hvSort = c.key; state.hvSortDir = c.dir; }
      renderHighVolume();
    });
    htr.appendChild(th);
  }
  head.appendChild(htr);

  const frag = document.createDocumentFragment();
  for (const r of rows) {
    const tr = el("tr");
    const tdT = el("td", { class: "ticker" });
    tdT.appendChild(el("a", {
      href: `https://finviz.com/quote.ashx?t=${encodeURIComponent(r.ticker)}`,
      target: "_blank", rel: "noopener",
    }, r.ticker));
    tr.appendChild(tdT);
    tr.appendChild(el("td", {}, hvBadge(r.type)));
    tr.appendChild(accelCell(r.ticker, true));
    tr.appendChild(el("td", {}, r.date || "—"));
    tr.appendChild(el("td", { class: "num " + (r.gap > 0 ? "up" : r.gap < 0 ? "down" : "") }, hvFmt(r.gap, 2)));
    tr.appendChild(el("td", { class: "num" }, hvFmt(r.close_range, 0)));
    tr.appendChild(el("td", { class: "num" }, hvFmt(r.relvol, 1)));
    tr.appendChild(el("td", { class: "num " + (r.since > 0 ? "up" : r.since < 0 ? "down" : "") }, hvFmt(r.since, 1)));
    const tdI = el("td", { class: "col-narrow" });
    tdI.appendChild(el("span", { class: "trunc", title: r.industry || "" }, r.industry ? indJa(r.industry) : "—"));
    tr.appendChild(tdI);
    tr.appendChild(el("td", { class: "num" }, r.market_cap == null ? "—" : Math.round(r.market_cap).toLocaleString()));
    frag.appendChild(tr);
  }
  body.appendChild(frag);
  document.getElementById("hv-empty").hidden = rows.length > 0;
}

function buildIndustryTrend() {
  const src = (state.data.industry_trend && state.data.industry_trend.length)
    ? state.data.industry_trend
    : (state.data.days || []);
  const days = src
    .filter((d) => d.industry_rs && d.industry_rs.length)
    .slice()
    .sort((a, b) => (a.date < b.date ? -1 : 1));

  const dates = days.map((d) => d.date);
  const map = new Map();
  for (const d of days) {
    for (const r of d.industry_rs) {
      if (!r.industry) continue;
      if (!map.has(r.industry)) {
        map.set(r.industry, { industry: r.industry, sector: r.sector || "", byDate: {} });
      }
      map.get(r.industry).byDate[d.date] = { rs: r.rs, rank: r.rank, count: r.count, grade: r.grade };
    }
  }
  return { dates, industries: Array.from(map.values()) };
}

function mondayKey(dateStr) {
  const dt = new Date(dateStr + "T00:00:00Z");
  const day = dt.getUTCDay();
  dt.setUTCDate(dt.getUTCDate() - (day === 0 ? 6 : day - 1));
  return dt.toISOString().slice(0, 10);
}
function buildColumns(dates, gran) {
  if (gran === "week") {
    const groups = new Map();
    for (const d of dates) {
      const wk = mondayKey(d);
      if (!groups.has(wk)) groups.set(wk, []);
      groups.get(wk).push(d);
    }
    return Array.from(groups.entries())
      .sort((a, b) => (a[0] < b[0] ? -1 : 1))
      .map(([, ds]) => {
        ds.sort();
        const last = ds[ds.length - 1];
        return { label: mmdd(last), title: `週 ${ds[0]}〜${last}`, days: ds };
      });
  }
  return dates.map((d) => ({ label: mmdd(d), title: d, days: [d] }));
}
function cellAt(ind, col) {
  for (let i = col.days.length - 1; i >= 0; i--) {
    const c = ind.byDate[col.days[i]];
    if (c) return c;
  }
  return null;
}
function lastCell(ind, cols) {
  for (let i = cols.length - 1; i >= 0; i--) { const v = cellAt(ind, cols[i]); if (v) return v; }
  return null;
}
const TREND_LOOKBACK = 4;
function rankSlope(ind, cols) {
  const recent = cols.slice(-TREND_LOOKBACK);
  const pts = [];
  recent.forEach((c, i) => {
    const cell = cellAt(ind, c);
    if (cell && cell.rank != null) pts.push([i, cell.rank]);
  });
  if (pts.length < 2) return null;
  const n = pts.length;
  const mx = pts.reduce((a, p) => a + p[0], 0) / n;
  const my = pts.reduce((a, p) => a + p[1], 0) / n;
  let num = 0, den = 0;
  for (const [x, y] of pts) { num += (x - mx) * (y - my); den += (x - mx) ** 2; }
  if (den === 0) return null;
  return -(num / den);
}

function rsColor(rs) {
  if (rs == null || isNaN(rs)) return null;
  const hue = Math.max(0, Math.min(120, (rs / 99) * 120));
  return `hsl(${hue}, 55%, 32%)`;
}

function mmdd(date) { return date.slice(5).replace("-", "/"); }

const TREND_SORT_DEFAULT_DIR = { latest: -1, delta: -1, name: 1 };

function renderTrend() {
  const { dates, industries } = state.trend || { dates: [], industries: [] };
  const head = document.getElementById("heatmap-head");
  const body = document.getElementById("heatmap-body");
  const movers = document.getElementById("trend-movers");
  const empty = document.getElementById("trend-empty");
  head.innerHTML = ""; body.innerHTML = ""; movers.innerHTML = "";

  const mode = document.getElementById("trend-mode").value;
  const sortBy = state.trendSort;
  const limit = Number(document.getElementById("trend-limit").value) || 0;
  const q = document.getElementById("trend-filter").value.trim().toLowerCase();
  const gran = document.getElementById("trend-gran").value;

  const cols = buildColumns(dates, gran);

  if (cols.length < 2) {
    empty.textContent = gran === "week"
      ? "週次表示には2週以上のデータが必要です（現在は1週間分のみ）。"
      : "Industry RSの時系列データが足りません（2日以上必要）。";
    empty.hidden = false;
    document.querySelector("#heatmap").hidden = true;
    return;
  }
  empty.hidden = true;
  document.querySelector("#heatmap").hidden = false;

  let list = industries;
  if (q) {
    list = list.filter((it) =>
      it.industry.toLowerCase().includes(q) || it.sector.toLowerCase().includes(q)
      || indJa(it.industry).toLowerCase().includes(q) || secJa(it.sector).toLowerCase().includes(q));
  }

  const latestRS = (it) => { const l = lastCell(it, cols); return l && l.rs != null ? l.rs : -1; };
  const dir = state.trendSortDir;
  if (sortBy === "name") {
    list = list.slice().sort((a, b) => a.industry.localeCompare(b.industry) * dir);
  } else if (sortBy === "delta") {
    list = list.slice().sort((a, b) => {
      const av = rankSlope(a, cols), bv = rankSlope(b, cols);
      const an = av == null, bn = bv == null;
      if (an && bn) return 0;
      if (an) return 1;
      if (bn) return -1;
      return (av - bv) * dir;
    });
  } else {
    list = list.slice().sort((a, b) => (latestRS(a) - latestRS(b)) * dir);
  }
  if (limit > 0) list = list.slice(0, limit);

  renderMovers(movers, industries, cols);

  const sortTh = (label, key, cls, title) => {
    const th = el("th", { class: cls + " trend-sortable", title }, label);
    if (sortBy === key) th.appendChild(el("span", { class: "arrow" }, state.trendSortDir === 1 ? " ▲" : " ▼"));
    th.addEventListener("click", () => {
      if (state.trendSort === key) state.trendSortDir *= -1;
      else { state.trendSort = key; state.trendSortDir = TREND_SORT_DEFAULT_DIR[key]; }
      renderTrend();
    });
    return th;
  };

  const htr = el("tr");
  htr.appendChild(sortTh("Industry", "name", "ind-h", "Industry名順（クリックで昇順/降順）"));
  htr.appendChild(sortTh("最新RS", "latest", "latest-rs-h", "最新のIndustry RS（クリックで昇順/降順）"));
  htr.appendChild(el("th", { class: "spark-h", title: "Industry RSの推移（左=古い, 右=新しい / 上=高い）" }, "推移"));
  for (const c of cols) htr.appendChild(el("th", { title: c.title }, c.label));
  htr.appendChild(sortTh("傾き", "delta", "delta-h", "直近数期の順位の傾き（+=上昇傾向）。クリックで昇順/降順"));
  head.appendChild(htr);

  const frag = document.createDocumentFragment();
  for (const it of list) {
    const tr = el("tr");
    const latest = lastCell(it, cols);
    const grade = (latest && latest.grade) ? latest.grade : gradeFromRS(latest ? latest.rs : null);

    const th = el("th", { class: "ind", title: it.industry });
    const top = el("div", { class: "ind-top" });
    top.appendChild(el("span", { class: `grade grade-${grade || "NA"}` }, grade || "—"));
    top.appendChild(el("span", { class: "ind-name" }, indJa(it.industry)));
    th.appendChild(top);
    const sub = el("div", { class: "ind-sub" });
    if (it.sector) sub.appendChild(el("span", { class: "sec" }, secJa(it.sector)));
    if (latest && latest.count != null) sub.appendChild(el("span", { class: "ind-count" }, latest.count + "銘柄"));
    th.appendChild(sub);
    tr.appendChild(th);

    tr.appendChild(el("td", { class: "latest-rs" },
      latest && latest.rs != null ? String(latest.rs) : "—"));

    tr.appendChild(el("td", { class: "spark" }, sparklineSVG(it, cols, mode)));

    for (const c of cols) {
      const cell = cellAt(it, c);
      if (!cell || cell.rs == null) {
        tr.appendChild(el("td", { class: "cell na" }, "—"));
        continue;
      }
      const td = el("td", {
        class: "cell",
        title: `${c.title}  RS ${cell.rs} / ${cell.rank != null ? cell.rank + "位" : "—"}`,
      }, String(mode === "rank" && cell.rank != null ? cell.rank : cell.rs));
      const bg = rsColor(cell.rs);
      if (bg) td.style.background = bg;
      tr.appendChild(td);
    }

    const slope = rankSlope(it, cols);
    let dcell;
    if (slope == null) dcell = el("td", { class: "delta" }, "—");
    else if (slope > 0.05) dcell = el("td", { class: "delta delta-up" }, "▲" + slope.toFixed(1));
    else if (slope < -0.05) dcell = el("td", { class: "delta delta-down" }, "▼" + Math.abs(slope).toFixed(1));
    else dcell = el("td", { class: "delta" }, "±0");
    tr.appendChild(dcell);

    frag.appendChild(tr);
  }
  body.appendChild(frag);
}

function renderMovers(root, industries, cols) {
  const scored = industries
    .map((it) => ({ it, d: rankSlope(it, cols) }))
    .filter((x) => x.d != null && Math.abs(x.d) > 0.05);
  const up = scored.slice().sort((a, b) => b.d - a.d).slice(0, 5);
  const down = scored.slice().sort((a, b) => a.d - b.d).slice(0, 5);
  const recent = cols.slice(-TREND_LOOKBACK);
  const span = `直近${recent.length}期`;

  const group = (label, items, cls, sign) => {
    const g = el("div", { class: "mv-group" }, el("span", { class: "mv-label" }, label));
    if (!items.length) { g.appendChild(el("span", { class: "mv-label" }, "—")); return g; }
    for (const x of items) {
      g.appendChild(el("span", { class: "mv" },
        indJa(x.it.industry) + " ",
        el("span", { class: "d " + cls }, sign + Math.abs(x.d).toFixed(1))));
    }
    return g;
  };
  root.appendChild(group(`🔼 上昇 (${span})`, up, "delta-up", "▲"));
  root.appendChild(group(`🔽 下降 (${span})`, down, "delta-down", "▼"));
}

function sparklineSVG(ind, cols, mode) {
  const useRank = mode === "rank";
  const W = 110, H = 26, pad = 3;
  const pts = cols.map((c) => {
    const cell = cellAt(ind, c);
    if (!cell) return null;
    const v = useRank ? cell.rank : cell.rs;
    return v != null ? { rs: cell.rs, v } : null;
  });
  const vals = pts.filter((p) => p).map((p) => p.v);
  const svg = svgEl("svg", { class: "spark", viewBox: `0 0 ${W} ${H}`, width: W, height: H });
  if (vals.length === 0) return svg;

  let vmin = Math.min(...vals), vmax = Math.max(...vals);
  if (vmin === vmax) { vmin -= 1; vmax += 1; }
  const n = cols.length;
  const xAt = (i) => pad + (n <= 1 ? (W - 2 * pad) / 2 : (i * (W - 2 * pad)) / (n - 1));
  const yAt = useRank
    ? (v) => pad + ((v - vmin) / (vmax - vmin)) * (H - 2 * pad)
    : (v) => pad + ((vmax - v) / (vmax - vmin)) * (H - 2 * pad);

  let seg = [];
  const flush = () => {
    if (seg.length >= 2) svg.appendChild(svgEl("polyline", { class: "spark-line", points: seg.join(" ") }));
    seg = [];
  };
  pts.forEach((p, i) => { if (!p) { flush(); return; } seg.push(`${xAt(i)},${yAt(p.v)}`); });
  flush();

  let lastIdx = -1;
  for (let i = pts.length - 1; i >= 0; i--) if (pts[i]) { lastIdx = i; break; }
  if (lastIdx >= 0) {
    const last = pts[lastIdx];
    svg.appendChild(svgEl("circle",
      { cx: xAt(lastIdx), cy: yAt(last.v), r: 2.5, fill: rsColor(last.rs) || "#4ea1ff" }));
  }
  const unit = useRank ? "順位" : "RS";
  svg.appendChild(svgEl("title", {}, `${indJa(ind.industry)}\n${unit} ${vals[0]} → ${vals[vals.length - 1]}`));
  return svg;
}

// ============================================================
// センチメントパネル
// ============================================================
const SENT_KEY = "sentiment_manual_v1";

function sentLoad() {
  try { return JSON.parse(localStorage.getItem(SENT_KEY)) || {}; } catch { return {}; }
}
function sentSave(obj) {
  try { localStorage.setItem(SENT_KEY, JSON.stringify(obj)); } catch {}
}

function calcVixScore(v)  { return v>=60?3:v>=45?2.5:v>=35?2:v>=25?1:0; }
function calcPcrScore(p)  { return p>=1.5?3:p>=1.2?2.5:p>=1.0?1.5:p>=0.85?1:0; }
function calcAaiiScore(a) { return a>=50?2:a>=45?1.5:a>=40?1:a>=35?0.5:0; }
function calcVtsScore(r)  { return r>=1.1?2:r>=1.0?1.5:r>=0.95?0.5:0; }

function getSignal(score) {
  if (score>=10)  return {label:"超全力買い", color:"#ff3860"};
  if (score>=8.5) return {label:"全力買い",   color:"#ffd600"};
  if (score>=6.5) return {label:"買い開始",   color:"#00e5a0"};
  if (score>=4.5) return {label:"打診のみ",   color:"#4d9fff"};
  return                  {label:"見送り",     color:"#6b7280"};
}

function vixLabel(v)  { if(v==null)return"—"; if(v>=35)return"恐怖"; if(v>=25)return"注意"; return"通常"; }
function pcrLabel(p)  { if(p==null)return"—"; if(p>=1.0)return"弱気"; if(p>=0.85)return"中立"; return"強気"; }
function aaiiLabel(a) { if(a==null)return"—"; if(a>=45)return"強弱気"; if(a>=35)return"弱気"; return"平均"; }
function vtsLabel(r)  { if(r==null)return"—"; if(r>=1.1)return"警戒"; if(r>=1.0)return"やや高"; return"通常"; }

const INPUT_STYLE = "width:72px;background:var(--panel-2);border:1px solid var(--border);color:var(--text);border-radius:4px;padding:2px 6px;font-size:11px;";
const LABEL_STYLE = "font-size:10px;color:var(--text-dim);white-space:nowrap;";
const LINK_STYLE  = "font-size:10px;color:var(--accent);white-space:nowrap;";

function buildSentimentCard() {
  const card = el("div", { class: "card", id: "sent-card", style: "min-width:240px" });
  card.appendChild(el("h3", {}, "📊 NQ1! センチメント ",
    el("a", {
      href: "sentiment-db.html",
      target: "_blank",
      style: "font-size:10px;color:var(--accent);font-weight:400;letter-spacing:0"
    }, "結果DB↗")
  ));

  const sent    = state.data.sentiment || {};
  const vix     = sent.vix  ?? null;
  const vts     = sent.vts  ?? null;
  const autoPcr = sent.pcr  ?? null;   // generate.py による自動取得値

  const manual  = sentLoad();

  // 有効PCR: 自動取得成功なら自動値、失敗なら手動保存値
  const initPcr  = autoPcr !== null ? autoPcr : (manual.pcr  ?? null);
  const initAaii = manual.aaii ?? null;

  // ---- PCR 入力行 ----
  const pcrInput = document.createElement("input");
  Object.assign(pcrInput, {
    type: "number", step: "0.01", min: "0", max: "10",
    placeholder: "PCR手動",
    value: initPcr !== null ? String(initPcr) : "",
  });
  pcrInput.style.cssText = INPUT_STYLE;
  // 自動取得成功時はグレーアウトして「自動取得済み」を示す
  if (autoPcr !== null) {
    pcrInput.style.opacity = "0.55";
    pcrInput.title = `generate.py が自動取得済み（${autoPcr}）。手動で上書きも可。`;
  }

  const pcrAutoLabel = autoPcr !== null
    ? el("span", { style: "font-size:10px;color:var(--accent);" }, "✓自動")
    : el("span", { style: "font-size:10px;color:#f59e0b;" }, "要手動");

  const pcrLink = el("a", {
    href: "https://www.cboe.com/markets/us/options/market-statistics/daily/",
    target: "_blank",
    style: LINK_STYLE,
    title: "CBOE Daily Market Statistics（Equity Put/Call Ratio を確認）"
  }, "CBOE↗");

  const pcrRow = el("div", { style: "display:flex;gap:6px;align-items:center;margin-bottom:4px;flex-wrap:wrap;" });
  pcrRow.append(
    el("span", { style: LABEL_STYLE }, "PCR:"),
    pcrInput,
    pcrAutoLabel,
    pcrLink
  );

  // ---- AAII 入力行 ----
  const aaiiInput = document.createElement("input");
  Object.assign(aaiiInput, {
    type: "number", step: "0.1", min: "0", max: "100",
    placeholder: "AAII弱気%",
    value: initAaii !== null ? String(initAaii) : "",
  });
  aaiiInput.style.cssText = INPUT_STYLE;

  const aaiiLink = el("a", {
    href: "https://www.aaii.com/sentimentsurvey",
    target: "_blank",
    style: LINK_STYLE,
  }, "AAII↗");

  const saveBtn = document.createElement("button");
  saveBtn.textContent = "保存";
  saveBtn.style.cssText = "font-size:10px;padding:2px 6px;";

  const scoresDiv = el("div", { id: "sent-scores" });

  saveBtn.addEventListener("click", () => {
    const aaii    = parseFloat(aaiiInput.value);
    const pcrManual = parseFloat(pcrInput.value);
    const saveAaii = isNaN(aaii)    ? null : aaii;
    const savePcr  = isNaN(pcrManual) ? null : pcrManual;
    sentSave({ aaii: saveAaii, pcr: savePcr });

    // 表示に使うPCR: 手動入力値 > 自動値 の順（保存した手動値を優先）
    const usePcr = savePcr !== null ? savePcr : autoPcr;
    renderSentScores(scoresDiv, vix, vts, usePcr, saveAaii);

    saveBtn.textContent = "保存済 ✓";
    setTimeout(() => { saveBtn.textContent = "保存"; }, 1500);
  });

  const aaiiRow = el("div", { style: "display:flex;gap:6px;align-items:center;margin-bottom:6px;flex-wrap:wrap;" });
  aaiiRow.append(
    el("span", { style: LABEL_STYLE }, "AAII弱気%:"),
    aaiiInput,
    aaiiLink,
    saveBtn
  );

  card.appendChild(pcrRow);
  card.appendChild(aaiiRow);
  card.appendChild(scoresDiv);

  // 初期描画（有効PCRを使用）
  renderSentScores(scoresDiv, vix, vts, initPcr, initAaii);

  return card;
}

function renderSentScores(target, vix, vts, pcr, aaii) {
  target.innerHTML = "";
  const maxScore = 13;
  const score = calcVixScore(vix) + calcPcrScore(pcr) + calcAaiiScore(aaii) + calcVtsScore(vts);
  const sig = getSignal(score);

  const metrics = [
    { label:"VIX",      val: vix  != null ? vix.toFixed(1)      : "—", sub: vixLabel(vix)  },
    { label:"PCR",      val: pcr  != null ? pcr.toFixed(2)      : "—", sub: pcrLabel(pcr)  },
    { label:"AAII弱気", val: aaii != null ? aaii.toFixed(1)+"%"  : "—", sub: aaiiLabel(aaii)},
    { label:"VTS",      val: vts  != null ? vts.toFixed(2)      : "—", sub: vtsLabel(vts)  },
    { label:"SCORE",    val: `${score.toFixed(1)}/${maxScore}`,          sub: sig.label, color: sig.color },
  ];

  const grid = el("div", { style:"display:grid;grid-template-columns:repeat(5,1fr);gap:2px 4px;margin-bottom:6px;" });
  for (const m of metrics) {
    const col = el("div", { style:"text-align:center;" });
    col.appendChild(el("div", { style:"font-size:10px;color:var(--text-dim);" }, m.label));
    col.appendChild(el("div", { style:`font-size:13px;font-weight:600;color:${m.color||"var(--text)"};font-variant-numeric:tabular-nums;` }, m.val));
    col.appendChild(el("div", { style:`font-size:10px;color:${m.color||"var(--text-dim)"};` }, m.sub));
    grid.appendChild(col);
  }
  target.appendChild(grid);

  const barWrap = el("div", { style:"background:var(--panel-2);border-radius:3px;height:6px;margin-bottom:5px;overflow:hidden;" });
  barWrap.appendChild(el("div", { style:`height:100%;width:${Math.min(100,score/maxScore*100).toFixed(1)}%;background:${sig.color};border-radius:3px;` }));
  target.appendChild(barWrap);

  let msg = score < 4.5 ? "→ VIX25+ / PCR0.85+ / AAII35%+ を待つ"
          : score < 6.5 ? "→ 小さく打診、追加は慎重に"
          : score < 8.5 ? "→ 分割買い開始"
          : score < 10  ? "→ 積極買い"
          : "→ 全力買い！";
  target.appendChild(el("div", { style:"font-size:10px;color:var(--text-dim);" }, msg));
}

init();
