from enum import Enum


class PipelineStage(str, Enum):
    INGESTION = "Ingesting content"
    CLEANING = "Cleaning text"
    CHUNKING = "Chunking text"
    ANALYZING = "Analyzing content"
    VALIDATING = "Validating output"
    RENDERING = "Rendering report"
    COMPLETE = "Complete"


STAGE_ORDER = [
    PipelineStage.INGESTION,
    PipelineStage.CLEANING,
    PipelineStage.CHUNKING,
    PipelineStage.ANALYZING,
    PipelineStage.VALIDATING,
    PipelineStage.RENDERING,
    PipelineStage.COMPLETE,
]

STAGE_WEIGHTS = {
    PipelineStage.INGESTION: 0.10,
    PipelineStage.CLEANING: 0.05,
    PipelineStage.CHUNKING: 0.05,
    PipelineStage.ANALYZING: 0.60,
    PipelineStage.VALIDATING: 0.05,
    PipelineStage.RENDERING: 0.10,
    PipelineStage.COMPLETE: 0.05,
}


def get_progress_value(stage: PipelineStage, sub_progress: float = 0.0) -> float:
    total_before = 0.0
    for s in STAGE_ORDER:
        if s == stage:
            break
        total_before += STAGE_WEIGHTS.get(s, 0.0)
    return total_before + STAGE_WEIGHTS.get(stage, 0.0) * sub_progress
