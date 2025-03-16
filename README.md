# Jamaica Police Intelligence System (JISP)

A backend API for real-time intelligence gathering and resource allocation for the Jamaica Police.

## Overview

JISP uses machine learning to analyze intelligence reports, predict crime levels, and optimally allocate police resources across Jamaica's 14 parishes. The system features real-time updates via WebSockets, an active learning component that continually improves predictions, and an API for integration with frontend applications.

## Features

- Real-time intelligence data collection and analysis
- ML-powered crime prediction using RandomForest classifier
- Automated resource allocation based on crime levels
- Parish-specific insights and statistics
- WebSocket support for live updates
- Active learning system that improves with new data

## Setup Instructions

### Prerequisites

- Python 3.9+
- PostgreSQL
- Poetry (for dependency management)

### Environment Setup

1. **Clone the repository**

```bash
git clone https://github.com/your-username/jamaica-police-intelligence.git
cd jamaica-police-intelligence
```

2. **Install dependencies with Poetry**

If you don't have Poetry installed, install it first:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Then install dependencies:

```bash
poetry install
```

Alternatively, you can use pip with the requirements file:

```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

Create a `.env` file in the project root:

```
DATABASE_URL=postgresql://postgres:postgres@localhost/police_intelligence_db
SECRET_KEY=your-secret-key-here
```

Adjust the `DATABASE_URL` according to your PostgreSQL setup.

### Database Setup

1. **Create PostgreSQL database**

```bash
createdb police_intelligence_db
```

2. **Initialize database tables**

```bash
python create_tables.py
```

3. **Populate database with initial data**

```bash
python add_data.py
```

4. **Train the initial ML model and allocate resources**

```bash
python train_and_allocate.py
```

This script will:
- Generate synthetic intelligence data
- Train the crime prediction model
- Update crime levels for all parishes
- Allocate police resources based on predictions

## Running the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

After starting the server, API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Key Endpoints

- `/api/v1/intelligence` - Create and retrieve intelligence data
- `/api/v1/parishes` - Parish information and statistics
- `/api/v1/parishes/allocate-resources` - Trigger resource allocation
- `/api/v1/insights` - Get system insights and recommendations
- `/ws` - WebSocket endpoint for real-time updates

## Additional Scripts

- `reset_db.py` - Reset the database and populate with fresh data
- `query_db.py` - Check database contents
- `fix_allocations.py` - Manually fix resource allocations if needed

## Architecture

The system follows a modular architecture:

- `app/api` - API endpoints
- `app/db` - Database session and initialization
- `app/models` - SQLAlchemy models
- `app/schemas` - Pydantic schemas for API
- `app/ml` - Machine learning models and feature engineering
- `app/services` - Business logic services
- `app/socket` - WebSocket connection management

## Machine Learning Models

The system employs two main ML components:

1. **Crime Prediction Model** - A RandomForest classifier that predicts crime levels based on intelligence data.
2. **Resource Allocator** - An algorithm that optimally distributes police officers across parishes based on predicted crime levels.

The active learning system continuously improves these models as new intelligence data comes in.

## Troubleshooting

If you encounter issues