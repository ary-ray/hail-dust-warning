import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="غبار حائل | نظام الإنذار المبكر",
    page_icon="🌪️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MODEL_AUC = 0.985
PRIMARY, DEEP, ACCENT, DANGER, SAFE, WARN = "#12304A", "#0F2A43", "#E8873A", "#D64545", "#2E9E6B", "#F2B134"

# ───────────────────────── الشعار ─────────────────────────
LOGO_SVG = """<svg viewBox="0 0 96 96" width="62" height="62" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0F2A43"/><stop offset="1" stop-color="#1F5D8C"/></linearGradient>
<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFC46B"/><stop offset="1" stop-color="#E8873A"/></linearGradient>
<clipPath id="c"><circle cx="48" cy="48" r="44"/></clipPath>
</defs>
<circle cx="48" cy="48" r="46" fill="url(#bg)"/>
<circle cx="48" cy="48" r="44" fill="none" stroke="#fff" stroke-opacity=".25" stroke-width="1.5"/>
<g clip-path="url(#c)">
<circle cx="62" cy="34" r="13" fill="url(#sun)"/>
<path d="M0 70 C20 58 38 58 56 68 S86 76 96 66 V96 H0Z" fill="#E8873A" fill-opacity=".92"/>
<path d="M0 78 C22 68 44 70 62 78 S86 84 96 76 V96 H0Z" fill="#C96B25"/>
<path d="M0 86 C24 80 50 82 70 88 S90 90 96 86 V96 H0Z" fill="#8F4817"/>
</g>
<path d="M18 40 H52 a7 7 0 1 0 -7 -7" fill="none" stroke="#fff" stroke-width="4.5" stroke-linecap="round"/>
<path d="M18 52 H66 a7 7 0 1 1 -7 7" fill="none" stroke="#fff" stroke-width="4.5" stroke-linecap="round" stroke-opacity=".92"/>
<path d="M18 28 H36" fill="none" stroke="#fff" stroke-width="4.5" stroke-linecap="round" stroke-opacity=".7"/>
</svg>"""

# ───────────────────────── التصميم ─────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
html, body, [class*="css"], .stApp { font-family:'Tajawal','Segoe UI',sans-serif; direction:rtl; text-align:right; }
.stApp { background:#F2F5F9; }
#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="collapsedControl"] { display:none !important; }
.block-container { padding-top:1rem; padding-bottom:2rem; max-width:1240px; }

/* الشريط العلوي */
.nav { display:flex; align-items:center; justify-content:space-between; gap:1rem; background:#fff; border:1px solid #E7ECF3;
 border-radius:18px; padding:.8rem 1.4rem; box-shadow:0 4px 18px rgba(15,42,67,.06); margin-bottom:1.1rem; }
.brand { display:flex; align-items:center; gap:.9rem; }
.brand-t { font-size:1.55rem; font-weight:800; color:__DEEP__; line-height:1.1; }
.brand-s { font-size:.9rem; color:#6B7A8C; margin-top:.15rem; }
.nav-chips { display:flex; gap:.6rem; flex-wrap:wrap; }
.pill { background:#F0F4F9; color:__DEEP__; border-radius:999px; padding:.35rem .9rem; font-size:.85rem; font-weight:500; }
.pill b { color:__ACCENT__; }

/* التبويبات */
div[data-baseweb="tab-list"] { gap:.5rem; background:transparent; }
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display:none; }
button[data-baseweb="tab"] { background:#fff; border:1px solid #E7ECF3; border-radius:12px; padding:.55rem 1.2rem; height:auto; }
button[data-baseweb="tab"] p { font-size:1rem; font-weight:700; color:#4A5A6C; }
button[data-baseweb="tab"][aria-selected="true"] { background:__DEEP__; border-color:__DEEP__; box-shadow:0 4px 12px rgba(15,42,67,.25); }
button[data-baseweb="tab"][aria-selected="true"] p { color:#fff; }

/* بطاقة الإنذار */
@keyframes pulse { 0% { box-shadow:0 0 0 0 var(--glow); } 70% { box-shadow:0 0 0 20px rgba(0,0,0,0); } 100% { box-shadow:0 0 0 0 rgba(0,0,0,0); } }
.alert { background:var(--c); background-image:linear-gradient(135deg, rgba(255,255,255,.2), rgba(0,0,0,.14)); color:#fff;
 border-radius:22px; padding:1.6rem 1.8rem; margin:.9rem 0 1.2rem 0; }
.alert.pulse { animation:pulse 2s infinite; }
.alert-top { display:flex; align-items:center; gap:1.2rem; }
.alert-ic { width:74px; height:74px; border-radius:20px; background:rgba(255,255,255,.2); display:flex; align-items:center; justify-content:center; font-size:2.6rem; flex:none; }
.alert-t { font-size:1.8rem; font-weight:800; line-height:1.2; }
.alert-s { opacity:.95; margin-top:.25rem; font-size:1.02rem; }
.chips { display:flex; gap:.6rem; flex-wrap:wrap; margin:1.1rem 0; }
.chip { background:rgba(255,255,255,.2); border-radius:999px; padding:.35rem .9rem; font-size:.9rem; }
.scale { display:flex; gap:.5rem; }
.seg { flex:1; text-align:center; padding:.5rem; border-radius:12px; background:rgba(255,255,255,.18); font-weight:700; font-size:.92rem; }
.seg.on { background:#fff; color:var(--c); box-shadow:0 4px 12px rgba(0,0,0,.18); }

/* البطاقات */
.kpi { display:flex; align-items:center; gap:.9rem; background:#fff; border:1px solid #E7ECF3; border-top:4px solid var(--c);
 border-radius:16px; padding:1rem 1.2rem; box-shadow:0 2px 12px rgba(15,42,67,.05); }
.kpi-ic { width:52px; height:52px; border-radius:14px; background:#F0F4F9; display:flex; align-items:center; justify-content:center; font-size:1.6rem; flex:none; }
.kpi-l { color:#6B7A8C; font-size:.9rem; }
.kpi-v { color:__DEEP__; font-size:1.7rem; font-weight:800; line-height:1.2; }
.kpi-h { color:#8A97A6; font-size:.8rem; }
.tip { background:#fff; border:1px solid #E7ECF3; border-top:4px solid var(--c); border-radius:16px; padding:1.1rem 1.2rem; height:100%; box-shadow:0 2px 12px rgba(15,42,67,.05); }
.tip-h { font-weight:800; color:__DEEP__; font-size:1.05rem; margin-bottom:.35rem; }
.tip-b { color:#4A5A6C; line-height:1.8; }
.sec { color:__DEEP__; font-weight:800; font-size:1.2rem; margin:1.5rem 0 .7rem 0; display:flex; align-items:center; gap:.6rem; }
.sec::before { content:""; width:6px; height:22px; border-radius:4px; background:__ACCENT__; }
.panel { background:#fff; border:1px solid #E7ECF3; border-radius:16px; padding:1rem 1.2rem; box-shadow:0 2px 12px rgba(15,42,67,.05); }
.foot { text-align:center; color:#8A97A6; font-size:.85rem; margin-top:2.2rem; }
div[data-testid="stPlotlyChart"] { background:#fff; border:1px solid #E7ECF3; border-radius:16px; padding:.4rem; box-shadow:0 2px 12px rgba(15,42,67,.05); }
div[data-testid="stDataFrame"] { border-radius:14px; overflow:hidden; }
</style>
"""
st.markdown(CSS.replace("__DEEP__", DEEP).replace("__ACCENT__", ACCENT), unsafe_allow_html=True)


# ───────────────────────── دوال مساعدة ─────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    d = pd.read_csv("hail_dust_predictions.csv")
    d["time"] = pd.to_datetime(d["time"])
    return d.sort_values("time").reset_index(drop=True)


def style(fig, h=400):
    fig.update_layout(
        height=h, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Tajawal, Segoe UI, sans-serif", size=13, color="#33414F"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E9EDF2")
    return fig


def kpi(icon, label, value, hint="", color=DEEP):
    return (f'<div class="kpi" style="--c:{color}"><div class="kpi-ic">{icon}</div>'
            f'<div><div class="kpi-l">{label}</div><div class="kpi-v">{value}</div><div class="kpi-h">{hint}</div></div></div>')


def scale_html(lvl):
    names, cols = ["آمن", "مراقبة", "تحذير", "خطر"], [SAFE, WARN, ACCENT, DANGER]
    segs = "".join(f'<div class="seg {"on" if i == lvl else ""}" style="--c:{cols[i]}">{names[i]}</div>' for i in range(4))
    return f'<div class="scale">{segs}</div>'


LEVELS = {
    0: ("الوضع آمن", "✅", SAFE, "لا يُتوقع غبار، والأجواء مناسبة للأنشطة المعتادة."),
    1: ("مراقبة", "👀", WARN, "رياح نشطة قد تثير الغبار، تابع التحديثات."),
    2: ("تحذير: غبار متوقع", "⚠️", ACCENT, "يُتوقع غبار، خذ احتياطاتك خصوصاً الفئات الحساسة."),
    3: ("خطر: عاصفة غبار محتملة", "🚨", DANGER, "رياح قوية وغبار متوقع، تجنب الخروج غير الضروري."),
}
ADVICE = {
    0: [("🫁", "مرضى الربو", "لا توجد قيود، وأبقِ البخاخ معك كالمعتاد."),
        ("🧒", "الأطفال", "اللعب في الخارج آمن."),
        ("🚗", "السائقون", "الرؤية طبيعية على الطرق.")],
    1: [("🫁", "مرضى الربو", "احمل البخاخ وتجنب الجهد الشديد في الخارج."),
        ("🧒", "الأطفال", "يُفضّل تقليل وقت اللعب في الأماكن المفتوحة."),
        ("🚗", "السائقون", "انتبه لتغيّر الرؤية على الطرق المفتوحة.")],
    2: [("🫁", "مرضى الربو", "ابقَ في الداخل قدر الإمكان والتزم بخطة العلاج."),
        ("🧒", "الأطفال", "أجّل الأنشطة الخارجية والرياضة المدرسية."),
        ("🚗", "السائقون", "خفّض السرعة وشغّل الإضاءة، وابتعد عن الطرق السريعة عند ضعف الرؤية.")],
    3: [("🫁", "مرضى الربو", "لا تخرج وأغلق النوافذ، وراجع الطوارئ عند ضيق التنفس."),
        ("🧒", "الأطفال", "ابقوا في الداخل وأوقفوا الأنشطة الخارجية."),
        ("🚗", "السائقون", "تجنب السفر إن أمكن، وعند انعدام الرؤية توقف في مكان آمن.")],
}


def risk_level(row, mod_thr, high_thr):
    g = row["wind_gusts_10m_max"]
    if row["predicted_dust"] == 1 and g >= high_thr:
        return 3
    if row["predicted_dust"] == 1:
        return 2
    return 1 if g >= mod_thr else 0


def estimate_risk(data, temp, wind, gust):
    for tol in (4, 6, 9, 14):
        m = data[(data["wind_gusts_10m_max"].sub(gust).abs() <= tol)
                 & (data["wind_speed_10m_max"].sub(wind).abs() <= tol)
                 & (data["temperature_2m_max"].sub(temp).abs() <= tol * 1.5)]
        if len(m) >= 20:
            return float(m["predicted_dust"].mean()), len(m)
    m = data[data["wind_gusts_10m_max"].sub(gust).abs() <= 15]
    return (float(m["predicted_dust"].mean()), len(m)) if len(m) else (0.0, 0)


# ───────────────────────── التطبيق ─────────────────────────
try:
    df = load_data()
    dust_df = df[df["predicted_dust"] == 1]
    base = dust_df if len(dust_df) >= 10 else df
    mod_thr = float(base["wind_gusts_10m_max"].quantile(0.25))
    high_thr = float(base["wind_gusts_10m_max"].quantile(0.75))
    min_d, max_d = df["time"].min().date(), df["time"].max().date()

    st.markdown(f"""
<div class="nav">
<div class="brand">{LOGO_SVG}<div><div class="brand-t">غبار حائل</div><div class="brand-s">نظام الإنذار المبكر لعواصف الغبار · منطقة حائل</div></div></div>
<div class="nav-chips"><span class="pill">📅 آخر سجل: <b>{max_d:%Y-%m-%d}</b></span><span class="pill">🎯 دقة النموذج: <b>{MODEL_AUC * 100:.1f}%</b></span></div>
</div>
""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🚨 مركز الإنذار", "🔍 المحاكي التفاعلي", "📊 التحليل", "ℹ️ عن النظام"])

    # ═════════ مركز الإنذار ═════════
    with tab1:
        pick = st.date_input("📅 اختر اليوم لعرض حالته", value=max_d, min_value=min_d, max_value=max_d, key="pick_day")
        r = df[df["time"].dt.date == pick]
        r = r.iloc[-1] if not r.empty else df.iloc[-1]
        lvl = risk_level(r, mod_thr, high_thr)
        title, icon, color, sub = LEVELS[lvl]

        if lvl >= 2 and not st.session_state.get("toasted"):
            st.toast(f"{title} — {r['time']:%Y-%m-%d}", icon=icon)
            st.session_state["toasted"] = True

        st.markdown(f"""
<div class="alert {'pulse' if lvl >= 2 else ''}" style="--c:{color}; --glow:{color}aa;">
<div class="alert-top"><div class="alert-ic">{icon}</div><div><div class="alert-t">{title}</div><div class="alert-s">{sub}</div></div></div>
<div class="chips"><span class="chip">📅 {r['time']:%Y-%m-%d}</span><span class="chip">💨 هبات الرياح {r['wind_gusts_10m_max']:.1f} كم/س</span><span class="chip">🌬️ سرعة الرياح {r['wind_speed_10m_max']:.1f} كم/س</span><span class="chip">🌡️ الحرارة العظمى {r['temperature_2m_max']:.1f}°م</span></div>
{scale_html(lvl)}
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="sec">الإرشادات الصحية حسب الفئة</div>', unsafe_allow_html=True)
        for col, (ic, grp, txt) in zip(st.columns(3), ADVICE[lvl]):
            col.markdown(f'<div class="tip" style="--c:{color}"><div class="tip-h">{ic} {grp}</div><div class="tip-b">{txt}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="sec">آخر أيام الغبار المتوقعة</div>', unsafe_allow_html=True)
        last_dust = dust_df.sort_values("time", ascending=False).head(8)[
            ["time", "temperature_2m_max", "wind_speed_10m_max", "wind_gusts_10m_max"]
        ].rename(columns={"time": "التاريخ", "temperature_2m_max": "الحرارة (°م)",
                          "wind_speed_10m_max": "سرعة الرياح", "wind_gusts_10m_max": "هبات الرياح"})
        last_dust["التاريخ"] = last_dust["التاريخ"].dt.strftime("%Y-%m-%d")
        st.dataframe(last_dust, use_container_width=True, hide_index=True)

    # ═════════ المحاكي ═════════
    with tab2:
        st.markdown('<div class="sec">جرّب ظروف جوية وشاهد احتمال الغبار</div>', unsafe_allow_html=True)
        st.caption("يقارن المحاكي الظروف التي تحددها بالأيام المشابهة في السجل التاريخي ويحسب نسبة الأيام التي حدث فيها غبار. هذا تقدير إرشادي وليس مخرج النموذج نفسه.")
        s1, s2, s3 = st.columns(3)
        temp = s1.slider("🌡️ الحرارة العظمى (°م)", float(df["temperature_2m_max"].min()), float(df["temperature_2m_max"].max()), float(df["temperature_2m_max"].median()))
        wind = s2.slider("🌬️ سرعة الرياح (كم/س)", float(df["wind_speed_10m_max"].min()), float(df["wind_speed_10m_max"].max()), float(df["wind_speed_10m_max"].median()))
        gust = s3.slider("💨 هبات الرياح (كم/س)", float(df["wind_gusts_10m_max"].min()), float(df["wind_gusts_10m_max"].max()), float(df["wind_gusts_10m_max"].median()))
        prob, n = estimate_risk(df, temp, wind, gust)

        g1, g2 = st.columns([1.4, 1])
        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=prob * 100, number={"suffix": "%", "font": {"size": 48, "color": DEEP}},
            title={"text": "احتمال حدوث الغبار"},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": DEEP, "thickness": 0.28},
                   "steps": [{"range": [0, 25], "color": "#D5EFE2"}, {"range": [25, 50], "color": "#FCEBC4"},
                             {"range": [50, 75], "color": "#F8D2B0"}, {"range": [75, 100], "color": "#F2B8B8"}]},
        ))
        gauge.update_layout(height=330, margin=dict(l=20, r=20, t=70, b=10), paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(family="Tajawal, Segoe UI, sans-serif"))
        g1.plotly_chart(gauge, use_container_width=True)
        with g2:
            if prob >= 0.75:
                lv, msg = 3, "احتمال مرتفع جداً للغبار"
            elif prob >= 0.5:
                lv, msg = 2, "احتمال مرتفع للغبار"
            elif prob >= 0.25:
                lv, msg = 1, "احتمال متوسط، يلزم المراقبة"
            else:
                lv, msg = 0, "احتمال منخفض للغبار"
            t_, i_, c_, _ = LEVELS[lv]
            st.markdown(f'<div class="tip" style="--c:{c_}"><div class="tip-h">{i_} {msg}</div><div class="tip-b">بناءً على {n:,} يوماً مشابهاً في السجل التاريخي.</div></div>', unsafe_allow_html=True)

    # ═════════ التحليل ═════════
    with tab3:
        f1, f2, f3 = st.columns([1.3, 1.3, 1])
        dr = f1.date_input("الفترة الزمنية", value=(min_d, max_d), min_value=min_d, max_value=max_d, key="range")
        user_thr = f2.slider("حد تنبيه لهبات الرياح (كم/س)", 20, int(df["wind_gusts_10m_max"].max()), int(mod_thr))
        only_dust = f3.toggle("أيام الغبار المتوقعة فقط", value=False)
        start, end = (dr if isinstance(dr, (tuple, list)) and len(dr) == 2 else (min_d, max_d))
        view = df[(df["time"].dt.date >= start) & (df["time"].dt.date <= end)]
        if only_dust:
            view = view[view["predicted_dust"] == 1]

        if view.empty:
            st.warning("لا توجد بيانات ضمن الفلاتر المحددة.")
        else:
            dd = int(view["predicted_dust"].sum())
            k1, k2, k3, k4 = st.columns(4)
            k1.markdown(kpi("📅", "الأيام المحللة", f"{len(view):,}", "ضمن الفترة المحددة", DEEP), unsafe_allow_html=True)
            k2.markdown(kpi("🌪️", "أيام الغبار المتوقعة", f"{dd:,}", "حسب النموذج", ACCENT), unsafe_allow_html=True)
            k3.markdown(kpi("📊", "نسبة أيام الغبار", f"{dd / len(view) * 100:.1f}%", "من إجمالي الأيام", DANGER), unsafe_allow_html=True)
            k4.markdown(kpi("🎯", "دقة النموذج (ROC-AUC)", f"{MODEL_AUC * 100:.1f}%", "على بيانات الاختبار", SAFE), unsafe_allow_html=True)

            st.markdown('<div class="sec">هبات الرياح وموجات الغبار</div>', unsafe_allow_html=True)
            pts = view[view["predicted_dust"] == 1]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=view["time"], y=view["wind_gusts_10m_max"], mode="lines", name="هبات الرياح",
                                     line=dict(color="#2F6690", width=1.5), fill="tozeroy", fillcolor="rgba(47,102,144,.10)"))
            fig.add_trace(go.Scatter(x=pts["time"], y=pts["wind_gusts_10m_max"], mode="markers", name="غبار متوقع",
                                     marker=dict(color=DANGER, size=7, line=dict(color="#fff", width=1))))
            fig.add_hline(y=user_thr, line_dash="dash", line_color=ACCENT, annotation_text="حد التنبيه")
            fig.update_xaxes(rangeslider_visible=True)
            fig.update_yaxes(title_text="كم/س")
            st.plotly_chart(style(fig, 460), use_container_width=True)

            months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="sec">الخريطة الحرارية: الشهر والسنة</div>', unsafe_allow_html=True)
                hm = (view.assign(y=view["time"].dt.year, m=view["time"].dt.month)
                      .pivot_table(index="y", columns="m", values="predicted_dust", aggfunc="sum", fill_value=0)
                      .reindex(columns=range(1, 13), fill_value=0))
                fh = go.Figure(go.Heatmap(z=hm.values, x=months, y=hm.index.astype(str), colorscale="YlOrRd",
                                          hovertemplate="%{y} - %{x}: %{z} يوم<extra></extra>"))
                st.plotly_chart(style(fh, 360), use_container_width=True)
            with c2:
                st.markdown('<div class="sec">الرياح مقابل الحرارة</div>', unsafe_allow_html=True)
                smp = view if len(view) <= 3000 else view.sample(3000, random_state=1)
                fs = px.scatter(smp, x="temperature_2m_max", y="wind_gusts_10m_max",
                                color=smp["predicted_dust"].map({0: "بدون غبار", 1: "غبار متوقع"}),
                                color_discrete_map={"بدون غبار": "#9FB3C8", "غبار متوقع": DANGER},
                                labels={"temperature_2m_max": "الحرارة (°م)", "wind_gusts_10m_max": "هبات الرياح", "color": ""}, opacity=0.7)
                st.plotly_chart(style(fs, 360), use_container_width=True)

            st.markdown('<div class="sec">السجل التفصيلي</div>', unsafe_allow_html=True)
            tbl = view[["time", "temperature_2m_max", "wind_speed_10m_max", "wind_gusts_10m_max", "predicted_dust"]].rename(columns={
                "time": "التاريخ", "temperature_2m_max": "الحرارة العظمى (°م)", "wind_speed_10m_max": "سرعة الرياح",
                "wind_gusts_10m_max": "هبات الرياح", "predicted_dust": "غبار متوقع"})
            tbl["التاريخ"] = tbl["التاريخ"].dt.strftime("%Y-%m-%d")
            tbl["غبار متوقع"] = tbl["غبار متوقع"].map({1: "نعم ⚠️", 0: "لا"})
            with st.expander("عرض الجدول الكامل"):
                st.dataframe(tbl, use_container_width=True, hide_index=True, height=380)
            st.download_button("⬇️ تحميل البيانات (CSV)", tbl.to_csv(index=False).encode("utf-8-sig"), "hail_dust_filtered.csv", "text/csv")

    # ═════════ عن النظام ═════════
    with tab4:
        st.markdown('<div class="sec">عن المشروع</div>', unsafe_allow_html=True)
        a1, a2, a3 = st.columns(3)
        a1.markdown('<div class="tip" style="--c:#2F6690"><div class="tip-h">🎯 الهدف</div><div class="tip-b">إنذار مبكر بعواصف الغبار في منطقة حائل لحماية الصحة العامة، وخاصة مرضى الربو والأطفال.</div></div>', unsafe_allow_html=True)
        a2.markdown('<div class="tip" style="--c:#E8873A"><div class="tip-h">🗂️ البيانات</div><div class="tip-b">سجلات مناخية يومية منذ 2015 تشمل درجة الحرارة العظمى وسرعة الرياح وهبات الرياح.</div></div>', unsafe_allow_html=True)
        a3.markdown(f'<div class="tip" style="--c:#2E9E6B"><div class="tip-h">🧠 النموذج</div><div class="tip-b">نموذج تنبؤي لأيام الغبار بدقة ROC-AUC تبلغ {MODEL_AUC * 100:.1f}%.</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="sec">مستويات الإنذار</div>', unsafe_allow_html=True)
        l1, l2, l3, l4 = st.columns(4)
        for col, (k, txt) in zip([l1, l2, l3, l4], [
            (0, "لا يُتوقع غبار."),
            (1, f"هبات الرياح ≥ {mod_thr:.0f} كم/س بدون توقع غبار."),
            (2, "النموذج يتوقع حدوث غبار."),
            (3, f"غبار متوقع مع هبات رياح ≥ {high_thr:.0f} كم/س."),
        ]):
            t_, i_, c_, _ = LEVELS[k]
            col.markdown(f'<div class="tip" style="--c:{c_}"><div class="tip-h">{i_} {t_}</div><div class="tip-b">{txt}</div></div>', unsafe_allow_html=True)
        st.caption("الإرشادات الصحية عامة ولا تغني عن استشارة الطبيب.")

    st.markdown('<div class="foot">غبار حائل · نظام الإنذار المبكر لعواصف الغبار · مبني على تحليل البيانات المناخية التاريخية</div>', unsafe_allow_html=True)

except FileNotFoundError:
    st.error("لم يتم العثور على الملف `hail_dust_predictions.csv`. تأكد من وجوده في نفس مجلد التطبيق.")
except Exception as e:
    st.error(f"حدث خطأ غير متوقع: {e}")
