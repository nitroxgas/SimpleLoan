# Fantasma Protocol - Quick Start Guide

## Prerequisites

✅ **Installed**:
- Python 3.11+
- Git

⚠️ **Required**:
- Node.js 18+ LTS ([Download](https://nodejs.org/))
- Elements Core (for testnet)

## Backend Setup (✅ Already Done!)

```bash
cd backend

# Virtual environment already created
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Dependencies already installed
# Database already migrated

# Start server
uvicorn src.main:app --reload
```

Backend running at: http://localhost:8000
API docs: http://localhost:8000/docs

## Frontend Setup (Next Step)

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm start
```

Frontend will run at: http://localhost:3000

## Testing the API

### Health Check
```bash
curl http://localhost:8000/health
```

### Supply Assets (Example)
```bash
curl -X POST http://localhost:8000/api/v1/supply \
  -H "Content-Type: application/json" \
  -d '{
    "user_address": "lq1qtest123",
    "asset_id": "btc_asset_id_placeholder",
    "amount": 100000000
  }'
```

### Get Positions
```bash
curl http://localhost:8000/api/v1/positions/lq1qtest123
```

## Project Status

✅ **Completed** (36/95 tasks):
- Backend API (FastAPI)
- Database (SQLite + Alembic)
- RAY math library
- Supply operations
- Position tracking
- Interest calculation
- Frontend components
- API client

⏳ **Next Steps**:
1. Install Node.js
2. Run `npm install` in frontend
3. Start frontend with `npm start`
4. Implement coordinator service (T031)
5. Setup Elements regtest
6. Deploy SimplicityHL validators

## Common Commands

### Backend
```bash
# Start server
uvicorn src.main:app --reload

# Run migrations
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "description"

# Run tests
pytest tests/ -v

# Format code
black src/
isort src/
```

### Frontend
```bash
# Start dev server
npm start

# Build for production
npm run build

# Run tests
npm test

# Lint
npm run lint

# Format
npm run format
```

## Troubleshooting

### Backend won't start
- Check if port 8000 is available
- Verify virtual environment is activated
- Run `pip install -r requirements.txt`

### Frontend won't start
- Install Node.js from https://nodejs.org/
- Run `npm install` in frontend directory
- Check if port 3000 is available

### Database errors
- Run `alembic upgrade head`
- Delete `fantasma.db` and re-run migrations

## Documentation

- **API Docs**: http://localhost:8000/docs (when backend running)
- **Specification**: `specs/001-utxo-lending-protocol/spec.md`
- **Implementation Status**: `IMPLEMENTATION_STATUS.md`
- **Tasks**: `specs/001-utxo-lending-protocol/tasks.md`
- **Contributing**: `CONTRIBUTING.md`

## Support

For issues or questions:
1. Check `IMPLEMENTATION_STATUS.md`
2. Review task list in `specs/001-utxo-lending-protocol/tasks.md`
3. Check API documentation at `/docs`

---

**Current Status**: Backend ✅ Running | Frontend ⏳ Needs `npm install`
