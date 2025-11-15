"""Predictive Analytics Service

Enhancement #36: Predictive Analytics
Forecast project completion and budget trends
"""
import logging
from typing import Dict, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class PredictiveAnalytics:
    """
    Forecast budget trends and project patterns

    Enhancement #36: Predictive Analytics
    Uses simple linear regression for trend forecasting
    """

    def __init__(self):
        logger.info("✓ PredictiveAnalytics initialized")

    def predict_budget_trends(self, df: pd.DataFrame, forecast_years: int = 2) -> Dict:
        """
        Predict budget trends for future years

        Args:
            df: DataFrame with project data
            forecast_years: Number of years to forecast

        Returns:
            Dict with historical data, predictions, and trend analysis
        """
        try:
            # Filter valid data
            valid_df = df[
                (df['InfraYear'].notna()) &
                (df['InfraYear'] > 0) &
                (df['ContractCost'].notna()) &
                (df['ContractCost'] > 0)
            ].copy()

            if len(valid_df) == 0:
                return {'error': 'No valid data for prediction'}

            # Group by year
            yearly = valid_df.groupby('InfraYear').agg({
                'ContractCost': 'sum',
                'ProjectComponentID': 'count'
            }).reset_index()

            yearly.columns = ['year', 'total_budget', 'project_count']
            yearly = yearly.sort_values('year')

            if len(yearly) < 2:
                return {'error': 'Insufficient historical data (need at least 2 years)'}

            # Fit simple linear regression manually
            X = yearly['year'].values
            y = yearly['total_budget'].values

            # Calculate coefficients
            x_mean = np.mean(X)
            y_mean = np.mean(y)

            numerator = np.sum((X - x_mean) * (y - y_mean))
            denominator = np.sum((X - x_mean) ** 2)

            if denominator == 0:
                return {'error': 'Cannot fit trend (insufficient variance)'}

            slope = numerator / denominator
            intercept = y_mean - slope * x_mean

            # Calculate R-squared
            y_pred_historical = slope * X + intercept
            ss_res = np.sum((y - y_pred_historical) ** 2)
            ss_tot = np.sum((y - y_mean) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            # Predict future years
            last_year = int(yearly['year'].max())
            future_years = np.arange(last_year + 1, last_year + forecast_years + 1)
            predictions_values = slope * future_years + intercept

            predictions = []
            for year, budget in zip(future_years, predictions_values):
                # Estimate project count based on average
                avg_budget_per_project = yearly['total_budget'].sum() / yearly['project_count'].sum()
                estimated_projects = int(budget / avg_budget_per_project) if avg_budget_per_project > 0 else 0

                predictions.append({
                    'year': int(year),
                    'predicted_budget': float(budget),
                    'estimated_projects': estimated_projects,
                    'confidence': 'high' if r_squared > 0.7 else 'medium' if r_squared > 0.4 else 'low'
                })

            # Trend analysis
            trend = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
            annual_change = slope
            pct_change = (slope / y_mean * 100) if y_mean != 0 else 0

            return {
                'historical': yearly.to_dict('records'),
                'predictions': predictions,
                'trend': {
                    'direction': trend,
                    'annual_change': float(annual_change),
                    'annual_change_pct': round(pct_change, 2),
                    'r_squared': round(r_squared, 3),
                    'confidence': 'high' if r_squared > 0.7 else 'medium' if r_squared > 0.4 else 'low'
                },
                'insights': self._generate_insights(trend, annual_change, r_squared, yearly)
            }

        except Exception as e:
            logger.error(f"Budget trend prediction failed: {e}")
            return {'error': str(e)}

    def predict_contractor_trends(self, df: pd.DataFrame, top_n: int = 10) -> List[Dict]:
        """
        Analyze contractor trends over time

        Args:
            df: DataFrame with project data
            top_n: Number of top contractors to analyze

        Returns:
            List of contractor trend analyses
        """
        try:
            valid_df = df[
                (df['InfraYear'].notna()) &
                (df['InfraYear'] > 0) &
                (df['Contractor'].notna()) &
                (df['Contractor'] != '')
            ].copy()

            if len(valid_df) == 0:
                return []

            # Get top contractors by total budget
            top_contractors = valid_df.groupby('Contractor')['ContractCost'].sum().nlargest(top_n).index

            trends = []
            for contractor in top_contractors:
                contractor_df = valid_df[valid_df['Contractor'] == contractor]

                # Yearly aggregation
                yearly = contractor_df.groupby('InfraYear').agg({
                    'ContractCost': 'sum',
                    'ProjectComponentID': 'count'
                }).reset_index()

                if len(yearly) < 2:
                    continue

                # Calculate trend
                X = yearly['InfraYear'].values
                y = yearly['ContractCost'].values

                x_mean = np.mean(X)
                y_mean = np.mean(y)

                numerator = np.sum((X - x_mean) * (y - y_mean))
                denominator = np.sum((X - x_mean) ** 2)

                if denominator == 0:
                    continue

                slope = numerator / denominator

                trends.append({
                    'contractor': str(contractor),
                    'total_budget': float(contractor_df['ContractCost'].sum()),
                    'total_projects': int(len(contractor_df)),
                    'years_active': int(len(yearly)),
                    'trend': 'increasing' if slope > 0 else 'decreasing',
                    'annual_change': float(slope),
                    'first_year': int(yearly['InfraYear'].min()),
                    'last_year': int(yearly['InfraYear'].max())
                })

            # Sort by total budget
            trends.sort(key=lambda x: x['total_budget'], reverse=True)

            return trends

        except Exception as e:
            logger.error(f"Contractor trend prediction failed: {e}")
            return []

    def predict_regional_growth(self, df: pd.DataFrame) -> List[Dict]:
        """
        Predict regional growth patterns

        Args:
            df: DataFrame with project data

        Returns:
            List of regional predictions
        """
        try:
            valid_df = df[
                (df['InfraYear'].notna()) &
                (df['InfraYear'] > 0) &
                (df['Region'].notna()) &
                (df['ContractCost'].notna()) &
                (df['ContractCost'] > 0)
            ].copy()

            if len(valid_df) == 0:
                return []

            regions = valid_df['Region'].unique()
            regional_predictions = []

            for region in regions:
                region_df = valid_df[valid_df['Region'] == region]

                # Yearly aggregation
                yearly = region_df.groupby('InfraYear')['ContractCost'].sum()

                if len(yearly) < 2:
                    continue

                # Calculate trend
                X = yearly.index.values
                y = yearly.values

                x_mean = np.mean(X)
                y_mean = np.mean(y)

                numerator = np.sum((X - x_mean) * (y - y_mean))
                denominator = np.sum((X - x_mean) ** 2)

                if denominator == 0:
                    continue

                slope = numerator / denominator

                # Predict next year
                last_year = int(yearly.index.max())
                next_year_budget = slope * (last_year + 1) + (y_mean - slope * x_mean)

                regional_predictions.append({
                    'region': str(region),
                    'current_year': last_year,
                    'current_budget': float(yearly.iloc[-1]),
                    'predicted_next_year': last_year + 1,
                    'predicted_budget': float(max(0, next_year_budget)),  # Don't predict negative
                    'trend': 'growth' if slope > 0 else 'decline',
                    'change_pct': round((slope / y_mean * 100), 2) if y_mean != 0 else 0
                })

            # Sort by predicted budget
            regional_predictions.sort(key=lambda x: x['predicted_budget'], reverse=True)

            return regional_predictions

        except Exception as e:
            logger.error(f"Regional growth prediction failed: {e}")
            return []

    def _generate_insights(self, trend: str, annual_change: float, r_squared: float, yearly_df: pd.DataFrame) -> List[str]:
        """Generate human-readable insights from trend analysis"""
        insights = []

        try:
            # Trend insight
            if trend == 'increasing':
                insights.append(f"Budget is increasing at ₱{abs(annual_change):,.0f} per year")
            elif trend == 'decreasing':
                insights.append(f"Budget is decreasing at ₱{abs(annual_change):,.0f} per year")
            else:
                insights.append("Budget remains relatively stable year-over-year")

            # Confidence insight
            if r_squared > 0.7:
                insights.append("High confidence in predictions (strong historical pattern)")
            elif r_squared > 0.4:
                insights.append("Medium confidence in predictions (moderate historical pattern)")
            else:
                insights.append("Low confidence in predictions (weak historical pattern)")

            # Growth rate insight
            avg_budget = yearly_df['total_budget'].mean()
            if avg_budget > 0:
                growth_rate = (annual_change / avg_budget) * 100
                if abs(growth_rate) > 10:
                    insights.append(f"Annual growth rate of {growth_rate:+.1f}% is significant")

            # Volatility insight
            std_budget = yearly_df['total_budget'].std()
            cv = (std_budget / avg_budget) if avg_budget > 0 else 0
            if cv > 0.3:
                insights.append("High budget volatility detected across years")

        except Exception as e:
            logger.warning(f"Failed to generate insights: {e}")

        return insights
