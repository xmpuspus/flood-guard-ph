"""Export API endpoints

Enhancement #23: Add Data Export Features
"""
import csv
import json
import io
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, Response

from backend.models.project import ProjectSearchFilters
from backend.services.project_service import ProjectService
import pandas as pd

router = APIRouter()


@router.post("/api/export/csv")
async def export_csv(filters: ProjectSearchFilters):
    """Export search results as CSV"""
    # Get app state
    from backend.main import app
    project_service: ProjectService = app.state.project_service

    # Get filtered projects
    results = project_service.search(filters=filters, limit=10000)

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'Project ID', 'Description', 'Contractor', 'Cost',
        'Province', 'Municipality', 'Region', 'Year', 'Type of Work',
        'Latitude', 'Longitude'
    ])

    writer.writeheader()
    for _, row in results.iterrows():
        writer.writerow({
            'Project ID': row.get('ProjectComponentID', ''),
            'Description': row.get('ProjectDescription', ''),
            'Contractor': row.get('Contractor', ''),
            'Cost': f"₱{row.get('ContractCost', 0):,.2f}",
            'Province': row.get('Province', ''),
            'Municipality': row.get('Municipality', ''),
            'Region': row.get('Region', ''),
            'Year': int(row.get('InfraYear', 0)) if pd.notna(row.get('InfraYear')) else '',
            'Type of Work': row.get('TypeofWork', ''),
            'Latitude': float(row.get('Latitude', 0)),
            'Longitude': float(row.get('Longitude', 0))
        })

    # Return as downloadable file
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=floodguard_export_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.post("/api/export/geojson")
async def export_geojson(filters: ProjectSearchFilters):
    """Export as GeoJSON for GIS tools"""
    # Get app state
    from backend.main import app
    project_service: ProjectService = app.state.project_service

    results = project_service.search(filters=filters, limit=10000)

    features = []
    for _, row in results.iterrows():
        if pd.notna(row.get('Latitude')) and pd.notna(row.get('Longitude')):
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row['Longitude']), float(row['Latitude'])]
                },
                "properties": {
                    "project_id": str(row.get('ProjectComponentID', '')),
                    "description": str(row.get('ProjectDescription', '')),
                    "contractor": str(row.get('Contractor', '')),
                    "cost": float(row.get('ContractCost', 0)),
                    "province": str(row.get('Province', '')),
                    "municipality": str(row.get('Municipality', '')),
                    "year": int(row.get('InfraYear', 0)) if pd.notna(row.get('InfraYear')) else None,
                    "type_of_work": str(row.get('TypeofWork', ''))
                }
            }
            features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    return Response(
        content=json.dumps(geojson, indent=2),
        media_type="application/geo+json",
        headers={
            "Content-Disposition": f"attachment; filename=floodguard_export_{datetime.now().strftime('%Y%m%d')}.geojson"
        }
    )


@router.get("/api/export/stats")
async def export_stats(filters: ProjectSearchFilters = Depends()):
    """Export statistics as JSON"""
    from backend.main import app
    project_service: ProjectService = app.state.project_service

    results = project_service.search(filters=filters, limit=10000)
    stats = project_service.get_stats(results)

    return {
        "exported_at": datetime.now().isoformat(),
        "filter_applied": filters.dict(exclude_none=True),
        "statistics": {
            "total_projects": stats.total_projects,
            "total_budget": stats.total_budget,
            "average_award": stats.avg_award,
            "contractors": stats.contractors[:10],
            "project_types": stats.project_types
        }
    }
