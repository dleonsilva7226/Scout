"""Job extraction using LlamaIndex structured output"""
import logging
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

from llama_index.llms.openai import OpenAI
from pydantic import ValidationError

from scout.models import JobInfo, JobLevel, RemoteType, AtsType
from scout.config import OPENAI_API_KEY, OPENAI_MODEL, validate_config

logger = logging.getLogger(__name__)

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
    
    llm = OpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0.1,  # Low temperature for consistent extraction
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
- level: Job level - must be one of: intern, entry, mid, senior, staff, principal, executive, or null if unclear
- remote_type: Remote work type - must be one of: on_site, remote, hybrid, flexible, or null if unclear
- ats: ATS system type - must be one of: greenhouse, lever, workday, taleo, icims, custom, unknown, or null

For enum fields (level, remote_type, ats), use the exact lowercase values shown above or null.
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
        logger.warning(f"Failed to create program with from_defaults: {e}")
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


def extract_job_info(text: str, url: str = "unknown") -> JobInfo:
    """
    Convert cleaned job description text into a JobInfo model.
    
    Args:
        text: Cleaned job description text
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
        
        # Preprocess text: normalize HTML if present, otherwise use as-is
        # LLM works better with original formatting
        text_for_extraction = text.strip()
        
        # Run the structured extraction
        try:
            result = program(input_text=text_for_extraction)
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
        logger.error(f"Unexpected error during job extraction: {e}")
        raise RuntimeError(f"Job extraction failed: {e}") from e