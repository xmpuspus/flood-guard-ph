from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Project(BaseModel):
    """Project model matching CSV schema"""

    object_id: int = Field(alias="ObjectId")
    project_id: str = Field(alias="ProjectID")
    project_component_id: str = Field(alias="ProjectComponentID")
    contract_id: Optional[str] = Field(None, alias="ContractID")

    # Location
    region: str = Field(alias="Region")
    province: str = Field(alias="Province")
    municipality: str = Field(alias="Municipality")
    legislative_district: Optional[str] = Field(None, alias="LegislativeDistrict")
    latitude: float = Field(alias="Latitude")
    longitude: float = Field(alias="Longitude")

    # Financial
    abc: float = Field(alias="ABC")
    abc_string: Optional[str] = Field(None, alias="ABC_String")
    contract_cost: float = Field(alias="ContractCost")
    contract_cost_string: Optional[str] = Field(None, alias="ContractCost_String")

    # Contractor & Office
    contractor: str = Field(alias="Contractor")
    district_engineering_office: Optional[str] = Field(
        None, alias="DistrictEngineeringOffice"
    )
    implementing_office: Optional[str] = Field(None, alias="ImplementingOffice")

    # Project Info
    project_description: str = Field(alias="ProjectDescription")
    project_component_description: Optional[str] = Field(
        None, alias="ProjectComponentDescription"
    )
    type_of_work: str = Field(alias="TypeofWork")
    infra_type: Optional[str] = Field(None, alias="infra_type")
    program: Optional[str] = Field(None, alias="Program")

    # Dates
    funding_year: Optional[int] = Field(None, alias="FundingYear")
    infra_year: Optional[int] = Field(None, alias="InfraYear")
    completion_year: Optional[int] = Field(None, alias="CompletionYear")
    start_date: Optional[datetime] = Field(None, alias="StartDate")
    completion_date_original: Optional[datetime] = Field(
        None, alias="CompletionDateOriginal"
    )
    completion_date_actual: Optional[datetime] = Field(
        None, alias="CompletionDateActual"
    )

    # Metadata
    creation_date: Optional[datetime] = Field(None, alias="CreationDate")
    creator: Optional[str] = Field(None, alias="Creator")
    edit_date: Optional[datetime] = Field(None, alias="EditDate")
    editor: Optional[str] = Field(None, alias="Editor")
    global_id: Optional[str] = Field(None, alias="GlobalID")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "ObjectId": 1,
                "ProjectID": "P00941153LZ",
                "ProjectComponentID": "P00941153LZ_25AG0078",
                "ContractID": "25AG0078",
                "Region": "Region I",
                "Province": "PANGASINAN",
                "Municipality": "CITY OF ALAMINOS",
                "Latitude": 16.09684657,
                "Longitude": 119.96915518,
                "ABC": 4950000,
                "ContractCost": 4850385.71,
                "Contractor": "GED CONSTRUCTION",
                "ProjectDescription": "Rehabilitation of Flood Mitigation Structure",
                "TypeofWork": "Rehabilitation / Major Repair of Structure",
                "InfraYear": 2025,
            }
        }


class ProjectSearchFilters(BaseModel):
    """Search filters for projects"""

    infra_year: Optional[list[int]] = None
    contractor: Optional[str] = None
    min_contract_cost: Optional[float] = None
    max_contract_cost: Optional[float] = None
    region: Optional[str] = None
    province: Optional[str] = None
    municipality: Optional[str] = None
    type_of_work: Optional[str] = None
    project_id: Optional[str] = None


class SpatialSearch(BaseModel):
    """Spatial search parameters"""

    type: str = Field(..., description="radius or bbox")
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius_km: Optional[float] = None
    bbox: Optional[list[list[float]]] = None


class ProjectSearchRequest(BaseModel):
    """Complete search request"""

    filters: Optional[ProjectSearchFilters] = None
    spatial: Optional[SpatialSearch] = None
    limit: int = 100
    sort: Optional[dict] = None


class ProjectStats(BaseModel):
    """Aggregated project statistics"""

    total_budget: float
    total_projects: int
    avg_award: float
    contractors: list[str]
    project_types: dict[str, int]