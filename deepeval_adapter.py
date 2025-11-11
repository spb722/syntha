from deepeval.models import DeepEvalBaseLLM
from ollama import Client


class OllamaJudge(DeepEvalBaseLLM):
    """
    DeepEval-compatible adapter that proxies prompts to a local Ollama model.
    """

    def __init__(
        self,
        model_name: str = "glm-4.6:cloud",
        host: str = "http://localhost:11434",
        options: dict | None = None,
    ):
        self._model_name = model_name
        self.client = Client(host=host)
        self.options = options or {"temperature": 0.0}

    def load_model(self):
        """
        DeepEval expects a model object; returning the name suffices for Ollama calls.
        """
        return self._model_name

    def generate(self, prompt: str) -> str:
        response = self.client.chat(
            model=self._model_name,
            messages=[{"role": "user", "content": prompt}],
            options=self.options,
        )
        return response["message"]["content"]

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self) -> str:
        return self._model_name
