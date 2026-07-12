# SupplyShield AI – Autonomous Supply Chain Disruption Platform (Phase 1)

SupplyShield AI is an enterprise-grade autonomous intelligence platform designed to monitor global disruptions, analyze supply chain risks, predict operational impact, suggest alternative suppliers, and compile automated executive briefs. 

This phase establishes the system architecture, logging foundations, database connectivity, and testing structures to serve as a robust launchpad for future multi-agent LangGraph orchestrations.

---

## 🏗️ System Architecture

SupplyShield AI is designed around **Clean Architecture** principles:
* **Presentation Layer (APIs)**: FastAPI manages request routing, input validation, and serialization.
* **Domain Layer (Models)**: SQLAlchemy 2.0 maps entity schemas dynamically with declarative typing.
* **Infrastructure Layer**: PostgreSQL handles reliable data persistence; Alembic automates structural migrations.
* **Cross-Cutting Concerns**: Pydantic V2 orchestrates type safety, python-dotenv reads environmental variables, and python logging rotates disk logs.

---

## 📁 Repository Structure

```
backend/
├── alembic/                  # Database migration schemas
│   ├── env.py                # Database connection lifecycle hook
│   └── script.py.mako        # Migration generator template
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── health.py  # Health monitoring APIs
│   │       │   └── security_placeholder.py
│   │       └── api.py        # Centralized version routing
│   ├── core/
│   │   ├── config.py         # Central settings configuration
│   │   ├── exceptions.py     # Custom exceptions & global handlers
│   │   ├── logger.py         # Logging configuration & middlewares
│   │   └── security.py       # Authentication placeholders (JWT/API Keys)
│   ├── db/
│   │   ├── base.py           # Unified model registry import
│   │   ├── session.py        # SQLAlchemy session factories
│   │   └── models/           # Declarative database entities
│   │       ├── base.py       # Custom base class with audit fields
│   │       └── disruption.py # DisruptionEvent schema
│   ├── schemas/
│   │   └── health.py         # Pydantic validation models
│   ├── services/             # Future agent services
│   ├── utils/                # General support functions
│   └── main.py               # Application bootstrap
├── tests/                    # Pytest suite
│   ├── conftest.py           # Test fixtures and database mocks
│   ├── test_config.py        # Environment loader checks
│   ├── test_errors.py        # Exception mapper checks
│   └── test_health.py        # Endpoint health checks
├── .env.example              # Development settings template
├── .gitignore                # Files excluded from source control
├── alembic.ini               # Alembic initialization config
├── README.md                 # Project README
└── requirements.txt          # Package dependencies file
```

---

## 🛠️ Local Installation & Setup

### 1. Prerequisites
Ensure you have **Python 3.12+** installed on your system.

### 2. Clone the Repository and Navigate to backend
```bash
cd backend
```

### 3. Create a Virtual Environment & Activate
On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```
On Windows:
```cmd
python -m venv venv
venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Variables Setup

Duplicate the `.env.example` file and create a `.env` file inside the `backend/` directory:
```bash
cp .env.example .env
```

Configure the connection variables as appropriate for your PostgreSQL environment:
```ini
APP_NAME="SupplyShield AI"
APP_VERSION="1.0.0"
DEBUG=true
ENVIRONMENT="development"
LOG_LEVEL="INFO"

# Database connection details
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=supplyshield
```

---

## 🗄️ Database Migrations

Alembic will automatically load database credentials from the settings module dynamically.

### Generate Initial Migration Revision
```bash
alembic revision --autogenerate -m "Initial schema setup"
```

### Apply Migrations to PostgreSQL Database
```bash
alembic upgrade head
```

---

## 🚀 Running the Platform

Launch the development server utilizing **Uvicorn**:
```bash
uvicorn app.main:app --reload
```
Once launched:
* The interactive API docs will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)
* Root welcome status check: [http://localhost:8000/](http://localhost:8000/)
* V1 API Health check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 🧪 Testing Suite

Execute the `pytest` test suite:
```bash
pytest tests/ -v
```
This runs assertions validating health status codes, connection query pings, configurations settings, validation errors, and custom exception handler payloads using SQLite memory databases for speed and environment isolation.

---

## 🛣️ Future Roadmap

* **Phase 2 (Agent Orchestration)**: Implement multi-agent workflows with LangGraph running LLM nodes via Google Gemini.
* **Phase 3 (RAG Integration)**: Add vector query indexing with Qdrant and knowledge graph ingestion.
* **Phase 4 (Reporting & Dashboard)**: Build a frontend interface displaying disruption maps and alternative supplier recommendation flows.
