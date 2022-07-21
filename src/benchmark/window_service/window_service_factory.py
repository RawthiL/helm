from proxy.models import get_model, get_model_names_with_tag, Model, WIDER_CONTEXT_WINDOW_TAG
from .ai21_window_service import AI21WindowService
from .anthropic_window_service import AnthropicWindowService
from .openai_window_service import OpenAIWindowService
from .wider_openai_window_service import WiderOpenAIWindowService
from .mt_nlg_window_service import MTNLGWindowService
from .gpt2_window_service import GPT2WindowService
from .gptj_window_service import GPTJWindowService
from .gptneox_window_service import GPTNeoXWindowService
from .window_service import WindowService
from .tokenizer_service import TokenizerService


class WindowServiceFactory:
    @staticmethod
    def get_window_service(model_name: str, service: TokenizerService) -> WindowService:
        """
        Returns a `WindowService` given the name of the model.
        Make sure this function returns instantaneously on repeated calls.
        """
        model: Model = get_model(model_name)
        organization: str = model.organization

        window_service: WindowService
        if model_name in get_model_names_with_tag(WIDER_CONTEXT_WINDOW_TAG):
            window_service = WiderOpenAIWindowService(service)
        elif organization == "openai" or organization == "simple":
            window_service = OpenAIWindowService(service)
        elif organization == "microsoft":
            window_service = MTNLGWindowService(service)
        elif organization == "anthropic":
            window_service = AnthropicWindowService(service)
        elif model_name == "huggingface/gpt2":
            window_service = GPT2WindowService(service)
        elif model_name in ["huggingface/gpt-j-6b", "together/gpt-j-6b", "gooseai/gpt-j-6b"]:
            window_service = GPTJWindowService(service)
        elif model_name in ["together/gpt-neox-20b", "gooseai/gpt-neo-20b"]:
            window_service = GPTNeoXWindowService(service)
        elif organization == "ai21":
            window_service = AI21WindowService(service=service, gpt2_window_service=GPT2WindowService(service))
        else:
            raise ValueError(f"Unhandled model name: {model_name}")

        return window_service
