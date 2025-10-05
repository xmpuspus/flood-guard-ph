import logging
from datetime import datetime
from typing import Optional

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from backend.config import settings
from backend.models.project import ProjectSearchFilters, ProjectStats, SpatialSearch

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for loading and searching project data"""

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.gdf: Optional[gpd.GeoDataFrame] = None
        self._load_data()

    def _load_data(self):
        """Load CSV data and create GeoDataFrame"""
        try:
            logger.info(f"Loading projects from {settings.projects_csv}")
            df = pd.read_csv(settings.projects_csv)

            # Clean and convert data
            df = self._clean_data(df)

            # Filter out rows with missing coordinates
            df = df.dropna(subset=["Latitude", "Longitude"])

            # Create GeoDataFrame
            geometry = [
                Point(xy) for xy in zip(df["Longitude"], df["Latitude"])
            ]
            self.gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
            self.df = df

            logger.info(f"Loaded {len(self.df)} projects")
        except Exception as e:
            logger.error(f"Error loading projects: {e}")
            raise

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize data"""
        # Convert ABC and ContractCost to numeric
        for col in ["ABC", "ContractCost"]:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(",", ""), errors="coerce"
                )

        # Normalize contractor names
        if "Contractor" in df.columns:
            df["Contractor"] = (
                df["Contractor"].astype(str).str.upper().str.strip()
            )

        # Parse dates
        date_columns = [
            "StartDate",
            "CompletionDateActual",
            "CompletionDateOriginal",
            "CreationDate",
            "EditDate",
        ]
        for col in date_columns:
            if col in df.columns:
                df[col] = self._parse_date(df[col])

        # Fill NaN values for string columns
        string_cols = df.select_dtypes(include=["object"]).columns
        df[string_cols] = df[string_cols].fillna("")

        return df

    def _parse_date(self, series: pd.Series) -> pd.Series:
        """Parse dates handling Unix timestamps"""
        try:
            # Try parsing as datetime first
            parsed = pd.to_datetime(series, errors="coerce")

            # Check for Unix timestamps (large numbers)
            numeric = pd.to_numeric(series, errors="coerce")
            unix_mask = numeric > 1000000000000  # Milliseconds since epoch

            if unix_mask.any():
                parsed.loc[unix_mask] = pd.to_datetime(
                    numeric.loc[unix_mask], unit="ms", errors="coerce"
                )

            return parsed
        except Exception as e:
            logger.warning(f"Error parsing dates: {e}")
            return series

    def search(
        self,
        filters: Optional[ProjectSearchFilters] = None,
        spatial: Optional[SpatialSearch] = None,
        limit: int = 100,
        sort_field: str = "ContractCost",
        sort_order: str = "desc",
    ) -> pd.DataFrame:
        """Search projects with filters and spatial queries"""
        if self.gdf is None:
            return pd.DataFrame()

        result = self.gdf.copy()

        # Apply filters
        if filters:
            if filters.infra_year:
                result = result[result["InfraYear"].isin(filters.infra_year)]

            if filters.contractor:
                result = result[
                    result["Contractor"].str.contains(
                        filters.contractor.upper(), case=False, na=False
                    )
                ]

            if filters.min_contract_cost:
                result = result[
                    result["ContractCost"] >= filters.min_contract_cost
                ]

            if filters.max_contract_cost:
                result = result[
                    result["ContractCost"] <= filters.max_contract_cost
                ]

            if filters.region:
                result = result[
                    result["Region"].str.contains(
                        filters.region, case=False, na=False
                    )
                ]

            if filters.province:
                result = result[
                    result["Province"].str.contains(
                        filters.province, case=False, na=False
                    )
                ]

            if filters.municipality:
                result = result[
                    result["Municipality"].str.contains(
                        filters.municipality, case=False, na=False
                    )
                ]

            if filters.type_of_work:
                result = result[
                    result["TypeofWork"].str.contains(
                        filters.type_of_work, case=False, na=False
                    )
                ]

            if filters.project_id:
                result = result[result["ProjectID"] == filters.project_id]

        # Apply spatial search
        if spatial:
            from backend.services.geospatial import GeospatialService

            geo_service = GeospatialService(self.gdf)

            if spatial.type == "radius" and spatial.lat and spatial.lon:
                result = geo_service.search_radius(
                    spatial.lat, spatial.lon, spatial.radius_km or 5.0
                )
            elif spatial.type == "bbox" and spatial.bbox:
                result = geo_service.search_bbox(spatial.bbox)

        # Sort
        if sort_field in result.columns:
            ascending = sort_order.lower() == "asc"
            result = result.sort_values(by=sort_field, ascending=ascending)

        # Limit
        result = result.head(limit)

        return result

    def get_stats(self, df: Optional[pd.DataFrame] = None) -> ProjectStats:
        """Calculate aggregate statistics"""
        if df is None:
            df = self.df

        if df is None or len(df) == 0:
            return ProjectStats(
                total_budget=0.0,
                total_projects=0,
                avg_award=0.0,
                contractors=[],
                project_types={},
            )

        total_budget = float(df["ContractCost"].sum())
        total_projects = len(df)
        avg_award = float(df["ContractCost"].mean())

        # Top contractors
        contractors = (
            df["Contractor"].value_counts().head(10).index.tolist()
        )

        # Project types
        project_types = df["TypeofWork"].value_counts().to_dict()

        return ProjectStats(
            total_budget=total_budget,
            total_projects=total_projects,
            avg_award=avg_award,
            contractors=contractors,
            project_types=project_types,
        )

    def get_project_by_id(self, project_id: str) -> Optional[dict]:
        """Get single project by ID"""
        if self.df is None:
            return None

        result = self.df[self.df["ProjectComponentID"] == project_id]
        if len(result) == 0:
            return None

        return result.iloc[0].to_dict()

    def get_bounds(self, df: pd.DataFrame) -> list[list[float]]:
        """Get bounding box for a set of projects"""
        if len(df) == 0:
            return [[121.0, 12.0], [122.0, 13.0]]  # Default Philippines

        min_lon = float(df["Longitude"].min())
        max_lon = float(df["Longitude"].max())
        min_lat = float(df["Latitude"].min())
        max_lat = float(df["Latitude"].max())

        # Add padding
        padding = 0.1
        return [
            [min_lon - padding, min_lat - padding],
            [max_lon + padding, max_lat + padding],
        ]