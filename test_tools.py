from app.agent.tools import tools_node


sample_state = {
    "selected_tools": [
        "contraindication_lookup",
        "renal_safety_check",
        "evidence_comparison",
    ],
    "evidence": [
        {
            "id": 1,
            "source": "dailymed-metformin.md",
            "section": "## 4 CONTRAINDICATIONS",
            "text": (
                "Metformin is contraindicated in patients "
                "with severe renal impairment "
                "(eGFR below 30 mL/min/1.73 m2)."
            ),
            "score": 0.03,
        }
    ],
}

result = tools_node(sample_state)

for tool_result in result["tool_results"]:
    print("\nTOOL:", tool_result["tool"])
    print("FINDINGS:", tool_result["findings"])