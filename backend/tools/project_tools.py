import json
import logging
from typing import Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from backend.models.project import ProjectSearchFilters, SpatialSearch
from backend.services.project_service import ProjectService

logger = logging.getLogger(__name__)


class ProjectSearchInput(BaseModel):
    """Input for project search tool"""

    query: str = Field(description="Natural language search query")
    infra_year: Optional[list[int]] = Field(
        None, description="Filter by infrastructure year"
    )
    contractor: Optional[str] = Field(None, description="Filter by contractor name")
    region: Optional[str] = Field(None, description="Filter by region")
    province: Optional[str] = Field(None, description="Filter by province")
    municipality: Optional[str] = Field(None, description="Filter by municipality")
    min_cost: Optional[float] = Field(
        None, description="Minimum contract cost in PHP"
    )
    max_cost: Optional[float] = Field(
        None, description="Maximum contract cost in PHP"
    )


class ProjectSearchTool(BaseTool):
    """Tool for searching projects"""

    name: str = "project_search"
    description: str = """
    Search for flood control projects using filters.
    Use this when the user asks about specific projects, locations, contractors, or years.
    Returns a list of matching projects with details.
    """
    args_schema: type = ProjectSearchInput
    project_service: ProjectService

    def __init__(self, project_service: ProjectService):
        super().__init__(project_service=project_service)

    def _run(
        self,
        query: str,
        infra_year: Optional[list[int]] = None,
        contractor: Optional[str] = None,
        region: Optional[str] = None,
        province: Optional[str] = None,
        municipality: Optional[str] = None,
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None,
    ) -> str:
        """Execute project search"""
        try:
            filters = ProjectSearchFilters(
                infra_year=infra_year,
                contractor=contractor,
                region=region,
                province=province,
                municipality=municipality,
                min_contract_cost=min_cost,
                max_contract_cost=max_cost,
            )

            results = self.project_service.search(filters=filters, limit=50)

            if len(results) == 0:
                return "No projects found matching the criteria."

            # Convert to dict for JSON serialization
            projects = []
            for _, row in results.iterrows():
                project = {
                    "project_id": row.get("ProjectComponentID", ""),
                    "description": row.get("ProjectDescription", ""),
                    "contractor": row.get("Contractor", ""),
                    "contract_cost": float(row.get("ContractCost", 0)),
                    "abc": float(row.get("ABC", 0)),
                    "region": row.get("Region", ""),
                    "province": row.get("Province", ""),
                    "municipality": row.get("Municipality", ""),
                    "infra_year": int(row.get("InfraYear", 0))
                    if row.get("InfraYear")
                    else None,
                    "type_of_work": row.get("TypeofWork", ""),
                    "lat": float(row.get("Latitude", 0)),
                    "lon": float(row.get("Longitude", 0)),
                }
                projects.append(project)

            return json.dumps(
                {"count": len(projects), "projects": projects}, indent=2
            )

        except Exception as e:
            logger.error(f"Error in project search: {e}")
            return f"Error searching projects: {str(e)}"


class ProjectStatsInput(BaseModel):
    """Input for project stats tool"""

    filters: Optional[dict] = Field(
        None, description="Optional filters to apply before calculating stats"
    )


class ProjectStatsTool(BaseTool):
    """Tool for calculating project statistics"""

    name: str = "project_stats"
    description: str = """
    Calculate aggregate statistics about projects.
    Use this when the user asks about totals, averages, counts, or comparisons.
    Returns total budget, project count, average cost, top contractors, and project types.
    """
    args_schema: type = ProjectStatsInput
    project_service: ProjectService

    def __init__(self, project_service: ProjectService):
        super().__init__(project_service=project_service)

    def _run(self, filters: Optional[dict] = None) -> str:
        """Calculate statistics"""
        try:
            # Apply filters if provided
            if filters:
                filter_obj = ProjectSearchFilters(**filters)
                df = self.project_service.search(filters=filter_obj, limit=10000)
            else:
                df = self.project_service.df

            stats = self.project_service.get_stats(df)

            return json.dumps(
                {
                    "total_budget": stats.total_budget,
                    "total_projects": stats.total_projects,
                    "average_award": stats.avg_award,
                    "top_contractors": stats.contractors[:5],
                    "project_types": dict(
                        list(stats.project_types.items())[:5]
                    ),
                },
                indent=2,
            )

        except Exception as e:
            logger.error(f"Error calculating stats: {e}")
            return f"Error calculating statistics: {str(e)}"


class ContractorAnalysisInput(BaseModel):
    """Input for contractor analysis tool"""

    contractor: str = Field(description="Contractor name to analyze")


class ContractorAnalysisTool(BaseTool):
    """Tool for analyzing contractor performance"""

    name: str = "contractor_analysis"
    description: str = """
    Analyze a specific contractor's projects and performance.
    Use this when the user asks about a specific contractor.
    Returns all projects, total awards, locations, and patterns.
    """
    args_schema: type = ContractorAnalysisInput
    project_service: ProjectService

    def __init__(self, project_service: ProjectService):
        super().__init__(project_service=project_service)

    def _run(self, contractor: str) -> str:
        """Analyze contractor"""
        try:
            filters = ProjectSearchFilters(contractor=contractor)
            results = self.project_service.search(filters=filters, limit=1000)

            if len(results) == 0:
                return f"No projects found for contractor: {contractor}"

            stats = self.project_service.get_stats(results)

            # Get location distribution
            locations = (
                results.groupby(["Province", "Municipality"])
                .size()
                .sort_values(ascending=False)
                .head(5)
                .to_dict()
            )

            # Get year distribution
            year_dist = (
                results["InfraYear"].value_counts().sort_index().to_dict()
            )

            return json.dumps(
                {
                    "contractor": contractor,
                    "total_projects": stats.total_projects,
                    "total_awards": stats.total_budget,
                    "average_award": stats.avg_award,
                    "project_types": stats.project_types,
                    "top_locations": {
                        f"{k[1]}, {k[0]}": v for k, v in locations.items()
                    },
                    "projects_by_year": year_dist,
                },
                indent=2,
            )

        except Exception as e:
            logger.error(f"Error analyzing contractor: {e}")
            return f"Error analyzing contractor: {str(e)}"


class GeospatialSearchInput(BaseModel):
    """Input for geospatial search tool"""

    lat: float = Field(description="Latitude")
    lon: float = Field(description="Longitude")
    radius_km: float = Field(default=5.0, description="Search radius in kilometers")


class GeospatialSearchTool(BaseTool):
    """Tool for location-based search"""

    name: str = "geospatial_search"
    description: str = """
    Find projects near a specific location using coordinates.
    Use this when the user asks about projects "near" a place or within a distance.
    Returns projects within the specified radius.
    """
    args_schema: type = GeospatialSearchInput
    project_service: ProjectService

    def __init__(self, project_service: ProjectService):
        super().__init__(project_service=project_service)

    def _run(self, lat: float, lon: float, radius_km: float = 5.0) -> str:
        """Search by location"""
        try:
            from backend.services.geospatial import GeospatialService

            geo_service = GeospatialService(self.project_service.gdf)
            results = geo_service.search_radius(lat, lon, radius_km)

            if len(results) == 0:
                return f"No projects found within {radius_km}km of ({lat}, {lon})"

            projects = []
            for _, row in results.iterrows():
                project = {
                    "project_id": row.get("ProjectComponentID", ""),
                    "description": row.get("ProjectDescription", ""),
                    "contractor": row.get("Contractor", ""),
                    "contract_cost": float(row.get("ContractCost", 0)),
                    "municipality": row.get("Municipality", ""),
                    "province": row.get("Province", ""),
                    "lat": float(row.get("Latitude", 0)),
                    "lon": float(row.get("Longitude", 0)),
                }
                projects.append(project)

            return json.dumps(
                {
                    "count": len(projects),
                    "search_location": {"lat": lat, "lon": lon},
                    "radius_km": radius_km,
                    "projects": projects,
                },
                indent=2,
            )

        except Exception as e:
            logger.error(f"Error in geospatial search: {e}")
            return f"Error in location search: {str(e)}"