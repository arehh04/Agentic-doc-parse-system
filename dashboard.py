import streamlit as st
import json
import pandas as pd
import os
import glob
import plotly.express as px
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SROIE Analytics Dashboard",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .metric-card { background: linear-gradient(135deg, #2e3a59, #3a4b7c); color: #ffffff; border-radius: 8px; padding: 1rem; text-align: center; }
    </style>
    """,
    unsafe_allow_html=True,
)

load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
STATS_PATH = os.path.join(DATA_DIR, "run_stats.json")
EVAL_PATH = os.path.join(DATA_DIR, "evaluation_report.json")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")

@st.cache_data(show_spinner=False)
def load_json(filepath: str):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@st.cache_data(show_spinner=False)
def load_extracted_data():
    all_data = []
    if os.path.exists(OUTPUT_DIR):
        for file in glob.glob(os.path.join(OUTPUT_DIR, "*.json")):
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['filename'] = os.path.basename(file)
                all_data.append(data)
    return pd.DataFrame(all_data)

run_stats = load_json(STATS_PATH)
eval_report = load_json(EVAL_PATH)
df_receipts = load_extracted_data()

st.sidebar.title("🛠️ Controls")
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.title("🧾 SROIE Analytics Dashboard")

# ---------------------------------------------------------------------------
# Chart rendering helper for the Chat tab
# ---------------------------------------------------------------------------
def _render_chart(chart_data: dict):
    """Render a Plotly chart from structured chart_data returned by the AnalyticsAgent."""
    try:
        chart_type = chart_data.get("chart_type", "bar")
        title = chart_data.get("title", "Chart")
        x_label = chart_data.get("x_label", "")
        y_label = chart_data.get("y_label", "")
        data_points = chart_data.get("data", [])
        
        if not data_points:
            return
            
        labels = [d.get("label", "") for d in data_points]
        values = [d.get("value", 0) for d in data_points]
        df_chart = pd.DataFrame({"label": labels, "value": values})
        
        if chart_type == "bar":
            fig = px.bar(df_chart, x="label", y="value", title=title, labels={"label": x_label, "value": y_label})
        elif chart_type == "line":
            fig = px.line(df_chart, x="label", y="value", title=title, markers=True, labels={"label": x_label, "value": y_label})
        elif chart_type == "pie":
            fig = px.pie(df_chart, names="label", values="value", title=title)
        elif chart_type == "scatter":
            fig = px.scatter(df_chart, x="label", y="value", title=title, labels={"label": x_label, "value": y_label})
        else:
            fig = px.bar(df_chart, x="label", y="value", title=title)
            
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not render chart: {e}")


tab_overview, tab_analysis, tab_accuracy, tab_db, tab_chat = st.tabs([
    "🏠 Overview",
    "📈 Data Analysis",
    "🎯 Accuracy & Errors",
    "☁️ Database",
    "💬 Chat with Database"
])

# ---------------------------------------------------------------------------
# Tab 1 – Overview
# ---------------------------------------------------------------------------
with tab_overview:
    st.header("Pipeline KPIs")
    total_files = run_stats.get("total_files", 0)
    json_rate = run_stats.get("json_success_rate", 0.0) * 100
    
    # Calculate Average Receipt Value
    avg_value = 0
    if not df_receipts.empty and 'total_amount' in df_receipts.columns:
        # Clean currency symbols and convert to float if needed
        # Assuming the pipeline already outputs floats, but let's be safe
        df_receipts['total_amount_num'] = pd.to_numeric(df_receipts['total_amount'], errors='coerce')
        avg_value = df_receipts['total_amount_num'].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Receipts Processed", f"{total_files}")
    col2.metric("Processing Success Rate", f"{json_rate:.0f}%")
    col3.metric("Average Receipt Value", f"${avg_value:.2f}" if pd.notna(avg_value) else "$0.00")
    overall_f1 = eval_report.get("aggregate_metrics", {}).get("overall_f1_score", 0) * 100
    col4.metric("Overall Field Accuracy (F1)", f"{overall_f1:.2f}%")

# ---------------------------------------------------------------------------
# Tab 2 – Data Analysis
# ---------------------------------------------------------------------------
with tab_analysis:
    st.header("Receipts Analysis")
    if not df_receipts.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Receipts by Company
            if 'company_name' in df_receipts.columns:
                company_counts = df_receipts['company_name'].value_counts().reset_index()
                company_counts.columns = ['Company', 'Count']
                fig_company = px.bar(company_counts.head(10), x='Count', y='Company', orientation='h', title="Top 10 Companies by Receipt Volume")
                fig_company.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_company, use_container_width=True)
                
        with col2:
            # Receipts by Month
            if 'receipt_date' in df_receipts.columns:
                df_receipts['date_parsed'] = pd.to_datetime(df_receipts['receipt_date'], errors='coerce')
                df_receipts['month_year'] = df_receipts['date_parsed'].dt.to_period('M').astype(str)
                month_counts = df_receipts['month_year'].value_counts().reset_index()
                month_counts.columns = ['Month', 'Count']
                month_counts = month_counts.sort_values('Month')
                # Filter out NaNs and weird dates
                month_counts = month_counts[month_counts['Month'] != 'NaT']
                
                fig_month = px.line(month_counts, x='Month', y='Count', markers=True, title="Receipts by Month")
                st.plotly_chart(fig_month, use_container_width=True)

# ---------------------------------------------------------------------------
# Tab 3 – Accuracy & Errors
# ---------------------------------------------------------------------------
with tab_accuracy:
    st.header("Field Extraction Accuracy")
    
    metric_fields, f1s = [], []
    for field in ["company", "date", "address", "total"]:
        data = eval_report.get("aggregate_metrics", {}).get(field, {})
        if data:
            metric_fields.append(field.capitalize())
            f1s.append(data.get("f1_score", 0) * 100)

    if metric_fields:
        df_metrics = pd.DataFrame({"Field": metric_fields, "Accuracy (F1)": f1s})
        fig = px.bar(df_metrics, x="Field", y="Accuracy (F1)", text="Accuracy (F1)", title="Accuracy by Field")
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(yaxis_range=[0, 110])
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Tab 4 – Database
# ---------------------------------------------------------------------------
with tab_db:
    st.header("Supabase Data")
    if not df_receipts.empty:
         st.dataframe(df_receipts.drop(columns=['date_parsed', 'month_year', 'total_amount_num'], errors='ignore'), use_container_width=True)

# ---------------------------------------------------------------------------
# Tab 5 – Chat with Database (RAG) — Multi-turn + Charts
# ---------------------------------------------------------------------------
with tab_chat:
    st.header("💬 Ask your Database")
    st.markdown(
        "Use natural language to query your Supabase receipts table. "
        "Try: *'What is the total spending?'*, *'Plot spending by company'*, "
        "*'Which month had the most receipts?'*"
    )
    
    # Persistent agent with conversation memory
    if "analytics_agent" not in st.session_state:
        try:
            from agents.analytics_agent import AnalyticsAgent
            st.session_state.analytics_agent = AnalyticsAgent()
        except Exception as e:
            st.error(f"Failed to initialize Analytics Agent: {e}")
            st.info("Make sure SUPABASE_URL and SUPABASE_KEY are set in your .env file.")
            st.session_state.analytics_agent = None
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Render conversation history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "chart_data" in msg and msg["chart_data"]:
                _render_chart(msg["chart_data"])
            if "timing" in msg and msg["timing"]:
                st.caption(f"⏱ Fetch: {msg['timing'].get('fetch_time', 0)}s | LLM: {msg['timing'].get('llm_time', 0)}s | Total: {msg['timing'].get('total_time', 0)}s")
            if "sql" in msg:
                with st.expander("View Query Details"):
                    st.code(msg["sql"], language="sql")
                    
    prompt = st.chat_input("Ask a question about your receipts...")
    
    if prompt and st.session_state.analytics_agent:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Querying Supabase and generating answer..."):
                response = st.session_state.analytics_agent.answer_query(prompt)
                
                # Clean chart fences from display text
                display_answer = response["answer"]
                if "```chart_json" in display_answer:
                    parts = display_answer.split("```chart_json")
                    clean_parts = []
                    for part in parts:
                        if "```" in part:
                            after_fence = part.split("```", 1)
                            if len(after_fence) > 1:
                                clean_parts.append(after_fence[1])
                        else:
                            clean_parts.append(part)
                    display_answer = "\n".join(clean_parts).strip()
                
                st.markdown(display_answer)
                
                # Render chart if present
                chart_data = response.get("chart_data")
                if chart_data:
                    _render_chart(chart_data)
                    
                # Show timing
                timing = response.get("timing", {})
                if timing:
                    st.caption(f"⏱ Fetch: {timing.get('fetch_time', 0)}s | LLM: {timing.get('llm_time', 0)}s | Total: {timing.get('total_time', 0)}s")
                
                with st.expander("View Query Details"):
                    st.code(response.get("sql_query", ""), language="sql")
                    
                msg_data = {
                    "role": "assistant", 
                    "content": display_answer,
                    "sql": response.get("sql_query", ""),
                    "chart_data": chart_data,
                    "timing": timing
                }
                st.session_state.messages.append(msg_data)

    # Sidebar: Clear Chat
    if st.sidebar.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        if "analytics_agent" in st.session_state:
            del st.session_state.analytics_agent
        st.rerun()
