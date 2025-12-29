"""Job extraction using LlamaIndex structured output"""
import logging
import os
import re
from typing import Optional, Callable
from bs4 import BeautifulSoup

try:
    from llama_index.core.program import StructuredLLMProgram
    STRUCTURED_PROGRAM_AVAILABLE = True
except ImportError:
    try:
        from llama_index.core.program import LLMTextCompletionProgram as StructuredLLMProgram
        STRUCTURED_PROGRAM_AVAILABLE = True
    except ImportError:
        try:
            from llama_index.core.program import PydanticProgram
            StructuredLLMProgram = PydanticProgram
            STRUCTURED_PROGRAM_AVAILABLE = True
        except ImportError:
            STRUCTURED_PROGRAM_AVAILABLE = False

from pydantic import ValidationError

# Try to import Ollama LLM wrapper, fallback to OpenAI if needed
try:
    from scout.llm.ollama_llm import OllamaCloudLLM
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    OllamaCloudLLM = None

# Fallback to OpenAI if needed
try:
    from llama_index.llms.openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

from scout.models import JobInfo, JobLevel, RemoteType, AtsType
from scout.config import (
    OLLAMA_API_KEY, OLLAMA_MODEL, OLLAMA_BASE_URL,
    OPENAI_API_KEY, OPENAI_MODEL,
    validate_config
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
    # Pattern: looks for strings that might be API keys (20+ chars, alphanumeric with dots/dashes)
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


HEADINGS = {
    "what_youll_do": ["what you'll do", "what you will do"],
    "responsibilities": ["responsibilities", "your responsibilities"],
    "who_you_are": ["who you are", "about you"],
    "qualifications": ["qualifications", "requirements"],
}

# Cache for the program instance
_program_cache: Optional[Callable] = None


def get_job_info_program() -> Callable:
    """
    Build and return the LlamaIndex structured program that produces JobInfo.
    (Called once per extraction; returns a callable)
    Caches the program instance for performance.
    """
    global _program_cache
    
    if _program_cache is not None:
        return _program_cache
    
    if not STRUCTURED_PROGRAM_AVAILABLE:
        raise ImportError(
            "LlamaIndex structured program not available. "
            "Please ensure llama-index-core is properly installed."
        )
    
    validate_config()
    
    # Try Ollama first (free option), fallback to OpenAI if not available or fails
    llm = None
    
    # Try Ollama if available and API key is set
    if OLLAMA_AVAILABLE and OllamaCloudLLM and OLLAMA_API_KEY:
        try:
            llm = OllamaCloudLLM(
                model=OLLAMA_MODEL,
                api_key=OLLAMA_API_KEY,
                base_url=OLLAMA_BASE_URL,
                temperature=0.1,
                request_timeout=120.0,
            )
            logger.info(f"Initialized Ollama LLM with model: {OLLAMA_MODEL}")
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama LLM: {_sanitize_error_message(str(e))}, will try OpenAI fallback")
            llm = None
    
    # Fallback to OpenAI if Ollama not available or failed
    if llm is None:
        if not OPENAI_AVAILABLE or not OpenAI:
            raise ImportError(
                "Neither Ollama nor OpenAI LLM is available. "
                "Please install: pip install ollama (for Ollama) or llama-index-llms-openai (for OpenAI)"
            )
        
        if not OPENAI_API_KEY:
            raise ValueError(
                "Ollama LLM failed or not configured, and OPENAI_API_KEY is not set. "
                "Please set either OLLAMA_API_KEY or OPENAI_API_KEY in your .env file."
            )
        
        logger.info("Using OpenAI as LLM (Ollama not available or failed)")
        try:
            llm = OpenAI(
                api_key=OPENAI_API_KEY,
                model=OPENAI_MODEL,
                temperature=0.1,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize OpenAI LLM: {e}. "
                "Please check your OPENAI_API_KEY is valid."
            )
    
    prompt_template_str = """\
Extract structured job information from the following job posting text.

Job Posting Text:
{input_text}

Extract the following information:
- company: The company name (required)
- contact_person: Contact person or HR name if mentioned, otherwise null
- title: Job title/position name (required)
- location: Job location (city, state, country, or remote) (required)
- salary: Salary range or compensation if mentioned, otherwise null
- url: The job posting URL (if not in text, use "unknown") (required)
- date_applied: Date applied if mentioned, otherwise null
- date_confirmation: Date of confirmation if mentioned, otherwise null
- date_latest_reply: Date of latest reply if mentioned, otherwise null
- status: Application status if mentioned, otherwise null
- reason_outcome: Reason for outcome if mentioned, otherwise null
- level: Job level - must be EXACTLY one of these lowercase strings: "intern", "entry", "mid", "senior", "staff", "principal", "executive", or null if unclear
- remote_type: Remote work type - must be EXACTLY one of these lowercase strings: "on_site", "remote", "hybrid", "flexible", or null if unclear
- ats: ATS system type - must be EXACTLY one of these lowercase strings: "greenhouse", "lever", "workday", "taleo", "icims", "custom", "unknown", or null

IMPORTANT: For enum fields (level, remote_type, ats), return ONLY the lowercase string value (e.g., "entry", "hybrid", "custom") or null. Do NOT return class names like "JobLevel.ENTRY" or "RemoteType.HYBRID".

Return only valid data. If information is not available, use null for optional fields.
"""
    
    try:
        _program_cache = StructuredLLMProgram.from_defaults(
            output_cls=JobInfo,
            prompt_template_str=prompt_template_str,
            llm=llm,
            verbose=False,
        )
    except Exception as e:
        # Fallback: try alternative initialization
        logger.warning(f"Failed to create program with from_defaults: {_sanitize_error_message(str(e))}")
        try:
            _program_cache = StructuredLLMProgram(
                output_cls=JobInfo,
                prompt_template_str=prompt_template_str,
                llm=llm,
            )
        except Exception as e2:
            raise RuntimeError(
                f"Failed to create structured program: {e2}. "
                "Please check LlamaIndex version compatibility."
            ) from e2
    
    return _program_cache


def normalize_html_text(html: str) -> str:
    """
    Normalize HTML text by extracting and cleaning it.
    
    Args:
        html: Raw HTML string
        
    Returns:
        Normalized text string
    """
    soup = BeautifulSoup(html, "html.parser")
    text_raw = "\n".join(
        line.strip() 
        for line in soup.get_text(separator="\n").splitlines() 
        if line.strip()
    )
    text_norm = (
        text_raw
        .replace("\u2019", "'")
        .replace("'", "'")
        .lower()
    )
    return text_norm


def find_heading_positions(text_norm: str) -> dict[str, int]:
    """
    Find positions of common job posting headings in normalized text.
    
    Args:
        text_norm: Normalized lowercase text
        
    Returns:
        Dictionary mapping heading keys to their positions in text
    """
    positions = {}
    for key, variations in HEADINGS.items():
        for variation in variations:
            pos = text_norm.find(variation.lower())
            if pos != -1:
                positions[key] = pos
                break
    return positions


def slice_by_positions(text_raw: str, text_norm: str, positions: dict[str, int]) -> dict[str, str]:
    """
    Slice text into sections based on heading positions.
    
    Args:
        text_raw: Original text (not normalized)
        text_norm: Normalized text
        positions: Dictionary of heading positions
        
    Returns:
        Dictionary mapping section names to text content
    """
    sections = {}
    sorted_positions = sorted(positions.items(), key=lambda x: x[1])
    
    for i, (key, pos) in enumerate(sorted_positions):
        start = pos
        end = sorted_positions[i + 1][1] if i + 1 < len(sorted_positions) else len(text_raw)
        sections[key] = text_raw[start:end].strip()
    
    return sections


def _clean_and_truncate_html(html: str, max_chars: int = 300000) -> str:
    """
    Clean HTML and extract text, truncating if necessary.
    
    Args:
        html: Raw HTML string
        max_chars: Maximum characters to keep (default: 300k ~ 100k tokens)
        
    Returns:
        Cleaned text string
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove script, style, and other non-content elements
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        element.decompose()
    
    # Extract text
    text = soup.get_text(separator="\n", strip=True)
    
    # Truncate if too long (keep first max_chars)
    if len(text) > max_chars:
        logger.warning(f"Text too long ({len(text)} chars), truncating to {max_chars} chars")
        text = text[:max_chars] + "\n[... truncated ...]"
    
    return text


def extract_job_info(text: str, url: str = "unknown") -> JobInfo:
    """
    Convert cleaned job description text into a JobInfo model.
    
    Args:
        text: Raw HTML or cleaned job description text
        url: Job posting URL (default: "unknown")
        
    Returns:
        JobInfo model instance
        
    Raises:
        ValueError: If text is empty or invalid
        RuntimeError: If extraction fails
        ValidationError: If extracted data doesn't match JobInfo schema
    """
    if not text or not text.strip():
        raise ValueError("Text input cannot be empty")
    
    try:
        program = get_job_info_program()
        
        # Clean HTML and truncate if needed (handles large pages)
        if "<html" in text.lower() or "<body" in text.lower():
            text_for_extraction = _clean_and_truncate_html(text)
        else:
            # Already text, just truncate if too long
            max_chars = 300000
            if len(text) > max_chars:
                logger.warning(f"Text too long ({len(text)} chars), truncating to {max_chars} chars")
                text_for_extraction = text[:max_chars] + "\n[... truncated ...]"
            else:
                text_for_extraction = text.strip()
        
        # Run the structured extraction
        # If Ollama hits rate limits, catch and retry with OpenAI
        try:
            result = program(input_text=text_for_extraction)
        except ValidationError as ve:
            # Catch ValidationError separately and re-raise as RuntimeError
            logger.error(f"Validation error during extraction: {ve}")
            raise RuntimeError(f"Extracted data validation failed: {ve}") from ve
        except Exception as e:
            error_msg = str(e).lower()
            # Check if it's a rate limit or API error that we can retry with OpenAI
            if ("rate limit" in error_msg or "429" in error_msg or 
                "usage limit" in error_msg) and OPENAI_API_KEY and OPENAI_AVAILABLE:
                logger.warning(f"Ollama rate limit hit: {_sanitize_error_message(str(e))}. Retrying with OpenAI fallback...")
                # Clear cache and recreate program with OpenAI
                global _program_cache
                _program_cache = None
                
                # Get prompt template (reuse the same one)
                prompt_template = """\
Extract structured job information from the following job posting text.

Job Posting Text:
{input_text}

Extract the following information:
- company: The company name (required)
- contact_person: Contact person or HR name if mentioned, otherwise null
- title: Job title/position name (required)
- location: Job location (city, state, country, or remote) (required)
- salary: Salary range or compensation if mentioned, otherwise null
- url: The job posting URL (if not in text, use "unknown") (required)
- date_applied: Date applied if mentioned, otherwise null
- date_confirmation: Date of confirmation if mentioned, otherwise null
- date_latest_reply: Date of latest reply if mentioned, otherwise null
- status: Application status if mentioned, otherwise null
- reason_outcome: Reason for outcome if mentioned, otherwise null
- level: Job level - must be EXACTLY one of these lowercase strings: "intern", "entry", "mid", "senior", "staff", "principal", "executive", or null if unclear
- remote_type: Remote work type - must be EXACTLY one of these lowercase strings: "on_site", "remote", "hybrid", "flexible", or null if unclear
- ats: ATS system type - must be EXACTLY one of these lowercase strings: "greenhouse", "lever", "workday", "taleo", "icims", "custom", "unknown", or null

IMPORTANT: For enum fields (level, remote_type, ats), return ONLY the lowercase string value (e.g., "entry", "hybrid", "custom") or null. Do NOT return class names like "JobLevel.ENTRY" or "RemoteType.HYBRID".

Return only valid data. If information is not available, use null for optional fields.
"""
                
                # Create OpenAI LLM
                openai_llm = OpenAI(
                    api_key=OPENAI_API_KEY,
                    model=OPENAI_MODEL,
                    temperature=0.1,
                )
                
                # Recreate program with OpenAI
                program = StructuredLLMProgram.from_defaults(
                    output_cls=JobInfo,
                    prompt_template_str=prompt_template,
                    llm=openai_llm,
                    verbose=False,
                )
                
                # Retry with OpenAI
                result = program(input_text=text_for_extraction)
            else:
                # Re-raise if not a rate limit or no OpenAI fallback
                raise
        
        try:
            # Fix enum values if LLM returned them as strings
            # The LLM should return lowercase string values (e.g., "entry", "hybrid", "greenhouse")
            # Convert to actual enum instances by matching against enum values or names
            
            if result.level and isinstance(result.level, str):
                level_str = result.level.strip().lower()
                # Try to match by enum value first (e.g., "entry" -> JobLevel.ENTRY)
                matched = False
                for level_enum in JobLevel:
                    if level_enum.value.lower() == level_str:
                        result.level = level_enum
                        matched = True
                        break
                    # Also try matching by enum name (e.g., "ENTRY" -> JobLevel.ENTRY)
                    if level_enum.name.upper() == level_str.upper():
                        result.level = level_enum
                        matched = True
                        break
                if not matched:
                    logger.warning(f"Invalid level value: {result.level}, setting to None")
                    result.level = None
            
            if result.remote_type and isinstance(result.remote_type, str):
                remote_str = result.remote_type.strip().lower()
                matched = False
                for remote_enum in RemoteType:
                    if remote_enum.value.lower() == remote_str:
                        result.remote_type = remote_enum
                        matched = True
                        break
                    if remote_enum.name.upper() == remote_str.upper():
                        result.remote_type = remote_enum
                        matched = True
                        break
                if not matched:
                    logger.warning(f"Invalid remote_type value: {result.remote_type}, setting to None")
                    result.remote_type = None
            
            if result.ats and isinstance(result.ats, str):
                ats_str = result.ats.strip().lower()
                matched = False
                for ats_enum in AtsType:
                    if ats_enum.value.lower() == ats_str:
                        result.ats = ats_enum
                        matched = True
                        break
                    if ats_enum.name.upper() == ats_str.upper():
                        result.ats = ats_enum
                        matched = True
                        break
                if not matched:
                    logger.warning(f"Invalid ats value: {result.ats}, setting to None")
                    result.ats = None
                    
        except ValidationError as ve:
            # Catch ValidationError from program/JobInfo creation
            logger.error(f"Validation error during extraction: {ve}")
            raise RuntimeError(f"Extracted data validation failed: {ve}") from ve
        
        # Ensure URL is set (override if program didn't extract it properly)
        if not result.url or result.url == "unknown" or result.url.lower() == "unknown":
            result.url = url
        
        # Validate the result has required fields
        if not result.company or not result.title or not result.location:
            raise ValueError(
                f"Extraction failed: missing required fields. "
                f"Got company={result.company}, title={result.title}, location={result.location}"
            )
        
        logger.info(f"Successfully extracted job info: {result.company} - {result.title}")
        return result
        
    except (ValueError, RuntimeError) as e:
        # Re-raise ValueError and RuntimeError as-is (already properly formatted)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during job extraction: {_sanitize_error_message(str(e))}")
        raise RuntimeError(f"Job extraction failed: {e}") from e