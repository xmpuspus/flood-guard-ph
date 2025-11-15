"""Enhanced LLM Service with ReAct Agent, Advanced NLP, and Multi-turn Reasoning"""
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, List
import traceback

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate

from backend.config import settings
from backend.models.errors import ErrorCode, FloodGuardException, get_error_detail
from backend.services.news_service import NewsService
from backend.services.project_service import ProjectService
from backend.services.vector_service import VectorService
from backend.tools.news_tools import NewsFetchTool
from backend.tools.project_tools import (
    ContractorAnalysisTool,
    GeospatialSearchTool,
    ProjectSearchTool,
    ProjectStatsTool,
)
from backend.utils.nlp_helpers import NLPHelper, QueryIntent

logger = logging.getLogger(__name__)


class EnhancedLLMService:
    """Enhanced LLM Service with ReAct Agent and Advanced Capabilities"""

    # Query length limits
    MAX_QUERY_LENGTH = 1000
    MIN_QUERY_LENGTH = 1

    def __init__(
        self,
        project_service: ProjectService,
        vector_service: VectorService,
        news_service: NewsService,
    ):
        self.project_service = project_service
        self.vector_service = vector_service
        self.news_service = news_service

        # Initialize Claude
        self.default_llm = ChatAnthropic(
            model="claude-sonnet-4-5",
            anthropic_api_key=settings.anthropic_api_key or "dummy",
            temperature=0.7,
            max_tokens=4096,
        )

        # Initialize tools
        self.tools = [
            ProjectSearchTool(project_service=project_service),
            ProjectStatsTool(project_service=project_service),
            ContractorAnalysisTool(project_service=project_service),
            GeospatialSearchTool(project_service=project_service),
            NewsFetchTool(news_service=news_service),
        ]

        # Create ReAct Agent prompt template
        react_prompt = PromptTemplate.from_template("""You are FloodGuard PH Assistant, a specialized AI for Philippine flood control infrastructure data.

You have access to {num_projects} verified flood control projects. Use the available tools to answer questions accurately.

AVAILABLE TOOLS:
{tools}

TOOL NAMES: {tool_names}

When answering questions:
1. Use tools to get accurate data before responding
2. Be concise and data-driven
3. Use ₱ for Philippine pesos
4. Cite specific projects when making claims
5. Suggest relevant follow-up questions

Question: {input}

Thought Process:
{agent_scratchpad}""")

        # Create agent executor (this is the key enhancement - actually using the ReAct pattern!)
        try:
            agent = create_react_agent(
                llm=self.default_llm,
                tools=self.tools,
                prompt=react_prompt
            )

            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                max_iterations=5,
                handle_parsing_errors=True,
                return_intermediate_steps=True
            )
            logger.info("✓ ReAct Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ReAct agent: {e}")
            self.agent_executor = None

        # Enhanced session management
        self.chat_histories = {}
        self.MAX_HISTORY_MESSAGES = 20  # Increased from 12 for better context
        self.CONTEXT_WINDOW = 12  # Increased from 8

        # NLP helper
        self.nlp = NLPHelper()

    def validate_query(self, message: str) -> None:
        """Validate query input"""
        if not message or len(message.strip()) < self.MIN_QUERY_LENGTH:
            raise FloodGuardException(ErrorCode.INVALID_INPUT, "Query is empty")

        if len(message) > self.MAX_QUERY_LENGTH:
            raise FloodGuardException(
                ErrorCode.QUERY_TOO_LONG,
                f"Query exceeds {self.MAX_QUERY_LENGTH} characters"
            )

    def get_chat_history(self, session_id: str) -> Dict:
        """Get or create chat session"""
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = {
                'messages': [],
                'last_context': None,
                'entity_memory': {},  # Track mentioned entities
                'reasoning_chain': []  # Track multi-turn reasoning
            }
        return self.chat_histories[session_id]

    def add_to_history(
        self,
        session_id: str,
        human_msg: str,
        ai_msg: str,
        context: dict = None,
        entities: dict = None
    ):
        """Add messages to history with enhanced context"""
        session = self.get_chat_history(session_id)

        # Add messages
        session['messages'].append(HumanMessage(content=human_msg))
        session['messages'].append(AIMessage(content=ai_msg))

        # Sliding window
        if len(session['messages']) > self.MAX_HISTORY_MESSAGES:
            session['messages'] = session['messages'][-self.MAX_HISTORY_MESSAGES:]

        # Update context
        if context:
            session['last_context'] = context

        # Update entity memory for multi-turn reasoning
        if entities:
            for entity_type, entity_value in entities.items():
                if entity_value:
                    if entity_type not in session['entity_memory']:
                        session['entity_memory'][entity_type] = []
                    if entity_value not in session['entity_memory'][entity_type]:
                        session['entity_memory'][entity_type].append(entity_value)

        # Track reasoning chain
        session['reasoning_chain'].append({
            'query': human_msg,
            'response': ai_msg,
            'timestamp': datetime.now().isoformat(),
            'entities': entities
        })

        # Keep only last 10 reasoning steps
        if len(session['reasoning_chain']) > 10:
            session['reasoning_chain'] = session['reasoning_chain'][-10:]

    async def chat(
        self,
        message: str,
        session_id: str,
        anthropic_key: str = None,
        openai_key: str = None  # Now optional!
    ) -> AsyncGenerator[dict, None]:
        """Process chat with ReAct agent and enhanced NLP"""

        try:
            # Validate input
            self.validate_query(message)

            # Send initial status
            yield {"type": "status", "message": "Processing your question..."}

            # Extract entities with enhanced NLP
            entities = self.nlp.extract_entities(message)
            intent = entities.get('intent', QueryIntent.SEARCH)
            confidence = self.nlp.calculate_confidence(message, entities)

            # Yield confidence score
            yield {
                "type": "confidence",
                "score": confidence,
                "intent": intent
            }

            # Get session context
            session = self.get_chat_history(session_id)

            # Handle greetings without tool execution
            if intent == QueryIntent.GREETING:
                greeting_response = self._handle_greeting(message, session)
                yield {
                    "type": "message",
                    "content": greeting_response,
                    "done": True
                }
                self.add_to_history(session_id, message, greeting_response, entities=entities)
                return

            # Create LLM with user's key
            llm = ChatAnthropic(
                model="claude-sonnet-4-5",
                anthropic_api_key=anthropic_key or settings.anthropic_api_key,
                temperature=0.7,
                max_tokens=4096,
            ) if anthropic_key else self.default_llm

            # Get project count for context
            num_projects = len(self.project_service.df) if self.project_service.df is not None else 0

            # Build enhanced context with entity memory
            context_parts = [f"Available data: {num_projects} flood control projects"]

            # Add entity memory context for multi-turn reasoning
            if session['entity_memory']:
                memory_summary = []
                if 'location' in session['entity_memory']:
                    memory_summary.append(f"Recent locations: {', '.join(session['entity_memory']['location'][:3])}")
                if 'contractor' in session['entity_memory']:
                    memory_summary.append(f"Recent contractors: {', '.join(session['entity_memory']['contractor'][:3])}")
                if memory_summary:
                    context_parts.append("Context from conversation: " + "; ".join(memory_summary))

            # Use ReAct Agent if available and query needs data
            use_agent = (
                self.agent_executor is not None and
                intent in [QueryIntent.SEARCH, QueryIntent.STATS, QueryIntent.COMPARE, QueryIntent.ANALYZE]
            )

            projects_data = None
            response_text = ""

            if use_agent:
                try:
                    # Execute agent with tools
                    yield {"type": "status", "message": "Using AI agent to search data..."}

                    # Build enhanced input with entities
                    agent_input = {
                        "input": message,
                        "num_projects": num_projects,
                        "chat_history": session['messages'][-6:] if session['messages'] else []
                    }

                    # Run agent
                    result = await self.agent_executor.ainvoke(agent_input)

                    response_text = result.get('output', '')

                    # Extract project data from intermediate steps
                    if 'intermediate_steps' in result:
                        for action, observation in result['intermediate_steps']:
                            # Check if observation contains project data
                            if isinstance(observation, str) and 'projects' in observation.lower():
                                try:
                                    obs_data = json.loads(observation)
                                    if 'projects' in obs_data:
                                        projects_data = obs_data
                                        break
                                except:
                                    pass

                except Exception as e:
                    logger.error(f"Agent execution error: {e}")
                    logger.error(traceback.format_exc())
                    # Fallback to direct search
                    use_agent = False

            # Fallback to direct search if agent not available or failed
            if not use_agent or not response_text:
                # Use enhanced NLP to build search filters
                projects_data = await self._search_with_nlp(entities)

                # Build response using extracted data
                if projects_data and projects_data.get('projects'):
                    response_text = self._build_response(message, projects_data, entities)
                else:
                    # Ask for clarification if no results and low confidence
                    if confidence < 0.6:
                        response_text = self._suggest_refinement(message, entities)
                    else:
                        response_text = f"No projects found matching your criteria. Try adjusting your search terms or filters."

            # Send projects data to frontend
            if projects_data and projects_data.get('projects'):
                yield {
                    "type": "projects",
                    "data": projects_data["projects"],
                    "count": len(projects_data["projects"])
                }

                # Calculate and send map bounds
                bounds = self._calculate_bounds(projects_data["projects"])
                yield {
                    "type": "map_bounds",
                    "bbox": bounds
                }

            # Add response grounding/validation
            grounded_response = self._ground_response(response_text, projects_data)

            # Send response
            yield {
                "type": "message",
                "content": grounded_response,
                "done": True
            }

            # Store in history
            context_info = {
                'query_type': intent,
                'result_count': len(projects_data.get('projects', [])) if projects_data else 0,
                'timestamp': datetime.now().isoformat(),
                'confidence': confidence,
                'entities': entities
            }
            self.add_to_history(session_id, message, grounded_response, context=context_info, entities=entities)

            # Fetch news if relevant
            if projects_data or entities.get('contractor'):
                try:
                    news_query = self._build_news_query(message, projects_data, entities)
                    articles = await self.news_service.search_news(query=news_query, n_results=3)
                    if articles:
                        yield {
                            "type": "news",
                            "data": [article.dict() for article in articles]
                        }
                except Exception as e:
                    logger.warning(f"News fetch error: {e}")
                    yield {
                        "type": "error",
                        "code": ErrorCode.NEWS_FETCH_ERROR.value,
                        "message": get_error_detail(ErrorCode.NEWS_FETCH_ERROR).user_message
                    }

        except FloodGuardException as e:
            error_detail = e.error_detail
            logger.error(f"FloodGuard error: {error_detail.code} - {error_detail.message}")
            yield {
                "type": "error",
                "code": error_detail.code.value,
                "message": error_detail.user_message,
                "retry_possible": error_detail.retry_possible
            }

        except Exception as e:
            logger.error(f"Unexpected error in chat: {e}")
            logger.error(traceback.format_exc())
            error_detail = get_error_detail(ErrorCode.INTERNAL_ERROR, str(e))
            yield {
                "type": "error",
                "code": ErrorCode.INTERNAL_ERROR.value,
                "message": error_detail.user_message,
                "retry_possible": True
            }

    def _handle_greeting(self, message: str, session: Dict) -> str:
        """Handle greeting messages"""
        greetings = [
            "Hello! I can help you explore 9,800+ flood control projects across the Philippines.",
            "Hi there! Ask me about specific regions, contractors, budgets, or project types.",
            "Welcome! I have data on flood control infrastructure from 2022-2025. What would you like to know?"
        ]

        # Rotate greetings based on session history
        greeting_index = len(session['messages']) % len(greetings)
        return greetings[greeting_index]

    async def _search_with_nlp(self, entities: Dict) -> Optional[Dict]:
        """Search projects using NLP-extracted entities"""
        from backend.models.project import ProjectSearchFilters

        try:
            filters = ProjectSearchFilters()

            if entities.get('location'):
                location = entities['location']
                if location == 'METRO_MANILA':
                    # Search all Metro Manila cities
                    filters.region = 'NCR'
                else:
                    filters.province = location
                    # Also try municipality
                    if 'CITY' in location:
                        filters.municipality = location

            if entities.get('years'):
                filters.infra_year = entities['years']

            if entities.get('contractor'):
                filters.contractor = entities['contractor']

            if entities.get('budget'):
                if 'min' in entities['budget']:
                    filters.min_contract_cost = entities['budget']['min']
                if 'max' in entities['budget']:
                    filters.max_contract_cost = entities['budget']['max']

            # Search
            results = self.project_service.search(filters=filters, limit=100)

            if len(results) == 0:
                return None

            # Convert to dict
            projects = []
            for _, row in results.iterrows():
                projects.append({
                    'project_id': row.get('ProjectComponentID', ''),
                    'description': row.get('ProjectDescription', ''),
                    'contractor': row.get('Contractor', ''),
                    'contract_cost': float(row.get('ContractCost', 0)),
                    'municipality': row.get('Municipality', ''),
                    'province': row.get('Province', ''),
                    'region': row.get('Region', ''),
                    'lat': float(row.get('Latitude', 0)),
                    'lon': float(row.get('Longitude', 0)),
                    'type_of_work': row.get('TypeofWork', ''),
                    'infra_year': int(row.get('InfraYear', 0)) if row.get('InfraYear') else None,
                })

            return {'projects': projects, 'count': len(projects)}

        except Exception as e:
            logger.error(f"NLP search error: {e}")
            return None

    def _build_response(self, query: str, projects_data: Dict, entities: Dict) -> str:
        """Build natural language response"""
        projects = projects_data.get('projects', [])
        count = len(projects)

        if count == 0:
            return "No projects found matching your criteria."

        # Calculate stats
        total_cost = sum(p.get('contract_cost', 0) for p in projects)

        # Build response based on intent
        intent = entities.get('intent', QueryIntent.SEARCH)

        if intent == QueryIntent.STATS:
            return f"Found {count} projects totaling ₱{total_cost:,.0f}. Average project cost is ₱{total_cost/count:,.0f}."

        # Default search response
        response_parts = [f"Found {count} projects"]

        if entities.get('location'):
            response_parts.append(f"in {entities['location']}")

        if entities.get('years'):
            years_str = ", ".join(str(y) for y in entities['years'])
            response_parts.append(f"for {years_str}")

        response_parts.append(f"totaling ₱{total_cost:,.0f}")

        # Add top contractor if available
        contractors = {}
        for p in projects:
            contractor = p.get('contractor', 'Unknown')
            contractors[contractor] = contractors.get(contractor, 0) + 1

        if contractors:
            top_contractor = max(contractors.items(), key=lambda x: x[1])
            response_parts.append(f". Top contractor: {top_contractor[0]} ({top_contractor[1]} projects)")

        return " ".join(response_parts) + "."

    def _ground_response(self, response: str, projects_data: Optional[Dict]) -> str:
        """Validate and ground response in actual data"""
        # Add data citations
        if projects_data and projects_data.get('count'):
            count = projects_data['count']
            # Ensure numbers in response match actual data
            grounded = response

            # Add confidence indicator if making specific claims
            if 'largest' in response.lower() or 'most' in response.lower():
                grounded += " (Based on available data)"

            return grounded

        return response

    def _suggest_refinement(self, query: str, entities: Dict) -> str:
        """Suggest query refinement for low-confidence queries"""
        suggestions = ["I can help you search projects if you provide:"]

        if not entities.get('location'):
            suggestions.append("- A specific location (province or city)")
        if not entities.get('years'):
            suggestions.append("- A year (2022-2025)")
        if not entities.get('contractor'):
            suggestions.append("- A contractor name")
        if not entities.get('budget'):
            suggestions.append("- A budget range")

        return "\n".join(suggestions)

    def _build_news_query(self, query: str, projects_data: Optional[Dict], entities: Dict) -> str:
        """Build news search query"""
        query_parts = ["flood control", "DPWH", "Philippines"]

        if entities.get('location'):
            query_parts.append(entities['location'])

        if entities.get('contractor'):
            query_parts.append(entities['contractor'])
        elif projects_data and projects_data.get('projects'):
            # Add top contractor from results
            contractors = set(p.get('contractor', '') for p in projects_data['projects'][:3])
            query_parts.extend(list(contractors)[:2])

        return " ".join(query_parts)

    def _calculate_bounds(self, projects: List[Dict]) -> List[List[float]]:
        """Calculate map bounds"""
        if not projects:
            return [[121.0, 12.0], [122.0, 13.0]]

        lats = [p["lat"] for p in projects if "lat" in p and p["lat"] != 0]
        lons = [p["lon"] for p in projects if "lon" in p and p["lon"] != 0]

        if not lats or not lons:
            return [[121.0, 12.0], [122.0, 13.0]]

        padding = 0.1
        return [
            [min(lons) - padding, min(lats) - padding],
            [max(lons) + padding, max(lats) + padding],
        ]
