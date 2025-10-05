import logging

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, box

logger = logging.getLogger(__name__)


class GeospatialService:
    """Service for geospatial operations"""

    def __init__(self, gdf: gpd.GeoDataFrame):
        self.gdf = gdf

    def search_radius(
        self, lat: float, lon: float, radius_km: float
    ) -> pd.DataFrame:
        """Find projects within radius of a point"""
        try:
            # Create point
            center = gpd.GeoDataFrame(
                {"geometry": [Point(lon, lat)]}, crs="EPSG:4326"
            )

            # Convert to metric CRS for distance calculation
            gdf_metric = self.gdf.to_crs("EPSG:3857")
            center_metric = center.to_crs("EPSG:3857")

            # Calculate distances in meters
            distances = gdf_metric.geometry.distance(
                center_metric.geometry.iloc[0]
            )

            # Filter by radius
            radius_m = radius_km * 1000
            mask = distances <= radius_m

            return self.gdf[mask]
        except Exception as e:
            logger.error(f"Error in radius search: {e}")
            return pd.DataFrame()

    def search_bbox(self, bbox: list[list[float]]) -> pd.DataFrame:
        """Find projects within bounding box"""
        try:
            # bbox format: [[min_lon, min_lat], [max_lon, max_lat]]
            min_lon, min_lat = bbox[0]
            max_lon, max_lat = bbox[1]

            # Create bounding box geometry
            bbox_geom = box(min_lon, min_lat, max_lon, max_lat)
            bbox_gdf = gpd.GeoDataFrame(
                {"geometry": [bbox_geom]}, crs="EPSG:4326"
            )

            # Spatial join
            result = gpd.sjoin(
                self.gdf, bbox_gdf, how="inner", predicate="within"
            )

            return result
        except Exception as e:
            logger.error(f"Error in bbox search: {e}")
            return pd.DataFrame()

    def get_nearest_projects(
        self, lat: float, lon: float, n: int = 5
    ) -> pd.DataFrame:
        """Find n nearest projects to a point"""
        try:
            # Create point
            center = gpd.GeoDataFrame(
                {"geometry": [Point(lon, lat)]}, crs="EPSG:4326"
            )

            # Convert to metric CRS
            gdf_metric = self.gdf.to_crs("EPSG:3857")
            center_metric = center.to_crs("EPSG:3857")

            # Calculate distances
            distances = gdf_metric.geometry.distance(
                center_metric.geometry.iloc[0]
            )

            # Get n nearest
            nearest_indices = distances.nsmallest(n).index
            return self.gdf.loc[nearest_indices]
        except Exception as e:
            logger.error(f"Error finding nearest projects: {e}")
            return pd.DataFrame()