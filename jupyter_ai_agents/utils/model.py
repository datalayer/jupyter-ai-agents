# Copyright (c) 2024-2025 Datalayer, Inc.
#
# BSD 3-Clause License

"""Model creation utilities for Jupyter AI Agents."""

import logging
import httpx

logger = logging.getLogger(__name__)


def get_model_string(model_provider: str, model_name: str) -> str:
    """
    Convert model provider and name to pydantic-ai model string format.
    
    Args:
        model_provider: Provider name (azure-openai, openai, anthropic, github-copilot, etc.)
        model_name: Model/deployment name
    
    Returns:
        Model string in format 'provider:model' 
        For Azure OpenAI, returns the model name and sets provider via create_model_with_provider()
    
    Note:
        For Azure OpenAI, the returned string is just the model name.
        The Azure provider configuration is handled separately via OpenAIModel(provider='azure').
        Required env vars for Azure:
        - AZURE_OPENAI_API_KEY
        - AZURE_OPENAI_ENDPOINT (base URL only, e.g., https://your-resource.openai.azure.com)
        - AZURE_OPENAI_API_VERSION (optional, defaults to latest)
    """
    # For Azure OpenAI, we return just the model name
    # The provider will be set to 'azure' when creating the OpenAIModel
    if model_provider.lower() == 'azure-openai':
        return model_name
    
    # Map provider names to pydantic-ai format for other providers
    provider_map = {
        'openai': 'openai',
        'anthropic': 'anthropic',
        'github-copilot': 'openai',      # GitHub Copilot uses OpenAI models
        'bedrock': 'bedrock',
        'google': 'google',
        'gemini': 'google',
        'groq': 'groq',
        'mistral': 'mistral',
        'cohere': 'cohere',
    }
    
    provider = provider_map.get(model_provider.lower(), model_provider)
    return f"{provider}:{model_name}"


def create_model_with_provider(
    model_provider: str, 
    model_name: str,
    timeout: float = 60.0,
):
    """
    Create a pydantic-ai model object with the appropriate provider configuration.
    
    This is necessary for providers like Azure OpenAI that need special initialization
    and timeout configuration.
    
    Args:
        model_provider: Provider name (e.g., 'azure-openai', 'openai', 'anthropic')
        model_name: Model/deployment name
        timeout: HTTP timeout in seconds (default: 60.0)
        
    Returns:
        Model object or string for pydantic-ai Agent
        
    Note:
        For Azure OpenAI, requires these environment variables:
        - AZURE_OPENAI_API_KEY
        - AZURE_OPENAI_ENDPOINT (base URL only, e.g., https://your-resource.openai.azure.com)
        - AZURE_OPENAI_API_VERSION (optional, defaults to latest)
    """
    # Create httpx timeout configuration with generous connect timeout
    # connect timeout is separate from read/write timeout
    http_timeout = httpx.Timeout(timeout, connect=30.0)
    
    logger.info(f"Creating model with timeout: {timeout}s (read/write), connect: 30.0s")
    
    if model_provider.lower() == 'azure-openai':
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers import infer_provider
        
        # For Azure OpenAI, create OpenAIChatModel with custom http_client via provider
        # Environment variables AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT must be set
        # First infer the Azure provider to get base_url, then pass custom http_client
        http_client = httpx.AsyncClient(timeout=http_timeout, follow_redirects=True)
        
        # Infer Azure provider first to get proper configuration
        from pydantic_ai.providers.openai import OpenAIProvider
        azure_provider_base = infer_provider('azure')
        
        # Create new provider with same base_url but custom http_client
        azure_provider = OpenAIProvider(
            base_url=str(azure_provider_base.client.base_url),
            http_client=http_client
        )
        
        return OpenAIChatModel(
            model_name, 
            provider=azure_provider
        )
    elif model_provider.lower() == 'anthropic':
        from pydantic_ai.models.anthropic import AnthropicModel
        from anthropic import AsyncAnthropic
        
        # Create Anthropic client with custom timeout
        client = AsyncAnthropic(
            timeout=http_timeout,
            max_retries=2
        )
        
        return AnthropicModel(
            model_name,
            provider=client
        )
    elif model_provider.lower() in ['openai', 'github-copilot']:
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers import infer_provider
        from pydantic_ai.providers.openai import OpenAIProvider
        
        # For OpenAI, create OpenAIChatModel with custom http_client via provider
        # First infer the OpenAI provider to get base_url, then pass custom http_client
        http_client = httpx.AsyncClient(timeout=http_timeout, follow_redirects=True)
        
        # Infer OpenAI provider first to get proper configuration
        openai_provider_base = infer_provider('openai')
        
        # Create new provider with same base_url but custom http_client
        openai_provider = OpenAIProvider(
            base_url=str(openai_provider_base.client.base_url),
            http_client=http_client
        )
        
        return OpenAIChatModel(
            model_name, 
            provider=openai_provider
        )
    else:
        # For other providers, use the standard string format
        # Note: String format doesn't allow custom timeout configuration
        return get_model_string(model_provider, model_name)
