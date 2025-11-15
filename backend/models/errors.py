"""Error handling models and codes for FloodGuard PH"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ErrorCode(str, Enum):
    """Error codes for structured error handling"""

    # Query/Input Errors (1xxx)
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_DATE_FORMAT = "INVALID_DATE_FORMAT"
    INVALID_COORDINATES = "INVALID_COORDINATES"
    QUERY_TOO_LONG = "QUERY_TOO_LONG"
    INVALID_FILTER = "INVALID_FILTER"

    # API/Service Errors (2xxx)
    API_KEY_INVALID = "API_KEY_INVALID"
    API_KEY_MISSING = "API_KEY_MISSING"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    API_TIMEOUT = "API_TIMEOUT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # Data Errors (3xxx)
    NO_RESULTS_FOUND = "NO_RESULTS_FOUND"
    DATA_NOT_LOADED = "DATA_NOT_LOADED"
    VECTOR_DB_ERROR = "VECTOR_DB_ERROR"
    DATA_PARSE_ERROR = "DATA_PARSE_ERROR"

    # Processing Errors (4xxx)
    LLM_ERROR = "LLM_ERROR"
    TOOL_EXECUTION_ERROR = "TOOL_EXECUTION_ERROR"
    NEWS_FETCH_ERROR = "NEWS_FETCH_ERROR"
    SEARCH_ERROR = "SEARCH_ERROR"

    # System Errors (5xxx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ErrorDetail(BaseModel):
    """Detailed error information"""
    code: ErrorCode
    message: str
    details: Optional[str] = None
    retry_possible: bool = False
    user_message: str


# Error code to user-friendly message mapping
ERROR_MESSAGES = {
    ErrorCode.INVALID_INPUT: ErrorDetail(
        code=ErrorCode.INVALID_INPUT,
        message="Invalid input provided",
        user_message="Please check your input and try again.",
        retry_possible=True
    ),
    ErrorCode.MISSING_REQUIRED_FIELD: ErrorDetail(
        code=ErrorCode.MISSING_REQUIRED_FIELD,
        message="Required field is missing",
        user_message="Some required information is missing. Please provide all necessary details.",
        retry_possible=True
    ),
    ErrorCode.QUERY_TOO_LONG: ErrorDetail(
        code=ErrorCode.QUERY_TOO_LONG,
        message="Query exceeds maximum length",
        user_message="Your message is too long. Please try a shorter query.",
        retry_possible=True
    ),
    ErrorCode.API_KEY_INVALID: ErrorDetail(
        code=ErrorCode.API_KEY_INVALID,
        message="API key is invalid",
        user_message="Your API key appears to be invalid. Please check your settings and try again.",
        retry_possible=True
    ),
    ErrorCode.API_KEY_MISSING: ErrorDetail(
        code=ErrorCode.API_KEY_MISSING,
        message="API key is required",
        user_message="Please provide your API key in the settings to use this feature.",
        retry_possible=True
    ),
    ErrorCode.API_RATE_LIMIT: ErrorDetail(
        code=ErrorCode.API_RATE_LIMIT,
        message="Rate limit exceeded",
        user_message="Too many requests. Please wait a moment and try again.",
        retry_possible=True
    ),
    ErrorCode.API_TIMEOUT: ErrorDetail(
        code=ErrorCode.API_TIMEOUT,
        message="Request timed out",
        user_message="The request took too long. Please try again.",
        retry_possible=True
    ),
    ErrorCode.SERVICE_UNAVAILABLE: ErrorDetail(
        code=ErrorCode.SERVICE_UNAVAILABLE,
        message="Service temporarily unavailable",
        user_message="The service is temporarily unavailable. Please try again in a few moments.",
        retry_possible=True
    ),
    ErrorCode.NO_RESULTS_FOUND: ErrorDetail(
        code=ErrorCode.NO_RESULTS_FOUND,
        message="No results found",
        user_message="No projects match your search criteria. Try adjusting your filters or search terms.",
        retry_possible=True
    ),
    ErrorCode.DATA_NOT_LOADED: ErrorDetail(
        code=ErrorCode.DATA_NOT_LOADED,
        message="Project data not loaded",
        user_message="Project data is not available. Please contact support.",
        retry_possible=False
    ),
    ErrorCode.VECTOR_DB_ERROR: ErrorDetail(
        code=ErrorCode.VECTOR_DB_ERROR,
        message="Vector database error",
        user_message="There was an error with the search system. Please try a different query.",
        retry_possible=True
    ),
    ErrorCode.LLM_ERROR: ErrorDetail(
        code=ErrorCode.LLM_ERROR,
        message="Language model error",
        user_message="There was an error processing your request. Please try rephrasing your question.",
        retry_possible=True
    ),
    ErrorCode.NEWS_FETCH_ERROR: ErrorDetail(
        code=ErrorCode.NEWS_FETCH_ERROR,
        message="Error fetching news",
        user_message="Unable to fetch news articles at this time. The project data is still available.",
        retry_possible=True
    ),
    ErrorCode.SEARCH_ERROR: ErrorDetail(
        code=ErrorCode.SEARCH_ERROR,
        message="Search operation failed",
        user_message="There was an error searching projects. Please try again or adjust your search criteria.",
        retry_possible=True
    ),
    ErrorCode.INTERNAL_ERROR: ErrorDetail(
        code=ErrorCode.INTERNAL_ERROR,
        message="Internal server error",
        user_message="An unexpected error occurred. Please try again later.",
        retry_possible=True
    ),
    ErrorCode.UNKNOWN_ERROR: ErrorDetail(
        code=ErrorCode.UNKNOWN_ERROR,
        message="Unknown error",
        user_message="An unexpected error occurred. Please try again.",
        retry_possible=True
    ),
}


def get_error_detail(code: ErrorCode, details: Optional[str] = None) -> ErrorDetail:
    """Get error detail with optional additional details"""
    error = ERROR_MESSAGES.get(code, ERROR_MESSAGES[ErrorCode.UNKNOWN_ERROR]).copy()
    if details:
        error.details = details
    return error


class FloodGuardException(Exception):
    """Base exception for FloodGuard PH"""
    def __init__(self, error_code: ErrorCode, details: Optional[str] = None):
        self.error_code = error_code
        self.error_detail = get_error_detail(error_code, details)
        super().__init__(self.error_detail.message)
