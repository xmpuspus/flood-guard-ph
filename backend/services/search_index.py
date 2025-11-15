"""SQLite FTS5 Search Index

Enhancement #31: Search Optimization with SQLite Full-Text Search
"""
import sqlite3
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


class SearchIndex:
    """
    SQLite FTS5 for fast full-text search

    Enhancement #31: Search Optimization
    Provides sub-100ms searches at scale using SQLite's FTS5 engine
    """

    def __init__(self, db_path: str = "./data/search_index.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True, parents=True)

        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.create_tables()
        logger.info(f"✓ SearchIndex initialized: {self.db_path}")

    def create_tables(self):
        """Create FTS5 virtual table and metadata table"""
        try:
            # FTS5 virtual table for full-text search
            self.conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS projects_fts
                USING fts5(
                    project_id,
                    description,
                    contractor,
                    province,
                    municipality,
                    type_of_work,
                    year,
                    cost,
                    tokenize='porter unicode61'
                )
            """)

            # Metadata table for additional info
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS projects_metadata (
                    project_id TEXT PRIMARY KEY,
                    lat REAL,
                    lon REAL,
                    region TEXT,
                    contract_cost REAL,
                    infra_year INTEGER,
                    full_data TEXT
                )
            """)

            # Index on common filters
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_year
                ON projects_metadata(infra_year)
            """)

            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cost
                ON projects_metadata(contract_cost)
            """)

            self.conn.commit()
            logger.info("✓ FTS5 tables created")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def index_projects(self, df: pd.DataFrame):
        """Index all projects for fast search"""
        try:
            logger.info(f"Indexing {len(df)} projects...")

            # Clear existing
            self.conn.execute("DELETE FROM projects_fts")
            self.conn.execute("DELETE FROM projects_metadata")

            # Batch insert
            fts_records = []
            metadata_records = []

            for _, row in df.iterrows():
                project_id = str(row.get('ProjectComponentID', ''))
                if not project_id:
                    continue

                # FTS record
                fts_records.append((
                    project_id,
                    str(row.get('ProjectDescription', '')),
                    str(row.get('Contractor', '')),
                    str(row.get('Province', '')),
                    str(row.get('Municipality', '')),
                    str(row.get('TypeofWork', '')),
                    str(int(row.get('InfraYear', 0))) if pd.notna(row.get('InfraYear')) else '',
                    str(float(row.get('ContractCost', 0))) if pd.notna(row.get('ContractCost')) else '0'
                ))

                # Metadata record
                metadata_records.append((
                    project_id,
                    float(row.get('Latitude', 0)) if pd.notna(row.get('Latitude')) else 0.0,
                    float(row.get('Longitude', 0)) if pd.notna(row.get('Longitude')) else 0.0,
                    str(row.get('Region', '')),
                    float(row.get('ContractCost', 0)) if pd.notna(row.get('ContractCost')) else 0.0,
                    int(row.get('InfraYear', 0)) if pd.notna(row.get('InfraYear')) else 0,
                    row.to_json()
                ))

            # Batch insert FTS
            self.conn.executemany("""
                INSERT INTO projects_fts VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, fts_records)

            # Batch insert metadata
            self.conn.executemany("""
                INSERT INTO projects_metadata VALUES (?, ?, ?, ?, ?, ?, ?)
            """, metadata_records)

            self.conn.commit()
            logger.info(f"✓ Indexed {len(fts_records)} projects")

        except Exception as e:
            logger.error(f"Failed to index projects: {e}")
            self.conn.rollback()
            raise

    def search(self, query: str, limit: int = 100, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Fast full-text search with optional filters

        Args:
            query: Search query (FTS5 syntax)
            limit: Max results
            filters: Optional filters (year, min_cost, max_cost, province)

        Returns:
            List of matching projects with rank scores
        """
        try:
            # Build WHERE clause for filters
            where_clauses = []
            params = [query]

            if filters:
                if 'year' in filters and filters['year']:
                    if isinstance(filters['year'], list):
                        placeholders = ','.join('?' * len(filters['year']))
                        where_clauses.append(f"m.infra_year IN ({placeholders})")
                        params.extend(filters['year'])
                    else:
                        where_clauses.append("m.infra_year = ?")
                        params.append(filters['year'])

                if 'min_cost' in filters and filters['min_cost']:
                    where_clauses.append("m.contract_cost >= ?")
                    params.append(filters['min_cost'])

                if 'max_cost' in filters and filters['max_cost']:
                    where_clauses.append("m.contract_cost <= ?")
                    params.append(filters['max_cost'])

                if 'province' in filters and filters['province']:
                    where_clauses.append("p.province = ?")
                    params.append(filters['province'])

            # Build SQL query
            where_sql = ""
            if where_clauses:
                where_sql = "AND " + " AND ".join(where_clauses)

            params.append(limit)

            sql = f"""
                SELECT
                    p.project_id,
                    p.description,
                    p.contractor,
                    p.province,
                    p.municipality,
                    p.type_of_work,
                    p.year,
                    m.contract_cost,
                    m.lat,
                    m.lon,
                    m.region,
                    m.full_data,
                    rank
                FROM projects_fts p
                JOIN projects_metadata m ON p.project_id = m.project_id
                WHERE projects_fts MATCH ?
                {where_sql}
                ORDER BY rank
                LIMIT ?
            """

            cursor = self.conn.execute(sql, params)

            results = []
            for row in cursor:
                try:
                    full_data = json.loads(row[11]) if row[11] else {}
                    results.append({
                        'project_id': row[0],
                        'description': row[1],
                        'contractor': row[2],
                        'province': row[3],
                        'municipality': row[4],
                        'type_of_work': row[5],
                        'year': row[6],
                        'cost': float(row[7]),
                        'lat': row[8],
                        'lon': row[9],
                        'region': row[10],
                        'full_data': full_data,
                        'rank': row[12]
                    })
                except Exception as e:
                    logger.warning(f"Error parsing result row: {e}")
                    continue

            logger.debug(f"Search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def search_by_prefix(self, field: str, prefix: str, limit: int = 10) -> List[str]:
        """
        Autocomplete search by field prefix

        Args:
            field: Field to search (contractor, province, municipality)
            prefix: Prefix to match
            limit: Max results

        Returns:
            List of matching values
        """
        try:
            # Map field names
            field_map = {
                'contractor': 'contractor',
                'province': 'province',
                'municipality': 'municipality',
                'type_of_work': 'type_of_work'
            }

            if field not in field_map:
                return []

            fts_field = field_map[field]

            # Use LIKE for prefix matching
            cursor = self.conn.execute(f"""
                SELECT DISTINCT {fts_field}
                FROM projects_fts
                WHERE {fts_field} LIKE ?
                LIMIT ?
            """, (f"{prefix}%", limit))

            return [row[0] for row in cursor if row[0]]

        except Exception as e:
            logger.error(f"Prefix search error: {e}")
            return []

    def get_stats(self) -> Dict:
        """Get index statistics"""
        try:
            # Total projects
            cursor = self.conn.execute("SELECT COUNT(*) FROM projects_fts")
            total = cursor.fetchone()[0]

            # Year distribution
            cursor = self.conn.execute("""
                SELECT infra_year, COUNT(*)
                FROM projects_metadata
                WHERE infra_year > 0
                GROUP BY infra_year
                ORDER BY infra_year DESC
                LIMIT 10
            """)
            year_dist = {row[0]: row[1] for row in cursor}

            # Cost stats
            cursor = self.conn.execute("""
                SELECT
                    MIN(contract_cost),
                    MAX(contract_cost),
                    AVG(contract_cost)
                FROM projects_metadata
                WHERE contract_cost > 0
            """)
            cost_stats = cursor.fetchone()

            return {
                'total_projects': total,
                'year_distribution': year_dist,
                'cost_range': {
                    'min': float(cost_stats[0]) if cost_stats[0] else 0,
                    'max': float(cost_stats[1]) if cost_stats[1] else 0,
                    'avg': float(cost_stats[2]) if cost_stats[2] else 0
                }
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def close(self):
        """Close database connection"""
        try:
            self.conn.close()
            logger.info("✓ SearchIndex connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
