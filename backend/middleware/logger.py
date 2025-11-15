"""Structured Request Logging & Analytics

Enhancement #30: Request Logging & Analytics
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class StructuredLogger:
    """
    JSON structured logging for analytics

    Enhancement #30: Request Logging
    Logs queries, errors, and performance metrics to separate JSON line files
    """

    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Separate log files
        self.query_log = self.log_dir / "queries.jsonl"
        self.error_log = self.log_dir / "errors.jsonl"
        self.performance_log = self.log_dir / "performance.jsonl"

        logger.info(f"✓ StructuredLogger initialized: {self.log_dir}")

    def log_query(self, session_id: str, query: str, intent: str,
                  result_count: int, duration_ms: float, user_agent: Optional[str] = None):
        """Log user query for analytics"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "query",
            "session_id": session_id,
            "query": query,
            "intent": intent,
            "result_count": result_count,
            "duration_ms": duration_ms,
            "user_agent": user_agent
        }

        try:
            with open(self.query_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to log query: {e}")

    def log_error(self, error_code: str, error_message: str,
                  session_id: Optional[str] = None, stack_trace: Optional[str] = None,
                  context: Optional[dict] = None):
        """Log error for debugging"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "error_code": error_code,
            "error_message": error_message,
            "session_id": session_id,
            "stack_trace": stack_trace,
            "context": context
        }

        try:
            with open(self.error_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to log error: {e}")

    def log_performance(self, endpoint: str, duration_ms: float,
                       cache_hit: bool = False, status_code: int = 200):
        """Log performance metrics"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "performance",
            "endpoint": endpoint,
            "duration_ms": duration_ms,
            "cache_hit": cache_hit,
            "status_code": status_code
        }

        try:
            with open(self.performance_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to log performance: {e}")

    def get_analytics(self, days: int = 7) -> dict:
        """Get analytics summary"""
        try:
            # Parse query log for analytics
            queries = []
            cutoff = datetime.now() - timedelta(days=days)

            if self.query_log.exists():
                with open(self.query_log, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if datetime.fromisoformat(entry['timestamp']) > cutoff:
                                queries.append(entry)
                        except:
                            continue

            # Calculate statistics
            total_queries = len(queries)
            avg_duration = sum(q.get('duration_ms', 0) for q in queries) / total_queries if total_queries > 0 else 0

            # Intent distribution
            intents = {}
            for q in queries:
                intent = q.get('intent', 'unknown')
                intents[intent] = intents.get(intent, 0) + 1

            # Parse error log
            errors = []
            if self.error_log.exists():
                with open(self.error_log, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if datetime.fromisoformat(entry['timestamp']) > cutoff:
                                errors.append(entry)
                        except:
                            continue

            # Error distribution
            error_codes = {}
            for e in errors:
                code = e.get('error_code', 'unknown')
                error_codes[code] = error_codes.get(code, 0) + 1

            # Parse performance log
            perf_metrics = []
            if self.performance_log.exists():
                with open(self.performance_log, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if datetime.fromisoformat(entry['timestamp']) > cutoff:
                                perf_metrics.append(entry)
                        except:
                            continue

            # Cache hit rate
            total_requests = len(perf_metrics)
            cache_hits = sum(1 for p in perf_metrics if p.get('cache_hit', False))
            cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0

            return {
                "date_range": f"Last {days} days",
                "queries": {
                    "total": total_queries,
                    "avg_duration_ms": round(avg_duration, 2),
                    "intent_distribution": intents
                },
                "errors": {
                    "total": len(errors),
                    "error_code_distribution": error_codes
                },
                "performance": {
                    "total_requests": total_requests,
                    "cache_hits": cache_hits,
                    "cache_hit_rate": round(cache_hit_rate * 100, 2)
                }
            }
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {"error": str(e)}

    def get_recent_errors(self, limit: int = 50) -> list:
        """Get recent errors"""
        try:
            errors = []
            if self.error_log.exists():
                with open(self.error_log, 'r') as f:
                    lines = f.readlines()
                    for line in reversed(lines[-limit:]):
                        try:
                            errors.append(json.loads(line))
                        except:
                            continue
            return errors
        except Exception as e:
            logger.error(f"Failed to get recent errors: {e}")
            return []

    def get_slow_queries(self, threshold_ms: float = 1000, limit: int = 20) -> list:
        """Get slow queries above threshold"""
        try:
            slow_queries = []
            if self.query_log.exists():
                with open(self.query_log, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if entry.get('duration_ms', 0) > threshold_ms:
                                slow_queries.append(entry)
                        except:
                            continue

            # Sort by duration, descending
            slow_queries.sort(key=lambda x: x.get('duration_ms', 0), reverse=True)
            return slow_queries[:limit]
        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []


# Global logger instance
structured_logger = StructuredLogger()
