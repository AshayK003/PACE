SYSTEM_PROMPT = """You are PACE (Precise Analysis and Compilation of Extracts), an elite analysis agent.

## Content Adaptability
Adapt your analysis style to the content type:
- **Conversational/transcript**: Extract key arguments, filter filler, identify speaker intent.
- **Academic/research**: Prioritize methodology, findings, limitations, citations.
- **News/opinion**: Identify claims vs evidence, detect bias, assess source credibility.
- **How-to/instructional**: Extract steps, prerequisites, expected outcomes.
- **Narrative/story**: Identify themes, character motivations, plot structure.
- **Technical/documentation**: Extract specs, procedures, compatibility, gotchas.
- **Business/strategy**: Identify decisions, trade-offs, metrics, competitive positioning.
- **Mixed/unknown**: Apply the most relevant lens per section.

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
EXECUTIVE_SUMMARY_PROMPT = """Produce a concise executive summary as 5-10 high-value bullet points.
Adapt to the content type: for academic work, summarize findings and methodology; for transcripts, capture the speaker's core message; for how-to content, state what the reader will learn; for news, state what happened and why it matters.

Content:
__CONTENT__

Executive Summary:"""
ALL_PROMPTS["executive_summary"] = EXECUTIVE_SUMMARY_PROMPT

KEY_TAKEAWAYS_PROMPT = """Extract the 3-7 highest-priority insights from this content.
Each takeaway should be a single clear statement. Prioritize insights that change how the reader thinks or act. Include confidence tags where applicable: [High] explicitly stated, [Medium] inferred, [Low] speculative.

Content:
__CONTENT__

Key Takeaways:"""
ALL_PROMPTS["key_takeaways"] = KEY_TAKEAWAYS_PROMPT

DETAILED_ANALYSIS_PROMPT = """Provide a structured breakdown of the content organized by topic or logical section.
For each section, cover the main point, supporting arguments or evidence, examples where given, and important implications. Use descriptive headings. If the content has no clear structure (e.g., a freeform transcript), impose a logical organization based on the themes discussed.

Content:
__CONTENT__

Detailed Analysis:"""
ALL_PROMPTS["detailed_analysis"] = DETAILED_ANALYSIS_PROMPT

SUPPORTING_EVIDENCE_PROMPT = """Extract all meaningful evidence the content uses to support its claims.
This includes: statistics, research findings, data points, studies, benchmarks, factual claims, concrete examples, case studies, analogies, personal anecdotes, expert citations, and references. For each piece of evidence, note what claim it supports. If the content is opinion-based with little evidence, note the claims that lack supporting evidence.

Content:
__CONTENT__

Supporting Evidence:"""
ALL_PROMPTS["supporting_evidence"] = SUPPORTING_EVIDENCE_PROMPT

FRAMEWORKS_PROMPT = """Identify any frameworks, methodologies, mental models, processes, decision criteria, conceptual approaches, or structured thinking present in the content.
This includes both explicitly named frameworks and implicit reasoning structures the author uses. For each, explain how it works and what it's used for. If the content presents a novel way of thinking about something, describe that too.

Content:
__CONTENT__

Frameworks & Models:"""
ALL_PROMPTS["frameworks"] = FRAMEWORKS_PROMPT

ACTION_ITEMS_PROMPT = """List all practical recommendations, actions, next steps, or implied actions from this content.
For prescriptive content (how-to, advice), extract the explicit steps. For informational content (analysis, news, opinion), infer what a reader should do with this information — whether that's a decision to make, a habit to adopt, a resource to check, or a perspective to reconsider. Be specific and actionable.

Content:
__CONTENT__

Action Items:"""
ALL_PROMPTS["action_items"] = ACTION_ITEMS_PROMPT

RISKS_PROMPT = """Identify all risks, limitations, caveats, trade-offs, uncertainties, and blind spots in this content.
Look for: explicit warnings mentioned, assumptions the author makes without justifying, counterarguments not addressed, edge cases not covered, potential downsides of recommendations, and contexts where the content's advice might fail. If the content is one-sided, note what perspectives are missing.

Content:
__CONTENT__

Risks & Limitations:"""
ALL_PROMPTS["risks"] = RISKS_PROMPT

NOTABLE_QUOTES_PROMPT = """Extract the most impactful statements from this content.
Prioritize: direct quotations that capture a core insight, memorable phrasings that stick, statements that surprise or challenge assumptions, and moments of unusual clarity. If the source contains no direct quotes, identify the strongest paraphrased highlights and attribute them to the source's argument.

Content:
__CONTENT__

Notable Quotes:"""
ALL_PROMPTS["notable_quotes"] = NOTABLE_QUOTES_PROMPT

MISSING_IMPORTANT_PROMPT = """What relevant questions, perspectives, or considerations were NOT addressed but would improve or complete this analysis?
Think about: counterarguments the author didn't engage with, data that would strengthen or weaken the claims, alternative interpretations not considered, practical implementation gaps, and audience-specific concerns left unaddressed. Only include genuinely relevant omissions, not generic "more research is needed" statements.

Content:
__CONTENT__

Missing But Important:"""
ALL_PROMPTS["missing_important"] = MISSING_IMPORTANT_PROMPT

FINAL_SYNTHESIS_PROMPT = """Synthesize the ultimate message of this content into a single coherent statement.
Combine the core thesis, the strongest evidence, the key implications, and what makes this content valuable or worth engaging with. State what the audience should take away and why it matters. If the content is exploratory rather than conclusive, describe what questions it raises rather than what it resolves.

Content:
__CONTENT__

Final Synthesis:"""
ALL_PROMPTS["final_synthesis"] = FINAL_SYNTHESIS_PROMPT


BATCH_A_PROMPT = """Analyze the following content and produce TWO separate sections. Use EXACTLY these delimiters:

===EXECUTIVE_SUMMARY===
Write 5-10 high-value bullet points summarizing the content. Adapt to content type: for academic work, summarize findings and methodology; for transcripts, capture the speaker's core message; for how-to content, state what the reader will learn; for news, state what happened and why it matters.

===KEY_TAKEAWAYS===
Write 3-7 highest-priority insights, each as a single clear statement. Include confidence tags: [High] for explicitly stated facts, [Medium] for inferred insights, [Low] for speculative points.

Here is the content to analyze:

__CONTENT__"""


BATCH_B_PROMPT = """Analyze the following content and produce TWO separate sections. Use EXACTLY these delimiters:

===DETAILED_ANALYSIS===
Write a structured breakdown organized by topic or logical section. For each section, cover the main point, supporting arguments, evidence, and implications. Use descriptive headings. If the content has no clear structure, impose a logical organization based on the themes discussed.

===SUPPORTING_EVIDENCE===
Extract all meaningful evidence: statistics, research findings, data points, examples, case studies, analogies, anecdotes, and citations. For each piece of evidence, note what claim it supports. If the content is opinion-based with little evidence, note the claims that lack support.

Here is the content to analyze:

__CONTENT__"""


BATCH_C_PROMPT = """Analyze the following content and produce FOUR separate sections. Use EXACTLY these delimiters:

===FRAMEWORKS===
Identify any frameworks, methodologies, mental models, processes, decision criteria, or structured thinking present. Both explicitly named and implicit. Explain how each works and what it is used for.

===ACTION_ITEMS===
List all practical recommendations, actions, or implied actions. For prescriptive content, extract explicit steps. For informational content, infer what a reader should do with this information. Be specific and actionable.

===RISKS===
Identify all risks, limitations, caveats, trade-offs, assumptions, counterarguments not addressed, and potential downsides. If the content is one-sided, note missing perspectives.

===NOTABLE_QUOTES===
Extract the most impactful statements. Prioritize direct quotations that capture core insights, memorable phrasings, and statements that challenge assumptions. If no direct quotes exist, identify the strongest paraphrased highlights.

Here is the content to analyze:

__CONTENT__"""
