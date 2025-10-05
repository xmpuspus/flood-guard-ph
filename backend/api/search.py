import logging

from fastapi import APIRouter, HTTPException

from backend.models.project import ProjectSearchRequest
from backend.services.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/search")
async def search_projects(request: ProjectSearchRequest):
    """Search projects with filters"""
    try:
        # Get project service from app state
        from backend.main import project_service

        # Execute search
        results = project_service.search(
            filters=request.filters,
            spatial=request.spatial,
            limit=request.limit,
            sort_field=request.sort.get("field", "ContractCost")
            if request.sort
            else "ContractCost",
            sort_order=request.sort.get("order", "desc")
            if request.sort
            else "desc",
        )

        # Convert to dict
        projects = []
        for _, row in results.iterrows():
            project = {
                "object_id": int(row.get("ObjectId", 0)),
                "project_id": row.get("ProjectID", ""),
                "project_component_id": row.get("ProjectComponentID", ""),
                "contract_id": row.get("ContractID", ""),
                "region": row.get("Region", ""),
                "province": row.get("Province", ""),
                "municipality": row.get("Municipality", ""),
                "latitude": float(row.get("Latitude", 0)),
                "longitude": float(row.get("Longitude", 0)),
                "abc": float(row.get("ABC", 0)),
                "contract_cost": float(row.get("ContractCost", 0)),
                "contractor": row.get("Contractor", ""),
                "project_description": row.get("ProjectDescription", ""),
                "type_of_work": row.get("TypeofWork", ""),
                "infra_year": int(row.get("InfraYear", 0))
                if row.get("InfraYear")
                else None,
                "district_engineering_office": row.get(
                    "DistrictEngineeringOffice", ""
                ),
                "implementing_office": row.get("ImplementingOffice", ""),
            }
            projects.append(project)

        # Calculate stats
        stats = project_service.get_stats(results)

        return {
            "projects": projects,
            "total": len(projects),
            "stats": {
                "total_budget": stats.total_budget,
                "avg_award": stats.avg_award,
                "contractors": stats.contractors,
                "project_types": stats.project_types,
            },
        }

    except Exception as e:
        logger.error(f"Error in search: {e}")
        raise HTTPException(status_code=500, detail=str(e))