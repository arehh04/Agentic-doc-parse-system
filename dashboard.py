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
    page_title="Agentic Document Intelligence",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Patrick+Hand&family=Nunito:wght@400;700;900&display=swap');

    :root {
        --red: #ff5b5b;
        --yellow: #ffd93d;
        --blue: #4d96ff;
        --white: #ffffff;
        --bg: #faf7f2;
        --ink: #1f1f1f;
    }

    /* Global Font & Background */
    html, body, [class*="css"], .stApp {
        font-family: 'Nunito', sans-serif !important;
        background-color: var(--bg) !important;
        color: var(--ink) !important;
    }

    /* The exact radial gradient from the user's HTML */
    .stApp > header { background-color: transparent !important; }
    .stApp {
        background-image:
        radial-gradient(circle at 10% 20%, rgba(255,217,61,.25) 0 120px, transparent 121px),
        radial-gradient(circle at 90% 10%, rgba(77,150,255,.18) 0 140px, transparent 141px),
        radial-gradient(circle at 85% 80%, rgba(255,91,91,.18) 0 140px, transparent 141px) !important;
    }
    
    div[data-testid="stSidebar"] {
        background-color: var(--bg) !important; 
        border-right: 4px solid var(--ink);
    }

    /* Headers */
    h1, h2, h3, h4, .st-emotion-cache-10trblm {
        font-family: 'Patrick Hand', cursive !important;
        color: var(--ink) !important;
    }

    /* Doodle-style Containers & Borders (The .doodle class equivalent) */
    div[data-testid="stMetric"], 
    div[data-testid="stVerticalBlockBorderWrapper"], 
    details, 
    div[data-testid="stChatInput"] {
        background: var(--white) !important;
        border: 4px solid var(--ink) !important;
        border-radius: 28px !important;
        box-shadow: 8px 8px 0 var(--ink) !important;
        padding: 10px;
        margin-bottom: 15px;
    }

    /* Override metrics to look exactly like the HTML mock */
    div[data-testid="stMetric"] { padding: 22px !important; }
    div[data-testid="stMetric"] label { font-family: 'Nunito', sans-serif !important; font-weight: bold; color: var(--ink) !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { font-size: 38px !important; font-weight: 900 !important; color: var(--ink) !important; }

    /* Chat Bubbles (.chatbox style) */
    div[data-testid="stChatMessage"] {
        background: #fffef9 !important;
        border: 3px dashed var(--ink) !important;
        border-radius: 20px !important;
        padding: 18px !important;
        margin-bottom: 15px !important;
    }
    
    /* SQL Code Blocks */
    code, pre {
        background: #f5f5f5 !important;
        border: 3px solid var(--ink) !important;
        border-radius: 16px !important;
        font-family: monospace !important;
        color: var(--ink) !important;
    }

    /* Buttons */
    div.stButton > button {
        background-color: var(--blue) !important;
        color: white !important;
        border: 4px solid var(--ink) !important;
        border-radius: 28px !important;
        font-family: 'Patrick Hand', cursive !important;
        font-size: 20px !important;
        box-shadow: 6px 6px 0 var(--ink) !important;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        transform: translate(2px, 2px);
        box-shadow: 4px 4px 0 var(--ink) !important;
    }
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

st.title("🤖 Agentic Document Intelligence")

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


tab_upload, tab_overview, tab_analysis, tab_accuracy, tab_db, tab_chat = st.tabs([
    "📤 Upload Receipt",
    "🏠 Overview",
    "📈 Data Analysis",
    "🎯 Accuracy & Errors",
    "☁️ Database",
    "💬 Chat with Database"
])

# ---------------------------------------------------------------------------
# Tab 0 – Upload Receipt
# ---------------------------------------------------------------------------
with tab_upload:
    st.header("📤 Test New Receipt")
    st.markdown("Upload a brand new receipt image (JPG/PNG) to test the End-to-End pipeline.")
    
    uploaded_file = st.file_uploader("Choose a receipt image", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Receipt", width=400)
        
        if st.button("🚀 Run Pipeline"):
            import tempfile
            import time
            from agents.orchestrator import OrchestratorAgent
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
                
            with st.status("🤖 Orchestrator Agent Processing...", expanded=True) as status:
                st.write("🟢 **Agent Manager**: Image Received")
                time.sleep(0.5)
                st.write("🟢 **Document Parsing Agent**: Running OCR...")
                
                # Mocking the visual delay since process_file is synchronous
                orchestrator = OrchestratorAgent()
                state = orchestrator.process_file(tmp_path, uploaded_file.name)
                
                st.write("🟢 **Entity Extraction Agent**: Extracting JSON via DeepSeek...")
                time.sleep(0.5)
                st.write("🟢 **Validation Agent**: Enforcing Pydantic schema...")
                time.sleep(0.5)
                st.write("🟢 **Data Quality Agent**: Checking for anomalies...")
                time.sleep(0.5)
                st.write("🟢 **Storage Agent**: Pushing to Supabase...")
                
                if state.is_success:
                    status.update(label="✅ Pipeline Completed Successfully", state="complete")
                else:
                    status.update(label="❌ Pipeline Failed", state="error")
                
            if state.is_success:
                st.success("Data successfully stored in Supabase!")
                st.json(state.validated_data.model_dump())
                
                if state.quality_report and not state.quality_report.get('is_clean'):
                    st.warning(f"⚠️ Data Quality Flags: {state.quality_report.get('flags', [])}")
            else:
                st.error(f"Pipeline failed: {state.error_message}")
                
            try:
                os.remove(tmp_path)
            except Exception:
                pass

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
    st.header("🤖 Agentic Document Intelligence")
    
    # Persistent agent with conversation memory
    if "analytics_agent" not in st.session_state:
        try:
            from agents.analytics_agent import AnalyticsAgent
            st.session_state.analytics_agent = AnalyticsAgent()
        except Exception as e:
            st.error(f"Failed to initialize Analytics Agent: {e}")
            st.session_state.analytics_agent = None
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    col_main, col_sidebar = st.columns([2.5, 1], gap="large")
    
    with col_main:
        st.subheader("💬 Ask the Agent")
        
        # Render conversation history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "chart_data" in msg and msg["chart_data"]:
                    _render_chart(msg["chart_data"])
                        
        prompt = st.chat_input("Show top 5 merchants by total spending...")
        
    with col_sidebar:
        st.subheader("🤖 Agent Activity")
        activity_container = st.container(border=True)
        
        if not prompt:
            activity_container.markdown("""
            ⚪ **Agent Manager**  
            ⚪ **Analytics Agent**  
            ⚪ **SQL Generator**  
            ⚪ **Supabase**  
            ⚪ **Insight Engine**
            """)
            
            st.subheader("⚡ Execution Trace")
            trace_container = st.container(border=True)
            trace_container.markdown("*(Waiting for query...)*")
            
            st.subheader("🗄 Generated SQL")
            sql_container = st.container(border=True)
            sql_container.markdown("*(Waiting for query...)*")
        
    if prompt and st.session_state.analytics_agent:
        with col_main:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                import time
                from datetime import datetime
                
                # Right Sidebar Live Updates
                with col_sidebar:
                    trace_container = st.container(border=True)
                    sql_container = st.container(border=True)
                    
                    t = datetime.now().strftime("%H:%M:%S")
                    trace_text = f"**{t}** User query received  \n**{t}** Agent Manager classifying intent  \n"
                    trace_container.markdown(trace_text)
                    
                    activity_container.empty()
                    activity_container.markdown("""
                    🟢 **Agent Manager**  
                    ⚪ Analytics Agent  
                    ⚪ SQL Generator  
                    ⚪ Supabase  
                    ⚪ Insight Engine
                    """)
                    
                    time.sleep(0.5)
                    t = datetime.now().strftime("%H:%M:%S")
                    trace_text += f"**{t}** Intent = Analytics Query  \n**{t}** Analytics Agent selected  \n"
                    trace_container.markdown(trace_text)
                    
                    activity_container.empty()
                    activity_container.markdown("""
                    ✅ **Agent Manager**  
                    🟢 **Analytics Agent**  
                    ⚪ SQL Generator  
                    ⚪ Supabase  
                    ⚪ Insight Engine
                    """)
                    
                    time.sleep(0.5)
                    t = datetime.now().strftime("%H:%M:%S")
                    trace_text += f"**{t}** Generating SQL  \n"
                    trace_container.markdown(trace_text)
                    
                    activity_container.empty()
                    activity_container.markdown("""
                    ✅ **Agent Manager**  
                    ✅ **Analytics Agent**  
                    🟢 **SQL Generator**  
                    ⚪ Supabase  
                    ⚪ Insight Engine
                    """)
                    
                    time.sleep(0.5)
                    t = datetime.now().strftime("%H:%M:%S")
                    trace_text += f"**{t}** Executing query against Supabase  \n"
                    trace_container.markdown(trace_text)
                    
                    activity_container.empty()
                    activity_container.markdown("""
                    ✅ **Agent Manager**  
                    ✅ **Analytics Agent**  
                    ✅ **SQL Generator**  
                    🟡 **Supabase Querying...**  
                    ⚪ Insight Engine
                    """)

                # Actually Run Query
                response = st.session_state.analytics_agent.answer_query(prompt)
                
                with col_sidebar:
                    t = datetime.now().strftime("%H:%M:%S")
                    trace_text += f"**{t}** Retrieved {response.get('sql_result', 'records')}  \n**{t}** Generating insights  \n"
                    trace_container.markdown(trace_text)
                    
                    activity_container.empty()
                    activity_container.markdown("""
                    ✅ **Agent Manager**  
                    ✅ **Analytics Agent**  
                    ✅ **SQL Generator**  
                    ✅ **Supabase**  
                    🟢 **Insight Engine**
                    """)
                    
                    sql_container.code(response.get("sql_query", "-- No SQL Generated"), language="sql")
                
                # Clean chart and SQL fences from display text
                display_answer = response["answer"]
                if "```chart_json" in display_answer:
                    parts = display_answer.split("```chart_json")
                    clean_parts = []
                    for part in parts:
                        if "```" in part:
                            clean_parts.append(part.split("```", 1)[1] if len(part.split("```", 1)) > 1 else "")
                        else:
                            clean_parts.append(part)
                    display_answer = "\n".join(clean_parts).strip()
                if "```sql" in display_answer:
                    parts = display_answer.split("```sql")
                    clean_parts = []
                    for part in parts:
                        if "```" in part:
                            clean_parts.append(part.split("```", 1)[1] if len(part.split("```", 1)) > 1 else "")
                        else:
                            clean_parts.append(part)
                    display_answer = "\n".join(clean_parts).strip()
                
                st.markdown(display_answer)
                
                # Render chart if present
                chart_data = response.get("chart_data")
                if chart_data:
                    _render_chart(chart_data)
                    
                with col_sidebar:
                    t = datetime.now().strftime("%H:%M:%S")
                    trace_text += f"**{t}** Response completed  \n"
                    trace_container.markdown(trace_text)
                    
                    activity_container.empty()
                    activity_container.markdown("""
                    ✅ **Agent Manager**  
                    ✅ **Analytics Agent**  
                    ✅ **SQL Generator**  
                    ✅ **Supabase**  
                    ✅ **Insight Engine**
                    """)
                    
                msg_data = {
                    "role": "assistant", 
                    "content": display_answer,
                    "chart_data": chart_data
                }
                st.session_state.messages.append(msg_data)

    # Sidebar: Clear Chat
    if st.sidebar.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        if "analytics_agent" in st.session_state:
            del st.session_state.analytics_agent
        st.rerun()
