from dataclasses import dataclass, field
from typing import Any, Callable

from app.analyzers.llm_client import LLMClient
from app.analyzers.prompts import ALL_PROMPTS


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
        prompt = step.prompt_template.format(content=context)
        return self.client.send(
            system_prompt="You are a precise, analytical AI assistant.",
            user_message=prompt,
        )

    def _format_context_for_step(self, step: PipelineStep, context: str) -> str:
        return context

    def run_all(
        self,
        context: str,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> dict[str, str]:
        self.results = {}
        total = len(self.steps)
        for i, step in enumerate(self.steps):
            progress = (i + 1) / total
            if progress_callback:
                progress_callback(step.name, progress)
            result = self.run_step(step, context)
            self.results[step.name] = result
        if progress_callback:
            progress_callback("complete", 1.0)
        return self.results


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
