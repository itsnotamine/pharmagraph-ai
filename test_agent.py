from app.agent.graph import graph


question = "Is metformin contraindicated at an eGFR of 25?"

print("\n=== PHARMAGRAPH AI — FULL AGENT TEST ===")
print("Question:", question)

result = graph.invoke(
    {
        "question": question,
        "retry_count": 0,
        "additional_queries": [],
        "evidence": [],
    }
)

print("\nPLAN:")
for step in result.get("plan", []):
    print("-", step)

print("\nTOOLS EXECUTED:")
for item in result.get("tool_results", []):
    print("-", item["tool"])

print("\nCRITIC:")
print("Approved:", result.get("approved"))
print("Feedback:", result.get("critic_feedback"))
print("Retries:", result.get("retry_count"))

print("\nFINAL ANSWER:")
print(result.get("final_answer"))