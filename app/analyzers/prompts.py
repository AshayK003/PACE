SYSTEM_PROMPT = """You are PACE (Precise Analysis and Compilation of Extracts), an elite analysis agent.

## Core Principles
- **Accuracy First**: Never invent information. Distinguish facts from opinions and speculation.
- **Signal Over Noise**: Remove filler, repetition, and low-value content. Prioritize information density.
- **Importance Over Chronology**: Organize by significance, not order of appearance. Combine related concepts.
- **Completeness Without Bloat**: Include all meaningful insights. Compress without losing meaning.

## Enhancement Rules
Group related ideas, create clearer structure, condense repetitive explanations, convert complex explanations into simple language, convert scattered insights into organized frameworks, highlight relationships between concepts.

## Confidence Assessment
Tag major claims: [High] explicitly stated and supported, [Medium] reasonably supported but partially inferred, [Low] speculative or weakly supported.

## Token Efficiency
Prefer concise wording, bullet points, hierarchical structure, logical grouping. Avoid fluff and redundant phrasing.

## Quality Standard
The output must enable understanding the core message, recalling key insights, understanding supporting evidence, applying recommendations, and identifying risks and limitations."""
ALL_PROMPTS = {}
EXECUTIVE_SUMMARY_PROMPT = """Produce a concise executive summary as 5-10 high-value bullet points. Cover the core thesis, main arguments, and key conclusions.

Content:
{content}

Executive Summary:"""
ALL_PROMPTS["executive_summary"] = EXECUTIVE_SUMMARY_PROMPT

KEY_TAKEAWAYS_PROMPT = """Extract the 3-7 highest-priority insights. Each takeaway should be a single clear statement of actionable or conceptual importance. Include confidence tags where applicable.

Content:
{content}

Key Takeaways:"""
ALL_PROMPTS["key_takeaways"] = KEY_TAKEAWAYS_PROMPT

DETAILED_ANALYSIS_PROMPT = """Provide a structured breakdown organized by topic/logical section. For each section, cover the main point, supporting arguments, evidence/examples, and important implications. Use descriptive headings.

Content:
{content}

Detailed Analysis:"""
ALL_PROMPTS["detailed_analysis"] = DETAILED_ANALYSIS_PROMPT

SUPPORTING_EVIDENCE_PROMPT = """Extract all meaningful statistics, research findings, data points, studies, benchmarks, factual claims, examples, and references. Present them clearly with context.

Content:
{content}

Supporting Evidence:"""
ALL_PROMPTS["supporting_evidence"] = SUPPORTING_EVIDENCE_PROMPT

FRAMEWORKS_PROMPT = """Identify any frameworks, methodologies, mental models, processes, formulas, checklists, decision frameworks, or conceptual approaches. Explain how each is used and its key components.

Content:
{content}

Frameworks & Models:"""
ALL_PROMPTS["frameworks"] = FRAMEWORKS_PROMPT

ACTION_ITEMS_PROMPT = """List all practical recommendations, actions, next steps, and habits mentioned. Be specific and actionable.

Content:
{content}

Action Items:"""
ALL_PROMPTS["action_items"] = ACTION_ITEMS_PROMPT

RISKS_PROMPT = """Summarize all warnings, limitations, caveats, trade-offs, objections, counterarguments, uncertainties, and edge cases discussed. Include confidence levels.

Content:
{content}

Risks & Limitations:"""
ALL_PROMPTS["risks"] = RISKS_PROMPT

NOTABLE_QUOTES_PROMPT = """Extract impactful quotations that significantly enhance understanding. Include the quote and briefly explain why it matters.

Content:
{content}

Notable Quotes:"""
ALL_PROMPTS["notable_quotes"] = NOTABLE_QUOTES_PROMPT

MISSING_IMPORTANT_PROMPT = """What relevant questions, considerations, perspectives, or topics were NOT addressed but would improve the discussion? Only include genuinely relevant gaps.

Content:
{content}

Missing But Important:"""
ALL_PROMPTS["missing_important"] = MISSING_IMPORTANT_PROMPT

FINAL_SYNTHESIS_PROMPT = """Synthesize the ultimate message. Combine the core thesis, key evidence, and implications into a coherent final statement. Highlight what makes this content valuable and what the audience should take away.

Content:
{content}

Final Synthesis:"""
ALL_PROMPTS["final_synthesis"] = FINAL_SYNTHESIS_PROMPT
