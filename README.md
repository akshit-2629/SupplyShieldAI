# SupplyShield AI — Enterprise Multi-Agent Autonomous Supply Chain Intelligence Platform

SupplyShield AI is an enterprise-grade autonomous intelligence platform designed to monitor, identify, analyze, and mitigate supply chain disruptions in real-time. It coordinates six specialized AI agents through a Master Orchestrator, running on top of an event-driven architecture, to trace dependencies, predict inventory stockouts, discover alternative suppliers, and compile board-ready reports.

---

## 🧠 Complete AI Agent Ecosystem

SupplyShield AI is designed around a decoupled, event-driven agent model. Instead of calling each other directly, agents publish event messages to a central event bus overseen by a Master Orchestrator.

```text
                     Master Orchestrator Agent
                                 │
           ┌───────────────┬─────┴─────────┬───────────────┐
           │               │               │               │
           ▼               ▼               ▼               ▼
     News Agent       Risk Agent      Graph Agent     Supplier Agent
           │                               │               │
           └───────────────┬───────────────┘               │
                           ▼                               ▼
                 Inventory Impact Agent         Recommendation Agent
                           │
                           ▼
                  Executive Dashboard
```

### Event-Driven Communication Architecture
By decoupling communication through a message/event dispatcher, agents remain independent and highly reusable.
- **News Agent** emits `NewsDisruptionDetectedEvent`
- **Master Orchestrator** intercepts the event and routes a task to the **Risk Agent**
- **Risk Agent** scores severity and emits `RiskScoreCalculatedEvent`
- **Graph Agent** listens to risk score updates and traces product/system blast-radius, emitting `BlastRadiusTracedEvent`
- **Inventory Agent** calculates remaining stock timelines and projects stockouts, emitting `StockImpactProjectedEvent`
- **Recommendation Agent** selects alternative suppliers and generates optimization metrics.

---

## 🚀 Final Implementation Roadmap

### Phase 0: Project Foundation (Completed)
Establish the system's skeleton and production environment parameters:
* Asynchronous FastAPI setup & clean API versioning routing structures.
* Vite + React frontend client mapping.
* PostgreSQL integration using SQLAlchemy connection pooling.
* Logging & custom request Timing middlewares.
* Global exception handling and validation overrides.
* CORS headers configuration & interactive Swagger documentation.

### Phase 1: Authentication + Database + Core Backend (Completed)
Secure authorization layer using Supabase:
* User registration (Email/Password) with password strength validators.
* Secure login, session storage configuration, and password recovery.
* Google OAuth 2.0 integration & callback token parsers.
* JWT signature validation middleware using `PyJWT`.
* PostgreSQL profile setup with dynamic trigger syncing on user registration.
* Route protection guards checking active sessions.

### Phase 2: Master Orchestrator Framework (Up Next)
Build the central planning engine:
* LangGraph state-graph workflow configurations.
* Agent registry schemas & prioritized task queuing.
* Decentralized message/event bus implementation.
* Sharing state, workflow planning DAGs, execution logs, and recovery/retry rules.

### Phase 3: News Intelligence Agent
Automated collection and classification of risk signals:
* RSS feeds, Google News, Reuters scraping, and Tavily search integration.
* Scheduler mechanisms, content deduplication, and parsing algorithms.
* Extraction of countries, industries, entities, and initial severity candidates.
* Semantic embeddings similarity calculations (e.g., Cosine Similarity).

### Phase 4: Risk Assessment Agent
Quantitative transformation of signal events into business metrics:
* Weighted risk scoring engines based on categories (Geopolitics, Weather, Port congestion).
* Supplier dependency weights & historical vulnerability maps.
* Timeline modeling and confidence level scoring formulas.

### Phase 5: Knowledge Graph Agent
Intelligent dependency modeling:
* Direct visualization of component-supplier-product connections.
* Blast-radius tracing algorithms (BFS, DFS, Dijkstra).
* Degree Centrality calculations showing critical single-point dependencies.
* Dynamic node/edge state updates inside a NetworkX graph structure.

### Phase 6: Supplier Intelligence Agent
Continual profiling and performance evaluation:
* Multi-axis KPI aggregations: Reliability, compliance, lead time, and cost metrics.
* Dynamic Tier categorizations.
* Country/geographical risks assessment.

### Phase 7: Inventory Impact Agent
Deep predictive logistics modeling:
* Stock run-out projections:
  $$\text{Inventory Remaining} = \frac{\text{Current Stock}}{\text{Daily Consumption}}$$
* Lead time comparison & buffer safety stock thresholds calculations.
* Estimated revenue impact projections and production-halt predictions.

### Phase 8: Recommendation Agent
Procurement helper recommending mitigations:
* Alternative supplier scoring using TOPSIS / Multi-Criteria Decision Making (MCDM).
* Comparison grids based on lead times, cost-premiums, and compliance profiles.
* Generative text generation explaining pros/cons of alternatives.

### Phase 9: Executive Dashboard APIs
Unified portal aggregation:
* Aggregated statistics queries & caching strategies.
* Endpoint data feeds supporting charts and KPIs.
* Manual analysis triggering controls.

### Phase 10: Disruption Monitor UI
Enterprise dashboard tables:
* Grid displaying live disruption incidents.
* Sortable, filterable, and paginated rows.
* Incident detail sidebars and timeline trackers.

### Phase 11: Global Risk Map UI
Geospatial risk tracking:
* Map visualization using Leaflet.
* Marker clustering and severity-colored pulse animations.
* Location search triggers and regional statistics overlays.

### Phase 12: Knowledge Graph UI
Interactive graph visualizer:
* Node-based drawing using React Flow.
* Drag-and-drop elements, auto-layout, minimap, and zoom controls.
* Highlight paths identifying primary source dependencies.

### Phase 13: Supplier Module UI
Partner relationship manager:
* Interactive directories profiling vendors.
* Supplier performance cards, tier gauges, and lead-time trends.

### Phase 14: Inventory Impact Module UI
LOG forecasting charts:
* Linear consumption projections.
* Interactive timeline gauges showing days-remaining before stockouts.
* Warning cards listing critical components and potential revenue losses.

### Phase 15: Recommendation Module UI
Sourcing alternatives interface:
* Side-by-side vendor comparisons.
* Multi-axis Recharts Radar Charts showing scores.
* Generation logs detailing recommendation histories.

### Phase 16: AI Orchestration Center UI
Live pipeline overview:
* Graphical flow showing the Master Orchestrator workflow in real-time.
* Status panels for each agent (Idle, Thinking, Running, Success, Failure).
* Parallel process queues and execution logs console.

### Phase 17: Reports Module
Report generation:
* Export engines supporting PDF compilation.
* Auto-generated executive summaries and charts.
* Scheduler panels for daily/weekly board summaries.

### Phase 18: Alerts Engine
Internal alerting framework:
* Custom warning thresholds setup dashboard.
* Escalation paths logic.
* Desktop push alerts & visual badge notification trays.

### Phase 19: Settings Module
System control deck:
* Personal profile editor & team configurations.
* Integration settings: API key forms (Supabase, OpenAI, Tavily).
* Theme controls (Dark Mode/Light Mode).

### Phase 20: Production Optimization
Enterprise optimization:
* Redis caching for database metrics & API endpoints.
* Rate limiting rules.
* Background workers configurations.
* CI/CD, performance benchmarks, and security hardening.

---

## 📁 Repository Directory Layout

```
ShieldSupplyAi/
├── backend/            # FastAPI app — API routes, AI agents, orchestrator
│   ├── app/
│   │   ├── agents/         # 6 AI agents (news, risk, graph, supplier, inventory, recommendation)
│   │   ├── api/v1/         # REST API endpoints
│   │   ├── core/           # Config, security, logging, exceptions
│   │   ├── orchestrator/   # Master Orchestrator + event bus
│   │   └── supplier_portal/ # Supplier Portal backend module
│   ├── alembic/            # Database migrations
│   ├── requirements.txt
│   └── .env.example
├── frontend/           # Vite + React — admin dashboard + supplier portal
│   ├── src/
│   │   ├── pages/          # Admin pages + supplier portal pages
│   │   ├── components/     # Shared UI components
│   │   ├── services/       # API service layer (supplierApi.js, api.js)
│   │   ├── context/        # Auth context providers
│   │   └── lib/            # Supabase client, React Query client
│   └── .env.example
└── database/           # PostgreSQL schema SQL (37 tables, RLS, indexes)
```

---

## 🛠️ Prerequisites

Before running the project, ensure you have:

| Tool | Minimum Version | Notes |
|---|---|---|
| **Node.js** | 20.x | `node -v` |
| **Python** | 3.11+ | `python3 --version` |
| **pip** | latest | `pip install --upgrade pip` |
| **Supabase account** | — | [supabase.com](https://supabase.com) — free tier works |
| **Google OAuth credentials** | — | [Google Cloud Console](https://console.cloud.google.com) |
| **Gemini API key** | — | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| **Tavily API key** | — | [app.tavily.com](https://app.tavily.com) (News Intelligence) |

---

## 🛠️ Dev Setup Guide

### 1 · Backend setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `backend/.env` and fill in the following:

| Variable | Where to find it |
|---|---|
| `SUPABASE_URL` | Supabase Dashboard → Settings → API |
| `SUPABASE_ANON_KEY` | Supabase Dashboard → Settings → API |
| `SUPABASE_JWT_SECRET` | Supabase Dashboard → Settings → API → JWT Secret |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Dashboard → Settings → API → service_role |
| `DATABASE_URL` | Supabase Dashboard → Settings → Database → Connection string (URI) |
| `GOOGLE_CLIENT_ID` | Google Cloud Console → Credentials → OAuth 2.0 Client ID |
| `GOOGLE_CLIENT_SECRET` | Google Cloud Console → Credentials → OAuth 2.0 Client Secret |
| `GEMINI_API_KEY` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) |

```bash
# Start the API server
uvicorn app.main:app --reload
```

Verify: open `http://localhost:8000/` — you should see:
```json
{ "service": "SupplyShield AI", "status": "production-ready" }
```

Interactive API docs: `http://localhost:8000/docs`

---

### 2 · Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env
```

Edit `frontend/.env` and fill in:

| Variable | Where to find it |
|---|---|
| `VITE_SUPABASE_URL` | Same as backend `SUPABASE_URL` |
| `VITE_SUPABASE_ANON_KEY` | Same as backend `SUPABASE_ANON_KEY` — safe to expose (anon/public key) |
| `VITE_API_URL` | `http://localhost:8000/api/v1` (default — update for production) |

```bash
# Start the development server
npm run dev
```

Verify: open `http://localhost:5173/` — you should see the SupplyShield AI landing page.

---

### 3 · Database setup

Run `database/supplyshield_complete_schema.sql` in your Supabase SQL Editor:

1. Open [Supabase SQL Editor](https://supabase.com/dashboard/project/_/sql/new)
2. Paste the contents of `database/supplyshield_complete_schema.sql`
3. Click **Run**

This creates all 37 tables, RLS policies, indexes, and triggers.

---

## 🔐 Security Notes

- **Never commit `.env` files** — all secrets are gitignored by default
- The Supabase **anon key** is safe in frontend code (it is a public key restricted by Row Level Security)
- The Supabase **service_role key** must only ever live in the backend `.env` — never in frontend code
- JWT tokens are validated on every protected API endpoint using `SUPABASE_JWT_SECRET`

