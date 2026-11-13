import json
import time
import urllib.error
import urllib.request

API_URL = "http://127.0.0.1:8000/ask"

QUESTIONS = [
    "What are the main contraindications of warfarin?",
    "Compare the contraindications of warfarin and apixaban.",
    "What is the bleeding risk of combining warfarin and sertraline, and what monitoring is recommended?",
    "Is metformin contraindicated at an eGFR of 25?",
]

results = []

for number, question in enumerate(QUESTIONS, start=1):
    print(f"\n{'=' * 65}", flush=True)
    print(f"TEST {number}/4: {question}", flush=True)

    start = time.perf_counter()

    try:
        payload = json.dumps({"question": question}).encode("utf-8")

        request = urllib.request.Request(
            API_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.load(response)

        duration = round(time.perf_counter() - start, 2)

        answer = data.get("answer", "")
        sources = data.get("sources", [])
        trace = data.get("agent_trace", {})

        result = {
            "question": question,
            "success": bool(answer and sources),
            "duration_seconds": duration,
            "sources_count": len(sources),
            "tools_executed": trace.get("tools_executed", []),
            "critic_approved": trace.get("critic_approved"),
            "retries": trace.get("retries"),
            "answer": answer,
        }

        results.append(result)

        print(f"Duration: {duration}s")
        print(f"Sources: {len(sources)}")
        print(f"Tools: {trace.get('tools_executed', [])}")
        print(f"Critic approved: {trace.get('critic_approved')}")
        print(f"Retries: {trace.get('retries')}")
        print(f"Answer preview: {answer[:350]}")

    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        print(f"ERROR: {error}")
        results.append({
            "question": question,
            "success": False,
            "error": str(error),
        })

with open("tests/benchmark_results.json", "w", encoding="utf-8") as file:
    json.dump(results, file, indent=2, ensure_ascii=False)

print(f"\n{'=' * 65}")
print("BENCHMARK SUMMARY")
print(f"Successful requests: {sum(r['success'] for r in results)}/{len(results)}")
print("Results saved to tests/benchmark_results.json")
