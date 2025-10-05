📌 Overview
FloodWatch PH is an intelligent chatbot interface that transforms how citizens explore Philippine flood control infrastructure data (2022–present). Through natural conversation powered by Claude Sonnet 4.5, users can ask questions, discover projects, and access related news—all while visualizing results on an interactive map.
Example Conversations:

"Show me all 2025 projects in Pangasinan"
"Which contractor has the most projects over ₱10M?"
"What flood control work is happening near Tarlac City?"
"Tell me about GED Construction's recent projects"

The system responds with:

Conversational answers with context and insights
Interactive map visualization of relevant projects
Live news feed for selected projects and contractors
Detailed project cards with budgets, dates, and locations


🏗️ System Architecture
Technology Stack
Backend:

FastAPI – High-performance async API server
LangChain – Conversational memory and retrieval chains
Anthropic Claude Sonnet 4.5 – Advanced LLM for natural dialogue
ChromaDB – Embedded vector database for semantic search
OpenAI Embeddings (text-embedding-3-small) – Project & news vectorization
Pandas + GeoPandas – Data processing and geospatial operations

Frontend (/demo_ui):

Pure HTML/CSS/JavaScript – No framework overhead, maximum performance
Leaflet.js – Industry-standard OpenStreetMap integration
WebSocket – Real-time streaming chat responses
CSS Grid + Flexbox – Modern, responsive three-pane layout
Intersection Observer API – Smooth lazy-loading and animations

Data:

CSV/GeoJSON – Project data (no heavy database required)
RSS/NewsAPI – Live Philippine news aggregation
In-memory spatial indexing – Fast geospatial queries


🧭 UI/UX Design Philosophy
Global Layout
┌─────────────┬──────────────────────┬─────────────────┐
│   CHAT      │      MAP             │   PROJECT       │
│   PANEL     │   (OpenStreetMap)    │   DETAILS       │
│   360px     │      (fluid)         │   420px         │
│             │                      │                 │
│  • Messages │  • Interactive pins  │  • Project card │
│  • Input    │  • Clustering        │  • News feed    │
│  • History  │  • Popups            │  • Metadata     │
└─────────────┴──────────────────────┴─────────────────┘
Design Standards
Visual Excellence:

Glassmorphism – Frosted glass panels with backdrop blur
Smooth animations – 60fps transitions, micro-interactions
Typography – Inter font family, perfect line-height ratios
Color system – WCAG AAA contrast, semantic color palette
Shadows & depth – Layered elevation system (Google Material-inspired)

Interaction Design:

Progressive disclosure – Show complexity only when needed
Optimistic UI – Instant feedback before server response
Skeleton loaders – Perceived performance improvements
Toast notifications – Non-intrusive status updates
Keyboard shortcuts – Full accessibility support

Responsive Behavior:

Mobile-first – Collapses to stacked layout on small screens
Tablet optimization – Two-pane layout (chat+map or map+details)
Desktop excellence – Full three-pane experience


🧱 Data Architecture
Projects Data Schema
python# CSV/GeoJSON Structure
{
  "project_id": "P00941153LZ_25AG0078",
  "region": "Region I",
  "district": "PANGASINAN (FIRST LEGISLATIVE DISTRICT)",
  "city": "CITY OF ALAMINOS (PANGASINAN)",
  "office": "Pangasinan 1st District Engineering Office",
  "dpwh_code": "P00941153LZ",
  "title": "Rehabilitation of Flood Mitigation Structure...",
  "project_type": "Rehabilitation / Major Repair of Structure",
  "year": 2025,
  "contract_id": "25AG0078",
  "abc_php": 4950000,
  "award_php": 4850385.71,
  "award_date": "2025-05-14",
  "contractor": "GED CONSTRUCTION",
  "contract_date": "2025-02-21",
  "lat": 16.09684657,
  "lon": 119.96915518,
  "geom": {"type": "Point", "coordinates": [119.96915518, 16.09684657]}
}
ChromaDB Collections
1. projects_collection

Documents: Concatenated project metadata (title + contractor + city + type + year)
Metadata: All project fields for filtering
Embeddings: OpenAI text-embedding-3-small (1536 dimensions)

2. news_collection

Documents: News article title + snippet + source
Metadata: {url, published_date, source, related_projects: []}
Embeddings: Same model for semantic search


🧠 Conversational AI Pipeline
LangChain Architecture
python# Conversation Flow
User Input → LangChain Agent → Tools → Response Generation

Tools Available:
1. ProjectSearchTool → Vector + metadata filtering
2. ProjectStatsTool → Aggregate analytics (total budget, count, etc.)
3. ContractorLookupTool → Find all projects by contractor
4. GeospatialSearchTool → Radius/bbox queries with GeoPandas
5. NewsFetchTool → Retrieve related news articles
Prompt Engineering Strategy
System Prompt (Claude Sonnet 4.5):
You are FloodWatch PH Assistant, an expert on Philippine flood control 
infrastructure projects from 2022-2025. You help citizens understand 
government spending, contractor performance, and project details through 
natural conversation.

Guidelines:
- Be conversational, helpful, and data-driven
- Always cite specific projects when making claims
- Use Philippine peso formatting (₱) and local place names
- Highlight red flags (cost overruns, delays, concentration of awards)
- Suggest follow-up questions to deepen understanding
- When showing projects on map, describe the geographic pattern

Available data: {num_projects} projects totaling ₱{total_budget}
Current conversation context: {chat_history}
Conversation Memory:

Buffer Memory – Last 10 messages for context
Summary Memory – Compress older conversations
Entity Memory – Track mentioned contractors, locations, projects


🌐 API Architecture
Core Endpoints
POST /api/chat (WebSocket)
Streaming conversational interface with tool execution.
Request:
json{
  "message": "Show me 2025 projects in Pangasinan over ₱4M",
  "session_id": "user_abc123"
}
Response Stream:
json// 1. Acknowledgment
{"type": "status", "message": "Searching projects..."}

// 2. Tool execution trace
{"type": "tool", "tool": "ProjectSearchTool", "query": {"year": 2025, "region": "Region I", "min_award": 4000000}}

// 3. Projects data
{"type": "projects", "data": [...], "count": 12}

// 4. Map viewport suggestion
{"type": "map_bounds", "bbox": [[119.5, 15.8], [120.5, 16.5]]}

// 5. Conversational response (streamed tokens)
{"type": "message", "content": "I found 12 flood control projects in Pangasinan for 2025...", "done": false}
{"type": "message", "content": " The largest is a ₱14.6M slope protection...", "done": false}
{"type": "message", "content": " Would you like to see the contractor breakdown?", "done": true}

// 6. News items
{"type": "news", "data": [...]}
POST /api/search
Direct project search with filters (for map interactions).
Request:
json{
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
  "limit": 100,
  "sort": {"field": "award_php", "order": "desc"}
}
Response:
json{
  "projects": [...],
  "total": 47,
  "stats": {
    "total_budget": 245000000,
    "avg_award": 5212765,
    "contractors": ["GED CONSTRUCTION", "..."],
    "project_types": {"Construction": 23, "Rehabilitation": 24}
  }
}
GET /api/news?project_id=X or ?contractor=Y
Fetch related news articles.
Response:
json{
  "articles": [
    {
      "title": "DPWH completes flood control project in Alaminos",
      "snippet": "The Department of Public Works...",
      "url": "https://...",
      "source": "Rappler",
      "published": "2025-06-15T10:30:00Z",
      "relevance_score": 0.89
    }
  ]
}

🗂️ Project Structure
floodwatch-ph/
├── backend/
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Settings, env vars
│   ├── models/
│   │   ├── project.py          # Pydantic models
│   │   └── conversation.py     # Chat schemas
│   ├── services/
│   │   ├── llm_service.py      # LangChain + Claude integration
│   │   ├── vector_service.py   # ChromaDB operations
│   │   ├── project_service.py  # Data loading & search
│   │   ├── news_service.py     # RSS/NewsAPI fetcher
│   │   └── geospatial.py       # GeoPandas utilities
│   ├── api/
│   │   ├── chat.py             # WebSocket endpoint
│   │   ├── search.py           # REST search endpoint
│   │   └── news.py             # News endpoint
│   └── tools/
│       ├── project_tools.py    # LangChain tools for projects
│       └── news_tools.py       # LangChain tools for news
│
├── demo_ui/                    # Beautiful web interface
│   ├── index.html              # Main HTML structure
│   ├── assets/
│   │   ├── css/
│   │   │   ├── reset.css       # CSS normalization
│   │   │   ├── variables.css   # Design tokens
│   │   │   ├── layout.css      # Grid system
│   │   │   ├── chat.css        # Chat panel styles
│   │   │   ├── map.css         # Map container styles
│   │   │   └── project.css     # Details panel styles
│   │   └── js/
│   │       ├── app.js          # Main application logic
│   │       ├── chat.js         # WebSocket chat handler
│   │       ├── map.js          # Leaflet map controller
│   │       ├── project.js      # Project card renderer
│   │       ├── news.js         # News feed handler
│   │       └── utils.js        # Helper functions
│
├── data/
│   ├── projects.csv            # Source project data
│   ├── projects.geojson        # GeoJSON export
│   └── sample_news.json        # Seed news data
│
├── scripts/
│   ├── setup_vectordb.py       # Initialize ChromaDB collections
│   ├── embed_projects.py       # Generate project embeddings
│   ├── fetch_news.py           # News scraper/embedder
│   └── normalize_contractors.py # Data cleaning
│
├── tests/
│   ├── test_chat.py            # Conversation flow tests
│   ├── test_search.py          # Search accuracy tests
│   └── test_geospatial.py      # Spatial query tests
│
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── README.md

🚀 Setup & Deployment
Prerequisites

Python 3.11+
Node.js 18+ (optional, for build tools)
Docker & Docker Compose (recommended)

Environment Variables
bash# .env
ANTHROPIC_API_KEY=sk-ant-xxx          # Claude Sonnet 4.5
OPENAI_API_KEY=sk-xxx                 # OpenAI embeddings
NEWS_API_KEY=xxx                      # NewsAPI.org (optional)

CHROMA_PERSIST_DIR=./chroma_data      # Local ChromaDB storage
PROJECTS_CSV=./data/projects.csv
PROJECTS_GEOJSON=./data/projects.geojson

CORS_ORIGINS=http://localhost:3000,http://localhost:8000
LOG_LEVEL=INFO
Local Development
bash# 1. Clone repository
git clone https://github.com/yourorg/floodwatch-ph.git
cd floodwatch-ph

# 2. Install dependencies
make install
# or manually:
pip install -r requirements.txt

# 3. Initialize vector database
make seed
# or:
python scripts/setup_vectordb.py
python scripts/embed_projects.py

# 4. Start development server
make dev
# or:
uvicorn backend.main:app --reload --port 8000

# 5. Open browser
open http://localhost:8000/demo_ui
Docker Deployment
yaml# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./chroma_data:/app/chroma_data
      - ./data:/app/data
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000
bash# Build and run
docker-compose up --build

# Access at http://localhost:8000/demo_ui

🎨 Frontend Implementation Guide
HTML Structure (demo_ui/index.html)
html<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FloodWatch PH - AI Project Explorer</title>
  
  <!-- Leaflet CSS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
  
  <!-- Custom styles -->
  <link rel="stylesheet" href="assets/css/reset.css">
  <link rel="stylesheet" href="assets/css/variables.css">
  <link rel="stylesheet" href="assets/css/layout.css">
  <link rel="stylesheet" href="assets/css/chat.css">
  <link rel="stylesheet" href="assets/css/map.css">
  <link rel="stylesheet" href="assets/css/project.css">
</head>
<body>
  <div class="app-container">
    <!-- Chat Panel -->
    <aside class="chat-panel">
      <header class="chat-header">
        <h1>FloodWatch PH</h1>
        <p class="subtitle">AI Project Explorer</p>
      </header>
      
      <div class="chat-messages" id="chatMessages">
        <!-- Messages rendered here -->
      </div>
      
      <div class="chat-input-container">
        <textarea 
          id="chatInput" 
          placeholder="Ask about flood control projects..."
          rows="1"
        ></textarea>
        <button id="sendBtn" class="send-btn">
          <svg><!-- Send icon --></svg>
        </button>
      </div>
    </aside>

    <!-- Map Panel -->
    <main class="map-panel">
      <div id="map" class="map-container"></div>
      
      <!-- Floating controls -->
      <div class="map-controls">
        <button class="control-btn" id="resetView">
          <svg><!-- Reset icon --></svg>
        </button>
        <button class="control-btn" id="toggleClusters">
          <svg><!-- Cluster icon --></svg>
        </button>
      </div>
      
      <!-- Stats overlay -->
      <div class="stats-overlay" id="statsOverlay">
        <div class="stat-item">
          <span class="stat-label">Projects</span>
          <span class="stat-value" id="projectCount">—</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Total Budget</span>
          <span class="stat-value" id="totalBudget">—</span>
        </div>
      </div>
    </main>

    <!-- Project Details Panel -->
    <aside class="details-panel">
      <div class="project-card" id="projectCard">
        <p class="empty-state">
          Click a project on the map or ask a question to see details
        </p>
      </div>
      
      <div class="news-feed" id="newsFeed">
        <h3>Related News</h3>
        <div class="news-items">
          <!-- News cards rendered here -->
        </div>
      </div>
    </aside>
  </div>

  <!-- Scripts -->
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
  <script type="module" src="assets/js/app.js"></script>
</body>
</html>
CSS Design Tokens (assets/css/variables.css)
css:root {
  /* Color Palette */
  --primary-blue: #2563eb;
  --primary-blue-dark: #1d4ed8;
  --secondary-emerald: #10b981;
  --accent-amber: #f59e0b;
  
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-tertiary: #f1f5f9;
  
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  
  --border-light: #e2e8f0;
  --border-medium: #cbd5e1;
  
  /* Glassmorphism */
  --glass-bg: rgba(255, 255, 255, 0.8);
  --glass-border: rgba(255, 255, 255, 0.3);
  --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  
  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  
  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  
  /* Elevation */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);
  
  /* Animations */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 300ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 500ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --text-primary: #f1f5f9;
    --text-secondary: #cbd5e1;
    --glass-bg: rgba(15, 23, 42, 0.8);
  }
}
JavaScript Architecture (assets/js/app.js)
javascript// Main application controller
import { ChatManager } from './chat.js';
import { MapController } from './map.js';
import { ProjectRenderer } from './project.js';
import { NewsManager } from './news.js';

class FloodWatchApp {
  constructor() {
    this.chat = new ChatManager({
      wsUrl: 'ws://localhost:8000/api/chat',
      onMessage: this.handleChatMessage.bind(this)
    });
    
    this.map = new MapController({
      containerId: 'map',
      center: [12.8797, 121.7740], // Philippines center
      zoom: 6,
      onProjectClick: this.handleProjectClick.bind(this)
    });
    
    this.projectRenderer = new ProjectRenderer({
      containerId: 'projectCard'
    });
    
    this.news = new NewsManager({
      containerId: 'newsFeed'
    });
    
    this.initializeEventListeners();
  }
  
  handleChatMessage(message) {
    switch(message.type) {
      case 'projects':
        this.map.updateProjects(message.data);
        this.updateStats(message.data);
        break;
      case 'map_bounds':
        this.map.fitBounds(message.bbox);
        break;
      case 'news':
        this.news.render(message.data);
        break;
    }
  }
  
  handleProjectClick(project) {
    this.projectRenderer.render(project);
    this.news.fetchForProject(project.project_id);
  }
  
  // ... more methods
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.app = new FloodWatchApp();
});

🧪 Testing Strategy
Unit Tests
python# tests/test_chat.py
import pytest
from backend.services.llm_service import LLMService

def test_contractor_extraction():
    llm = LLMService()
    result = llm.extract_entities("Show me GED Construction projects")
    assert "GED CONSTRUCTION" in result.contractors

def test_budget_parsing():
    llm = LLMService()
    result = llm.parse_query("projects over ₱4M")
    assert result.filters['min_award_php'] == 4_000_000
Integration Tests
python# tests/test_search.py
def test_search_accuracy():
    response = client.post('/api/search', json={
        'filters': {'year': 2025, 'region': 'Region I'}
    })
    projects = response.json()['projects']
    assert all(p['year'] == 2025 for p in projects)
    assert all(p['region'] == 'Region I' for p in projects)
Performance Benchmarks
python# tests/test_performance.py
def test_chat_latency():
    # First response < 2s, streaming < 100ms/token
    start = time.time()
    response = websocket.send({"message": "Show projects"})
    first_token = time.time() - start
    assert first_token < 2.0

📊 Sample Queries & Responses
Query 1: Regional Overview
User: "What flood control work is happening in Region I?"
Response:
Region I has 47 active flood control projects totaling ₱245.3 million. 
The work is concentrated in Pangasinan (34 projects) and La Union (13 projects).

Top contractors:
- GED Construction - 12 projects, ₱58.2M
- Big Bertha Construction - 8 projects, ₱42.1M

Most common project type is "Construction of Flood Mitigation Structure" 
(23 projects). Would you like to see the largest projects or filter by city?
[Map zooms to Region I, pins cluster by contractor]
Query 2: Contractor Deep Dive
User: "Tell me about GED Construction"
Response:
GED Construction has been awarded 12 flood control contracts in 2025, 
all in Pangasinan's 1st District. Total awards: ₱58.2M

Notable projects:
1. Rehabilitation of Flood Mitigation Structure, Telbang - ₱4.85M
2. Construction of Line Canal, Quibuar - ₱4.85M

Average award is ₱4.85M. All contracts signed between Feb-May 2025.
Recent news mentions completion of 3 projects ahead of schedule.

⚠️ Note: 8/12 projects are concentrated in Alaminos City. 
Would you like to see the geographic distribution?
[Project cards slide in on right, news feed populates]

🎯 Advanced Features
1. Permalink Generation
javascript// Encode current state in URL
function generatePermalink() {
  const state = {
    query: currentQuery,
    filters: activeFilters,
    bounds: map.getBounds(),
    project: selectedProject?.id
  };
  const encoded = btoa(JSON.stringify(state));
  return `${window.location.origin}/?s=${encoded}`;
}
2. CSV Export
python# backend/api/export.py
@router.get("/api/export/csv")
async def export_projects(filters: ProjectFilters):
    df = search_service.search(filters).to_dataframe()
    csv = df.to_csv(index=False)
    return Response(
        content=csv,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=projects.csv"}
    )
3. Real-time Collaboration
python# Multi-user session sharing via Redis
@router.websocket("/api/chat/{session_id}")
async def chat_endpoint(websocket: WebSocket, session_id: str):
    await redis.publish(f"session:{session_id}", message)
    # Other users in same session see updates