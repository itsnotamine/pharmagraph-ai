import json
import re
import time
import urllib.request
from pathlib import Path

QUESTIONS = [
    ("simple", "What are the main contraindications of ibuprofen?"),
    ("simple", "What are the major warnings associated with sertraline?"),
    ("simple", "What are the contraindications of amoxicillin?"),
    ("comparison", "Compare the contraindications of aspirin and ibuprofen."),
    ("comparison", "Compare the safety warnings of warfarin and apixaban."),
    ("interaction", "What are the risks of combining aspirin and warfarin?"),
    ("interaction", "What are the risks of combining ibuprofen and sertraline?"),
    ("complex", "Compare the bleeding risks of warfarin, aspirin, and apixaban."),
    ("out_of_corpus", "What are the contraindications of semaglutide?"),
    ("out_of_corpus", "What are the contraindications of rivaroxaban?"),
]

results = []

for index, (category, question) in enumerate(QUESTIONS, 1):
    print(f"\n{'=' * 65}", flush=True)
    print(f"TEST {index}/{len(QUESTIONS)} [{category}]", flush=True)
    print(question, flush=True)

    start = time.time()

    try:
        payload = json.dumps({"question": question}).encode()

        request = urllib.request.Request(
            "http://127.0.0.1:8000/ask",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.load(response)

        duration = round(time.time() - start, 2)
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        trace = data.get("agent_trace", {})

        cited_ids = set(re.findall(r"\[E\d+\]", answer))
        source_ids = {
            f"[{source['id']}]"
            for source in sources
            if source.get("id")
        }

        missing_citations = sorted(cited_ids - source_ids)

        result = {
            "category": category,
            "question": question,
            "success": bool(answer.strip()),
            "duration_seconds": duration,
            "answer": answer,
            "sources": sources,
            "tools": trace.get("tools_executed", []),
            "critic_approved": trace.get("critic_approved"),
            "critic_feedback": trace.get("critic_feedback"),
            "retries": trace.get("retries", 0),
            "missing_citations": missing_citations,
        }

        print("Duration:", duration, "seconds", flush=True)
        print("Sources:", len(sources), flush=True)
        print("Tools:", result["tools"], flush=True)
        print("Critic approved:", result["critic_approved"], flush=True)
        print("Retries:", result["retries"], flush=True)
        print("Missing citations:", missing_citations, flush=True)
        print("Answer preview:", answer[:450], flush=True)

    except Exception as error:
        result = {
            "category": category,
            "question": question,
            "success": False,
            "error": str(error),
        }
        print("ERROR:", error, flush=True)

    results.append(result)

    Path("tests/validation_results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

print(f"\n{'=' * 65}")
print("VALIDATION SUMMARY")
print("Requests completed:", sum(r["success"] for r in results), "/", len(results))
print("Critic approved:", sum(r.get("critic_approved") is True for r in results))
print("Results saved to tests/validation_results.json")
