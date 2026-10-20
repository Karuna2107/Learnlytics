import base64
import io
import re
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="Learnlytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- UI/UX CUSTOM CSS ----------------
st.markdown("""
<style>
    /* Padding adjustments */
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}

    /* Sidebar layout */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #172554 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.24);
    }
    [data-testid="stSidebar"] > div:first-child {
        padding: 1.25rem 1rem 2rem;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] h1 {
        margin-bottom: 0.15rem;
        font-size: 1.65rem;
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: #93c5fd !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        padding: 0.75rem;
        border: 1px solid rgba(147, 197, 253, 0.28);
        border-radius: 12px;
        background: rgba(30, 64, 175, 0.28);
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: rgba(15, 23, 42, 0.42);
        border: 1px dashed rgba(147, 197, 253, 0.55);
        border-radius: 9px;
    }
    [data-testid="stSidebar"] [data-testid="stSlider"],
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] {
        padding: 0.8rem 0.75rem 0.35rem;
        margin-bottom: 0.75rem;
        border: 1px solid rgba(147, 197, 253, 0.2);
        border-radius: 10px;
        background: rgba(15, 23, 42, 0.28);
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(147, 197, 253, 0.25);
        margin: 1rem 0;
    }
    
    /* KPI cards */
    [data-testid="stMetric"] {
        min-height: 132px;
        padding: 20px 22px;
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 16px;
        background: linear-gradient(135deg, #172554 0%, #1e3a8a 100%);
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.14);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 14px 28px rgba(15, 23, 42, 0.22);
    }
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricLabel"] {
        color: #bfdbfe !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em;
    }
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] div {
        color: #ffffff !important;
        font-size: 2rem !important;
        font-weight: 750 !important;
        line-height: 1.2 !important;
    }
    [data-testid="stMetricDelta"],
    [data-testid="stMetricDelta"] div {
        color: #dbeafe !important;
    }
    
    /* Headers and text */
    h1, h2, h3 {
        color: #1E293B;
        font-family: 'Inter', sans-serif;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 4px 4px 0 0;
        padding-top: 10px;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- CHART THEME ----------------
CHART_THEME = "plotly_white"
COLOR_DISCRETE_SEQUENCE = px.colors.qualitative.Pastel

# ---------------- HELPERS ----------------
def clean_text(value):
    return re.sub(r"\s+", " ", str(value)).strip()

def short_label(value, limit=42):
    value = clean_text(value)
    return value if len(value) <= limit else value[:limit - 3] + "..."

def find_column(columns, pattern):
    for col in columns:
        if re.search(pattern, col, re.I):
            return col
    return None

def response_counts(series):
    return (
        series.dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .value_counts()
        .rename_axis("Response")
        .reset_index(name="Responses")
    )

def style_fig(fig):
    fig.update_layout(
        template=CHART_THEME,
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("📊 Learnlytics")
    st.caption("Student Learning Analytics")
    
    st.divider()
    st.markdown("### 📁 Data source")
    
    uploaded = st.file_uploader(
        "Upload Google Forms responses",
        type=["csv", "xlsx"],
        help="Upload your latest survey export to refresh the dashboard."
    )

if uploaded is None:
    background_path = Path(__file__).resolve().parent / "assets" / "background.png"
    background_data = base64.b64encode(background_path.read_bytes()).decode("ascii")
    st.markdown(
        f"""
        <style>
            .stAppViewContainer {{
                background:
                    linear-gradient(90deg, rgba(7, 18, 34, 0.78), rgba(7, 18, 34, 0.28)),
                    url("data:image/png;base64,{background_data}") center / cover fixed no-repeat;
            }}
            .stAppViewContainer h1,
            .stAppViewContainer h2,
            .stAppViewContainer h3,
            .stAppViewContainer p,
            .stAppViewContainer li {{
                color: #f8fafc;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Welcome to Learnlytics 🎓")
    st.markdown("### Online Learning vs Classroom Learning Analysis")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.info("👈 **Please upload your survey response file in the sidebar to generate the dashboard.**")
        st.markdown("""
        **What you'll get in this dashboard:**
        * 📊 **Overall survey statistics** & KPI tracking
        * 🧠 **Learning preference comparison**
        * 🎯 **Focus, engagement & understanding metrics**
        * 💻 **Technical issues & flexibility insights**
        * 👥 **Demographic breakdowns**
        """)
    st.stop()


# ---------------- LOAD DATA ----------------
try:
    with st.spinner("Crunching the data..."):
        if uploaded.name.lower().endswith(".csv"):
            raw = pd.read_csv(uploaded)
        else:
            raw = pd.read_excel(uploaded)

        raw.columns = [clean_text(c) for c in raw.columns]
        raw = raw.loc[:, ~pd.Index(raw.columns).duplicated()]
        raw = raw.dropna(how="all")

except Exception as error:
    st.error(f"Unable to read the uploaded file: {error}")
    st.stop()

if raw.empty:
    st.error("The uploaded dataset has no data rows.")
    st.stop()

# Identify columns using the form's question headings
columns = raw.columns.tolist()

age_col = find_column(columns, r"^Enter your age$")
occupation_col = find_column(columns, r"^Occupation$")
timestamp_col = find_column(columns, r"^Timestamp$")
preference_col = find_column(columns, r"^1\.\s*Which mode of learning do you prefer")
focus_col = find_column(columns, r"^6\.\s*Which mode helps you stay more focused")
understanding_col = find_column(columns, r"^3\.\s*Which method provides better understanding")
engagement_col = find_column(columns, r"^9\.\s*Which mode is more engaging")
future_col = find_column(columns, r"^10\.\s*Which method do you think is better for future education")
technical_col = find_column(columns, r"^8\.\s*Do you face technical issues")
flexibility_col = find_column(columns, r"^4\.\s*Online learning is more flexible")

question_cols = [c for c in columns if re.match(r"^\d+\.", c)]
private_cols = [c for c in columns if re.search(r"\b(name|email|e-mail)\b", c, re.I)]
analysis_data = raw.drop(columns=private_cols, errors="ignore").copy()

# ---------------- FILTERS ----------------
st.sidebar.divider()
st.sidebar.markdown("### 🎯 Dashboard filters")

filtered = analysis_data.copy()

if age_col and age_col in filtered.columns:
    age_values = pd.to_numeric(filtered[age_col], errors="coerce")
    valid_ages = age_values.dropna()

    if not valid_ages.empty:
        min_age = int(valid_ages.min())
        max_age = int(valid_ages.max())

        if min_age < max_age:
            age_range = st.sidebar.slider(
                "Age range", min_age, max_age, (min_age, max_age)
            )
            filtered = filtered[age_values.between(age_range[0], age_range[1])]

if occupation_col and occupation_col in filtered.columns:
    occupations = sorted(filtered[occupation_col].dropna().astype(str).unique().tolist())
    chosen_occupations = st.sidebar.multiselect(
        "Occupation", occupations, default=occupations
    )
    filtered = filtered[filtered[occupation_col].astype(str).isin(chosen_occupations)]

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()


# ---------------- DASHBOARD HEADER ----------------
st.title("📊 Learning Analytics Dashboard")
st.caption(f"Source: **{uploaded.name}** | Showing **{len(filtered)}** of {len(analysis_data)} responses")

# ---------------- KPI CARDS ----------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Responses", len(filtered))
k2.metric("Survey Questions", len(question_cols))
k3.metric("Missing Cells", int(filtered.isna().sum().sum()))
k4.metric("Duplicate Rows", int(filtered.duplicated().sum()))
st.write("") # Spacer

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["📊 Overview & Insights", "📈 Question Explorer", "📁 Data & Exports"])

# ---------------- TAB 1: OVERVIEW ----------------
with tab1:
    col_left, col_right = st.columns([1.2, 1])
    
    with col_left:
        st.markdown("### 🏆 Learning Preference")
        if preference_col:
            counts = response_counts(filtered[preference_col])
            if not counts.empty:
                fig = px.pie(
                    counts, names="Response", values="Responses", hole=0.55,
                    color_discrete_sequence=COLOR_DISCRETE_SEQUENCE
                )
                fig.update_traces(textposition="inside", textinfo="label+percent", hoverinfo="label+percent+value")
                fig.update_layout(showlegend=False, annotations=[dict(text='Preference', x=0.5, y=0.5, font_size=20, showarrow=False)])
                st.plotly_chart(style_fig(fig), use_container_width=True)
            else:
                st.info("No valid preference responses.")
        else:
            st.warning("Preference question was not found.")

    with col_right:
        st.markdown("### 🔎 Key Findings")
        with st.container(border=True):
            insights = []
            def add_top_insight(label, col, emoji="📌"):
                if col and col in filtered.columns:
                    counts = response_counts(filtered[col])
                    if not counts.empty:
                        top = counts.iloc[0]
                        pct = top["Responses"] / max(len(filtered), 1) * 100
                        insights.append(f"{emoji} **{label}:** Majority chose **'{top['Response']}'** ({pct:.0f}%)")

            add_top_insight("Mode Preference", preference_col, "❤️")
            add_top_insight("Better Understanding", understanding_col, "🧠")
            add_top_insight("Maintains Focus", focus_col, "🎯")
            add_top_insight("Most Engaging", engagement_col, "⚡")
            add_top_insight("Future of Ed", future_col, "🚀")
            add_top_insight("Tech Issues", technical_col, "💻")

            if insights:
                for insight in insights:
                    st.markdown(insight)
            else:
                st.info("More survey responses needed to generate insights.")
    
    st.divider()
    
    st.markdown("### ⚖️ Learning Experience Comparison")
    comparison_cols = {
        "Understanding": understanding_col,
        "Focus": focus_col,
        "Engagement": engagement_col,
        "Future Education": future_col
    }

    comparison_data = []
    for topic, col in comparison_cols.items():
        if col:
            for _, row in response_counts(filtered[col]).iterrows():
                comparison_data.append({
                    "Dimension": topic,
                    "Response": row["Response"],
                    "Votes": row["Responses"]
                })

    if comparison_data:
        comparison = pd.DataFrame(comparison_data)
        fig = px.bar(
            comparison, x="Dimension", y="Votes", color="Response", barmode="group",
            color_discrete_sequence=COLOR_DISCRETE_SEQUENCE
        )
        st.plotly_chart(style_fig(fig), use_container_width=True)
    else:
        st.info("No comparison questions were detected.")

    st.divider()
    st.markdown("### 👥 Respondent Profile")
    d1, d2 = st.columns(2)
    with d1:
        if age_col and age_col in filtered.columns:
            ages = pd.to_numeric(filtered[age_col], errors="coerce").dropna()
            if not ages.empty:
                fig = px.histogram(pd.DataFrame({"Age": ages}), x="Age", nbins=min(10, max(1, ages.nunique())),
                                   color_discrete_sequence=[COLOR_DISCRETE_SEQUENCE[0]])
                fig.update_layout(yaxis_title="Count")
                st.plotly_chart(style_fig(fig), use_container_width=True)
            else:
                st.info("No valid age data.")
    with d2:
        if occupation_col and occupation_col in filtered.columns:
            occupation_counts = response_counts(filtered[occupation_col])
            if not occupation_counts.empty:
                fig = px.bar(occupation_counts, x="Response", y="Responses", 
                             color="Response", color_discrete_sequence=COLOR_DISCRETE_SEQUENCE)
                fig.update_layout(xaxis_title="", showlegend=False)
                st.plotly_chart(style_fig(fig), use_container_width=True)
            else:
                st.info("No occupation data.")


# ---------------- TAB 2: DEEP DIVE ----------------
with tab2:
    st.markdown("### 📈 Individual Question Analysis")
    if question_cols:
        selected_question = st.selectbox(
            "Select a survey question to visualize:",
            question_cols,
            format_func=lambda x: short_label(x, 85)
        )

        q_counts = response_counts(filtered[selected_question])

        if not q_counts.empty:
            c1, c2 = st.columns([2, 1])
            with c2:
                chart_type = st.radio("Chart Type", ["Bar Chart", "Pie Chart"], horizontal=True)
                q_counts["Percentage"] = (q_counts["Responses"] / q_counts["Responses"].sum() * 100).round(1)
                st.dataframe(
                    q_counts.style.format({'Percentage': '{:.1f}%'}), 
                    hide_index=True, use_container_width=True
                )
            
            with c1:
                if chart_type == "Bar Chart":
                    fig = px.bar(
                        q_counts, x="Response", y="Responses", text="Responses",
                        color="Response", color_discrete_sequence=COLOR_DISCRETE_SEQUENCE
                    )
                    fig.update_traces(textposition="outside", showlegend=False)
                    fig.update_layout(title=short_label(selected_question, 80))
                else:
                    fig = px.pie(
                        q_counts, names="Response", values="Responses", 
                        color_discrete_sequence=COLOR_DISCRETE_SEQUENCE
                    )
                    fig.update_layout(title=short_label(selected_question, 80))
                
                st.plotly_chart(style_fig(fig), use_container_width=True)
        else:
            st.info("This question has no valid responses.")


# ---------------- TAB 3: DATA & EXPORT ----------------
with tab3:
    st.markdown("### 🗃️ Data Quality & Raw Data")
    
    col_dl1, col_dl2 = st.columns(2)
    
    csv_bytes = filtered.to_csv(index=False).encode("utf-8-sig")
    col_dl1.download_button(
        "📥 Download Analyzed Dataset (CSV)",
        data=csv_bytes,
        file_name="learnlytics_filtered_data.csv",
        mime="text/csv",
        use_container_width=True
    )

    if question_cols:
        summaries = []
        for col in question_cols:
            counts = response_counts(filtered[col])
            total = counts["Responses"].sum()
            for _, row in counts.iterrows():
                summaries.append({
                    "Question": col,
                    "Response": row["Response"],
                    "Count": row["Responses"],
                    "Percentage": round(row["Responses"] / total * 100, 2) if total else 0
                })
        summary_df = pd.DataFrame(summaries)
        col_dl2.download_button(
            "📥 Download Question Summaries (CSV)",
            data=summary_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="learnlytics_summaries.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.write("#### Preview of Analyzed Data")
    st.dataframe(filtered, use_container_width=True, height=300)

    st.write("#### Data Quality Report")
    quality = pd.DataFrame({
        "Missing Values": filtered.isna().sum(),
        "Missing (%)": (filtered.isna().mean() * 100).round(1),
        "Unique Values": filtered.nunique()
    })
    st.dataframe(quality, use_container_width=True)