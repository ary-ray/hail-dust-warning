import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ───────────────────────── إعدادات الصفحة ─────────────────────────
st.set_page_config(
    page_title="غبار حائل | نظام الإنذار المبكر",
    page_icon="🌪️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MODEL_AUC = 0.985
PRIMARY, ACCENT, DANGER, SAFE, WARN = "#1E3D59", "#E8873A", "#D64545", "#2E9E6B", "#F2B134"

# ───────────────────────── الشعار (SVG) ─────────────────────────
LOGO_SVG = """<svg width="74" height="74" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#2F6690"/><stop offset="1" stop-color="#E8873A"/></linearGradient></defs>
<rect width="64" height="64" rx="18" fill="url(#lg)"/>
<circle cx="47" cy="17" r="6" fill="#FFE3C2"/>
<path d="M11 28h27a6 6 0 1 0-6-6" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round"/>
<path d="M11 38h38a6 6 0 1 1-6 6" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round"/>
<path d="M11 48h18" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round"/>
</svg>"""

# ───────────────────────── التصميم (CSS) ─────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
html, body, [class*="css"], .stApp {{ font-family:'Tajawal','Segoe UI',sans-serif; direction:rtl; text-align:right; }}
.stApp {{ background:#F4F6F9; }}
#MainMenu, footer {{ visibility:hidden; }}
.block-container {{ padding-top:1.2rem; max-width:1250px; }}
.hero {{ display:flex; align-items:center; gap:1.2rem; background:linear-gradient(135deg,{PRIMARY} 0%,#2F6690 65%,{ACCENT} 150%);
 color:#fff; padding:1.6rem 2rem; border-radius:20px; box-shadow:0 8px 24px rgba(30,61,89,.25); margin-bottom:1.2rem; }}
.hero h1 {{ color:#fff; margin:0; font-size:1.9rem; font-weight:800; }}
.hero p {{ color:#E3ECF5; margin:.3rem 0 0 0; font-size:1rem; line-height:1.8; }}
@keyframes pulse {{ 0% {{ box-shadow:0 0 0 0 var(--glow); }} 70% {{ box-shadow:0 0 0 18px rgba(0,0,0,0); }} 100% {{ box-shadow:0 0 0 0 rgba(0,0,0,0); }} }}
.alert-box {{ display:flex; align-items:center; gap:1.2rem; padding:1.4rem 1.6rem; border-radius:18px; color:#fff; margin-bottom:1.2rem; }}
.alert-box.pulse {{ animation:pulse 1.8s infinite; }}
.alert-icon {{ font-size:3rem; line-height:1; }}
.alert-title {{ font-size:1.5rem; font-weight:800; }}
.alert-sub {{ opacity:.95; margin-top:.2rem; }}
.tips {{ background:#fff; border-radius:14px; padding:1rem 1.2rem; box-shadow:0 2px 10px rgba(0,0,0,.06); height:100%; }}
.tips b {{ color:{PRIMARY}; }}
div[data-testid="stMetric"] {{ background:#fff; padding:1rem 1.2rem; border-radius:14px; border-right:5px solid {ACCENT}; box-shadow:0 2px 10px rgba(0,0,0,.06); }}
div[data-testid="stMetricValue"] {{ color:{PRIMARY}; font-weight:800; }}
.section-title {{ color:{PRIMARY}; font-weight:800; font-size:1.25rem; margin:1.2rem 0 .6rem 0; padding-right:.7rem; border-right:4px solid {ACCENT}; }}
button[data-baseweb="tab"] {{ font-size:1.05rem; font-weight:700; }}
.footer-note {{ text-align:center; color:#8A97A6; font-size:.85rem; margin-top:2rem; }}
</style>
""", unsafe_allow_html=True)


# ───────────────────────── البيانات ─────────────────────────
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


# مستويات الخطر
LEVELS = {
    0: ("الوضع آمن", "✅", SAFE, "لا يُتوقع غبار، الأجواء مناسبة للأنشطة المعتادة."),
    1: ("مراقبة", "👀", WARN, "رياح نشطة قد تثير الغبار. تابع التحديثات."),
    2: ("تحذير: غبار متوقع", "⚠️", ACCENT, "يُتوقع غبار، خذ احتياطاتك خصوصاً الفئات الحساسة."),
    3: ("خطر: عاصفة غبار محتملة", "🚨", DANGER, "رياح قوية وغبار متوقع. تجنب الخروج غير الضروري."),
}
ADVICE = {
    0: [("🫁", "مرضى الربو", "لا توجد قيود، وأبقِ البخاخ معك كالمعتاد."),
        ("🧒", "الأطفال", "اللعب في الخارج آمن."),
        ("🚗", "السائقون", "الرؤية طبيعية.")],
    1: [("🫁", "مرضى الربو", "احمل البخاخ معك وتجنب الجهد الشديد في الخارج."),
        ("🧒", "الأطفال", "يُفضّل تقليل وقت اللعب في الأماكن المفتوحة."),
        ("🚗", "السائقون", "انتبه لتغيّر الرؤية على الطرق المفتوحة.")],
    2: [("🫁", "مرضى الربو", "ابقَ في الداخل قدر الإمكان والتزم بخطة العلاج."),
        ("🧒", "الأطفال", "أجّل الأنشطة الخارجية والرياضة المدرسية."),
        ("🚗", "السائقون", "خفّض السرعة وشغّل الإضاءة وابتعد عن الطرق السريعة عند ضعف الرؤية.")],
    3: [("🫁", "مرضى الربو", "لا تخرج، أغلق النوافذ، وراجع الطوارئ عند ضيق التنفس."),
        ("🧒", "الأطفال", "ابقوا في الداخل، ويُنصح بإيقاف الأنشطة الخارجية."),
        ("🚗", "السائقون", "تجنب السفر إن أمكن، وإذا اضطررت فاركن بأمان عند انعدام الرؤية.")],
}


def risk_level(row, mod_thr, high_thr):
    g = row["wind_gusts_10m_max"]
    if row["predicted_dust"] == 1 and g >= high_thr:
        return 3
    if row["predicted_dust"] == 1:
        return 2
    if g >= mod_thr:
        return 1
    return 0


def estimate_risk(data, temp, wind, gust):
    """احتمال تجريبي من السجلات التاريخية: نسبة أيام الغبار في الأيام المشابهة."""
    for tol in (4, 6, 9, 14):
        m = data[
            (data["wind_gusts_10m_max"].sub(gust).abs() <= tol)
            & (data["wind_speed_10m_max"].sub(wind).abs() <= tol)
            & (data["temperature_2m_max"].sub(temp).abs() <= tol * 1.5)
        ]
        if len(m) >= 20:
            return float(m["predicted_dust"].mean()), len(m)
    m = data[data["wind_gusts_10m_max"].sub(gust).abs() <= 15]
    return (float(m["predicted_dust"].mean()), len(m)) if len(m) else (0.0, 0)


# ───────────────────────── الواجهة ─────────────────────────
st.markdown(f"""
<div class="hero">
<div>{LOGO_SVG}</div>
<div>
<h1>غبار حائل | نظام الإنذار المبكر لعواصف الغبار</h1>
<p>منصة تحليل تنبؤية تعتمد على البيانات المناخية التاريخية لحماية الصحة العامة، وخاصة مرضى الربو والأطفال.</p>
</div>
</div>
""", unsafe_allow_html=True)

try:
    df = load_data()
    dust_df = df[df["predicted_dust"] == 1]
    base = dust_df if len(dust_df) >= 10 else df
    mod_thr = float(base["wind_gusts_10m_max"].quantile(0.25))
    high_thr = float(base["wind_gusts_10m_max"].quantile(0.75))
    min_d, max_d = df["time"].min().date(), df["time"].max().date()

    with st.sidebar:
        st.markdown("## ⚙️ خيارات التحليل")
        dr = st.date_input("الفترة الزمنية", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        user_thr = st.slider("حد تنبيه مخصص لهبات الرياح (كم/س)", 20, int(df["wind_gusts_10m_max"].max()), int(mod_thr))
        only_dust = st.toggle("أيام الغبار المتوقعة فقط", value=False)
    start, end = (dr if isinstance(dr, (tuple, list)) and len(dr) == 2 else (min_d, max_d))
    view = df[(df["time"].dt.date >= start) & (df["time"].dt.date <= end)]
    if only_dust:
        view = view[view["predicted_dust"] == 1]

    tab1, tab2, tab3, tab4 = st.tabs(["🚨 مركز الإنذار", "🔍 المحاكي التفاعلي", "📊 التحليل", "ℹ️ عن النظام"])

    # ═════════ التبويب 1: مركز الإنذار ═════════
    with tab1:
        pick = st.date_input("اختر اليوم لعرض حالته", value=max_d, min_value=min_d, max_value=max_d, key="pick_day")
        row = df[df["time"].dt.date == pick]
        row = row.iloc[-1] if not row.empty else df.iloc[-1]
        lvl = risk_level(row, mod_thr, high_thr)
        title, icon, color, sub = LEVELS[lvl]

        if lvl >= 2 and not st.session_state.get("toasted"):
            st.toast(f"{title} — {row['time']:%Y-%m-%d}", icon=icon)
            st.session_state["toasted"] = True

        pulse = "pulse" if lvl >= 2 else ""
        st.markdown(f"""
<div class="alert-box {pulse}" style="background:{color}; --glow:{color}99;">
<div class="alert-icon">{icon}</div>
<div>
<div class="alert-title">{title}</div>
<div class="alert-sub">{sub}</div>
<div class="alert-sub">📅 {row['time']:%Y-%m-%d} &nbsp;|&nbsp; 💨 هبات الرياح {row['wind_gusts_10m_max']:.1f} كم/س &nbsp;|&nbsp; 🌡️ الحرارة العظمى {row['temperature_2m_max']:.1f}°م</div>
</div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="section-title">🩺 إرشادات حسب الفئة</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for col, (ic, grp, txt) in zip(cols, ADVICE[lvl]):
            col.markdown(f'<div class="tips"><b>{ic} {grp}</b><br>{txt}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">🕒 آخر أيام الغبار المتوقعة</div>', unsafe_allow_html=True)
        last_dust = dust_df.sort_values("time", ascending=False).head(8)[
            ["time", "temperature_2m_max", "wind_speed_10m_max", "wind_gusts_10m_max"]
        ].rename(columns={"time": "التاريخ", "temperature_2m_max": "الحرارة (°م)",
                          "wind_speed_10m_max": "سرعة الرياح", "wind_gusts_10m_max": "هبات الرياح"})
        last_dust["التاريخ"] = last_dust["التاريخ"].dt.strftime("%Y-%m-%d")
        st.dataframe(last_dust, use_container_width=True, hide_index=True)

    # ═════════ التبويب 2: المحاكي ═════════
    with tab2:
        st.markdown('<div class="section-title">🔍 جرّب ظروف جوية وشوف احتمال الغبار</div>', unsafe_allow_html=True)
        st.caption("المحاكي يقارن ظروفك بالأيام المشابهة في السجل التاريخي ويحسب نسبة الأيام اللي صار فيها غبار. هو تقدير إرشادي مو نتيجة النموذج نفسه.")
        s1, s2, s3 = st.columns(3)
        temp = s1.slider("🌡️ الحرارة العظمى (°م)", float(df["temperature_2m_max"].min()), float(df["temperature_2m_max"].max()), float(df["temperature_2m_max"].median()))
        wind = s2.slider("🌬️ سرعة الرياح (كم/س)", float(df["wind_speed_10m_max"].min()), float(df["wind_speed_10m_max"].max()), float(df["wind_speed_10m_max"].median()))
        gust = s3.slider("💨 هبات الرياح (كم/س)", float(df["wind_gusts_10m_max"].min()), float(df["wind_gusts_10m_max"].max()), float(df["wind_gusts_10m_max"].median()))

        prob, n = estimate_risk(df, temp, wind, gust)
        g1, g2 = st.columns([1.3, 1])
        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=prob * 100, number={"suffix": "%", "font": {"size": 46}},
            title={"text": "احتمال حدوث الغبار"},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": PRIMARY},
                   "steps": [{"range": [0, 25], "color": "#D5EFE2"}, {"range": [25, 50], "color": "#FCEBC4"},
                             {"range": [50, 75], "color": "#F8D2B0"}, {"range": [75, 100], "color": "#F2B8B8"}]},
        ))
        gauge.update_layout(height=320, margin=dict(l=20, r=20, t=60, b=10), paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(family="Tajawal, Segoe UI, sans-serif"))
        g1.plotly_chart(gauge, use_container_width=True)
        with g2:
            if prob >= 0.75:
                st.error("🚨 احتمال مرتفع جداً للغبار")
            elif prob >= 0.5:
                st.warning("⚠️ احتمال مرتفع للغبار")
            elif prob >= 0.25:
                st.info("👀 احتمال متوسط، يلزم المراقبة")
            else:
                st.success("✅ احتمال منخفض")
            st.metric("عدد الأيام المشابهة في السجل", f"{n:,}")

    # ═════════ التبويب 3: التحليل ═════════
    with tab3:
        if view.empty:
            st.warning("لا توجد بيانات ضمن الفلاتر المحددة.")
        else:
            dd = int(view["predicted_dust"].sum())
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📅 الأيام المحللة", f"{len(view):,}")
            m2.metric("🌪️ أيام الغبار المتوقعة", f"{dd:,}")
            m3.metric("📊 نسبة أيام الغبار", f"{dd / len(view) * 100:.1f}%")
            m4.metric("🎯 دقة النموذج (ROC-AUC)", f"{MODEL_AUC * 100:.1f}%")

            st.markdown('<div class="section-title">📈 هبات الرياح وموجات الغبار</div>', unsafe_allow_html=True)
            pts = view[view["predicted_dust"] == 1]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=view["time"], y=view["wind_gusts_10m_max"], mode="lines", name="هبات الرياح",
                                     line=dict(color=PRIMARY, width=1.5), fill="tozeroy", fillcolor="rgba(30,61,89,.08)"))
            fig.add_trace(go.Scatter(x=pts["time"], y=pts["wind_gusts_10m_max"], mode="markers", name="غبار متوقع",
                                     marker=dict(color=DANGER, size=7, line=dict(color="#fff", width=1))))
            fig.add_hline(y=user_thr, line_dash="dash", line_color=ACCENT, annotation_text="حد التنبيه")
            fig.update_xaxes(rangeslider_visible=True)
            fig.update_yaxes(title_text="كم/س")
            st.plotly_chart(style(fig, 460), use_container_width=True)

            c1, c2 = st.columns(2)
            months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
            with c1:
                st.markdown('<div class="section-title">🗓️ خريطة حرارية: الشهر والسنة</div>', unsafe_allow_html=True)
                hm = (view.assign(y=view["time"].dt.year, m=view["time"].dt.month)
                      .pivot_table(index="y", columns="m", values="predicted_dust", aggfunc="sum", fill_value=0)
                      .reindex(columns=range(1, 13), fill_value=0))
                fh = go.Figure(go.Heatmap(z=hm.values, x=months, y=hm.index.astype(str), colorscale="YlOrRd",
                                          hovertemplate="%{y} - %{x}: %{z} يوم<extra></extra>"))
                st.plotly_chart(style(fh, 360), use_container_width=True)
            with c2:
                st.markdown('<div class="section-title">🔬 الرياح مقابل الحرارة</div>', unsafe_allow_html=True)
                smp = view if len(view) <= 3000 else view.sample(3000, random_state=1)
                fs = px.scatter(smp, x="temperature_2m_max", y="wind_gusts_10m_max",
                                color=smp["predicted_dust"].map({0: "بدون غبار", 1: "غبار متوقع"}),
                                color_discrete_map={"بدون غبار": "#9FB3C8", "غبار متوقع": DANGER},
                                labels={"temperature_2m_max": "الحرارة (°م)", "wind_gusts_10m_max": "هبات الرياح", "color": ""},
                                opacity=0.7)
                st.plotly_chart(style(fs, 360), use_container_width=True)

            st.markdown('<div class="section-title">📋 السجل التفصيلي</div>', unsafe_allow_html=True)
            tbl = view[["time", "temperature_2m_max", "wind_speed_10m_max", "wind_gusts_10m_max", "predicted_dust"]].rename(columns={
                "time": "التاريخ", "temperature_2m_max": "الحرارة العظمى (°م)", "wind_speed_10m_max": "سرعة الرياح",
                "wind_gusts_10m_max": "هبات الرياح", "predicted_dust": "غبار متوقع"})
            tbl["التاريخ"] = tbl["التاريخ"].dt.strftime("%Y-%m-%d")
            tbl["غبار متوقع"] = tbl["غبار متوقع"].map({1: "نعم ⚠️", 0: "لا"})
            with st.expander("عرض الجدول الكامل"):
                st.dataframe(tbl, use_container_width=True, hide_index=True, height=380)
            st.download_button("⬇️ تحميل البيانات (CSV)", tbl.to_csv(index=False).encode("utf-8-sig"),
                               "hail_dust_filtered.csv", "text/csv")

    # ═════════ التبويب 4: عن النظام ═════════
    with tab4:
        st.markdown(f"""
### عن المشروع
نظام تحليلي للإنذار المبكر بعواصف الغبار في منطقة حائل، مبني على بيانات مناخية يومية منذ 2015.

**مستويات الإنذار**
- ✅ **آمن:** لا يُتوقع غبار.
- 👀 **مراقبة:** هبات رياح مرتفعة بدون توقع غبار.
- ⚠️ **تحذير:** النموذج يتوقع غبار.
- 🚨 **خطر:** غبار متوقع مع هبات رياح قوية (≥ {high_thr:.0f} كم/س).

**ملاحظات**
- المستويات مبنية على مخرجات النموذج وعلى توزيع هبات الرياح في أيام الغبار التاريخية.
- المعلومات الصحية إرشادية عامة وليست بديلاً عن استشارة الطبيب.
""")

    st.markdown('<div class="footer-note">غبار حائل · نظام الإنذار المبكر · مبني على تحليل البيانات المناخية التاريخية</div>', unsafe_allow_html=True)

except FileNotFoundError:
    st.error("لم يتم العثور على الملف `hail_dust_predictions.csv`. تأكد من وجوده في نفس مجلد التطبيق.")
except Exception as e:
    st.error(f"حدث خطأ غير متوقع: {e}")

