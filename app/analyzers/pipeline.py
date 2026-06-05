import time
from dataclasses import dataclass
from typing import Any, Callable

from app.analyzers.llm_client import LLMClient
from app.analyzers.prompts import ALL_PROMPTS, SYSTEM_PROMPT

_MAX_CONTENT_CHARS = 50000


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
        if len(context) > _MAX_CONTENT_CHARS:
            context = context[:_MAX_CONTENT_CHARS] + "\n\n[Content truncated due to length]"
        prompt = step.prompt_template.format(content=context)
        return self.client.send(
            system_prompt=SYSTEM_PROMPT,
            user_message=prompt,
        )

    def run_all(
        self,
        context: str,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> dict[str, str]:
        self.results = {}
        total = len(self.steps)

        effective_context = self._truncate_if_needed(context)

        for i, step in enumerate(self.steps):
            progress = (i + 1) / total
            if progress_callback:
                progress_callback(step.name, progress)

            if i > 0 and i < total - 1:
                time.sleep(0.3)

            result = self._run_step_safe(step, effective_context)
            self.results[step.name] = result

        if progress_callback:
            progress_callback("complete", 1.0)
        return self.results

    def _run_step_safe(self, step: PipelineStep, context: str) -> str:
        try:
            context_for_step = self._format_context_for_step(step, context)
            result = self.run_step(step, context_for_step)
            if len(result.strip()) < 20:
                context_for_step = self._format_context_for_step(step, context)
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
