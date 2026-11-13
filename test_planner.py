import json

from app.agent.planner import planner_node


questions = [
    "What are the main contraindications for warfarin?",
    "Compare the contraindications of warfarin and apixaban.",
    "What is the bleeding risk when combining warfarin and sertraline?",
    "Is metformin contraindicated at an eGFR of 25?",
]


for question in questions:
    print("\n" + "=" * 70)
    print("QUESTION:", question)

    result = planner_node({"question": question})

    print(json.dumps(result, indent=2, ensure_ascii=False))