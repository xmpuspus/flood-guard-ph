"""Anomaly Detection Service

Enhancement #35: Anomaly Detection
Flags unusual patterns in project data for investigative purposes
"""
import logging
from typing import List, Dict
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detect anomalies and unusual patterns in project data

    Enhancement #35: Anomaly Detection
    """

    def __init__(self):
        logger.info("✓ AnomalyDetector initialized")

    def detect_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect various anomalies in project data

        Returns:
            List of anomaly reports with severity levels
        """
        anomalies = []

        try:
            # 1. Unusual cost (> 3 standard deviations from mean)
            cost_anomalies = self._detect_cost_anomalies(df)
            anomalies.extend(cost_anomalies)

            # 2. Contractor concentration
            contractor_anomalies = self._detect_contractor_concentration(df)
            anomalies.extend(contractor_anomalies)

            # 3. Geographic concentration
            geo_anomalies = self._detect_geographic_concentration(df)
            anomalies.extend(geo_anomalies)

            # 4. Temporal anomalies (unusual project counts in specific years)
            temporal_anomalies = self._detect_temporal_anomalies(df)
            anomalies.extend(temporal_anomalies)

            # 5. Missing critical data
            data_quality_issues = self._detect_data_quality_issues(df)
            anomalies.extend(data_quality_issues)

            logger.info(f"Detected {len(anomalies)} anomalies")
            return anomalies

        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return []

    def _detect_cost_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Detect projects with unusually high or low costs"""
        anomalies = []

        try:
            # Filter valid costs
            valid_costs = df[df['ContractCost'] > 0]['ContractCost']

            if len(valid_costs) == 0:
                return anomalies

            mean_cost = valid_costs.mean()
            std_cost = valid_costs.std()

            # High cost threshold (3 standard deviations)
            high_threshold = mean_cost + (3 * std_cost)

            # Low cost threshold (projects with suspiciously low costs)
            low_threshold = mean_cost * 0.01  # 1% of mean

            # High cost anomalies
            unusual_high = df[df['ContractCost'] > high_threshold]
            for _, row in unusual_high.iterrows():
                sigma = (row['ContractCost'] - mean_cost) / std_cost if std_cost > 0 else 0
                anomalies.append({
                    'type': 'unusual_high_cost',
                    'project_id': str(row.get('ProjectComponentID', '')),
                    'contractor': str(row.get('Contractor', '')),
                    'cost': float(row['ContractCost']),
                    'severity': 'high',
                    'message': f"Cost ₱{row['ContractCost']:,.0f} is {sigma:.1f}σ above average (avg: ₱{mean_cost:,.0f})",
                    'details': {
                        'province': str(row.get('Province', '')),
                        'year': int(row.get('InfraYear', 0)) if pd.notna(row.get('InfraYear')) else None
                    }
                })

            # Low cost anomalies (suspiciously cheap)
            unusual_low = df[(df['ContractCost'] > 0) & (df['ContractCost'] < low_threshold)]
            for _, row in unusual_low.iterrows():
                anomalies.append({
                    'type': 'unusual_low_cost',
                    'project_id': str(row.get('ProjectComponentID', '')),
                    'contractor': str(row.get('Contractor', '')),
                    'cost': float(row['ContractCost']),
                    'severity': 'medium',
                    'message': f"Cost ₱{row['ContractCost']:,.0f} is unusually low (avg: ₱{mean_cost:,.0f})",
                    'details': {
                        'province': str(row.get('Province', '')),
                        'year': int(row.get('InfraYear', 0)) if pd.notna(row.get('InfraYear')) else None
                    }
                })

        except Exception as e:
            logger.warning(f"Cost anomaly detection failed: {e}")

        return anomalies

    def _detect_contractor_concentration(self, df: pd.DataFrame) -> List[Dict]:
        """Detect contractors with unusually high project concentration"""
        anomalies = []

        try:
            contractor_counts = df['Contractor'].value_counts()
            total_projects = len(df)

            for contractor, count in contractor_counts.items():
                pct = count / total_projects * 100

                # Flag if contractor has > 20% of all projects
                if pct > 20:
                    anomalies.append({
                        'type': 'contractor_concentration',
                        'contractor': str(contractor),
                        'project_count': int(count),
                        'percentage': round(pct, 2),
                        'severity': 'high' if pct > 30 else 'medium',
                        'message': f"{contractor} has {pct:.1f}% of all projects ({count} projects)",
                        'details': {
                            'total_projects': total_projects
                        }
                    })

                # Flag if contractor has > 10% but specific to one province
                elif pct > 10:
                    contractor_df = df[df['Contractor'] == contractor]
                    province_dist = contractor_df['Province'].value_counts()
                    top_province_pct = (province_dist.iloc[0] / len(contractor_df) * 100) if len(province_dist) > 0 else 0

                    if top_province_pct > 80:
                        anomalies.append({
                            'type': 'contractor_geographic_concentration',
                            'contractor': str(contractor),
                            'province': str(province_dist.index[0]),
                            'project_count': int(count),
                            'severity': 'low',
                            'message': f"{contractor} has {count} projects, {top_province_pct:.0f}% in {province_dist.index[0]}",
                            'details': {
                                'concentration_percentage': round(top_province_pct, 2)
                            }
                        })

        except Exception as e:
            logger.warning(f"Contractor concentration detection failed: {e}")

        return anomalies

    def _detect_geographic_concentration(self, df: pd.DataFrame) -> List[Dict]:
        """Detect unusual geographic concentration of projects or budgets"""
        anomalies = []

        try:
            # Province-level budget concentration
            province_budgets = df.groupby('Province')['ContractCost'].sum()
            total_budget = province_budgets.sum()

            for province, budget in province_budgets.items():
                pct = budget / total_budget * 100 if total_budget > 0 else 0

                # Flag if province has > 30% of total budget
                if pct > 30:
                    project_count = len(df[df['Province'] == province])
                    anomalies.append({
                        'type': 'geographic_budget_concentration',
                        'province': str(province),
                        'total_budget': float(budget),
                        'percentage': round(pct, 2),
                        'project_count': int(project_count),
                        'severity': 'medium',
                        'message': f"{province} has {pct:.1f}% of total budget (₱{budget:,.0f})",
                        'details': {
                            'total_national_budget': float(total_budget)
                        }
                    })

        except Exception as e:
            logger.warning(f"Geographic concentration detection failed: {e}")

        return anomalies

    def _detect_temporal_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Detect unusual patterns in project counts over time"""
        anomalies = []

        try:
            yearly_counts = df.groupby('InfraYear').size()

            if len(yearly_counts) < 3:
                return anomalies

            mean_count = yearly_counts.mean()
            std_count = yearly_counts.std()

            for year, count in yearly_counts.items():
                if pd.notna(year) and year > 0:
                    sigma = (count - mean_count) / std_count if std_count > 0 else 0

                    # Flag years with unusual project counts
                    if abs(sigma) > 2:
                        anomalies.append({
                            'type': 'temporal_anomaly',
                            'year': int(year),
                            'project_count': int(count),
                            'severity': 'low',
                            'message': f"Year {int(year)} has {count} projects ({sigma:+.1f}σ from average {mean_count:.0f})",
                            'details': {
                                'deviation': round(sigma, 2),
                                'average_count': round(mean_count, 1)
                            }
                        })

        except Exception as e:
            logger.warning(f"Temporal anomaly detection failed: {e}")

        return anomalies

    def _detect_data_quality_issues(self, df: pd.DataFrame) -> List[Dict]:
        """Detect data quality issues like missing critical fields"""
        anomalies = []

        try:
            total = len(df)

            # Missing coordinates
            missing_coords = df[(df['Latitude'].isna()) | (df['Longitude'].isna())]
            if len(missing_coords) > 0:
                pct = len(missing_coords) / total * 100
                anomalies.append({
                    'type': 'data_quality_missing_coords',
                    'count': len(missing_coords),
                    'percentage': round(pct, 2),
                    'severity': 'medium' if pct > 10 else 'low',
                    'message': f"{len(missing_coords)} projects ({pct:.1f}%) missing coordinates",
                    'details': {
                        'total_projects': total
                    }
                })

            # Missing contractor info
            missing_contractor = df[df['Contractor'].isna() | (df['Contractor'] == '')]
            if len(missing_contractor) > 0:
                pct = len(missing_contractor) / total * 100
                anomalies.append({
                    'type': 'data_quality_missing_contractor',
                    'count': len(missing_contractor),
                    'percentage': round(pct, 2),
                    'severity': 'low',
                    'message': f"{len(missing_contractor)} projects ({pct:.1f}%) missing contractor info",
                    'details': {
                        'total_projects': total
                    }
                })

            # Zero or missing cost
            missing_cost = df[(df['ContractCost'].isna()) | (df['ContractCost'] <= 0)]
            if len(missing_cost) > 0:
                pct = len(missing_cost) / total * 100
                anomalies.append({
                    'type': 'data_quality_missing_cost',
                    'count': len(missing_cost),
                    'percentage': round(pct, 2),
                    'severity': 'high' if pct > 5 else 'medium',
                    'message': f"{len(missing_cost)} projects ({pct:.1f}%) with missing or zero cost",
                    'details': {
                        'total_projects': total
                    }
                })

        except Exception as e:
            logger.warning(f"Data quality detection failed: {e}")

        return anomalies

    def get_summary(self, anomalies: List[Dict]) -> Dict:
        """Get summary statistics of detected anomalies"""
        try:
            by_severity = {'high': 0, 'medium': 0, 'low': 0}
            by_type = {}

            for anomaly in anomalies:
                severity = anomaly.get('severity', 'low')
                anom_type = anomaly.get('type', 'unknown')

                by_severity[severity] = by_severity.get(severity, 0) + 1
                by_type[anom_type] = by_type.get(anom_type, 0) + 1

            return {
                'total_anomalies': len(anomalies),
                'by_severity': by_severity,
                'by_type': by_type,
                'high_priority_count': by_severity.get('high', 0)
            }
        except Exception as e:
            logger.error(f"Failed to generate anomaly summary: {e}")
            return {}
