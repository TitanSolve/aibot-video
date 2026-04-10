# AI Video Animation Search System

AI-powered search and recommendation system for video animations. Automatically analyzes videos, detects scenes, and generates rich metadata for semantic search.

## Features

- 🎬 **Automatic Scene Detection** - PySceneDetect for intelligent segmentation
- 🤖 **AI-Powered Analysis** - Gemini 2.0 for 20-parameter animation description
- 🔍 **Semantic Search** - Vector embeddings for natural language queries
- 📊 **Rich Metadata** - Animation type, style, industry, metaphors, and more
- ⚡ **Async Processing** - Celery task queue for scalable video processing
- 🗄️ **PostgreSQL + pgvector** - Structured data with vector search

## Architecture

```
Upload Video → Scene Detection → Frame Extraction → AI Description → Embeddings → Search
     ↓              ↓                   ↓                  ↓              ↓
  FastAPI      PySceneDetect        ffmpeg           Gemini 2.0      OpenAI
```

## Prerequisites

- Python 3.10+
- PostgreSQL with pgvector extension
- Redis
- ffmpeg
- Docker & Docker Compose (recommended)

## Quick Start

### 1. Clone and Setup

```bash
cd /home/ubuntu/Documents/aibot-video
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Services (Docker)

```bash
docker-compose up -d
```

This starts:
- PostgreSQL with pgvector (port 5432)
- Redis (port 6379)
- Qdrant vector database (port 6333)

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys:
# OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=...
```

### 4. Initialize Database

```bash
python -c "from app.database import init_db; init_db()"
```

### 5. Start API Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Start Celery Worker (separate terminal)

```bash
source venv/bin/activate
celery -A app.tasks.video_tasks worker --loglevel=info -Q video_processing
```

## Usage

### Upload Video

```bash
curl -X POST "http://localhost:8000/videos/upload" \
  -F "file=@your-video.mp4" \
  -F "author=Your Name" \
  -F "source=Website"
```

### Check Processing Status

```bash
curl "http://localhost:8000/videos/{video_id}"
```

### API Documentation

Visit http://localhost:8000/docs for interactive API documentation.

## 20-Parameter Analysis

Each video segment is analyzed with:

### Visual Content (4)
1. Content description
2. UI elements
3. Visual hierarchy

### Animation (5)
4. Animation type
5. Motion style
6. Easing
7. Tempo
8. Complexity

### Context (3)
9. Usage context
10. Interaction type
11. Device target

### Style (4)
12. Design style
13. Color palette
14. Typography

### Semantic (4)
15. Industries
16. Metaphors
17. Mood
18. Brand identity

### Technical (2)
19. Performance notes
20. Accessibility notes

## Project Structure

```
aibot-video/
├── app/
│   ├── api/              # API endpoints
│   │   └── upload.py     # Video upload
│   ├── services/         # Core services
│   │   ├── scene_detector.py
│   │   ├── ai_describer.py
│   │   └── embeddings.py
│   ├── tasks/            # Celery tasks
│   │   └── video_tasks.py
│   ├── utils/            # Utilities
│   │   └── video_utils.py
│   ├── config.py         # Configuration
│   ├── database.py       # Database models
│   ├── schemas.py        # Pydantic schemas
│   └── main.py           # FastAPI app
├── uploads/              # Uploaded videos
├── frames/               # Extracted frames
├── docker-compose.yml    # Services setup
└── requirements.txt      # Dependencies
```

## Development Status

### ✅ Phase 1 - Complete
- [x] Project structure
- [x] Database models (20 parameters)
- [x] Video upload API
- [x] Scene detection
- [x] Frame extraction
- [x] AI description (Gemini)
- [x] Embeddings generation
- [x] Background task processing

### 🚧 Phase 2 - Next Steps
- [ ] Search API implementation
- [ ] Qdrant integration
- [ ] Frontend interface
- [ ] Batch video processing
- [ ] Performance optimization

### 📋 Phase 3 - Future
- [ ] Chatbot interface
- [ ] Advanced recommendations
- [ ] User feedback loop
- [ ] Analytics dashboard

## Troubleshooting

### ffmpeg not found
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

### Database connection error
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart services
docker-compose restart postgres
```

### Celery tasks not processing
```bash
# Check Redis connection
redis-cli ping

# View Celery logs
celery -A app.tasks.video_tasks worker --loglevel=debug
```

## Contributing

This is Phase 1 implementation. Contributions welcome!

## License

MIT
