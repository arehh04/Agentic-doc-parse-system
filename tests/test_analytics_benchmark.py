"""
Analytics Agent Benchmark
=========================
Measures AnalyticsAgent performance for 5 test questions.
Captures: REST API fetch latency, LLM response latency, total time, and the answer.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, ".")

import os
import json
import time
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI


# ── Test Questions ──────────────────────────────────────────────────────────
QUESTIONS = [
    "How many receipts are in the database?",
    "What is the total spending across all receipts?",
    "Which company appears most frequently?",
    "What is the average receipt amount?",
    "Show me receipts above 100",
]


def build_agent_components():
    """Build the same components AnalyticsAgent uses, so we can time each phase."""
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    supabase = create_client(url, key)

    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
        temperature=0.0,
    )

    answer_prompt = PromptTemplate.from_template(
        """You are a data analyst assistant. You have access to a receipts dataset with the following columns:
- filename: The receipt file name
- company_name: The store or merchant name
- receipt_date: Date of the receipt (YYYY-MM-DD)
- receipt_time: Time of the receipt
- address: Store address
- total_amount: Total amount paid (numeric)
- tax_amount: Tax amount (numeric)
- currency: Currency used
- raw_text: Raw OCR text

Here is a sample of the data (JSON format, up to 200 rows):
{data_sample}

Total records in dataset: {total_count}

User Question: {question}

Provide a clear, accurate, and friendly answer based on the data above.
If the question requires calculation (sum, average, count, etc.), compute it from the data.
Answer:"""
    )

    chain = answer_prompt | llm | StrOutputParser()
    return supabase, chain


def run_benchmark():
    print("=" * 80)
    print("  ANALYTICS AGENT BENCHMARK")
    print("=" * 80)

    supabase, chain = build_agent_components()
    results = []

    for i, question in enumerate(QUESTIONS, 1):
        print(f"\n[{i}/5] {question}")
        total_start = time.time()

        # ── Phase 1: REST API fetch ────────────────────────────────────────
        fetch_start = time.time()
        response = supabase.table("receipts").select(
            "filename, company_name, receipt_date, receipt_time, address, total_amount, tax_amount, currency"
        ).limit(1000).execute()
        data = response.data or []
        fetch_end = time.time()
        fetch_latency = fetch_end - fetch_start

        total_count = len(data)
        data_sample = json.dumps(data[:200], indent=2, default=str)

        # ── Phase 2: LLM response ─────────────────────────────────────────
        llm_start = time.time()
        answer = chain.invoke({
            "data_sample": data_sample,
            "total_count": total_count,
            "question": question,
        })
        llm_end = time.time()
        llm_latency = llm_end - llm_start

        total_time = time.time() - total_start

        result = {
            "question": question,
            "fetch_latency_s": round(fetch_latency, 3),
            "llm_latency_s": round(llm_latency, 3),
            "total_time_s": round(total_time, 3),
            "answer": answer.strip(),
        }
        results.append(result)
        print(f"      Fetch: {fetch_latency:.3f}s | LLM: {llm_latency:.3f}s | Total: {total_time:.3f}s")

    # ── Summary Table ──────────────────────────────────────────────────────
    print("\n" + "=" * 110)
    print(f"{'#':<4} {'Question':<45} {'Fetch (s)':<12} {'LLM (s)':<12} {'Total (s)':<12} {'Answer (first 60 chars)'}")
    print("-" * 110)
    for i, r in enumerate(results, 1):
        ans_short = r["answer"][:60].replace("\n", " ")
        print(f"{i:<4} {r['question']:<45} {r['fetch_latency_s']:<12.3f} {r['llm_latency_s']:<12.3f} {r['total_time_s']:<12.3f} {ans_short}")
    print("-" * 110)

    avg_fetch = sum(r["fetch_latency_s"] for r in results) / len(results)
    avg_llm = sum(r["llm_latency_s"] for r in results) / len(results)
    avg_total = sum(r["total_time_s"] for r in results) / len(results)
    print(f"{'AVG':<4} {'':<45} {avg_fetch:<12.3f} {avg_llm:<12.3f} {avg_total:<12.3f}")
    print("=" * 110)

    # ── Save to JSON ───────────────────────────────────────────────────────
    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "analytics_benchmark.json")
    payload = {
        "benchmark": "analytics_agent",
        "num_questions": len(results),
        "avg_fetch_latency_s": round(avg_fetch, 3),
        "avg_llm_latency_s": round(avg_llm, 3),
        "avg_total_time_s": round(avg_total, 3),
        "results": results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    run_benchmark()
