"""Custom Ollama LLM wrapper for LlamaIndex that supports cloud API"""
import logging
import re
from typing import Optional, List, Any
from llama_index.core.llms import (
    ChatMessage,
    MessageRole,
    LLMMetadata,
    CompletionResponse,
    CompletionResponseGen,
    LLM,
)

logger = logging.getLogger(__name__)


def _sanitize_error_message(error_msg: str) -> str:
    """
    Sanitize error messages to prevent leaking API keys or secrets.
    
    Args:
        error_msg: The error message to sanitize
        
    Returns:
        Sanitized error message with potential secrets redacted
    """
    if not error_msg:
        return error_msg
    
    # Redact potential API keys (long alphanumeric strings)
    error_msg = re.sub(
        r'(api[_-]?key|apikey|token|secret|password)\s*[:=]\s*["\']?([a-zA-Z0-9._-]{20,})["\']?',
        r'\1=***REDACTED***',
        error_msg,
        flags=re.IGNORECASE
    )
    
    # Redact Bearer tokens (with or without "token:" prefix)
    error_msg = re.sub(
        r'Bearer\s+[a-zA-Z0-9._-]{20,}',
        'Bearer ***REDACTED***',
        error_msg,
        flags=re.IGNORECASE
    )
    
    # Redact API keys in format "API key: sk-..." or "key: ..."
    error_msg = re.sub(
        r'(api\s+key|key)\s*:\s*([a-zA-Z0-9._-]{20,})',
        r'\1: ***REDACTED***',
        error_msg,
        flags=re.IGNORECASE
    )
    
    # Redact any long alphanumeric strings that look like keys (40+ chars)
    # But be careful not to redact URLs or other legitimate long strings
    # Only redact if they look like keys (start with sk-, contain many alphanumeric chars)
    error_msg = re.sub(
        r'\b(sk-[a-zA-Z0-9._-]{30,}|[a-zA-Z0-9._-]{50,})\b',
        '***REDACTED***',
        error_msg
    )
    
    return error_msg


class OllamaCloudLLM(LLM):
    """Custom LLM wrapper for Ollama Cloud API"""
    
    model: str
    api_key: Optional[str] = None
    base_url: str = "https://ollama.com"
    request_timeout: float = 120.0
    
    # Allow extra fields for internal attributes
    model_config = {"extra": "allow"}
    
    def __init__(
        self,
        model: str = "llama3.2",
        api_key: Optional[str] = None,
        base_url: str = "https://ollama.com",
        temperature: float = 0.1,
        request_timeout: float = 120.0,
        **kwargs: Any,
    ):
        try:
            from ollama import Client
        except ImportError:
            raise ImportError(
                "ollama package is required. Install with: pip install ollama"
            )
        
        # Initialize parent LLM class with model and temperature
        super().__init__(
            model=model,
            temperature=temperature,
            callback_manager=kwargs.get("callback_manager"),
            **kwargs
        )
        
        # Set additional attributes (allowed by model_config extra="allow")
        self.api_key = api_key
        self.base_url = base_url
        self.request_timeout = request_timeout
        
        # Initialize Ollama client (stored as extra field)
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self.client = Client(
            host=base_url,
            headers=headers if headers else None
        )
    
    @property
    def metadata(self) -> LLMMetadata:
        """Return LLM metadata"""
        return LLMMetadata(
            model_name=self.model,
            temperature=self.temperature,
        )
    
    def complete(
        self,
        prompt: str,
        formatted: bool = False,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Complete a prompt"""
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": self.temperature,
                    **kwargs.get("options", {}),
                },
            )
            
            # Ollama returns a GenerateResponse object, access response attribute
            if hasattr(response, 'response'):
                text = response.response
            elif isinstance(response, dict):
                text = response.get("response", "")
            else:
                # Try to get response as string
                text = str(response) if response else ""
            
            if not text:
                logger.warning(f"Empty response from Ollama for model {self.model}")
                text = ""
            
            return CompletionResponse(text=text, raw=response)
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower() or "404" in error_msg:
                logger.error(
                    f"Ollama model '{self.model}' not found. "
                    f"Available models may vary. Set OLLAMA_MODEL in .env to a valid model name. "
                    f"Check https://ollama.com/models for available models."
                )
            else:
                logger.error(f"Ollama API error: {_sanitize_error_message(str(e))}")
            raise
    
    def chat(
        self,
        messages: List[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResponse:
        """Chat completion"""
        try:
            # Convert ChatMessage to Ollama format
            ollama_messages = []
            for msg in messages:
                ollama_messages.append({
                    "role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role),
                    "content": msg.content,
                })
            
            response = self.client.chat(
                model=self.model,
                messages=ollama_messages,
                options={
                    "temperature": self.temperature,
                    **kwargs.get("options", {}),
                },
            )
            
            # Ollama returns a ChatResponse object, access message.content
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                text = response.message.content
            elif hasattr(response, 'message') and isinstance(response.message, dict):
                text = response.message.get("content", "")
            elif isinstance(response, dict):
                text = response.get("message", {}).get("content", "")
            else:
                text = str(response) if response else ""
            
            if not text:
                logger.warning(f"Empty response from Ollama chat for model {self.model}")
                text = ""
            
            return CompletionResponse(text=text, raw=response)
        except Exception as e:
            logger.error(f"Ollama API error: {_sanitize_error_message(str(e))}")
            raise
    
    def stream_complete(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> CompletionResponseGen:
        """Stream completion"""
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=True,
                options={
                    "temperature": self.temperature,
                    **kwargs.get("options", {}),
                },
            )
            
            def gen() -> CompletionResponseGen:
                full_text = ""
                for chunk in response:
                    # Handle both object and dict responses
                    if hasattr(chunk, 'response'):
                        text = chunk.response
                    elif isinstance(chunk, dict):
                        text = chunk.get("response", "")
                    else:
                        text = str(chunk) if chunk else ""
                    full_text += text
                    yield CompletionResponse(text=text, delta=text, raw=chunk)
                yield CompletionResponse(text=full_text, raw={})
            
            return gen()
        except Exception as e:
            logger.error(f"Ollama API error: {_sanitize_error_message(str(e))}")
            raise
    
    def stream_chat(
        self,
        messages: List[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResponseGen:
        """Stream chat completion"""
        try:
            ollama_messages = []
            for msg in messages:
                ollama_messages.append({
                    "role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role),
                    "content": msg.content,
                })
            
            response = self.client.chat(
                model=self.model,
                messages=ollama_messages,
                stream=True,
                options={
                    "temperature": self.temperature,
                    **kwargs.get("options", {}),
                },
            )
            
            def gen() -> CompletionResponseGen:
                full_text = ""
                for chunk in response:
                    # Handle both object and dict responses
                    if hasattr(chunk, 'message') and hasattr(chunk.message, 'content'):
                        text = chunk.message.content
                    elif hasattr(chunk, 'message') and isinstance(chunk.message, dict):
                        text = chunk.message.get("content", "")
                    elif isinstance(chunk, dict):
                        text = chunk.get("message", {}).get("content", "")
                    else:
                        text = str(chunk) if chunk else ""
                    full_text += text
                    yield CompletionResponse(text=text, delta=text, raw=chunk)
                yield CompletionResponse(text=full_text, raw={})
            
            return gen()
        except Exception as e:
            logger.error(f"Ollama API error: {_sanitize_error_message(str(e))}")
            raise
    
    async def acomplete(
        self,
        prompt: str,
        formatted: bool = False,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Async complete - not implemented, use sync version"""
        # For now, just call the sync version
        return self.complete(prompt, formatted, **kwargs)
    
    async def achat(
        self,
        messages: List[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResponse:
        """Async chat - not implemented, use sync version"""
        # For now, just call the sync version
        return self.chat(messages, **kwargs)
    
    async def astream_complete(
        self,
        prompt: str,
        **kwargs: Any,
    ):
        """Async stream complete - not implemented, use sync version"""
        # For now, just call the sync version
        for item in self.stream_complete(prompt, **kwargs):
            yield item
    
    async def astream_chat(
        self,
        messages: List[ChatMessage],
        **kwargs: Any,
    ):
        """Async stream chat - not implemented, use sync version"""
        # For now, just call the sync version
        for item in self.stream_chat(messages, **kwargs):
            yield item

