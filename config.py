from services.azure_ai_service import AzureAIService
from services.google_ai_service import GoogleAIService
from services.open_ai_service import OpenAIService
from services.huggingface_ai_service import HuggingFaceAIService
from services.mock_ai_service import MockAIService

services = {
    "azure": AzureAIService,
    "google": GoogleAIService,
    "openai": OpenAIService,
    "huggingface": HuggingFaceAIService,
    "mock": MockAIService
}
