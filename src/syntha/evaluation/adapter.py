from deepeval.models import DeepEvalBaseLLM

from syntha.utils import ClientManager


class OllamaJudge(DeepEvalBaseLLM):
    """
    DeepEval-compatible adapter that proxies prompts to Ollama with multi-client rotation.
    """

    def __init__(
        self,
        config_path: str = "configs/generation_config.yaml",
        options: dict | None = None,
    ):
        # Initialize ClientManager with multi-client rotation support
        self.client_manager = ClientManager(config_path=config_path)
        self._model_name = self.client_manager.model
        self.options = options or {"temperature": 0.0}

    def load_model(self):
        """
        DeepEval expects a model object; returning the name suffices for Ollama calls.
        """
        return self._model_name

    def generate(self, prompt: str) -> str:
        response = self.client_manager.chat(
            messages=[{"role": "user", "content": prompt}],
            options=self.options,
        )
        return response["message"]["content"]

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self) -> str:
        return self._model_name
