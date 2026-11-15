import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ───────────────────────── إعدادات الصفحة ─────────────────────────
st.set_page_config(
    page_title="نظام الإنذار المبكر للغبار بحائل",
    page_icon="🌪️",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL_AUC = 0.985  # مؤشر دقة النموذج (ROC-AUC)
PRIMARY = "#1E3D59"
ACCENT = "#E8873A"
DANGER = "#D64545"
SAFE = "#2E9E6B"

# ───────────────────────── التصميم (CSS) ─────────────────────────
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: 'Tajawal', 'Segoe UI', sans-serif;
    direction: rtl;
    text-align: right;
}}
.stApp {{ background: #F4F6F9; }}
#MainMenu, footer {{ visibility: hidden; }}
.block-container {{ padding-top: 1.5rem; max-width: 1250px; }}

/* الشريط العلوي */
.hero {{
    background: linear-gradient(135deg, {PRIMARY} 0%, #2F6690 60%, {ACCENT} 140%);
    color: #fff;
    padding: 2rem 2.2rem;
    border-radius: 18px;
    box-shadow: 0 8px 24px rgba(30,61,89,.25);
    margin-bottom: 1.4rem;
}}
.hero h1 {{ color:#fff; margin:0 0 .4rem 0; font-size:2rem; font-weight:800; }}
.hero p  {{ color:#E3ECF5; margin:0; font-size:1.05rem; line-height:1.9; }}
.badge {{
    display:inline-block; background:rgba(255,255,255,.18);
    padding:.25rem .8rem; border-radius:999px; font-size:.85rem; margin-bottom:.8rem;
}}

/* بطاقات المؤشرات */
div[data-testid="stMetric"] {{
    background:#fff; padding:1.1rem 1.2rem; border-radius:14px;
    border-right:5px solid {ACCENT};
    box-shadow:0 2px 10px rgba(0,0,0,.06);
}}
div[data-testid="stMetricLabel"] p {{ color:#6B7A8C; font-weight:500; }}
div[data-testid="stMetricValue"] {{ color:{PRIMARY}; font-weight:800; }}

/* بطاقة الحالة */
.status {{
    padding:1.1rem 1.4rem; border-radius:14px; color:#fff;
    font-size:1.1rem; font-weight:700; margin-bottom:1.2rem;
    box-shadow:0 4px 14px rgba(0,0,0,.12);
}}
.status small {{ display:block; font-weight:400; opacity:.92; margin-top:.2rem; }}

/* العناوين */
h2, h3 {{ color:{PRIMARY}; font-weight:700; }}
.section-title {{
    color:{PRIMARY}; font-weight:800; font-size:1.3rem;
    margin:1.6rem 0 .6rem 0; padding-right:.7rem; border-right:4px solid {ACCENT};
}}
.card {{
    background:#fff; border-radius:14px; padding:.6rem 1rem;
    box-shadow:0 2px 10px rgba(0,0,0,.06);
}}
.footer-note {{ text-align:center; color:#8A97A6; font-size:.85rem; margin-top:2rem; }}

section[data-testid="stSidebar"] {{ background:#fff; border-left:1px solid #E6EAF0; }}
</style>
""",
    unsafe_allow_html=True,
)


# ───────────────────────── تحميل البيانات ─────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    data = pd.read_csv("hail_dust_predictions.csv")
    data["time"] = pd.to_datetime(data["time"])
    return data.sort_values("time").reset_index(drop=True)


def chart_layout(fig, height=420):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Tajawal, Segoe UI, sans-serif", size=13, color="#33414F"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E9EDF2")
    return fig


# ───────────────────────── الواجهة ─────────────────────────
st.markdown(
    """
<div class="hero">
    <span class="badge">🛰️ منصة تحليل تنبؤية</span>
    <h1>🌪️ نظام الإنذار المبكر لعواصف الغبار — منطقة حائل</h1>
    <p>منصة تحليلية تعتمد على البيانات المناخية التاريخية للتنبؤ بموجات الغبار،
    بهدف حماية الصحة العامة وخاصة مرضى الربو والأطفال.</p>
</div>
""",
    unsafe_allow_html=True,
)

try:
    df = load_data()

    # ─── الشريط الجانبي: عوامل التصفية ───
    with st.sidebar:
        st.markdown("## ⚙️ خيارات التصفية")
        min_d, max_d = df["time"].min().date(), df["time"].max().date()
        date_range = st.date_input(
            "الفترة الزمنية", value=(min_d, max_d), min_value=min_d, max_value=max_d
        )
        gust_threshold = st.slider(
            "حد هبات الرياح للتنبيه (كم/س)",
            min_value=20,
            max_value=int(df["wind_gusts_10m_max"].max()),
            value=50,
        )
        only_dust = st.toggle("عرض أيام الغبار المتوقعة فقط", value=False)
        st.divider()
        st.caption("البيانات: سجلات مناخية يومية منذ 2015 لمنطقة حائل.")

    # تطبيق الفلاتر
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start, end = date_range
    else:
        start, end = min_d, max_d
    view = df[(df["time"].dt.date >= start) & (df["time"].dt.date <= end)]
    if only_dust:
        view = view[view["predicted_dust"] == 1]

    if view.empty:
        st.warning("لا توجد بيانات ضمن الفلاتر المحددة. جرّب توسيع الفترة الزمنية.")
        st.stop()

    # ─── بطاقة الحالة (آخر يوم في السجل) ───
    last = df.iloc[-1]
    is_dust = int(last["predicted_dust"]) == 1
    color = DANGER if is_dust else SAFE
    label = "⚠️ تحذير: يُتوقع حدوث غبار" if is_dust else "✅ الوضع مستقر: لا يُتوقع غبار"
    st.markdown(
        f"""
<div class="status" style="background:{color}">
    {label}
    <small>آخر سجل بتاريخ {last['time']:%Y-%m-%d} — هبات الرياح القصوى
    {last['wind_gusts_10m_max']:.1f} كم/س ودرجة الحرارة العظمى {last['temperature_2m_max']:.1f}°م</small>
</div>
""",
        unsafe_allow_html=True,
    )

    # ─── المؤشرات ───
    dust_days = int(view["predicted_dust"].sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📅 الأيام المحللة", f"{len(view):,}")
    c2.metric("🌪️ أيام الغبار المتوقعة", f"{dust_days:,}")
    c3.metric("📊 نسبة أيام الغبار", f"{dust_days / len(view) * 100:.1f}%")
    c4.metric("🎯 دقة النموذج (ROC-AUC)", f"{MODEL_AUC * 100:.1f}%")

    # ─── الرسم الزمني ───
    st.markdown('<div class="section-title">📈 هبات الرياح وعلاقتها بموجات الغبار</div>', unsafe_allow_html=True)
    st.caption("الخط يمثل هبات الرياح القصوى، والنقاط الحمراء أيام الغبار المتوقعة، والخط المتقطع حد التنبيه.")

    dust_pts = view[view["predicted_dust"] == 1]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=view["time"], y=view["wind_gusts_10m_max"], mode="lines",
        name="هبات الرياح القصوى", line=dict(color=PRIMARY, width=1.6),
        fill="tozeroy", fillcolor="rgba(30,61,89,.08)",
    ))
    fig.add_trace(go.Scatter(
        x=dust_pts["time"], y=dust_pts["wind_gusts_10m_max"], mode="markers",
        name="غبار متوقع", marker=dict(color=DANGER, size=7, line=dict(color="#fff", width=1)),
    ))
    fig.add_hline(y=gust_threshold, line_dash="dash", line_color=ACCENT,
                  annotation_text="حد التنبيه", annotation_position="top left")
    fig.update_yaxes(title_text="كم/س")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.plotly_chart(chart_layout(fig), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ─── التحليل الموسمي + العلاقة بين المتغيرات ───
    left, right = st.columns(2)

    with left:
        st.markdown('<div class="section-title">🗓️ التوزيع الشهري لأيام الغبار</div>', unsafe_allow_html=True)
        monthly = view.assign(month=view["time"].dt.month).groupby("month")["predicted_dust"].sum().reindex(range(1, 13), fill_value=0)
        month_names = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                       "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
        fig2 = px.bar(x=month_names, y=monthly.values, labels={"x": "", "y": "عدد الأيام"})
        fig2.update_traces(marker_color=ACCENT)
        st.plotly_chart(chart_layout(fig2, 340), use_container_width=True)

    with right:
        st.markdown('<div class="section-title">🔬 الرياح مقابل الحرارة</div>', unsafe_allow_html=True)
        sample = view if len(view) <= 3000 else view.sample(3000, random_state=1)
        fig3 = px.scatter(
            sample, x="temperature_2m_max", y="wind_gusts_10m_max",
            color=sample["predicted_dust"].map({0: "بدون غبار", 1: "غبار متوقع"}),
            color_discrete_map={"بدون غبار": "#9FB3C8", "غبار متوقع": DANGER},
            labels={"temperature_2m_max": "الحرارة العظمى (°م)", "wind_gusts_10m_max": "هبات الرياح (كم/س)", "color": ""},
            opacity=0.7,
        )
        st.plotly_chart(chart_layout(fig3, 340), use_container_width=True)

    # ─── الجدول ───
    st.markdown('<div class="section-title">📋 سجل التنبؤات والبيانات المناخية</div>', unsafe_allow_html=True)
    table = view[["time", "temperature_2m_max", "wind_speed_10m_max", "wind_gusts_10m_max", "predicted_dust"]].rename(columns={
        "time": "التاريخ",
        "temperature_2m_max": "الحرارة العظمى (°م)",
        "wind_speed_10m_max": "سرعة الرياح (كم/س)",
        "wind_gusts_10m_max": "هبات الرياح (كم/س)",
        "predicted_dust": "غبار متوقع",
    })
    table["التاريخ"] = table["التاريخ"].dt.strftime("%Y-%m-%d")
    table["غبار متوقع"] = table["غبار متوقع"].map({1: "نعم ⚠️", 0: "لا"})

    with st.expander("عرض الجدول الكامل", expanded=False):
        st.dataframe(table, use_container_width=True, hide_index=True, height=380)
    st.download_button(
        "⬇️ تحميل البيانات (CSV)",
        data=table.to_csv(index=False).encode("utf-8-sig"),
        file_name="hail_dust_filtered.csv",
        mime="text/csv",
    )

    st.markdown(
        '<div class="footer-note">نظام الإنذار المبكر للغبار — حائل · مبني على تحليل البيانات المناخية التاريخية</div>',
        unsafe_allow_html=True,
    )

except FileNotFoundError:
    st.error("لم يتم العثور على الملف `hail_dust_predictions.csv`. تأكد من وجوده في نفس مجلد التطبيق.")
except Exception as e:
    st.error(f"حدث خطأ غير متوقع: {e}")
