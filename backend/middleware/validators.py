"""Input validation utilities

Enhancement #4: Add Input Validation & Security to all endpoints
Enhancement #32: Improve Data Quality Validation
"""
import re
from typing import Optional, List, Any
from pydantic import BaseModel, validator, Field
from datetime import datetime

from backend.models.errors import ErrorCode, FloodGuardException


class CoordinateValidator:
    """Validate geographic coordinates"""

    # Philippines bounding box
    MIN_LAT = 4.0
    MAX_LAT = 21.5
    MIN_LON = 116.0
    MAX_LON = 127.0

    @staticmethod
    def validate_latitude(lat: float) -> float:
        """Validate latitude is within Philippines bounds"""
        if not isinstance(lat, (int, float)):
            raise FloodGuardException(
                ErrorCode.INVALID_COORDINATES,
                f"Latitude must be a number, got {type(lat)}"
            )

        if not (CoordinateValidator.MIN_LAT <= lat <= CoordinateValidator.MAX_LAT):
            raise FloodGuardException(
                ErrorCode.INVALID_COORDINATES,
                f"Latitude {lat} is outside Philippines bounds ({CoordinateValidator.MIN_LAT}, {CoordinateValidator.MAX_LAT})"
            )

        return lat

    @staticmethod
    def validate_longitude(lon: float) -> float:
        """Validate longitude is within Philippines bounds"""
        if not isinstance(lon, (int, float)):
            raise FloodGuardException(
                ErrorCode.INVALID_COORDINATES,
                f"Longitude must be a number, got {type(lon)}"
            )

        if not (CoordinateValidator.MIN_LON <= lon <= CoordinateValidator.MAX_LON):
            raise FloodGuardException(
                ErrorCode.INVALID_COORDINATES,
                f"Longitude {lon} is outside Philippines bounds ({CoordinateValidator.MIN_LON}, {CoordinateValidator.MAX_LON})"
            )

        return lon


class SearchFiltersValidator(BaseModel):
    """
    Validated search filters with security checks

    Enhancement #4: Input validation
    """

    # Year validation
    infra_year: Optional[List[int]] = Field(None, description="Infrastructure years")

    # Text filters (with XSS protection)
    contractor: Optional[str] = Field(None, max_length=200)
    region: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    municipality: Optional[str] = Field(None, max_length=100)
    project_type: Optional[str] = Field(None, max_length=200)

    # Numeric filters
    min_contract_cost: Optional[float] = Field(None, ge=0, le=1e12)
    max_contract_cost: Optional[float] = Field(None, ge=0, le=1e12)

    # Pagination
    limit: Optional[int] = Field(100, ge=1, le=1000)
    offset: Optional[int] = Field(0, ge=0)

    @validator('infra_year')
    def validate_years(cls, v):
        """Validate years are within reasonable range"""
        if v is None:
            return v

        for year in v:
            if not isinstance(year, int):
                raise FloodGuardException(
                    ErrorCode.INVALID_INPUT,
                    f"Year must be an integer, got {type(year)}"
                )
            if not (2020 <= year <= 2030):
                raise FloodGuardException(
                    ErrorCode.INVALID_INPUT,
                    f"Year {year} is out of valid range (2020-2030)"
                )

        return v

    @validator('contractor', 'region', 'province', 'municipality', 'project_type')
    def sanitize_text(cls, v):
        """Sanitize text inputs to prevent XSS and SQL injection"""
        if v is None:
            return v

        # Remove potentially dangerous characters
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'onclick=',
            r'onload=',
            r'--',  # SQL comment
            r';',   # SQL statement separator (in some contexts)
            r'DROP TABLE',
            r'DELETE FROM',
            r'INSERT INTO',
            r'UPDATE ',
        ]

        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in v_lower:
                raise FloodGuardException(
                    ErrorCode.INVALID_INPUT,
                    f"Input contains potentially dangerous content: {pattern}"
                )

        # Trim and normalize whitespace
        v = ' '.join(v.split())

        return v

    @validator('max_contract_cost')
    def validate_cost_range(cls, v, values):
        """Ensure max >= min if both specified"""
        if v is None:
            return v

        min_cost = values.get('min_contract_cost')
        if min_cost is not None and v < min_cost:
            raise FloodGuardException(
                ErrorCode.INVALID_INPUT,
                f"max_contract_cost ({v}) must be >= min_contract_cost ({min_cost})"
            )

        return v


class SpatialSearchValidator(BaseModel):
    """Validated spatial search parameters"""

    lat: float
    lon: float
    radius_km: float = Field(default=5.0, ge=0.1, le=500)

    @validator('lat')
    def validate_lat(cls, v):
        return CoordinateValidator.validate_latitude(v)

    @validator('lon')
    def validate_lon(cls, v):
        return CoordinateValidator.validate_longitude(v)


class NewsQueryValidator(BaseModel):
    """Validated news query parameters"""

    query: str = Field(..., min_length=1, max_length=500)
    project_id: Optional[str] = Field(None, max_length=100)
    contractor: Optional[str] = Field(None, max_length=200)
    n_results: int = Field(5, ge=1, le=50)

    @validator('query', 'contractor')
    def sanitize_query(cls, v):
        """Sanitize query text"""
        if v is None:
            return v

        # Remove special characters that could cause issues
        v = re.sub(r'[<>{}\\]', '', v)

        # Trim
        v = v.strip()

        if len(v) == 0:
            raise FloodGuardException(
                ErrorCode.INVALID_INPUT,
                "Query cannot be empty after sanitization"
            )

        return v


class ChatMessageValidator(BaseModel):
    """
    Validated chat message

    Enhancement #4: Input validation
    Enhancement #5: Make OpenAI key optional
    """

    message: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(..., min_length=1, max_length=100)
    anthropic_key: Optional[str] = Field(None, min_length=20, max_length=200)
    openai_key: Optional[str] = Field(None, min_length=20, max_length=200)  # Now optional!

    @validator('message')
    def validate_message(cls, v):
        """Validate and sanitize message"""
        # Trim whitespace
        v = v.strip()

        if len(v) == 0:
            raise FloodGuardException(
                ErrorCode.INVALID_INPUT,
                "Message cannot be empty"
            )

        # Check for excessively long words (potential attack)
        words = v.split()
        for word in words:
            if len(word) > 100:
                raise FloodGuardException(
                    ErrorCode.INVALID_INPUT,
                    "Message contains excessively long words"
                )

        return v

    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate session ID format"""
        # Only allow alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise FloodGuardException(
                ErrorCode.INVALID_INPUT,
                "Session ID contains invalid characters"
            )

        return v

    @validator('anthropic_key', 'openai_key')
    def validate_api_key_format(cls, v):
        """Basic API key format validation"""
        if v is None:
            return v

        # Check for obvious fake/test keys
        if v.lower() in ['dummy', 'test', 'fake', 'placeholder']:
            raise FloodGuardException(
                ErrorCode.API_KEY_INVALID,
                "Please provide a valid API key"
            )

        # Basic format check (should start with expected prefix)
        if 'anthropic' in cls.__fields__ and v:
            if not v.startswith('sk-ant-'):
                raise FloodGuardException(
                    ErrorCode.API_KEY_INVALID,
                    "Anthropic API key should start with 'sk-ant-'"
                )

        return v


class PaginationParams(BaseModel):
    """Validated pagination parameters"""

    offset: int = Field(0, ge=0, le=100000)
    limit: int = Field(100, ge=1, le=1000)
    cursor: Optional[str] = Field(None, max_length=200)

    def get_page_number(self) -> int:
        """Calculate page number from offset/limit"""
        return (self.offset // self.limit) + 1


def validate_project_data(df) -> tuple[bool, List[str]]:
    """
    Validate project DataFrame quality

    Enhancement #32: Improve Data Quality Validation

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    # Check for required columns
    required_cols = [
        'ProjectComponentID',
        'ProjectDescription',
        'Contractor',
        'ContractCost',
        'Latitude',
        'Longitude',
        'Province',
        'InfraYear'
    ]

    for col in required_cols:
        if col not in df.columns:
            issues.append(f"Missing required column: {col}")

    if issues:
        return False, issues

    # Check for data quality issues
    total_rows = len(df)

    # 1. Check for missing coordinates
    missing_coords = df[
        (df['Latitude'].isna()) | (df['Longitude'].isna()) |
        (df['Latitude'] == 0) | (df['Longitude'] == 0)
    ]
    if len(missing_coords) > 0:
        pct = len(missing_coords) / total_rows * 100
        issues.append(f"{len(missing_coords)} projects ({pct:.1f}%) have missing/zero coordinates")

    # 2. Check for invalid coordinates (outside Philippines)
    invalid_coords = df[
        (df['Latitude'] < CoordinateValidator.MIN_LAT) |
        (df['Latitude'] > CoordinateValidator.MAX_LAT) |
        (df['Longitude'] < CoordinateValidator.MIN_LON) |
        (df['Longitude'] > CoordinateValidator.MAX_LON)
    ]
    if len(invalid_coords) > 0:
        pct = len(invalid_coords) / total_rows * 100
        issues.append(f"{len(invalid_coords)} projects ({pct:.1f}%) have coordinates outside Philippines bounds")

    # 3. Check for missing contract costs
    missing_cost = df[df['ContractCost'].isna() | (df['ContractCost'] <= 0)]
    if len(missing_cost) > 0:
        pct = len(missing_cost) / total_rows * 100
        issues.append(f"{len(missing_cost)} projects ({pct:.1f}%) have missing/zero contract cost")

    # 4. Check for missing contractors
    missing_contractor = df[df['Contractor'].isna() | (df['Contractor'].str.strip() == '')]
    if len(missing_contractor) > 0:
        pct = len(missing_contractor) / total_rows * 100
        issues.append(f"{len(missing_contractor)} projects ({pct:.1f}%) have missing contractor")

    # 5. Check for unrealistic costs (> 1 billion or < 10,000)
    unrealistic_cost = df[
        (df['ContractCost'] > 1_000_000_000) |
        (df['ContractCost'] < 10_000)
    ]
    if len(unrealistic_cost) > 0:
        pct = len(unrealistic_cost) / total_rows * 100
        issues.append(f"{len(unrealistic_cost)} projects ({pct:.1f}%) have unrealistic contract costs")

    # 6. Check for future years
    current_year = datetime.now().year
    future_years = df[df['InfraYear'] > current_year + 1]
    if len(future_years) > 0:
        pct = len(future_years) / total_rows * 100
        issues.append(f"{len(future_years)} projects ({pct:.1f}%) have future infrastructure years")

    # Overall validation
    is_valid = len(issues) == 0

    return is_valid, issues
