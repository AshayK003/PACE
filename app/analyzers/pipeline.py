import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable

from app.analyzers.llm_client import LLMClient
from app.analyzers.prompts import (
    ALL_PROMPTS, SYSTEM_PROMPT,
    BATCH_A_PROMPT, BATCH_B_PROMPT, BATCH_C_PROMPT,
)
from app.analyzers.parser import batch_a_response, batch_b_response, batch_c_response

_MAX_CONTENT_CHARS = 50000

_BATCH_A_SECTIONS = ["executive_summary", "key_takeaways"]
_BATCH_B_SECTIONS = ["detailed_analysis", "supporting_evidence"]
_BATCH_C_SECTIONS = ["frameworks", "action_items", "risks", "notable_quotes"]
_DEPENDENT_SECTIONS = ["missing_important", "final_synthesis"]


@dataclass
class PipelineStep:
    name: str
    prompt_template: str
    order: int


class AnalysisPipeline:
    def __init__(self, client: LLMClient | None = None):
        self.client = client or LLMClient()
        self.results: dict[str, str] = {}
        self.steps: list[PipelineStep] = [
            PipelineStep(name=name, prompt_template=template, order=i)
            for i, (name, template) in enumerate(ALL_PROMPTS.items())
        ]

    def run_step(self, step: PipelineStep, context: str) -> str:
        prompt = step.prompt_template.replace("__CONTENT__", context)
        return self.client.send(
            system_prompt=SYSTEM_PROMPT,
            user_message=prompt,
        )

    def _send_batch(self, prompt: str, max_tokens: int = 8000) -> str:
        return self.client.send(
            system_prompt=SYSTEM_PROMPT,
            user_message=prompt,
            max_tokens=max_tokens,
        )

    def _run_batch_a(self, context: str) -> dict[str, str]:
        try:
            prompt = BATCH_A_PROMPT.replace("__CONTENT__", context)
            response = self._send_batch(prompt)
            if response:
                result = batch_a_response(response)
                if all(len(result[s].strip()) >= 20 for s in _BATCH_A_SECTIONS if result[s]):
                    return result
        except Exception:
            pass
        fallback = {}
        for name in _BATCH_A_SECTIONS:
            step = next(s for s in self.steps if s.name == name)
            fallback[name] = self._run_step_safe(step, context)
        return fallback

    def _run_batch_b(self, context: str) -> dict[str, str]:
        try:
            prompt = BATCH_B_PROMPT.replace("__CONTENT__", context)
            response = self._send_batch(prompt)
            if response:
                result = batch_b_response(response)
                if all(len(result[s].strip()) >= 20 for s in _BATCH_B_SECTIONS if result[s]):
                    return result
        except Exception:
            pass
        fallback = {}
        for name in _BATCH_B_SECTIONS:
            step = next(s for s in self.steps if s.name == name)
            fallback[name] = self._run_step_safe(step, context)
        return fallback

    def _run_batch_c(self, context: str) -> dict[str, str]:
        try:
            prompt = BATCH_C_PROMPT.replace("__CONTENT__", context)
            response = self._send_batch(prompt)
            if response:
                result = batch_c_response(response)
                if all(len(result[s].strip()) >= 20 for s in _BATCH_C_SECTIONS if result[s]):
                    return result
        except Exception:
            pass
        fallback = {}
        for name in _BATCH_C_SECTIONS:
            step = next(s for s in self.steps if s.name == name)
            fallback[name] = self._run_step_safe(step, context)
        return fallback

    def run_all(
        self,
        context: str,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> dict[str, str]:
        self.results = {}

        if not context or not context.strip():
            empty_msg = "[No content provided for analysis. Please provide text, a URL, or a file to analyze.]"
            for name in list(ALL_PROMPTS.keys()):
                self.results[name] = empty_msg
            return self.results

        effective_context = self._truncate_if_needed(context)

        if progress_callback:
            progress_callback("batch_a", 0.05)
        try:
            self.results.update(self._run_batch_a(effective_context))
        except Exception:
            for s in _BATCH_A_SECTIONS:
                self.results[s] = f"[Analysis failed for {s}]"

        time.sleep(2)

        if progress_callback:
            progress_callback("batch_b", 0.30)
        try:
            self.results.update(self._run_batch_b(effective_context))
        except Exception:
            for s in _BATCH_B_SECTIONS:
                self.results[s] = f"[Analysis failed for {s}]"

        time.sleep(2)

        if progress_callback:
            progress_callback("batch_c", 0.55)
        try:
            self.results.update(self._run_batch_c(effective_context))
        except Exception:
            for s in _BATCH_C_SECTIONS:
                self.results[s] = f"[Analysis failed for {s}]"

        if progress_callback:
            progress_callback("extraction", 0.75)

        for step in self.steps:
            if step.name in _DEPENDENT_SECTIONS:
                if progress_callback:
                    progress_callback(step.name, 0.80 + 0.10 * (step.order - 8))
                result = self._run_step_safe(step, effective_context)
                self.results[step.name] = result
                time.sleep(1)

        if progress_callback:
            progress_callback("complete", 1.0)
        return self.results

    def _run_step_safe(self, step: PipelineStep, context: str) -> str:
        try:
            if not context or not context.strip():
                return f"[No content to analyze for {step.name}]"
            context_for_step = self._format_context_for_step(step, context)
            result = self.run_step(step, context_for_step)
            if len(result.strip()) < 20:
                result = self.run_step(step, context_for_step)
            return result
        except Exception as e:
            return f"[Analysis failed for {step.name}: {e}]"

    def _truncate_if_needed(self, context: str) -> str:
        if len(context) > _MAX_CONTENT_CHARS:
            return context[:_MAX_CONTENT_CHARS] + "\n\n[Content truncated due to length]"
        return context

    def _format_context_for_step(self, step: PipelineStep, context: str) -> str:
        if step.name in ("final_synthesis", "missing_important"):
            previous = []
            for name, result in self.results.items():
                if result:
                    previous.append(f"--- {name} ---\n{result}")
            if previous:
                return context + "\n\nEarlier findings:\n" + "\n\n".join(previous)
        return context


def validate_output(output: str) -> dict[str, Any]:
    passed = len(output.strip()) >= 50
    return {"passed": passed, "length": len(output.strip())}


def validate_section(content: str | None) -> dict[str, Any]:
    if not content:
        return {"passed": False, "reason": "empty"}
    stripped = content.strip()
    if not stripped:
        return {"passed": False, "reason": "whitespace only"}
    return {"passed": True}


def validate_format(output: str) -> dict[str, Any]:
    if not output or not output.strip():
        return {"passed": False, "reason": "empty"}
    return {"passed": True}
