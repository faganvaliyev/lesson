"""Rəqəmsal uçurum və əmək bazarı — Streamlit dashboard.

Data:
  * data/wdi_snapshot.csv — World Bank WDI API-dən 23.11.2026-da yüklənib.
  * data/manual.csv — WDI-də olmayan göstəricilər (cins və şəhər/kənd üzrə internet istifadəsi).
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


def az(x, digits=1):
    """Rəqəmi Azərbaycan formatında yazır: 7.3 -> 7,3."""
    return f"{x:.{digits}f}".replace(".", ",")


@st.cache_data
def load_wdi():
    return pd.read_csv(DATA_DIR / "wdi_snapshot.csv")


@st.cache_data
def load_manual():
    return pd.read_csv(DATA_DIR / "manual.csv")


def style(fig, y_title=None):
    fig.update_layout(
        xaxis_title=None,
        yaxis_title=y_title,
        legend_title=None,
        margin=dict(t=40, b=10, l=10, r=10),
        hovermode="x unified",
        separators=",.",
    )
    return fig


st.set_page_config(page_title="Rəqəmsal uçurum və əmək bazarı", page_icon="📶", layout="wide")

wdi = load_wdi()
wdi["Ölkə"] = wdi["country"].map(COUNTRIES)
manual = load_manual()

# ---------- Sidebar ----------
st.sidebar.header("Filtrlər")
selected_names = st.sidebar.multiselect(
    "Ölkələr", list(COUNTRIES.values()), default=list(COUNTRIES.values())
)
selected = [code for code, name in COUNTRIES.items() if name in selected_names] or ["AZE"]
year = st.sidebar.slider("Müqayisə ili", 2010, 2025, 2024)
st.sidebar.divider()
st.sidebar.info(f"Data tarixi: {DATA_DATE} (World Bank WDI)")
st.sidebar.caption(
    "Mənbələr: World Bank WDI, ITU, DSK. Bütün göstəricilər «Data» bölməsində yüklənə bilər."
)

# ---------- Header ----------
st.title("Rəqəmsal uçurum və əmək bazarı")
st.markdown(
    "**Sual:** Azərbaycanda internet istifadəsində cins və bölgə fərqləri necə dəyişib "
    "və onlar əmək bazarındakı fərqlərlə üst-üstə düşürmü?"
)

# ---------- Shared calculations ----------
sex = manual[manual["indicator"] == "internet_users_by_sex"].copy()
sex["year"] = sex["year"].astype(int)  # manual.csv-də boş illər var, pandas onları float oxuyur
sex["Qrup"] = sex["group"].map(SEX_LABELS)
sex_gap = sex.pivot_table(index="year", columns="group", values="value").reset_index()
sex_gap["gap"] = sex_gap["male"] - sex_gap["female"]
sex_gap = sex_gap.merge(sex.groupby("year", as_index=False)["source"].first(), on="year")
sex_gap["Mənbə"] = sex_gap["source"].str.split(" ").str[0]
gap_by_year = sex_gap.set_index("year")["gap"]
latest_sex_year = int(sex_gap["year"].max())

area = manual[manual["indicator"] == "internet_users_by_area"].copy()
area["Ərazi"] = area["group"].map(AREA_LABELS)
area_vals = area.set_index("group")["value"]
area_gap = area_vals["urban"] - area_vals["rural"]

labour = wdi[wdi["indicator"].isin(LABOUR)].copy()
labour["Göstərici"] = labour["indicator"].map(lambda i: LABOUR[i][0])
labour["Qrup"] = labour["indicator"].map(lambda i: LABOUR[i][1])


def wdi_value(indicator, country, yr):
    match = wdi[(wdi["indicator"] == indicator) & (wdi["country"] == country) & (wdi["year"] == yr)]
    return None if match.empty else float(match["value"].iloc[0])


tab_sex, tab_countries, tab_area, tab_labour, tab_findings, tab_data = st.tabs(
    ["Cins fərqi", "Ölkələrlə müqayisə", "Şəhər və kənd", "Əmək bazarı", "Tapıntılar", "Data"]
)

# ---------- 1. Gender gap over time ----------
with tab_sex:
    st.subheader("Kişi və qadınlar arasında internet istifadəsi, Azərbaycan")
    cols = st.columns(len(sex_gap))
    for col, row in zip(cols, sex_gap.itertuples()):
        col.metric(str(row.year), f"{az(row.gap)} bənd", help=f"Kişilər {az(row.male)}%, qadınlar {az(row.female)}%")

    left, right = st.columns(2)
    fig = px.line(
        sex, x="year", y="value", color="Qrup", markers=True, text="value",
        color_discrete_map=SEX_COLORS,
    )
    fig.update_traces(texttemplate="%{y:.1f}", textposition="top center")
    fig.update_xaxes(tickvals=sex_gap["year"])
    left.plotly_chart(style(fig, "İnternet istifadə edənlər, %"), use_container_width=True)

    fig = px.bar(
        sex_gap, x=sex_gap["year"].astype(str), y="gap", color="Mənbə", text=sex_gap["gap"].map(az),
        color_discrete_map={"DSK": "#95A5A6", "ITU": "#C0392B"},
    )
    right.plotly_chart(style(fig, "Fərq, faiz bəndi"), use_container_width=True)
    st.caption(
        "Diqqət: 2010–2015 DSK, 2019–2024 ITU datasıdır — metodologiya fərqli ola bilər, "
        "ona görə sütunlar mənbəyə görə rənglənib."
    )

# ---------- 2. Country comparison ----------
with tab_countries:
    net = wdi[(wdi["indicator"] == "IT.NET.USER.ZS") & (wdi["country"].isin(selected))]
    st.subheader("İnternet istifadəçiləri, əhalinin %-i (WDI)")
    fig = px.line(net.sort_values("year"), x="year", y="value", color="Ölkə", markers=True,
                  color_discrete_map=COUNTRY_COLORS)
    st.plotly_chart(style(fig, "%"), use_container_width=True)

    left, right = st.columns(2)
    snap = net[net["year"] == year].sort_values("value")
    missing = sorted(set(COUNTRIES[c] for c in selected) - set(snap["Ölkə"]))
    left.markdown(f"**{year}-ci il üzrə sıralama**")
    if snap.empty:
        left.info(f"{year} üçün data yoxdur.")
    else:
        fig = px.bar(snap, x="value", y="Ölkə", orientation="h", text=snap["value"].map(az),
                     color="Ölkə", color_discrete_map=COUNTRY_COLORS)
        fig.update_layout(showlegend=False)
        left.plotly_chart(style(fig), use_container_width=True)
    if missing:
        left.caption(f"{year} üçün data yoxdur: {', '.join(missing)}")

    gaps = manual[manual["indicator"] == "gender_gap_pp"].copy()
    gaps = pd.concat(
        [pd.DataFrame([{"country": "AZE", "year": latest_sex_year, "value": gap_by_year[latest_sex_year]}]), gaps]
    )
    gaps["Etiket"] = gaps.apply(
        lambda r: f"{COUNTRIES[r['country']]} ({int(r['year']) if pd.notna(r['year']) else 'son mövcud il'})",
        axis=1,
    )
    right.markdown("**Kişi və qadın arasında fərq, faiz bəndi**")
    fig = px.bar(gaps, x="Etiket", y="value", text=gaps["value"].map(az), color="Etiket",
                 color_discrete_sequence=["#C0392B", "#2C3E50", "#17A589"])
    fig.update_layout(showlegend=False)
    right.plotly_chart(style(fig, "bənd"), use_container_width=True)
    right.caption("Mənbə: ITU (Report.az, 10.03.2025); ITU Facts and Figures 2025; dig.watch. İllər fərqlidir.")

# ---------- 3. Urban vs rural ----------
with tab_area:
    st.subheader(f"Şəhər və kənd: internet istifadə edənlər, %, {int(area['year'].iloc[0])}")
    left, right = st.columns([1, 2])
    left.metric("Şəhər", f"{az(area_vals['urban'])}%")
    left.metric("Kənd", f"{az(area_vals['rural'])}%")
    left.metric("Fərq", f"{az(area_gap)} bənd",
                help=f"Cins fərqi ({latest_sex_year}): {az(gap_by_year[latest_sex_year])} bənd")
    fig = px.bar(area, x="Ərazi", y="value", text=area["value"].map(az), color="Ərazi",
                 color_discrete_map={"Şəhər": "#2E86C1", "Kənd": "#C0392B"})
    fig.update_layout(showlegend=False, yaxis_range=[0, 100])
    right.plotly_chart(style(fig, "%"), use_container_width=True)
    st.caption("Mənbə: ITU (APA, 10.03.2025)")

    st.subheader("Sabit genişzolaqlı internet, 100 nəfərə abunə (WDI)")
    bb = wdi[(wdi["indicator"] == "IT.NET.BBND.P2") & (wdi["country"].isin(selected))]
    fig = px.line(bb.sort_values("year"), x="year", y="value", color="Ölkə", markers=True,
                  color_discrete_map=COUNTRY_COLORS)
    st.plotly_chart(style(fig, "abunə / 100 nəfər"), use_container_width=True)
    st.caption("Kənddə istifadənin aşağı olmasının mümkün səbəbi: sabit şəbəkə zəifdir və 2015-dən bəri az artıb.")

# ---------- 4. Labour market ----------
with tab_labour:
    st.subheader(f"İşçi qüvvəsində iştirak və məşğulluq, cins üzrə, {year} (WDI, 15+ yaş)")
    lab_year = labour[(labour["year"] == year) & (labour["country"].isin(selected))]
    if lab_year.empty:
        st.info(f"{year} üçün əmək bazarı datası yoxdur.")
    else:
        fig = px.bar(lab_year, x="Ölkə", y="value", color="Qrup", barmode="group", facet_col="Göstərici",
                     text=lab_year["value"].map(lambda v: az(v, 0)), color_discrete_map=SEX_COLORS)
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.update_xaxes(title=None)
        st.plotly_chart(style(fig, "%"), use_container_width=True)

    left, right = st.columns(2)
    lfp = labour[(labour["Göstərici"] == "İşçi qüvvəsində iştirak") & (labour["country"].isin(selected))]
    lfp_gap = lfp.pivot_table(index=["Ölkə", "year"], columns="Qrup", values="value").reset_index()
    lfp_gap["gap"] = lfp_gap["Kişilər"] - lfp_gap["Qadınlar"]
    left.markdown("**İşçi qüvvəsində iştirak: kişi − qadın fərqi, bənd**")
    fig = px.line(lfp_gap, x="year", y="gap", color="Ölkə", markers=True, color_discrete_map=COUNTRY_COLORS)
    left.plotly_chart(style(fig, "bənd"), use_container_width=True)

    # Ölkələr arasında: internet istifadəsi yüksək olan yerdə qadınlar daha çox işləyirmi?
    right.markdown(f"**İnternet istifadəsi və qadınların işçi qüvvəsində iştirakı, {year}**")
    scatter = (
        wdi[(wdi["year"] == year) & (wdi["country"].isin(selected))
            & wdi["indicator"].isin(["IT.NET.USER.ZS", "SL.TLF.CACT.FE.ZS"])]
        .pivot_table(index="Ölkə", columns="indicator", values="value")
        .dropna()
        .reset_index()
    )
    if scatter.empty:
        right.info(f"{year} üçün hər iki göstərici yoxdur.")
    else:
        fig = px.scatter(scatter, x="IT.NET.USER.ZS", y="SL.TLF.CACT.FE.ZS", color="Ölkə", text="Ölkə",
                         color_discrete_map=COUNTRY_COLORS)
        fig.update_traces(textposition="top center", marker_size=12)
        fig.update_layout(showlegend=False, xaxis_title="İnternet istifadəçiləri, %",
                          yaxis_title="Qadınların işçi qüvvəsində iştirakı, %",
                          margin=dict(t=40, b=10, l=10, r=10), separators=",.")
        right.plotly_chart(fig, use_container_width=True)
        right.caption("Hər nöqtə bir ölkədir. Əlaqə zəifdirsə, internet tək başına məşğulluğu izah etmir.")

    shares = manual[manual["indicator"] == "women_share_of_workers"].set_index("group")["value"]
    c1, c2 = st.columns(2)
    c1.metric("Nəqliyyat və anbar sektorunda qadın payı", f"{az(shares['transport_storage'])}%")
    c2.metric("Enerji sektorunda qadın payı", f"{az(shares['energy'])}%")
    st.caption(
        "Mənbə: World Bank WDI (ILO modelləşdirilmiş qiymətlər, 15+ yaş); sektor payları — Dünya Bankı, "
        "«Breaking Barriers to Women's Employment in Azerbaijan». Hesabatdakı rəqəmlər fərqli yaş qrupuna "
        "aid ola bilər, ona görə WDI rəqəmləri ilə üst-üstə düşməyə bilər."
    )

# ---------- 5. Findings ----------
with tab_findings:
    st.subheader("Üç tapıntı")
    first_year = int(sex_gap["year"].min())
    lfp_m = wdi_value("SL.TLF.CACT.MA.ZS", "AZE", year)
    lfp_f = wdi_value("SL.TLF.CACT.FE.ZS", "AZE", year)
    emp_m = wdi_value("SL.EMP.TOTL.SP.MA.ZS", "AZE", year)
    emp_f = wdi_value("SL.EMP.TOTL.SP.FE.ZS", "AZE", year)

    f1, f2, f3 = st.columns(3)
    with f1.container(border=True):
        st.markdown("**TAPINTI 1 · Cins fərqi dayanıb**")
        st.metric("Fərq", f"{az(gap_by_year[latest_sex_year])} bənd",
                  delta=f"{az(gap_by_year[latest_sex_year] - gap_by_year[first_year])} bənd ({first_year}-dən)",
                  delta_color="inverse")
        st.write(
            f"Fərq {first_year}-də {az(gap_by_year[first_year])} bənd idi, 2015-də "
            f"{az(gap_by_year[2015])} bəndə düşdü və {latest_sex_year}-də {az(gap_by_year[latest_sex_year])} "
            "bənddə qaldı."
        )
        st.caption("Mümkün səbəb: giriş əsasən var; qalan fərq bacarıq və sosial normalarla bağlı ola bilər.")
    with f2.container(border=True):
        st.markdown("**TAPINTI 2 · Kənd fərqi daha böyükdür**")
        st.metric("Şəhər − kənd", f"{az(area_gap)} bənd")
        st.write(
            f"Kənddə istifadə {az(area_vals['rural'])}%, şəhərdə {az(area_vals['urban'])}%. "
            f"Bu, cins fərqindən ({az(gap_by_year[latest_sex_year])} bənd) "
            f"{az(area_gap / gap_by_year[latest_sex_year])} dəfə böyükdür."
        )
        bb_aze = wdi_value("IT.NET.BBND.P2", "AZE", 2024)
        if bb_aze is not None:
            st.caption(f"Mümkün səbəb: sabit internet zəifdir — 100 nəfərə {az(bb_aze, 2)} abunə (2024).")
    with f3.container(border=True):
        st.markdown(f"**TAPINTI 3 · Əmək bazarında fərq ({year})**")
        if None in (lfp_m, lfp_f, emp_m, emp_f):
            st.info(f"{year} üçün Azərbaycan əmək datası yoxdur — başqa il seçin.")
        else:
            st.metric("Məşğulluq fərqi", f"{az(emp_m - emp_f)} bənd")
            st.write(
                f"Qadınların məşğulluğu {az(emp_f)}%, kişilərin {az(emp_m)}%. İşçi qüvvəsində iştirak: "
                f"{az(lfp_f)}% və {az(lfp_m)}% ({az(lfp_m - lfp_f)} bənd fərq)."
            )
        st.caption("Bu korrelyasiyadır, səbəb deyil: təhsil seçimi və normalar hər ikisinə təsir edə bilər.")

    st.subheader("Data nəyi göstərmir")
    st.table(pd.DataFrame(
        [
            ["Yaş qrupları üzrə istifadə", "Yaşlı işçilərin riskini görmək", "DSK-nın ev təsərrüfatlarında İKT sorğusu"],
            ["İqtisadi rayonlar üzrə istifadə", "Kənd fərqinin harada ən böyük olduğunu tapmaq",
             "DSK; Dünya Bankı «Rural Digital Needs Assessment» (2024)"],
            ["İnternetin sürəti və məqsədi", "«İstifadə edir» hələ «işdə istifadə edir» demək deyil",
             "Provayderlər, Ookla, sorğular"],
            ["Fərd səviyyəsində bacarıq və iş", "Korrelyasiyanı səbəbdən ayırmaq",
             "İşçi qüvvəsi sorğusunun mikrodatası (DSK, ILO)"],
            ["Vakansiyalarda rəqəmsal tələb", "İşəgötürənlərin real ehtiyacı", "HH.az, Boss.az elanları"],
        ],
        columns=["Çatışmayan data", "Niyə lazımdır", "Harada ola bilər"],
    ))

# ---------- 6. Data & sources ----------
with tab_data:
    st.subheader(f"World Bank WDI (data tarixi: {DATA_DATE})")
    wdi_table = wdi.assign(Göstərici=wdi["indicator"].map(INDICATORS))[
        ["Göstərici", "indicator", "Ölkə", "year", "value"]
    ].sort_values(["indicator", "Ölkə", "year"])
    st.dataframe(wdi_table, use_container_width=True, hide_index=True)
    st.download_button("WDI datasını yüklə (CSV)", wdi_table.to_csv(index=False).encode("utf-8"),
                       "wdi.csv", "text/csv")
    st.markdown("\n".join(
        f"- [{name}](https://data.worldbank.org/indicator/{code}) — `{code}`" for code, name in INDICATORS.items()
    ))

    st.subheader("Əl ilə toplanmış göstəricilər (ITU, DSK, Dünya Bankı hesabatları)")
    st.dataframe(manual, use_container_width=True, hide_index=True)
    st.download_button("Əl ilə toplanmış datanı yüklə (CSV)", manual.to_csv(index=False).encode("utf-8"),
                       "manual.csv", "text/csv")
