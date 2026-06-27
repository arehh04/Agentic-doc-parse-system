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
1. Provide a clear, accurate, and friendly answer based on the data above. DO NOT self-correct, apologize, or output multiple tables for the same question. Compute the final answer and output it once.
2. If the question requires calculation (sum, average, count, etc.), compute it carefully from the data. Be sure to group similar company names together (e.g. 'MR. D.I.Y. (M) SDN BHD' and 'MR. D.I.Y. SDN BHD' are the same merchant).
3. You MUST provide the equivalent PostgreSQL query that would have retrieved this exact insight. Wrap it in a ```sql ... ``` block at the end of your answer. This is for transparency purposes.
4. If the user asks to "plot", "chart", "graph", or "visualize" something, you MUST respond with a JSON block wrapped in ```chart_json``` fences. The JSON must have:
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

5. Reference the conversation history if the user asks follow-up questions.

Answer:"""
        )

        self.chain = self.answer_prompt | self.llm | StrOutputParser()

        self.router_prompt = PromptTemplate.from_template(
            "Classify the following user message as either 'DATA' (if it asks for analytics, stats, or querying the receipts dataset) or 'CHAT' (if it is a general greeting, thanks, or conversational message).\nUser: {question}\nOutput ONLY 'DATA' or 'CHAT'."
        )
        self.router_chain = self.router_prompt | self.llm | StrOutputParser()
        
        self.chat_prompt = PromptTemplate.from_template(
            "You are a friendly data analyst assistant named Elfaria. You help users analyze their receipt data. Respond concisely and pleasantly to the user's conversational message.\nHistory: {history}\nUser: {question}\nAnswer:"
        )
        self.chat_chain = self.chat_prompt | self.llm | StrOutputParser()

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
            history = self._build_history_string()
            
            # Semantic Routing
            route_start = time.time()
            route = self.router_chain.invoke({"question": natural_language_query}).strip().upper()
            
            if "CHAT" in route:
                llm_start = time.time()
                answer = self.chat_chain.invoke({"question": natural_language_query, "history": history})
                llm_time = time.time() - llm_start
                
                self.conversation_history.append({"role": "user", "content": natural_language_query})
                self.conversation_history.append({"role": "assistant", "content": answer})
                
                return {
                    "question": natural_language_query,
                    "sql_query": "Semantic Router: Bypassed DB fetch for general conversation.",
                    "sql_result": "0 records",
                    "answer": answer,
                    "chart_data": None,
                    "timing": {
                        "fetch_time": 0.0,
                        "llm_time": round(llm_time, 3),
                        "total_time": round(time.time() - route_start, 3)
                    }
                }

            # Original Data Flow for Analytics
            fetch_start = time.time()
            data = self._fetch_data()
            fetch_time = time.time() - fetch_start
            total_count = len(data)

            data_sample = json.dumps(data[:200], indent=2, default=str)

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

            # Parse SQL if present
            sql_gen = f"REST API: fetched {total_count} rows ({fetch_time:.2f}s)"
            if "```sql" in answer:
                try:
                    sql_gen = answer.split("```sql")[1].split("```")[0].strip()
                except IndexError:
                    pass
                    
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
                "sql_query": sql_gen,
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
