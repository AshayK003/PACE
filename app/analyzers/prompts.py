EXECUTIVE_SUMMARY_PROMPT = """You are a precise AI analyst. Produce a concise executive summary of the following content. Focus on the core thesis, main argument, and key conclusions in 3-5 sentences.

Content:
{content}

Executive Summary:"""

KEY_TAKEAWAYS_PROMPT = """Extract the 3-7 highest-priority insights from this content. Each takeaway should be a single clear statement of actionable or conceptual importance.

Content:
{content}

Key Takeaways:"""

DETAILED_ANALYSIS_PROMPT = """Provide a structured detailed analysis of this content. Break it down by topic or logical section. For each section, explain the key arguments, evidence, and reasoning presented.

Content:
{content}

Detailed Analysis:"""

SUPPORTING_EVIDENCE_PROMPT = """Identify and list the key supporting evidence presented in this content. Include specific examples, statistics, case studies, data points, and references cited.

Content:
{content}

Supporting Evidence:"""

FRAMEWORKS_PROMPT = """Identify any frameworks, methodologies, mental models, or conceptual approaches mentioned or implied in this content. Explain how each framework is used.

Content:
{content}

Frameworks & Models:"""

ACTION_ITEMS_PROMPT = """Based on this content, what practical actions or recommendations can be derived? List concrete, actionable steps.

Content:
{content}

Action Items:"""

RISKS_PROMPT = """What risks, limitations, caveats, or trade-offs are mentioned or implied in this content? Consider edge cases, assumptions, and potential pitfalls.

Content:
{content}

Risks & Limitations:"""

NOTABLE_QUOTES_PROMPT = """Extract the most impactful quotations from this content. Include the quote and briefly explain why it is significant.

Content:
{content}

Notable Quotes:"""

MISSING_IMPORTANT_PROMPT = """What important topics or perspectives does this content NOT address? Identify gaps, omitted viewpoints, and questions left unanswered.

Content:
{content}

Missing But Important:"""

FINAL_SYNTHESIS_PROMPT = """Synthesize the ultimate message of this content. Combine the main thesis, key evidence, and implications into a coherent final statement.

Content:
{content}

Final Synthesis:"""

ALL_PROMPTS = {
    "executive_summary": EXECUTIVE_SUMMARY_PROMPT,
    "key_takeaways": KEY_TAKEAWAYS_PROMPT,
    "detailed_analysis": DETAILED_ANALYSIS_PROMPT,
    "supporting_evidence": SUPPORTING_EVIDENCE_PROMPT,
    "frameworks": FRAMEWORKS_PROMPT,
    "action_items": ACTION_ITEMS_PROMPT,
    "risks": RISKS_PROMPT,
    "notable_quotes": NOTABLE_QUOTES_PROMPT,
    "missing_important": MISSING_IMPORTANT_PROMPT,
    "final_synthesis": FINAL_SYNTHESIS_PROMPT,
}
