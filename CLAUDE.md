# CLAUDE.md - FloodGuard PH Developer Guide for AI Assistants

## Project Overview

**FloodGuard PH** is an AI-powered chatbot interface that enables citizens to explore Philippine flood control infrastructure data through natural conversation. The system combines Claude Sonnet 4.5 LLM with interactive map visualization to help users discover and analyze 9,800+ government flood control projects from 2022-2025.

### Key Capabilities
- Natural language querying of flood control projects
- Interactive map visualization with Leaflet.js
- Real-time WebSocket streaming chat
- Semantic search using vector embeddings
- News aggregation for projects and contractors
- Geospatial queries (radius, bounding box)
- Budget and contractor analytics

### Technology Stack

**Backend:**
- FastAPI 0.115.0 (async web framework)
- Python 3.12.0
- LangChain 0.3.7 (AI agent framework)
- Anthropic Claude Sonnet 4.5 (LLM)
- ChromaDB 0.5.20 (vector database)
- Pandas 2.2.3 + GeoPandas 1.0.1 (data processing)
- OpenAI Embeddings (text-embedding-3-small)

**Frontend:**
- Pure HTML5/CSS3/JavaScript (no frameworks)
- Leaflet.js 1.9.4 (interactive maps)
- WebSocket API (real-time streaming)
- CSS Grid + Flexbox (responsive layout)

**Data:**
- 9,800+ projects in CSV format (7.9MB)
- ChromaDB collections for semantic search
- RSS feeds for news aggregation

## Directory Structure

```
flood-guard-ph/
├── backend/                          # Python FastAPI backend (23 files)
│   ├── main.py                       # FastAPI app entry + service initialization
│   ├── config.py                     # Pydantic settings + environment config
│   │
│   ├── models/                       # Pydantic data models
│   │   ├── project.py                # Project, SearchFilters, Stats models
│   │   └── conversation.py           # ChatMessage, ChatResponse, NewsArticle
│   │
│   ├── services/                     # Business logic layer
│   │   ├── project_service.py        # CSV loading, filtering, spatial queries
│   │   ├── vector_service.py         # ChromaDB semantic search interface
│   │   ├── llm_service.py            # LangChain agent + Claude integration
│   │   ├── news_service.py           # RSS feed parsing & news fetching
│   │   └── geospatial.py             # GeoPandas spatial operations
│   │
│   ├── api/                          # FastAPI route handlers
│   │   ├── chat.py                   # WebSocket /api/chat endpoint
│   │   ├── search.py                 # REST POST /api/search endpoint
│   │   └── news.py                   # REST GET /api/news endpoint
│   │
│   └── tools/                        # LangChain tool definitions
│       ├── project_tools.py          # ProjectSearch, Stats, Contractor, Geo tools
│       └── news_tools.py             # NewsFetch tool
│
├── demo_ui/                          # Frontend interface
│   ├── index.html                    # Main HTML (three-pane layout)
│   └── assets/
│       ├── css/                      # Modular stylesheets (6 files)
│       │   ├── variables.css         # Design tokens, colors, spacing
│       │   ├── layout.css            # Three-pane grid system
│       │   ├── chat.css              # Chat panel styles
│       │   ├── map.css               # Map container styles
│       │   ├── project.css           # Project details panel
│       │   └── modal.css             # Settings modal
│       │
│       └── js/                       # ES6 JavaScript modules (7 files)
│           ├── app.js                # Main application controller
│           ├── chat.js               # WebSocket chat manager
│           ├── map.js                # Leaflet map controller
│           ├── project.js            # Project card renderer
│           ├── news.js               # News feed manager
│           ├── api-keys.js           # API key configuration UI
│           └── utils.js              # Helper functions
│
├── data/                             # Data directory
│   └── flood_control__floodcontrol_data__0__20251004_233415.csv
│                                     # Main dataset (7.9MB, 9,800+ projects)
│
├── scripts/                          # Setup & initialization scripts
│   ├── embed_projects.py             # Embed projects into ChromaDB
│   ├── setup_vectordb.py             # Initialize ChromaDB collections
│   └── create_sample_data.py         # Generate sample data
│
├── Configuration Files:
│   ├── Makefile                      # make install, dev, seed, clean
│   ├── requirements.txt              # Python dependencies (19 packages)
│   ├── .env.example                  # Environment variable template
│   ├── .gitignore                    # Git exclusions
│   ├── runtime.txt                   # Python 3.12.0
│   ├── build.sh                      # Render.com build script
│   ├── Procfile                      # Heroku/Railway start command
│   ├── render.yaml                   # Render.com deployment config
│   └── vercel.json                   # Vercel deployment config
```

## Key Files Deep Dive

### Backend Core Files

#### `backend/main.py` (126 lines)
**Purpose:** FastAPI application entry point

**Key responsibilities:**
- Initializes FastAPI app with CORS middleware
- Creates global service instances on startup event
- Includes API routers (chat, search, news)
- Serves static assets and demo UI
- Health check endpoint

**Important patterns:**
- Services initialized as singletons in `app.state`
- Global service variables for easy access
- Startup event handler for async initialization
- Static file mounting for frontend assets

#### `backend/config.py` (20 lines)
**Purpose:** Centralized configuration management

**Key settings:**
- `anthropic_api_key`: Default "dummy" (users provide their own)
- `openai_api_key`: Default "dummy" (users provide their own)
- `chroma_persist_dir`: "./chroma_data" (vector DB storage)
- `projects_csv`: Path to main CSV data file
- `cors_origins`: "*" (allow all origins)

**Important:** This uses Pydantic Settings with automatic .env file loading

#### `backend/services/project_service.py` (~250 lines)
**Purpose:** Project data loading, filtering, and spatial queries

**Key methods:**
- `__init__()`: Loads CSV into Pandas DataFrame + GeoPandas GeoDataFrame
- `search()`: Filters by year, contractor, cost, region, location, type
- `get_stats()`: Calculates total budget, avg award, project counts
- `get_bounds()`: Returns map viewport for filtered results
- `_normalize_contractor()`: Converts contractor names to uppercase

**Data processing:**
- Cleans numeric fields (removes commas, converts to float)
- Parses dates (ISO format)
- Creates GeoJSON geometries from lat/lon
- Handles missing values gracefully

#### `backend/services/llm_service.py` (~200 lines)
**Purpose:** LangChain agent with Claude Sonnet 4.5 integration

**Key responsibilities:**
- Initializes Claude LLM via LangChain
- Creates ReACT agent with 5 tools
- Manages chat history per session (sliding window: 12 messages)
- Streams responses asynchronously

**Available tools:**
1. ProjectSearchTool - Semantic + metadata search
2. ProjectStatsTool - Budget aggregation
3. ContractorAnalysisTool - Find projects by contractor
4. GeospatialSearchTool - Radius/bbox queries
5. NewsFetchTool - Related news articles

**Important patterns:**
- Accepts user-provided API keys per request
- Session-based chat history
- Async generator for streaming responses
- Tool execution with automatic parsing

#### `backend/services/vector_service.py` (~116 lines)
**Purpose:** ChromaDB vector database interface

**Collections:**
1. **projects_collection**
   - Documents: Concatenated project metadata
   - Embeddings: OpenAI text-embedding-3-small (1536 dims)
   - Metadata: All project fields

2. **news_collection**
   - Documents: News title + snippet
   - Embeddings: Same model
   - Metadata: URL, published date, source, related projects

**Key methods:**
- `search_projects()`: Semantic search with metadata filters
- `search_news()`: Semantic search in news
- `get_or_create_*_collection()`: Lazy initialization

### API Endpoints

#### `POST /api/chat` (WebSocket)
**File:** `backend/api/chat.py`

**Request format:**
```json
{
  "message": "Show me 2025 projects in Pangasinan over ₱4M",
  "session_id": "user_abc123",
  "anthropic_key": "sk-ant-...",
  "openai_key": "sk-..."
}
```

**Response stream types:**
- `{"type": "status", "message": "..."}` - Status updates
- `{"type": "tool", ...}` - Tool execution trace
- `{"type": "projects", "data": [...]}` - Project results
- `{"type": "map_bounds", "bbox": [...]}` - Map viewport
- `{"type": "message", "content": "..."}` - Chat response (streamed)
- `{"type": "news", "data": [...]}` - News articles

#### `POST /api/search`
**File:** `backend/api/search.py`

**Request format:**
```json
{
  "filters": {
    "year": [2024, 2025],
    "contractor": "GED CONSTRUCTION",
    "min_award_php": 4000000,
    "region": "Region I"
  },
  "spatial": {
    "type": "radius",
    "lat": 16.18,
    "lon": 120.0,
    "radius_km": 5.0
  },
  "limit": 100
}
```

**Response format:**
```json
{
  "projects": [...],
  "total": 47,
  "stats": {
    "total_budget": 245000000,
    "avg_award": 5212765,
    "contractors": ["GED CONSTRUCTION"],
    "project_types": {"Construction": 23}
  }
}
```

#### `GET /api/news`
**File:** `backend/api/news.py`

**Query params:**
- `project_id` - Fetch news for specific project
- `contractor` - Fetch news for contractor

### Frontend Architecture

#### Three-Pane Layout
```
┌─────────────┬──────────────────────┬─────────────────┐
│   CHAT      │      MAP             │   PROJECT       │
│   PANEL     │   (OpenStreetMap)    │   DETAILS       │
│   360px     │      (fluid)         │   420px         │
└─────────────┴──────────────────────┴─────────────────┘
```

#### `demo_ui/assets/js/app.js`
**Main application controller**

**Responsibilities:**
- Initializes ChatManager, MapController, ProjectRenderer, NewsManager
- Loads initial 10,000 projects for map clustering
- Coordinates communication between components
- Updates stats overlay (project count, total budget)

**Event flow:**
1. Chat message sent → WebSocket
2. Receives projects → Updates map
3. Receives map_bounds → Fits map viewport
4. Receives news → Updates news feed
5. Map marker clicked → Shows project details

#### Design System (`demo_ui/assets/css/variables.css`)
**Color palette:**
- Primary: #2563eb (blue)
- Secondary: #10b981 (emerald)
- Accent: #f59e0b (amber)

**Spacing system:**
- xs: 0.25rem, sm: 0.5rem, md: 1rem, lg: 1.5rem, xl: 2rem

**Elevation:**
- Four shadow levels (sm, md, lg, xl)
- Glassmorphism effects with backdrop blur

**Typography:**
- Font family: Inter (sans-serif)
- Monospace: JetBrains Mono

## Data Models

### Project Schema (CSV)
**Key columns:**
- `ProjectID` - Unique identifier
- `ProjectDescription` - Full project title
- `Contractor` - Contractor name (normalized to UPPERCASE)
- `ContractCost` - Award amount in Philippine Pesos
- `FundingYear` - Year of funding (2022-2025)
- `Region`, `Province`, `Municipality` - Location hierarchy
- `Latitude`, `Longitude` - Geographic coordinates
- `TypeofWork` - Project type (Construction, Rehabilitation, etc.)
- `DistrictEngineeringOffice` - Implementing office
- `StartDate`, `CompletionDateActual` - Timeline

**Total records:** 9,800+ projects
**File size:** 7.9 MB

### Pydantic Models

#### `Project` (backend/models/project.py)
62 fields matching CSV schema + computed fields

#### `ProjectSearchFilters`
```python
class ProjectSearchFilters(BaseModel):
    year: Optional[List[int]] = None
    contractor: Optional[str] = None
    min_award_php: Optional[float] = None
    max_award_php: Optional[float] = None
    region: Optional[str] = None
    province: Optional[str] = None
    municipality: Optional[str] = None
    project_type: Optional[str] = None
```

#### `ProjectStats`
```python
class ProjectStats(BaseModel):
    total_budget: float
    project_count: int
    avg_award: float
    contractors: List[str]
    project_types: Dict[str, int]
```

## Development Workflows

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/yourorg/flood-guard-ph.git
cd flood-guard-ph

# 2. Install dependencies
make install
# or: pip install -r requirements.txt

# 3. Copy environment template (optional for local dev)
cp .env.example .env

# 4. Initialize vector database
make seed
# or:
python scripts/setup_vectordb.py
python scripts/embed_projects.py

# 5. Start development server
make dev
# or: uvicorn backend.main:app --reload --port 8000

# 6. Open browser
open http://localhost:8000/demo_ui
```

### Common Development Tasks

#### Adding a new API endpoint
1. Create route handler in `backend/api/`
2. Define Pydantic request/response models in `backend/models/`
3. Implement business logic in appropriate service
4. Register router in `backend/main.py`
5. Update CORS if needed

#### Adding a new LangChain tool
1. Create tool class in `backend/tools/project_tools.py`
2. Inherit from `BaseTool`
3. Define `name`, `description`, `args_schema`
4. Implement `_run()` method
5. Add to tools list in `llm_service.py`

#### Modifying frontend UI
1. HTML structure: `demo_ui/index.html`
2. Styles: `demo_ui/assets/css/*.css` (modular)
3. Behavior: `demo_ui/assets/js/*.js` (ES6 modules)
4. No build step required - pure HTML/CSS/JS

#### Re-embedding projects after data changes
```bash
# Delete existing vector DB
rm -rf chroma_data/

# Re-run embedding script
python scripts/embed_projects.py
```

### Testing

**Current status:** No automated tests in repository

**Recommended testing areas:**
- Unit tests for `ProjectService` filtering logic
- Integration tests for API endpoints
- E2E tests for chat workflow
- Performance benchmarks for vector search

## Coding Conventions

### Python Code Style
- **Formatting:** Follow PEP 8
- **Type hints:** Use throughout (Pydantic models, function signatures)
- **Async/await:** Use for I/O operations (API calls, DB queries)
- **Logging:** Use `logging` module, not print statements
- **Error handling:** Raise appropriate HTTP exceptions in API routes

### Service Pattern
All business logic lives in services (`backend/services/`):
- Services are stateful (load data once on initialization)
- Services are singletons (initialized in `main.py` startup)
- Services expose clean public APIs
- Internal methods prefixed with `_`

### API Patterns
- **Request validation:** Use Pydantic models
- **Response models:** Always define response schemas
- **Error responses:** Use FastAPI HTTPException
- **Async endpoints:** All endpoints should be async
- **CORS:** Already configured globally

### Frontend Patterns
- **Pure JavaScript:** No frameworks, no build step
- **ES6 modules:** Use import/export
- **CSS modularity:** One file per component
- **Design tokens:** Use CSS variables from `variables.css`
- **Responsive:** Mobile-first approach

## Important Considerations for AI Assistants

### API Key Security
⚠️ **CRITICAL:** This application uses a user-provided API key model
- Server has dummy keys ("dummy") in environment
- Users provide their own Anthropic + OpenAI keys via UI settings modal
- Keys sent with each WebSocket request
- Keys NOT stored on server (in-memory only during request)

**When modifying API key handling:**
- Never store user keys in database or logs
- Never expose keys in error messages
- Always validate keys before use
- Frontend stores keys in localStorage (user's browser only)

### Vector Database Initialization
- ChromaDB requires initialization before first use
- Run `scripts/embed_projects.py` to populate collections
- Embeddings stored in `./chroma_data/` directory
- Collection names: `projects_collection`, `news_collection`

**When modifying vector DB:**
- Always check collection exists before querying
- Use `get_or_create_*_collection()` methods
- Re-embed if data schema changes

### Geospatial Queries
- Uses GeoPandas for spatial operations
- Coordinate system: WGS84 (EPSG:4326)
- Latitude: -90 to 90, Longitude: -180 to 180
- Philippines center: ~12.8797°N, 121.7740°E

**Spatial query types:**
1. **Radius:** Distance from point in kilometers
2. **Bounding box:** Rectangle defined by min/max lat/lon

### Chat Session Management
- Sessions identified by `session_id` string
- Chat history stored in memory (not persistent)
- Sliding window: keeps last 12 messages
- Sessions expire when server restarts

**When modifying chat:**
- Always include session_id in requests
- Clear old sessions periodically to prevent memory leaks
- Consider adding session timeout mechanism

### LangChain Agent Behavior
- Uses ReACT (Reasoning + Acting) pattern
- Agent decides which tools to call based on query
- Multiple tools may be called in sequence
- Tool outputs fed back to agent for final response

**Tool execution flow:**
1. User query → Agent
2. Agent analyzes query
3. Agent selects appropriate tool(s)
4. Tools execute and return results
5. Agent synthesizes final response

**When adding tools:**
- Provide clear, descriptive tool names
- Write detailed tool descriptions (agent uses these to decide)
- Define strict input schemas with Pydantic
- Handle errors gracefully in tool code

### Performance Considerations
- **CSV loading:** 9,800 projects load in ~1-2 seconds
- **Vector search:** ChromaDB queries in <100ms
- **Map clustering:** Frontend handles 10,000+ markers via Leaflet.markercluster
- **Streaming:** WebSocket streams tokens ~50ms each

**Optimization tips:**
- Cache filtered results when possible
- Use pagination for large result sets
- Debounce user input in frontend
- Consider indexing frequently-queried columns

### Deployment Considerations
- **Platform:** Optimized for Render.com (free tier)
- **Build time:** 5-10 minutes (embedding generation)
- **Cold starts:** ~30 seconds on free tier
- **Environment:** All config via environment variables
- **Static files:** Served directly by FastAPI (no CDN needed)

**Deployment checklist:**
1. Push to GitHub
2. Connect to Render
3. Environment variables auto-set from render.yaml
4. Build script runs embedding automatically
5. Health check at `/health`

### Common Gotchas

1. **NumPy version:** Must be <2.0.0 (ChromaDB compatibility)
2. **Contractor names:** Always uppercase in database
3. **Philippine Peso formatting:** Use ₱ symbol, format with commas
4. **Date formats:** ISO 8601 (YYYY-MM-DD)
5. **CORS:** Already configured for all origins (*)
6. **WebSocket path:** Must be `/api/chat` (not /ws/chat)
7. **Static files:** Mounted at `/assets` (not /demo_ui/assets)

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (demo_ui)                        │
│  • index.html (three-pane layout)                           │
│  • 7 JS modules (app, chat, map, project, news, etc.)      │
│  • 6 CSS modules (variables, layout, chat, map, etc.)      │
└────────────────────────┬────────────────────────────────────┘
                         │
                    WebSocket (/api/chat)
                    REST (/api/search, /api/news)
                         │
┌────────────────────────▼────────────────────────────────────┐
│                 FastAPI (backend/main.py)                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Routers: chat.py, search.py, news.py               │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                  │
        ▼                                  ▼
┌──────────────────┐            ┌──────────────────┐
│   LLMService     │            │ ProjectService   │
│                  │            │                  │
│ • Claude Sonnet  │            │ • CSV loader     │
│ • LangChain      │            │ • Filters        │
│ • ReACT agent    │            │ • Spatial ops    │
│ • 5 Tools        │            │ • Stats calc     │
└────────┬─────────┘            └────────┬─────────┘
         │                               │
         │                               │
    ┌────▼──────┐                  ┌─────▼────────┐
    │  Vector   │                  │    News      │
    │  Service  │                  │   Service    │
    │           │                  │              │
    │• ChromaDB │                  │ • RSS feeds  │
    │• Semantic │                  │ • Web search │
    └───────────┘                  └──────────────┘
         │
         │
    ┌────▼─────────────────┐
    │   ChromaDB Storage   │
    │  ./chroma_data/      │
    │                      │
    │ • projects_collection│
    │ • news_collection    │
    └──────────────────────┘
```

## Quick Reference Commands

```bash
# Development
make install          # Install Python dependencies
make seed            # Initialize vector database
make dev             # Start development server (port 8000)
make clean           # Remove generated files and caches

# Manual equivalents
pip install -r requirements.txt
python scripts/setup_vectordb.py && python scripts/embed_projects.py
uvicorn backend.main:app --reload --port 8000
rm -rf chroma_data/ && find . -name "__pycache__" -exec rm -rf {} +

# Testing (manual)
curl http://localhost:8000/health
curl http://localhost:8000/
open http://localhost:8000/demo_ui

# Deployment (Render.com)
git push origin main  # Auto-deploys if connected to Render
```

## Project Statistics

- **Total Python files:** 23
- **Total JavaScript files:** 7
- **Total CSS files:** 6
- **Total lines of code:** ~2,500 (Python) + ~1,500 (JS/CSS)
- **Dependencies:** 19 Python packages
- **Data records:** 9,800+ projects
- **Supported browsers:** Modern browsers (ES6 required)
- **Python version:** 3.12.0
- **License:** MIT

## Support and Documentation

- **Main README:** `/README.md` (comprehensive documentation)
- **API Docs:** `http://localhost:8000/docs` (FastAPI auto-generated)
- **Health Check:** `http://localhost:8000/health`
- **Demo UI:** `http://localhost:8000/demo_ui`

---

**Last Updated:** 2025-11-15
**Version:** 1.0.0
**Maintained by:** FloodGuard PH Team
