"""Session Storage Service

Enhancement #20: Context Persistence
"""
import json
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class SessionStore:
    """
    Persistent session storage using file system

    Enhancement #20: Context Persistence
    In production, use Redis or PostgreSQL for distributed systems
    """

    def __init__(self, storage_dir: str = "./sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.session_ttl = timedelta(hours=24)
        logger.info(f"✓ SessionStore initialized: {self.storage_dir}")

    def save_session(self, session_id: str, data: Dict):
        """Save session data to disk"""
        try:
            session_file = self.storage_dir / f"{session_id}.json"

            session_data = {
                "session_id": session_id,
                "data": data,
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat()
            }

            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)

            logger.debug(f"Session saved: {session_id}")
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")

    def load_session(self, session_id: str) -> Optional[Dict]:
        """Load session data from disk"""
        try:
            session_file = self.storage_dir / f"{session_id}.json"

            if not session_file.exists():
                logger.debug(f"Session not found: {session_id}")
                return None

            with open(session_file, 'r') as f:
                session_data = json.load(f)

            # Check if expired
            last_accessed = datetime.fromisoformat(session_data["last_accessed"])
            if datetime.now() - last_accessed > self.session_ttl:
                # Expired, delete
                logger.info(f"Session expired: {session_id}")
                session_file.unlink()
                return None

            # Update last accessed
            session_data["last_accessed"] = datetime.now().isoformat()
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)

            logger.debug(f"Session loaded: {session_id}")
            return session_data["data"]

        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def delete_session(self, session_id: str):
        """Delete session"""
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                logger.info(f"Session deleted: {session_id}")
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")

    def cleanup_expired(self):
        """Remove expired sessions"""
        cleaned_count = 0
        try:
            for session_file in self.storage_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)

                    last_accessed = datetime.fromisoformat(session_data["last_accessed"])
                    if datetime.now() - last_accessed > self.session_ttl:
                        session_file.unlink()
                        cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Error cleaning session {session_file}: {e}")
                    continue

            if cleaned_count > 0:
                logger.info(f"Cleaned {cleaned_count} expired sessions")
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")

    def get_active_sessions_count(self) -> int:
        """Get count of active (non-expired) sessions"""
        count = 0
        try:
            for session_file in self.storage_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    last_accessed = datetime.fromisoformat(session_data["last_accessed"])
                    if datetime.now() - last_accessed <= self.session_ttl:
                        count += 1
                except:
                    continue
        except:
            pass
        return count

    def update_session_data(self, session_id: str, key: str, value):
        """Update specific key in session data"""
        try:
            session_data = self.load_session(session_id)
            if session_data is None:
                session_data = {}

            session_data[key] = value
            self.save_session(session_id, session_data)
            logger.debug(f"Session {session_id} updated: {key}")
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
