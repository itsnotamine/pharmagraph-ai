import re
from typing import Any


def contraindication_lookup(evidence: list[dict]) -> dict[str, Any]:
    """Identify evidence about formal contraindications."""
    matches = [
        item for item in evidence
        if "contraindication" in (
            item.get("section", "") + " " + item.get("text", "")
        ).lower()
    ]
    matches.sort(
        key=lambda x: "contraindication" in x.get("section", "").lower(),
        reverse=True,
    )
    return {
        "tool": "contraindication_lookup",
        "findings": matches[:6],
    }


def interaction_analysis(evidence: list[dict]) -> dict[str, Any]:
    """Identify evidence about drug interactions and bleeding."""
    keywords = (
        "interaction", "concomitant", "bleeding",
        "hemorrhage", "anticoagulant", "monitor",
    )

    matches = [
        item for item in evidence
        if any(word in item.get("text", "").lower() for word in keywords)
    ]

    return {
        "tool": "interaction_analysis",
        "findings": matches[:6],
    }


def renal_safety_check(evidence: list[dict]) -> dict[str, Any]:
    """Identify renal thresholds mentioned in retrieved evidence."""
    findings = []

    for item in evidence:
        text = item.get("text", "")

        if not re.search(r"egfr|renal|kidney", text, re.IGNORECASE):
            continue

        thresholds = re.findall(
            r"(?:eGFR|GFR)[^\n.]{0,110}",
            text,
            flags=re.IGNORECASE,
        )

        findings.append({
            "source": item.get("source"),
            "section": item.get("section"),
            "threshold_mentions": thresholds[:5],
            "evidence_id": item.get("id"),
        })

    return {
        "tool": "renal_safety_check",
        "findings": findings[:8],
    }


def evidence_comparison(evidence: list[dict]) -> dict[str, Any]:
    """Group retrieved evidence by document."""
    grouped = {}

    for item in evidence:
        source = item.get("source", "unknown")
        grouped.setdefault(source, []).append({
            "evidence_id": item.get("id"),
            "section": item.get("section"),
        })

    return {
        "tool": "evidence_comparison",
        "findings": grouped,
    }


TOOL_REGISTRY = {
    "contraindication_lookup": contraindication_lookup,
    "interaction_analysis": interaction_analysis,
    "renal_safety_check": renal_safety_check,
    "evidence_comparison": evidence_comparison,
}


def tools_node(state: dict) -> dict:
    """Execute the tools selected by the LLM Planner."""
    evidence = state.get("evidence", [])
    selected_tools = state.get("selected_tools", [])

    results = []

    for tool_name in selected_tools:
        tool = TOOL_REGISTRY.get(tool_name)

        if tool is None:
            continue

        results.append(tool(evidence))

    return {"tool_results": results}