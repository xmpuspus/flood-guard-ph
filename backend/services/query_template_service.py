"""Query Template Service

Enhancement #37: Query Templates
Pre-built query templates for common searches
"""
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class QueryTemplateService:
    """
    Manage and populate query templates

    Enhancement #37: Query Templates
    Provides pre-built queries that users can customize
    """

    def __init__(self, templates_file: str = "./backend/templates/query_templates.json"):
        self.templates_file = Path(templates_file)
        self.templates = self._load_templates()
        logger.info(f"✓ QueryTemplateService initialized with {len(self.templates)} templates")

    def _load_templates(self) -> List[Dict]:
        """Load query templates from JSON file"""
        try:
            if not self.templates_file.exists():
                logger.warning(f"Templates file not found: {self.templates_file}")
                return []

            with open(self.templates_file, 'r') as f:
                data = json.load(f)
                return data.get('templates', [])

        except Exception as e:
            logger.error(f"Failed to load query templates: {e}")
            return []

    def get_all_templates(self) -> List[Dict]:
        """Get all available templates"""
        return self.templates

    def get_template_by_id(self, template_id: str) -> Optional[Dict]:
        """Get a specific template by ID"""
        for template in self.templates:
            if template.get('id') == template_id:
                return template
        return None

    def get_templates_by_category(self, category: str) -> List[Dict]:
        """Get templates filtered by category"""
        return [t for t in self.templates if t.get('category') == category]

    def populate_template(self, template_id: str, params: Dict) -> Optional[str]:
        """
        Populate a template with user-provided parameters

        Args:
            template_id: ID of the template
            params: Dictionary of parameter values

        Returns:
            Populated query string or None if template not found
        """
        template = self.get_template_by_id(template_id)

        if not template:
            logger.warning(f"Template not found: {template_id}")
            return None

        try:
            # Get query string
            query = template.get('query', '')

            # Validate required params
            template_params = template.get('params', [])
            required_params = [p['name'] for p in template_params if p.get('required', False)]

            missing_params = [p for p in required_params if p not in params]
            if missing_params:
                logger.warning(f"Missing required parameters: {missing_params}")
                return None

            # Populate template
            for param_name, param_value in params.items():
                placeholder = f"{{{param_name}}}"
                if placeholder in query:
                    query = query.replace(placeholder, str(param_value))

            # Check if all placeholders were replaced
            if '{' in query and '}' in query:
                logger.warning(f"Some placeholders not replaced in query: {query}")

            return query

        except Exception as e:
            logger.error(f"Failed to populate template {template_id}: {e}")
            return None

    def suggest_templates(self, user_query: str, max_suggestions: int = 5) -> List[Dict]:
        """
        Suggest relevant templates based on user query

        Args:
            user_query: User's natural language query
            max_suggestions: Maximum number of suggestions

        Returns:
            List of relevant templates with relevance scores
        """
        try:
            query_lower = user_query.lower()
            suggestions = []

            for template in self.templates:
                score = 0

                # Check template name
                if any(word in template.get('name', '').lower() for word in query_lower.split()):
                    score += 2

                # Check description
                if any(word in template.get('description', '').lower() for word in query_lower.split()):
                    score += 1

                # Check query pattern
                if any(word in template.get('query', '').lower() for word in query_lower.split()):
                    score += 1

                # Keyword matching
                keywords = {
                    'contractor': ['contractor', 'company', 'builder'],
                    'budget': ['budget', 'cost', 'money', 'million', 'expensive'],
                    'region': ['region', 'regional'],
                    'province': ['province'],
                    'municipality': ['municipality', 'city', 'town'],
                    'compare': ['compare', 'comparison', 'vs', 'versus'],
                    'trend': ['trend', 'over time', 'yearly', 'growth'],
                    'top': ['top', 'best', 'highest', 'largest']
                }

                for keyword, synonyms in keywords.items():
                    if any(syn in query_lower for syn in synonyms):
                        template_text = (template.get('name', '') + ' ' +
                                       template.get('description', '') + ' ' +
                                       template.get('category', '')).lower()
                        if keyword in template_text:
                            score += 3

                if score > 0:
                    suggestions.append({
                        'template': template,
                        'relevance_score': score
                    })

            # Sort by relevance
            suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)

            return suggestions[:max_suggestions]

        except Exception as e:
            logger.error(f"Failed to suggest templates: {e}")
            return []

    def get_categories(self) -> List[str]:
        """Get list of unique categories"""
        categories = set()
        for template in self.templates:
            if 'category' in template:
                categories.add(template['category'])
        return sorted(list(categories))

    def validate_params(self, template_id: str, params: Dict) -> Dict:
        """
        Validate parameters for a template

        Args:
            template_id: ID of the template
            params: Parameters to validate

        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        template = self.get_template_by_id(template_id)

        if not template:
            return {
                'valid': False,
                'errors': [f"Template '{template_id}' not found"]
            }

        errors = []
        template_params = template.get('params', [])

        # Check required params
        for param_def in template_params:
            param_name = param_def.get('name')
            required = param_def.get('required', False)

            if required and param_name not in params:
                errors.append(f"Missing required parameter: {param_name}")
                continue

            if param_name in params:
                # Type validation
                param_type = param_def.get('type', 'string')
                param_value = params[param_name]

                if param_type == 'integer':
                    try:
                        int(param_value)
                    except (ValueError, TypeError):
                        errors.append(f"Parameter '{param_name}' must be an integer")

                elif param_type == 'number':
                    try:
                        float(param_value)
                    except (ValueError, TypeError):
                        errors.append(f"Parameter '{param_name}' must be a number")

                elif param_type == 'string':
                    if not isinstance(param_value, str) or not param_value.strip():
                        errors.append(f"Parameter '{param_name}' must be a non-empty string")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def get_param_info(self, template_id: str) -> Optional[List[Dict]]:
        """Get parameter definitions for a template"""
        template = self.get_template_by_id(template_id)
        if template:
            return template.get('params', [])
        return None
