"""Rəqəmsal uçurum və əmək bazarı — Streamlit dashboard.

Data:
  * data/wdi_snapshot.csv — World Bank WDI API-dən 23.11.2026-da yüklənib.
  * data/manual.csv — WDI-də olmayan göstəricilər (cins və şəhər/kənd üzrə internet istifadəsi).

Hər bölmə ayrıca səhifədir (st.navigation): /, /cins-ferqi, /olkeler, /seher-kend,
/emek-bazari, /tapintilar, /data.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
DATA_DATE = "23.11.2026"

COUNTRIES = {
    "AZE": "Azərbaycan",
    "GEO": "Gürcüstan",
    "KAZ": "Qazaxıstan",
    "ARM": "Ermənistan",
    "TUR": "Türkiyə",
    "UZB": "Özbəkistan",
    "WLD": "Dünya",
}
COUNTRY_COLORS = {
    "Azərbaycan": "#C0392B",
    "Gürcüstan": "#2E86C1",
    "Qazaxıstan": "#17A589",
    "Ermənistan": "#AF7AC5",
    "Türkiyə": "#E67E22",
    "Özbəkistan": "#5D6D7E",
    "Dünya": "#2C3E50",
}
SEX_LABELS = {"male": "Kişilər", "female": "Qadınlar"}
SEX_COLORS = {"Kişilər": "#2E86C1", "Qadınlar": "#C0392B"}
AREA_LABELS = {"urban": "Şəhər", "rural": "Kənd"}

INDICATORS = {
    "IT.NET.USER.ZS": "İnternet istifadəçiləri, əhalinin %-i",
    "IT.NET.BBND.P2": "Sabit genişzolaqlı abunə, 100 nəfərə",
    "SL.TLF.CACT.FE.ZS": "İşçi qüvvəsində iştirak, qadınlar (15+, %)",
    "SL.TLF.CACT.MA.ZS": "İşçi qüvvəsində iştirak, kişilər (15+, %)",
    "SL.EMP.TOTL.SP.FE.ZS": "Məşğulluq/əhali nisbəti, qadınlar (15+, %)",
    "SL.EMP.TOTL.SP.MA.ZS": "Məşğulluq/əhali nisbəti, kişilər (15+, %)",
}
LABOUR = {
    "SL.TLF.CACT.MA.ZS": ("İşçi qüvvəsində iştirak", "Kişilər"),
    "SL.TLF.CACT.FE.ZS": ("İşçi qüvvəsində iştirak", "Qadınlar"),
    "SL.EMP.TOTL.SP.MA.ZS": ("Məşğulluq", "Kişilər"),
    "SL.EMP.TOTL.SP.FE.ZS": ("Məşğulluq", "Qadınlar"),
}
MISSING_DATA = [
    ("Yaş qrupları üzrə istifadə", "Yaşlı işçilərin riskini görmək", "DSK-nın ev təsərrüfatlarında İKT sorğusu"),
    ("İqtisadi rayonlar üzrə istifadə", "Kənd fərqinin harada ən böyük olduğunu tapmaq",
     "DSK; Dünya Bankı «Rural Digital Needs Assessment» (2024)"),
    ("İnternetin sürəti və məqsədi", "«İstifadə edir» hələ «işdə istifadə edir» demək deyil",
     "Provayderlər, Ookla, sorğular"),
    ("Fərd səviyyəsində bacarıq və iş", "Korrelyasiyanı səbəbdən ayırmaq",
     "İşçi qüvvəsi sorğusunun mikrodatası (DSK, ILO)"),
    ("Vakansiyalarda rəqəmsal tələb", "İşəgötürənlərin real ehtiyacı", "HH.az, Boss.az elanları"),
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, .stApp, .stMarkdown, button, input, textarea { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 2.2rem; max-width: 1180px; }
footer { visibility: hidden; }

.kicker { font-size: .72rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
          color: #C0392B; margin-bottom: .35rem; }
.page-title { font-size: 2.1rem; font-weight: 800; color: #111827; line-height: 1.15; margin: 0 0 .4rem; }
.page-sub { font-size: 1.02rem; color: #4B5563; max-width: 820px; margin-bottom: 1.4rem; }

.hero { background: linear-gradient(135deg, #1F2937 0%, #7B241C 100%); border-radius: 18px;
        padding: 2.4rem 2.4rem 2.1rem; margin-bottom: 1.6rem; color: #F9FAFB; }
.hero .kicker { color: #FCA5A5; }
.hero h1 { font-size: 2.5rem; font-weight: 800; margin: 0 0 .7rem; color: #FFFFFF; line-height: 1.1; }
.hero p { font-size: 1.08rem; color: #E5E7EB; max-width: 760px; margin: 0; }
.hero .badge { display: inline-block; margin-top: 1.2rem; padding: .3rem .75rem; border-radius: 999px;
               background: rgba(255,255,255,.12); font-size: .8rem; color: #F3F4F6; }

.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem;
             margin: .2rem 0 1.6rem; }
.stat-card { background: #FFFFFF; border: 1px solid #E5E7EB; border-top: 4px solid var(--accent, #C0392B);
             border-radius: 14px; padding: 1rem 1.15rem; box-shadow: 0 1px 2px rgba(17,24,39,.04); }
.stat-card .label { font-size: .74rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase;
                    color: #6B7280; }
.stat-card .value { font-size: 2rem; font-weight: 800; color: #111827; line-height: 1.15; margin: .35rem 0 .2rem; }
.stat-card .note { font-size: .84rem; color: #6B7280; }

.chart-title { font-size: 1.02rem; font-weight: 700; color: #111827; margin: .1rem 0 .1rem; }
.chart-sub { font-size: .84rem; color: #6B7280; margin-bottom: .2rem; }
.source { font-size: .78rem; color: #6B7280; border-left: 3px solid #E5E7EB; padding-left: .65rem;
          margin: .2rem 0 1.6rem; }
.callout { background: #FFF7ED; border-left: 4px solid #F59E0B; border-radius: 10px; padding: .85rem 1rem;
           font-size: .9rem; color: #78350F; margin: .4rem 0 1.4rem; }

.finding { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 16px; padding: 1.3rem 1.3rem 1.1rem;
           height: 100%; box-shadow: 0 1px 2px rgba(17,24,39,.04); }
.finding .tag { font-size: .7rem; font-weight: 700; letter-spacing: .1em; color: #C0392B; }
.finding .big { font-size: 2.3rem; font-weight: 800; color: #111827; margin: .3rem 0 .5rem; }
.finding .text { font-size: .95rem; color: #374151; margin-bottom: .9rem; }
.finding .why { font-size: .86rem; color: #4B5563; background: #F9FAFB; border-radius: 10px; padding: .7rem .8rem; }
.finding .why b { color: #111827; }

table.nice { width: 100%; border-collapse: collapse; font-size: .9rem; background: #FFFFFF;
             border: 1px solid #E5E7EB; border-radius: 12px; overflow: hidden; }
table.nice th { text-align: left; font-size: .72rem; letter-spacing: .06em; text-transform: uppercase;
                color: #6B7280; background: #F9FAFB; padding: .7rem .9rem; border-bottom: 1px solid #E5E7EB; }
table.nice td { padding: .7rem .9rem; border-bottom: 1px solid #F3F4F6; color: #374151; vertical-align: top; }
table.nice tr:last-child td { border-bottom: none; }
table.nice td:first-child { font-weight: 600; color: #111827; }

[data-testid="stVerticalBlockBorderWrapper"] { background: #FFFFFF; border-radius: 16px; }
[data-testid="stSidebar"] { background: #111827; }
[data-testid="stSidebar"] * { color: #E5E7EB; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: rgba(192,57,43,.25); }
.side-brand { font-weight: 800; font-size: 1.05rem; color: #FFFFFF; margin: .2rem 0 .1rem; }
.side-date { margin-top: 1rem; font-size: .8rem; padding: .55rem .75rem; border-radius: 10px;
             background: rgba(255,255,255,.07); }
</style>
"""


# ---------- Helpers ----------
def az(x, digits=1):
    """Rəqəmi Azərbaycan formatında yazır: 7.3 -> 7,3."""
    return f"{x:.{digits}f}".replace(".", ",")


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def page_header(kicker, title, subtitle=None):
    sub = f'<div class="page-sub">{subtitle}</div>' if subtitle else ""
    html(f'<div class="kicker">{kicker}</div><div class="page-title">{title}</div>{sub}')


def stat_cards(cards):
    """cards: (label, value, note, accent) siyahısı."""
    items = "".join(
        f'<div class="stat-card" style="--accent:{accent}"><div class="label">{label}</div>'
        f'<div class="value">{value}</div><div class="note">{note}</div></div>'
        for label, value, note, accent in cards
    )
    html(f'<div class="stat-grid">{items}</div>')


def source(text):
    html(f'<div class="source">Mənbə: {text}</div>')


def chart(fig, title, subtitle=None, y_title=None, x_title=None, height=380, hovermode="x unified"):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Inter, sans-serif", size=13, color="#374151"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title=x_title,
        yaxis_title=y_title,
        legend_title=None,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(t=30, b=10, l=10, r=10),
        height=height,
        hovermode=hovermode,
        separators=",.",
    )
    with st.container(border=True):
        sub = f'<div class="chart-sub">{subtitle}</div>' if subtitle else ""
        html(f'<div class="chart-title">{title}</div>{sub}')
        st.plotly_chart(fig, use_container_width=True, theme=None, config={"displayModeBar": False})


def _keep(key):
    st.session_state[key] = st.session_state["_" + key]


def persistent(widget, key, default, **kwargs):
    """Widget dəyərini səhifələr arasında saxlayır (Streamlit görünməyən widget-in state-ini silir)."""
    if key not in st.session_state:
        st.session_state[key] = default
    st.session_state["_" + key] = st.session_state[key]
    return widget(key="_" + key, on_change=_keep, args=(key,), **kwargs)


def filters(show_year=True):
    with st.container(border=True):
        cols = st.columns([3, 1]) if show_year else [st.container()]
        names = persistent(cols[0].multiselect, "countries", list(COUNTRIES.values()),
                           label="Ölkələr", options=list(COUNTRIES.values()))
        year = None
        if show_year:
            year = persistent(cols[1].selectbox, "year", 2024, label="İl", options=list(range(2025, 2009, -1)))
    codes = [code for code, name in COUNTRIES.items() if name in names] or ["AZE"]
    return codes, year


# ---------- Data ----------
@st.cache_data
def load_wdi():
    return pd.read_csv(DATA_DIR / "wdi_snapshot.csv")


@st.cache_data
def load_manual():
    return pd.read_csv(DATA_DIR / "manual.csv")


wdi = load_wdi()
wdi["Ölkə"] = wdi["country"].map(COUNTRIES)
manual = load_manual()

sex = manual[manual["indicator"] == "internet_users_by_sex"].copy()
sex["year"] = sex["year"].astype(int)  # manual.csv-də boş illər var, pandas onları float oxuyur
sex["Qrup"] = sex["group"].map(SEX_LABELS)
sex_gap = sex.pivot_table(index="year", columns="group", values="value").reset_index()
sex_gap["gap"] = sex_gap["male"] - sex_gap["female"]
sex_gap = sex_gap.merge(sex.groupby("year", as_index=False)["source"].first(), on="year")
sex_gap["Mənbə"] = sex_gap["source"].str.split(" ").str[0]
gap_by_year = sex_gap.set_index("year")["gap"]
first_sex_year = int(sex_gap["year"].min())
latest_sex_year = int(sex_gap["year"].max())

area = manual[manual["indicator"] == "internet_users_by_area"].copy()
area["Ərazi"] = area["group"].map(AREA_LABELS)
area_vals = area.set_index("group")["value"]
area_gap = area_vals["urban"] - area_vals["rural"]
area_year = int(area["year"].iloc[0])

labour = wdi[wdi["indicator"].isin(LABOUR)].copy()
labour["Göstərici"] = labour["indicator"].map(lambda i: LABOUR[i][0])
labour["Qrup"] = labour["indicator"].map(lambda i: LABOUR[i][1])


def wdi_value(indicator, country, yr):
    match = wdi[(wdi["indicator"] == indicator) & (wdi["country"] == country) & (wdi["year"] == yr)]
    return None if match.empty else float(match["value"].iloc[0])


def latest_wdi(indicator, country):
    match = wdi[(wdi["indicator"] == indicator) & (wdi["country"] == country)].sort_values("year")
    return int(match["year"].iloc[-1]), float(match["value"].iloc[-1])


# ---------- Pages ----------
def page_overview():
    net_year, net_value = latest_wdi("IT.NET.USER.ZS", "AZE")
    emp_gap = wdi_value("SL.EMP.TOTL.SP.MA.ZS", "AZE", 2024) - wdi_value("SL.EMP.TOTL.SP.FE.ZS", "AZE", 2024)
    html(
        '<div class="hero"><div class="kicker">Kollokvium layihəsi · Format A: açıq data ilə alət</div>'
        "<h1>Rəqəmsal uçurum və əmək bazarı</h1>"
        "<p>Azərbaycanda internet istifadəsində cins və bölgə fərqləri necə dəyişib və onlar əmək "
        "bazarındakı fərqlərlə üst-üstə düşürmü?</p>"
        f'<span class="badge">Data tarixi: {DATA_DATE} · World Bank WDI, ITU, DSK</span></div>'
    )
    stat_cards([
        ("İnternet istifadəçiləri", f"{az(net_value)}%", f"əhalinin payı, {net_year}", "#2C3E50"),
        ("Cins fərqi", f"{az(gap_by_year[latest_sex_year])} bənd", f"kişi − qadın, {latest_sex_year}", "#C0392B"),
        ("Şəhər − kənd", f"{az(area_gap)} bənd", f"internet istifadəsi, {area_year}", "#E67E22"),
        ("Məşğulluq fərqi", f"{az(emp_gap)} bənd", "kişi − qadın, 2024", "#2E86C1"),
    ])
    html('<div class="chart-title" style="margin-bottom:.6rem">Bölmələr</div>')
    cols = st.columns(3)
    for i, (page, text) in enumerate(SECTION_CARDS):
        with cols[i % 3].container(border=True):
            st.page_link(page, label=page.title, icon=page.icon)
            st.caption(text)


def page_sex():
    page_header("Qrafik 1 · Zamanla dəyişmə", "Cins fərqi: əvvəl azaldı, sonra dayandı",
                "Kişi və qadınlar arasında internet istifadəsi, Azərbaycan, 2010–2024.")
    stat_cards([
        (str(row.year), f"{az(row.gap)} bənd", f"kişilər {az(row.male)}% · qadınlar {az(row.female)}%",
         "#95A5A6" if row.year < 2019 else "#C0392B")
        for row in sex_gap.itertuples()
    ])
    left, right = st.columns(2)
    with left:
        fig = px.line(sex, x="year", y="value", color="Qrup", markers=True, text="value",
                      color_discrete_map=SEX_COLORS)
        fig.update_traces(texttemplate="%{y:.1f}", textposition="top center")
        fig.update_xaxes(tickvals=sex_gap["year"])
        chart(fig, "İnternet istifadə edənlər, %", "Kişilər və qadınlar")
    with right:
        fig = px.bar(sex_gap, x=sex_gap["year"].astype(str), y="gap", color="Mənbə",
                     text=sex_gap["gap"].map(az), color_discrete_map={"DSK": "#95A5A6", "ITU": "#C0392B"})
        chart(fig, "Fərq, faiz bəndi", "Sütunlar mənbəyə görə rənglənib")
    html('<div class="callout">2010–2015 DSK, 2019–2024 ITU datasıdır — metodologiya fərqli ola bilər.</div>')
    source("DSK (Report.az, 01.09.2016) — 2010, 2015; ITU (CAREC, 2023) — 2019; ITU (Report.az, 10.03.2025) — 2024")


def page_countries():
    page_header("Qrafik 2 · Ölkələrlə müqayisə", "Azərbaycan regionda harada dayanır?",
                "Ümumi internet istifadəsi və kişi–qadın fərqi qonşu ölkələr və dünya ilə müqayisədə.")
    selected, year = filters()
    net = wdi[(wdi["indicator"] == "IT.NET.USER.ZS") & (wdi["country"].isin(selected))]
    fig = px.line(net.sort_values("year"), x="year", y="value", color="Ölkə", markers=True,
                  color_discrete_map=COUNTRY_COLORS)
    chart(fig, "İnternet istifadəçiləri, əhalinin %-i", "2010–2025", height=420)

    left, right = st.columns(2)
    with left:
        snap = net[net["year"] == year].sort_values("value")
        missing = sorted(set(COUNTRIES[c] for c in selected) - set(snap["Ölkə"]))
        if snap.empty:
            st.info(f"{year} üçün data yoxdur.")
        else:
            fig = px.bar(snap, x="value", y="Ölkə", orientation="h", text=snap["value"].map(az),
                         color="Ölkə", color_discrete_map=COUNTRY_COLORS)
            fig.update_layout(showlegend=False)
            chart(fig, f"{year}-ci il üzrə sıralama", "İnternet istifadəçiləri, %",
                  hovermode="closest")
        if missing:
            st.caption(f"{year} üçün data yoxdur: {', '.join(missing)}")
    with right:
        gaps = manual[manual["indicator"] == "gender_gap_pp"].copy()
        gaps = pd.concat(
            [pd.DataFrame([{"country": "AZE", "year": latest_sex_year, "value": gap_by_year[latest_sex_year]}]), gaps]
        )
        gaps["Etiket"] = gaps.apply(
            lambda r: f"{COUNTRIES[r['country']]} ({int(r['year']) if pd.notna(r['year']) else 'son mövcud il'})",
            axis=1,
        )
        fig = px.bar(gaps, x="Etiket", y="value", text=gaps["value"].map(az), color="Etiket",
                     color_discrete_sequence=["#C0392B", "#2C3E50", "#17A589"])
        fig.update_layout(showlegend=False)
        chart(fig, "Kişi və qadın arasında fərq", "Faiz bəndi; illər fərqlidir", hovermode="closest")
    source(f"World Bank WDI ({DATA_DATE}); ITU (Report.az, 10.03.2025); ITU Facts and Figures 2025; dig.watch")


def page_area():
    page_header("Qrafik 3 · Bölgə", "Şəhər və kənd: ən böyük fərq",
                f"İnternet istifadə edənlər, {area_year}, və sabit genişzolaqlı internetin inkişafı.")
    stat_cards([
        ("Şəhər", f"{az(area_vals['urban'])}%", f"internet istifadəsi, {area_year}", "#2E86C1"),
        ("Kənd", f"{az(area_vals['rural'])}%", f"internet istifadəsi, {area_year}", "#C0392B"),
        ("Fərq", f"{az(area_gap)} bənd",
         f"cins fərqindən ({az(gap_by_year[latest_sex_year])}) {az(area_gap / gap_by_year[latest_sex_year])} dəfə böyük",
         "#E67E22"),
    ])
    left, right = st.columns([2, 3])
    with left:
        fig = px.bar(area, x="Ərazi", y="value", text=area["value"].map(az), color="Ərazi",
                     color_discrete_map={"Şəhər": "#2E86C1", "Kənd": "#C0392B"})
        fig.update_layout(showlegend=False, yaxis_range=[0, 100])
        chart(fig, "İnternet istifadə edənlər, %", f"Azərbaycan, {area_year}", hovermode="closest")
    with right:
        selected, _ = filters(show_year=False)
        bb = wdi[(wdi["indicator"] == "IT.NET.BBND.P2") & (wdi["country"].isin(selected))]
        fig = px.line(bb.sort_values("year"), x="year", y="value", color="Ölkə", markers=True,
                      color_discrete_map=COUNTRY_COLORS)
        chart(fig, "Sabit genişzolaqlı internet", "100 nəfərə abunə", height=300)
    html('<div class="callout">Mümkün səbəb: sabit şəbəkə zəifdir və Azərbaycanda 2015-dən bəri az artıb.</div>')
    source(f"ITU (APA, 10.03.2025); World Bank WDI, IT.NET.BBND.P2 ({DATA_DATE})")


def page_labour():
    page_header("Qrafik 4 · Əmək bazarı", "Əmək bazarında da qadınlar geri qalır",
                "İşçi qüvvəsində iştirak və məşğulluq, cins üzrə (ILO modelləşdirilmiş qiymətlər, 15+ yaş).")
    selected, year = filters()
    lab_year = labour[(labour["year"] == year) & (labour["country"].isin(selected))]
    if lab_year.empty:
        st.info(f"{year} üçün əmək bazarı datası yoxdur.")
    else:
        fig = px.bar(lab_year, x="Ölkə", y="value", color="Qrup", barmode="group", facet_col="Göstərici",
                     text=lab_year["value"].map(lambda v: az(v, 0)), color_discrete_map=SEX_COLORS)
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font_size=14))
        fig.update_xaxes(title=None)
        chart(fig, "Kişilər və qadınlar", f"{year}, %", height=420, hovermode="closest")

    left, right = st.columns(2)
    with left:
        lfp = labour[(labour["Göstərici"] == "İşçi qüvvəsində iştirak") & (labour["country"].isin(selected))]
        lfp_gap = lfp.pivot_table(index=["Ölkə", "year"], columns="Qrup", values="value").reset_index()
        lfp_gap["gap"] = lfp_gap["Kişilər"] - lfp_gap["Qadınlar"]
        fig = px.line(lfp_gap, x="year", y="gap", color="Ölkə", markers=True, color_discrete_map=COUNTRY_COLORS)
        chart(fig, "İşçi qüvvəsində iştirak: kişi − qadın", "Faiz bəndi, 2010–2025")
    with right:
        # Ölkələr arasında: internet istifadəsi yüksək olan yerdə qadınlar daha çox işləyirmi?
        scatter = (
            wdi[(wdi["year"] == year) & (wdi["country"].isin(selected))
                & wdi["indicator"].isin(["IT.NET.USER.ZS", "SL.TLF.CACT.FE.ZS"])]
            .pivot_table(index="Ölkə", columns="indicator", values="value")
            .dropna()
            .reset_index()
        )
        if scatter.empty:
            st.info(f"{year} üçün hər iki göstərici yoxdur.")
        else:
            fig = px.scatter(scatter, x="IT.NET.USER.ZS", y="SL.TLF.CACT.FE.ZS", color="Ölkə", text="Ölkə",
                             color_discrete_map=COUNTRY_COLORS)
            fig.update_traces(textposition="top center", marker_size=13)
            fig.update_layout(showlegend=False)
            chart(fig, "İnternet və qadınların işçi qüvvəsində iştirakı", f"{year}; hər nöqtə bir ölkədir",
                  y_title="Qadınlar, işçi qüvvəsində %", x_title="İnternet istifadəçiləri, %", hovermode="closest")

    shares = manual[manual["indicator"] == "women_share_of_workers"].set_index("group")["value"]
    stat_cards([
        ("Nəqliyyat və anbar", f"{az(shares['transport_storage'])}%", "işçilərin qadın payı", "#C0392B"),
        ("Enerji", f"{az(shares['energy'])}%", "işçilərin qadın payı", "#C0392B"),
    ])
    source(f"World Bank WDI ({DATA_DATE}); sektor payları — Dünya Bankı, «Breaking Barriers to Women's "
           "Employment in Azerbaijan»")


def page_findings():
    page_header("Nəticələr", "Üç tapıntı", "Hər tapıntı rəqəm və müqayisə ilə, mümkün səbəbi ilə birlikdə.")
    year = persistent(st.selectbox, "year", 2024, label="Əmək bazarı üçün il", options=list(range(2025, 2009, -1)))
    lfp_m = wdi_value("SL.TLF.CACT.MA.ZS", "AZE", year)
    lfp_f = wdi_value("SL.TLF.CACT.FE.ZS", "AZE", year)
    emp_m = wdi_value("SL.EMP.TOTL.SP.MA.ZS", "AZE", year)
    emp_f = wdi_value("SL.EMP.TOTL.SP.FE.ZS", "AZE", year)
    bb_aze = wdi_value("IT.NET.BBND.P2", "AZE", 2024)
    latest_gap = gap_by_year[latest_sex_year]

    if None in (lfp_m, lfp_f, emp_m, emp_f):
        third = ("—", f"{year} üçün Azərbaycan əmək datası yoxdur — başqa il seçin.")
    else:
        third = (
            f"{az(emp_m - emp_f)} bənd",
            f"Qadınların məşğulluğu {az(emp_f)}%, kişilərin {az(emp_m)}% ({year}). İşçi qüvvəsində iştirak: "
            f"{az(lfp_f)}% və {az(lfp_m)}%. İnternetdə fərq isə {az(latest_gap)} bənd.",
        )
    findings = [
        ("Tapıntı 1 · Cins fərqi dayanıb", f"{az(latest_gap)} bənd",
         f"Fərq {first_sex_year}-də {az(gap_by_year[first_sex_year])} bənd idi, 2015-də {az(gap_by_year[2015])} "
         f"bəndə düşdü və {latest_sex_year}-də {az(latest_gap)} bənddə qaldı.",
         "Giriş əsasən var; qalan fərq bacarıq və sosial normalarla bağlı ola bilər."),
        ("Tapıntı 2 · Kənd fərqi daha böyükdür", f"{az(area_gap)} bənd",
         f"Kənddə istifadə {az(area_vals['rural'])}%, şəhərdə {az(area_vals['urban'])}% — cins fərqindən "
         f"{az(area_gap / latest_gap)} dəfə böyük.",
         f"Sabit internet zəifdir: 100 nəfərə {az(bb_aze, 2)} abunə (2024)."),
        ("Tapıntı 3 · Əmək bazarında fərq", third[0], third[1],
         "Bu korrelyasiyadır, səbəb deyil: təhsil seçimi və normalar hər ikisinə təsir edə bilər."),
    ]
    cols = st.columns(3)
    for col, (tag, big, text, why) in zip(cols, findings):
        with col:
            html(f'<div class="finding"><div class="tag">{tag.upper()}</div><div class="big">{big}</div>'
                 f'<div class="text">{text}</div><div class="why"><b>Mümkün səbəb:</b> {why}</div></div>')

    html('<div class="page-title" style="font-size:1.4rem;margin-top:2.2rem">Data nəyi göstərmir</div>')
    rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in MISSING_DATA)
    html(f'<table class="nice"><tr><th>Çatışmayan data</th><th>Niyə lazımdır</th><th>Harada ola bilər</th></tr>'
         f"{rows}</table>")
    html('<div class="callout" style="margin-top:1rem">2010–2015 DSK, 2019–2024 ITU datasıdır — '
         "metodologiya fərqli ola bilər.</div>")


def page_data():
    page_header("Data", "Data və mənbələr", f"WDI datası World Bank API-dən {DATA_DATE}-da yüklənib.")
    wdi_table = wdi.assign(Göstərici=wdi["indicator"].map(INDICATORS))[
        ["Göstərici", "indicator", "Ölkə", "year", "value"]
    ].sort_values(["indicator", "Ölkə", "year"])
    with st.container(border=True):
        html(f'<div class="chart-title">World Bank WDI ({DATA_DATE})</div>')
        st.dataframe(wdi_table, use_container_width=True, hide_index=True, height=320)
        st.download_button("CSV yüklə", wdi_table.to_csv(index=False).encode("utf-8"), "wdi.csv", "text/csv")
    with st.container(border=True):
        html('<div class="chart-title">Əl ilə toplanmış göstəricilər (ITU, DSK, Dünya Bankı hesabatları)</div>')
        st.dataframe(manual, use_container_width=True, hide_index=True)
        st.download_button("CSV yüklə", manual.to_csv(index=False).encode("utf-8"), "manual.csv", "text/csv",
                           key="manual_csv")
    html('<div class="chart-title" style="margin-top:1rem">WDI göstəriciləri</div>')
    st.markdown("\n".join(
        f"- [{name}](https://data.worldbank.org/indicator/{code}) — `{code}`" for code, name in INDICATORS.items()
    ))


# ---------- App ----------
st.set_page_config(page_title="Rəqəmsal uçurum və əmək bazarı", page_icon="📶", layout="wide")
html(CSS)

PAGE_OVERVIEW = st.Page(page_overview, title="Ümumi baxış", icon=":material/home:", url_path="umumi-baxis", default=True)
PAGE_SEX = st.Page(page_sex, title="Cins fərqi", icon=":material/wc:", url_path="cins-ferqi")
PAGE_COUNTRIES = st.Page(page_countries, title="Ölkələrlə müqayisə", icon=":material/public:", url_path="olkeler")
PAGE_AREA = st.Page(page_area, title="Şəhər və kənd", icon=":material/location_city:", url_path="seher-kend")
PAGE_LABOUR = st.Page(page_labour, title="Əmək bazarı", icon=":material/work:", url_path="emek-bazari")
PAGE_FINDINGS = st.Page(page_findings, title="Tapıntılar", icon=":material/lightbulb:", url_path="tapintilar")
PAGE_DATA = st.Page(page_data, title="Data", icon=":material/table_chart:", url_path="data")

SECTION_CARDS = [
    (PAGE_SEX, "Kişi və qadın arasında fərq, 2010–2024"),
    (PAGE_COUNTRIES, "Gürcüstan, Qazaxıstan, dünya və digərləri"),
    (PAGE_AREA, "Şəhər–kənd fərqi və sabit internet"),
    (PAGE_LABOUR, "İşçi qüvvəsi və məşğulluq, cins üzrə"),
    (PAGE_FINDINGS, "Üç tapıntı və data boşluqları"),
    (PAGE_DATA, "Bütün rəqəmlər, CSV və mənbələr"),
]

nav = st.navigation({
    "": [PAGE_OVERVIEW],
    "Analiz": [PAGE_SEX, PAGE_COUNTRIES, PAGE_AREA, PAGE_LABOUR],
    "Nəticə": [PAGE_FINDINGS, PAGE_DATA],
})
with st.sidebar:
    html(f'<div class="side-date">Data tarixi: <b>{DATA_DATE}</b><br>World Bank WDI · ITU · DSK</div>')
nav.run()
