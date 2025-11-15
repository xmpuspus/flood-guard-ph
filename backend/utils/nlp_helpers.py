"""NLP helper utilities for query processing"""
import re
from typing import Optional, Dict, List, Tuple
from difflib import SequenceMatcher


class QueryIntent:
    """Query intent classification"""
    SEARCH = "search"
    STATS = "stats"
    COMPARE = "compare"
    ANALYZE = "analyze"
    INFO = "info"
    GREETING = "greeting"


class NLPHelper:
    """Enhanced NLP utilities for better query understanding"""

    # Comprehensive location mapping with fuzzy matching support
    LOCATION_MAP = {
        # Provinces (full names and common variations)
        'bulacan': 'BULACAN', 'cebu': 'CEBU', 'isabela': 'ISABELA',
        'pangasinan': 'PANGASINAN', 'pampanga': 'PAMPANGA', 'albay': 'ALBAY',
        'leyte': 'LEYTE', 'tarlac': 'TARLAC', 'camarines sur': 'CAMARINES SUR',
        'cam sur': 'CAMARINES SUR', 'camsur': 'CAMARINES SUR',
        'ilocos norte': 'ILOCOS NORTE', 'ilocos norte': 'ILOCOS NORTE',
        'negros occidental': 'NEGROS OCCIDENTAL', 'negros occ': 'NEGROS OCCIDENTAL',
        'cavite': 'CAVITE', 'batangas': 'BATANGAS', 'rizal': 'RIZAL',
        'iloilo': 'ILOILO', 'cagayan': 'CAGAYAN', 'la union': 'LA UNION',
        'nueva ecija': 'NUEVA ECIJA', 'laguna': 'LAGUNA', 'ilocos sur': 'ILOCOS SUR',
        'quezon': 'QUEZON', 'sorsogon': 'SORSOGON', 'negros oriental': 'NEGROS ORIENTAL',
        'negros or': 'NEGROS ORIENTAL', 'bukidnon': 'BUKIDNON', 'abra': 'ABRA',
        'bataan': 'BATAAN', 'camarines norte': 'CAMARINES NORTE', 'cam norte': 'CAMARINES NORTE',
        'palawan': 'PALAWAN', 'oriental mindoro': 'ORIENTAL MINDORO',
        'occidental mindoro': 'OCCIDENTAL MINDORO',

        # Metro Manila cities
        'manila': 'CITY OF MANILA', 'quezon city': 'QUEZON CITY', 'qc': 'QUEZON CITY',
        'caloocan': 'CALOOCAN CITY', 'pasig': 'PASIG CITY', 'taguig': 'TAGUIG CITY',
        'malabon': 'MALABON CITY', 'navotas': 'NAVOTAS CITY', 'valenzuela': 'VALENZUELA CITY',
        'marikina': 'MARIKINA CITY', 'makati': 'MAKATI CITY', 'parañaque': 'PARAÑAQUE CITY',
        'paranaque': 'PARAÑAQUE CITY', 'las piñas': 'LAS PIÑAS CITY', 'las pinas': 'LAS PIÑAS CITY',
        'pasay': 'PASAY CITY', 'pateros': 'PATEROS', 'muntinlupa': 'MUNTINLUPA CITY',
        'san juan': 'SAN JUAN CITY', 'mandaluyong': 'MANDALUYONG CITY',

        # Metro Manila variations
        'metro manila': 'METRO_MANILA', 'ncr': 'METRO_MANILA',

        # Davao provinces
        'davao del sur': 'DAVAO DEL SUR', 'davao del norte': 'DAVAO DEL NORTE',
        'davao sur': 'DAVAO DEL SUR', 'davao norte': 'DAVAO DEL NORTE',
        'davao oriental': 'DAVAO ORIENTAL', 'davao occidental': 'DAVAO OCCIDENTAL',
        'davao de oro': 'DAVAO DE ORO', 'compostela valley': 'DAVAO DE ORO',

        # Mindanao provinces
        'misamis oriental': 'MISAMIS ORIENTAL', 'misamis occidental': 'MISAMIS OCCIDENTAL',
        'mis or': 'MISAMIS ORIENTAL', 'mis occ': 'MISAMIS OCCIDENTAL',
        'agusan del norte': 'AGUSAN DEL NORTE', 'agusan del sur': 'AGUSAN DEL SUR',
        'agusan norte': 'AGUSAN DEL NORTE', 'agusan sur': 'AGUSAN DEL SUR',
        'south cotabato': 'SOUTH COTABATO', 'sultan kudarat': 'SULTAN KUDARAT',
        'cotabato': 'COTABATO (NORTH COTABATO)', 'north cotabato': 'COTABATO (NORTH COTABATO)',
        'lanao del norte': 'LANAO DEL NORTE', 'lanao del sur': 'LANAO DEL SUR',
        'zamboanga del sur': 'ZAMBOANGA DEL SUR', 'zamboanga del norte': 'ZAMBOANGA DEL NORTE',
        'zamboanga sibugay': 'ZAMBOANGA SIBUGAY', 'zam sur': 'ZAMBOANGA DEL SUR',
        'surigao del norte': 'SURIGAO DEL NORTE', 'surigao del sur': 'SURIGAO DEL SUR',
        'maguindanao': 'MAGUINDANAO DEL SUR', 'basilan': 'BASILAN',
        'dinagat islands': 'DINAGAT ISLANDS', 'camiguin': 'CAMIGUIN',

        # Visayas
        'bohol': 'BOHOL', 'biliran': 'BILIRAN', 'samar': 'SAMAR (WESTERN SAMAR)',
        'western samar': 'SAMAR (WESTERN SAMAR)', 'southern leyte': 'SOUTHERN LEYTE',
        'northern samar': 'NORTHERN SAMAR', 'eastern samar': 'EASTERN SAMAR',
        'aklan': 'AKLAN', 'antique': 'ANTIQUE', 'capiz': 'CAPIZ', 'guimaras': 'GUIMARAS',
        'romblon': 'ROMBLON', 'masbate': 'MASBATE', 'siquijor': 'SIQUIJOR',

        # CAR & Northern Luzon
        'nueva vizcaya': 'NUEVA VIZCAYA', 'benguet': 'BENGUET', 'baguio': 'BENGUET',
        'kalinga': 'KALINGA', 'mountain province': 'MOUNTAIN PROVINCE',
        'apayao': 'APAYAO', 'ifugao': 'IFUGAO', 'aurora': 'AURORA',
        'zambales': 'ZAMBALES', 'marinduque': 'MARINDUQUE', 'catanduanes': 'CATANDUANES',
        'batanes': 'BATANES', 'quirino': 'QUIRINO', 'sarangani': 'SARANGANI', 'sulu': 'SULU'
    }

    @staticmethod
    def fuzzy_match_location(query: str, threshold: float = 0.6) -> Optional[str]:
        """Fuzzy match location with similarity threshold"""
        query_lower = query.lower()

        # Try exact match first (sorted by length for multi-word matches)
        for location_key in sorted(NLPHelper.LOCATION_MAP.keys(), key=len, reverse=True):
            if location_key in query_lower:
                return NLPHelper.LOCATION_MAP[location_key]

        # Try fuzzy matching if no exact match
        best_match = None
        best_ratio = threshold

        for location_key, location_value in NLPHelper.LOCATION_MAP.items():
            # Check if query contains partial match
            for word in query_lower.split():
                if len(word) < 3:  # Skip very short words
                    continue
                ratio = SequenceMatcher(None, word, location_key).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = location_value

        return best_match

    @staticmethod
    def extract_budget(query: str) -> Optional[Dict[str, float]]:
        """Extract budget amounts with multiple pattern support"""
        query_lower = query.lower()

        patterns = [
            # "15 million", "15M", "15 m"
            (r'(\d+(?:\.\d+)?)\s*(?:million|m)(?:\s+php|₱)?', 1_000_000),
            # "₱15,000,000", "P 15,000,000"
            (r'[₱p]\s*(\d+(?:,\d{3})*(?:\.\d+)?)', 1),
            # "15000000" (raw number > 100k treated as full amount)
            (r'(\d{6,})(?!\s*(?:million|m|k))', 1),
            # "15k", "15 thousand"
            (r'(\d+(?:\.\d+)?)\s*(?:thousand|k)', 1_000),
            # "over X", "above X", "more than X"
            (r'(?:over|above|more than|greater than|>\s*)(\d+(?:\.\d+)?)\s*(?:million|m)', 1_000_000),
            # "under X", "below X", "less than X"
            (r'(?:under|below|less than|<\s*)(\d+(?:\.\d+)?)\s*(?:million|m)', 1_000_000),
        ]

        result = {}

        for pattern, multiplier in patterns:
            match = re.search(pattern, query_lower)
            if match:
                amount = float(match.group(1).replace(',', '')) * multiplier

                # Determine if it's min or max based on keywords
                if any(kw in query_lower for kw in ['over', 'above', 'more than', 'greater', '>']):
                    result['min'] = amount
                elif any(kw in query_lower for kw in ['under', 'below', 'less than', '<']):
                    result['max'] = amount
                else:
                    # Default to minimum threshold
                    result['min'] = amount

                break

        return result if result else None

    @staticmethod
    def extract_year(query: str) -> Optional[List[int]]:
        """Extract years from query"""
        years = []
        for year in range(2020, 2026):  # 2020-2025
            if str(year) in query:
                years.append(year)
        return years if years else None

    @staticmethod
    def extract_contractor(query: str) -> Optional[str]:
        """Extract contractor name from query"""
        query_lower = query.lower()

        # Common contractor patterns
        contractor_patterns = [
            'ged', 'azarraga', 'big bertha', 'bertha',
            'construction', 'contractor', 'builders'
        ]

        for pattern in contractor_patterns:
            if pattern in query_lower:
                # Extract the full contractor name
                if 'ged' in query_lower:
                    return 'GED'
                elif 'azarraga' in query_lower:
                    return 'AZARRAGA'
                elif 'bertha' in query_lower or 'big bertha' in query_lower:
                    return 'BIG BERTHA'

        # Try to extract capitalized words after "contractor" or "by"
        contractor_match = re.search(r'(?:contractor|by|from)\s+([A-Z][A-Za-z\s]+)', query)
        if contractor_match:
            return contractor_match.group(1).strip().upper()

        return None

    @staticmethod
    def classify_intent(query: str) -> str:
        """Classify query intent"""
        query_lower = query.lower()

        # Greetings
        greeting_keywords = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        if any(kw in query_lower for kw in greeting_keywords):
            return QueryIntent.GREETING

        # Search queries
        search_keywords = ['show', 'find', 'search', 'get', 'list', 'display', 'where', 'which']
        if any(kw in query_lower for kw in search_keywords):
            return QueryIntent.SEARCH

        # Stats queries
        stats_keywords = ['total', 'how many', 'count', 'sum', 'average', 'statistics', 'stats']
        if any(kw in query_lower for kw in stats_keywords):
            return QueryIntent.STATS

        # Compare queries
        compare_keywords = ['compare', 'difference', 'versus', 'vs', 'between']
        if any(kw in query_lower for kw in compare_keywords):
            return QueryIntent.COMPARE

        # Analyze queries
        analyze_keywords = ['analyze', 'analysis', 'trends', 'pattern', 'why', 'how']
        if any(kw in query_lower for kw in analyze_keywords):
            return QueryIntent.ANALYZE

        # Info queries
        info_keywords = ['what is', 'tell me about', 'explain', 'describe', 'info', 'information']
        if any(kw in query_lower for kw in info_keywords):
            return QueryIntent.INFO

        # Default to search
        return QueryIntent.SEARCH

    @staticmethod
    def extract_entities(query: str) -> Dict:
        """Extract all entities from query"""
        return {
            'location': NLPHelper.fuzzy_match_location(query),
            'budget': NLPHelper.extract_budget(query),
            'years': NLPHelper.extract_year(query),
            'contractor': NLPHelper.extract_contractor(query),
            'intent': NLPHelper.classify_intent(query)
        }

    @staticmethod
    def calculate_confidence(query: str, entities: Dict) -> float:
        """Calculate confidence score for query understanding"""
        confidence = 0.5  # Base confidence

        # Boost confidence based on extracted entities
        if entities.get('location'):
            confidence += 0.15
        if entities.get('budget'):
            confidence += 0.1
        if entities.get('years'):
            confidence += 0.1
        if entities.get('contractor'):
            confidence += 0.15

        # Penalize very short or very long queries
        word_count = len(query.split())
        if word_count < 3:
            confidence -= 0.1
        elif word_count > 50:
            confidence -= 0.1

        return min(1.0, max(0.0, confidence))
