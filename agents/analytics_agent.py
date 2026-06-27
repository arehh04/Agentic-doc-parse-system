import os
import json
import time
import hashlib
from dotenv import load_dotenv
from supabase import create_client
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

load_dotenv()

class AnalyticsAgent:
    """
    Text-to-SQL RAG Agent with multi-turn memory, query caching, and chart generation.
    
    Features:
    - Fetches receipts via Supabase REST API
    - Caches data to avoid repeated fetches within a session
    - Maintains conversation history for multi-turn context
    - Detects chart requests and returns structured chart data
    """
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY are missing from .env file.")
        
        self.supabase = create_client(url, key)
        self._data_cache = None
        self._cache_time = 0
        self._cache_ttl = 60  # Cache for 60 seconds
        self.conversation_history = []
        
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url="https://api.deepseek.com",
            temperature=0.0
        )

        self.answer_prompt = PromptTemplate.from_template(
            """You are a data analyst assistant. You have access to a receipts dataset with the following columns:
- filename: The receipt file name
- company_name: The store or merchant name
- receipt_date: Date of the receipt (YYYY-MM-DD)
- receipt_time: Time of the receipt
- address: Store address
- total_amount: Total amount paid (numeric)
- tax_amount: Tax amount (numeric)
- currency: Currency used

Here is the data (JSON format, up to 200 rows):
{data_sample}

Total records in dataset: {total_count}

Conversation history:
{history}

User Question: {question}

IMPORTANT INSTRUCTIONS:
1. Provide a clear, accurate, and friendly answer based on the data above.
2. If the question requires calculation (sum, average, count, etc.), compute it from the data.
3. If the user asks to "plot", "chart", "graph", or "visualize" something, you MUST respond with a JSON block wrapped in ```chart_json``` fences. The JSON must have:
   - "chart_type": one of "bar", "line", "pie", "scatter"
   - "title": chart title
   - "x_label": x-axis label
   - "y_label": y-axis label
   - "data": a list of objects with "label" and "value" keys
   
   Example:
   ```chart_json
   {{"chart_type": "bar", "title": "Spending by Company", "x_label": "Company", "y_label": "Total (RM)", "data": [{{"label": "KFC", "value": 150.5}}, {{"label": "99 Speedmart", "value": 230.0}}]}}
   ```
   
   After the chart JSON, also include a brief text explanation.

4. Reference the conversation history if the user asks follow-up questions.

Answer:"""
        )

        self.chain = self.answer_prompt | self.llm | StrOutputParser()

    def _fetch_data(self) -> list:
        """Fetch all receipts from Supabase via REST API with caching."""
        now = time.time()
        if self._data_cache is not None and (now - self._cache_time) < self._cache_ttl:
            return self._data_cache
            
        response = self.supabase.table("receipts").select(
            "filename, company_name, receipt_date, receipt_time, address, total_amount, tax_amount, currency"
        ).limit(1000).execute()
        self._data_cache = response.data or []
        self._cache_time = now
        return self._data_cache

    def _build_history_string(self) -> str:
        """Build a formatted conversation history string."""
        if not self.conversation_history:
            return "(No prior conversation)"
        lines = []
        for turn in self.conversation_history[-6:]:  # Last 6 turns for context window
            role = turn["role"].upper()
            content = turn["content"][:300]  # Truncate long answers
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def answer_query(self, natural_language_query: str) -> dict:
        try:
            fetch_start = time.time()
            data = self._fetch_data()
            fetch_time = time.time() - fetch_start
            total_count = len(data)

            data_sample = json.dumps(data[:200], indent=2, default=str)
            history = self._build_history_string()

            llm_start = time.time()
            answer = self.chain.invoke({
                "data_sample": data_sample,
                "total_count": total_count,
                "question": natural_language_query,
                "history": history
            })
            llm_time = time.time() - llm_start

            # Store in conversation history
            self.conversation_history.append({"role": "user", "content": natural_language_query})
            self.conversation_history.append({"role": "assistant", "content": answer})

            # Parse chart data if present
            chart_data = None
            if "```chart_json" in answer:
                try:
                    chart_block = answer.split("```chart_json")[1].split("```")[0].strip()
                    chart_data = json.loads(chart_block)
                except (IndexError, json.JSONDecodeError):
                    pass

            return {
                "question": natural_language_query,
                "sql_query": f"REST API: fetched {total_count} rows ({fetch_time:.2f}s)",
                "sql_result": f"{total_count} records",
                "answer": answer,
                "chart_data": chart_data,
                "timing": {
                    "fetch_time": round(fetch_time, 3),
                    "llm_time": round(llm_time, 3),
                    "total_time": round(fetch_time + llm_time, 3)
                }
            }

        except Exception as e:
            return {
                "question": natural_language_query,
                "error": str(e),
                "answer": f"Error querying the database: `{e}`",
                "chart_data": None,
                "timing": {}
            }
