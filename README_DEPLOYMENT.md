# 📄 CVision AI - CV Analysis & Interview Simulation Platform

> Intelligent CV analysis and AI-powered interview preparation with job matching

## 🎯 Features

- 📄 **CV Analysis**: Extract and analyze CV information using AI
- 🎤 **Interview Simulation**: Practice with AI-generated interview questions
- 📊 **Scoring System**: Real-time evaluation of interview answers
- 💼 **Job Matching**: Match your profile to job opportunities
- 🔐 **User Authentication**: Secure login and registration with JWT tokens
- 🚀 **Production Ready**: Deployed on Render with PostgreSQL

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│     CVision AI Application              │
├──────────────────┬──────────────────────┤
│   Frontend       │      Backend         │
│   (React)        │      (FastAPI)       │
│   Port: 5173     │      Port: 8000      │
│   Vite dev       │      SQLAlchemy ORM  │
│                  │      PostgreSQL      │
└──────────────────┴──────────────────────┘
```

## 📋 Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database management
- **PostgreSQL**: Production database (SQLite for local dev)
- **Pydantic**: Data validation
- **JWT**: Authentication
- **Alembic**: Database migrations

### Frontend
- **React 18**: UI framework
- **Vite**: Build tool
- **TailwindCSS**: Styling (if used)
- **Zustand**: State management
- **Axios**: HTTP client

### AI/ML
- **spaCy**: NLP processing
- **sentence-transformers**: Semantic similarity
- **scikit-learn**: ML utilities

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (for production) or SQLite (for development)

### Local Development

#### 1. Clone and Setup Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

#### 2. Configure Database

Create `.env` in `backend/` directory:

```env
# Local Development (SQLite)
DATABASE_URL=sqlite+aiosqlite:///./cv_vision_ai.db
SYNC_DATABASE_URL=sqlite:///./cv_vision_ai.db

# Or PostgreSQL (if installed)
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cv_vision_ai
# SYNC_DATABASE_URL=postgresql://user:password@localhost:5432/cv_vision_ai

SECRET_KEY=your-secret-key-minimum-32-characters-long
DEBUG=True
ENVIRONMENT=development
```

#### 3. Initialize Database

```bash
cd backend
alembic upgrade head
```

#### 4. Run Backend

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend accessible at: http://127.0.0.1:8000

#### 5. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend accessible at: http://localhost:5173

## 📖 API Documentation

Once backend is running:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 🔑 Authentication Flow

1. User registers → POST `/api/v1/auth/register`
2. JWT tokens issued → access_token + refresh_token
3. Tokens stored in localStorage
4. All API requests include Authorization header
5. Token refresh on expiry → POST `/api/v1/auth/refresh`

## 📚 Project Structure

```
cv-vision-ai/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py          # Configuration
│   │   ├── models/
│   │   │   ├── user.py            # User model
│   │   │   ├── interview.py        # Interview models
│   │   │   └── ...
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py         # Auth endpoints
│   │   │       ├── interviews.py   # Interview endpoints
│   │   │       └── ...
│   │   ├── services/
│   │   │   └── interview_service.py
│   │   ├── database.py
│   │   └── main.py                # App entry point
│   ├── alembic/
│   │   └── versions/              # DB migrations
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
│   ├── vite.config.js
│   └── package.json
├── alembic.ini
├── render.yaml                    # Render deployment config
└── DEPLOYMENT.md                  # Detailed deployment guide
```

## 🐛 Common Issues & Fixes

### Backend doesn't start
```
ERROR: Exception in ASGI application
```
**Solution**: Ensure `.env` is properly configured and database is initialized

### Frontend infinite loading
**Solution**: Check CORS configuration in `backend/app/main.py`

### Database connection error
**Solution**: 
```bash
# Recreate database
rm cv_vision_ai.db
alembic upgrade head
```

### Port already in use
```bash
# Change port
uvicorn app.main:app --port 8001
```

## 🚀 Deployment on Render

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

### Quick Deploy

1. Push to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Connect GitHub account
4. Create new Web Service
5. Select `cv-vision-ai` repository
6. Render reads `render.yaml` automatically
7. PostgreSQL database is created automatically
8. Click "Create Web Service" and deploy!

**Deployment URL**: Will be provided by Render after deployment (~5-10 min)

## 📝 Environment Variables

### Development
```env
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=sqlite+aiosqlite:///./cv_vision_ai.db
```

### Production (Render)
```env
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=<Render PostgreSQL URL>  # Auto-injected
SECRET_KEY=<Generate with: openssl rand -hex 32>
```

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
pytest
```

### Run Frontend Tests
```bash
cd frontend
npm test
```

## 📚 Database Migrations

### Create New Migration
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations
```bash
alembic upgrade head
```

### Rollback Migration
```bash
alembic downgrade -1
```

## 🔒 Security

- ✅ JWT token-based authentication
- ✅ Password hashing with bcrypt
- ✅ CORS protection
- ✅ Environment variables for secrets
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ⚠️ Always change `SECRET_KEY` in production
- ⚠️ Never commit `.env` files

## 📦 Deployment Checklist

- [ ] Create `.env.production` with secure values
- [ ] Generate strong `SECRET_KEY`: `openssl rand -hex 32`
- [ ] Set `DEBUG=False`
- [ ] Set `ENVIRONMENT=production`
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Configure PostgreSQL on Render
- [ ] Test all endpoints before going live
- [ ] Setup monitoring and logging
- [ ] Configure backups for database

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 👨‍💻 Author

Created with ❤️ for CV analysis and interview preparation

## 🆘 Support

- 📧 Email: support@cvisionai.com (placeholder)
- 💬 Issues: GitHub Issues
- 📖 Docs: [DEPLOYMENT.md](./DEPLOYMENT.md)

---

**Happy interviewing! 🚀**
