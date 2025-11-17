from typing import Any, Dict, Optional, Type

from deepeval.metrics import JsonCorrectnessMetric
from deepeval.metrics.base_metric import BaseMetric
from deepeval.test_case import LLMTestCase
from pydantic import BaseModel

from .adapter import OllamaJudge
class StructuredOutputSchema(BaseModel):
    normal_statements: list[str]
    schedule: str


class SchemaMetric(JsonCorrectnessMetric):
    """
    Thin wrapper around DeepEval's JSON correctness metric.
    """

    def __init__(
        self,
        expected_schema: Type[BaseModel] = StructuredOutputSchema,
        model=None,
    ):
        super().__init__(
            expected_schema=expected_schema,
            include_reason=True,
            model=model,
        )


class FaithfulnessMetric(BaseMetric):
    """
    Judge whether statements faithfully represent the original instruction.
    """

    name = "faithfulness"

    def __init__(self, llm: Optional[OllamaJudge] = None, threshold: float = 0.8):
        self.llm = llm or OllamaJudge()
        self.threshold = threshold

    def measure(self, test_case: LLMTestCase) -> Dict[str, Any]:
        utterance = test_case.input  # original instruction
        statements = test_case.actual_output  # newline-joined statements
        prompt = (
            "You are an evaluator. Given a telecom campaign instruction and the extracted "
            "normal statements, decide if the statements faithfully cover all business logic "
            "(targeting criteria, actions, conditions, limits) "
            "without adding hallucinated details.\n\n"
            "NOTE: Schedule/timing information is extracted separately, so do NOT penalize "
            "the statements for missing schedule details.\n\n"
            "IMPORTANT: The use case should be in English.\n\n"
            f"Instruction:\n{utterance}\n\n"
            f"Statements:\n{statements}\n\n"
            "Answer YES if the statements faithfully cover all non-schedule business logic, "
            "otherwise NO. Provide a short reason."
        )
        response = self.llm.generate(prompt).strip()
        passed = response.upper().startswith("YES")
        score = 1.0 if passed else 0.0
        return {
            "score": score,
            "passed": score >= self.threshold,
            "reason": response,
        }


class ScheduleIsolationMetric(BaseMetric):
    """
    Judge whether the extracted schedule matches and contains only timing info.
    """

    name = "schedule_isolation"

    def __init__(self, llm: Optional[OllamaJudge] = None, threshold: float = 0.8):
        self.llm = llm or OllamaJudge()
        self.threshold = threshold

    def measure(self, test_case: LLMTestCase) -> Dict[str, Any]:
        utterance = test_case.input  # original instruction
        schedule = test_case.actual_output  # extracted schedule string
        prompt = (
            "You are an evaluator. Check whether the extracted schedule text matches the "
            "timing instructions in the campaign and does not contain targeting/actions.\n\n"
            "IMPORTANT: The use case should be in English.\n\n"
            f"Instruction:\n{utterance}\n\n"
            f"Extracted schedule:\n{schedule}\n\n"
            "Answer YES if the schedule faithfully captures only the timing info present in "
            "the instruction. Otherwise answer NO and explain why."
        )
        response = self.llm.generate(prompt).strip()
        passed = response.upper().startswith("YES")
        score = 1.0 if passed else 0.0
        return {
            "score": score,
            "passed": score >= self.threshold,
            "reason": response,
        }
