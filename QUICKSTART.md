# 🚀 Quick Start Guide - AI Video Animation Search

## Phase 1 Implementation Complete ✅

You now have a fully functional video processing and analysis system!

---

## What's Included

### ✅ Core Features
- **Video Upload API** - Upload videos via web interface or API
- **Automatic Scene Detection** - PySceneDetect splits videos into segments
- **Frame Extraction** - ffmpeg extracts key frames from each segment
- **AI Analysis** - Gemini 2.0 describes animations with 20 parameters
- **Vector Embeddings** - OpenAI embeddings for semantic search
- **Background Processing** - Celery handles async video processing
- **Database Storage** - PostgreSQL with pgvector for efficient queries

### 📊 20-Parameter Analysis
Each segment gets analyzed for:
1. Content description
2. UI elements
3. Visual hierarchy
4. Animation type
5. Motion style
6. Easing
7. Tempo
8. Complexity
9. Usage context
10. Interaction type
11. Device target
12. Design style
13. Color palette
14. Typography
15. Industries
16. Metaphors
17. Mood
18. Brand identity
19. Performance notes
20. Accessibility notes

---

## Setup (5 minutes)

### Option 1: Automatic Setup

```bash
cd /home/ubuntu/Documents/aibot-video
./setup.sh
```

This will:
- Check dependencies
- Install ffmpeg if needed
- Create virtual environment
- Install Python packages
- Start Docker services (PostgreSQL, Redis, Qdrant)
- Initialize database

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment file
cp .env.example .env
# Edit .env with your API keys

# 4. Start services
docker-compose up -d

# 5. Initialize database
python -c "from app.database import init_db; init_db()"
```

---

## Running the System

You need **3 terminals**:

### Terminal 1: API Server
```bash
cd /home/ubuntu/Documents/aibot-video
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Celery Worker
```bash
cd /home/ubuntu/Documents/aibot-video
source venv/bin/activate
celery -A app.tasks.video_tasks worker --loglevel=info -Q video_processing
```

### Terminal 3: Optional - Monitor
```bash
# Watch Celery tasks
celery -A app.tasks.video_tasks flower

# Or monitor logs
docker-compose logs -f
```

---

## Usage Examples

### 1. Web Interface
Open browser: **http://localhost:8000**
- Upload video via drag-and-drop interface
- Monitor processing status
- View completed videos

### 2. API Upload
```bash
curl -X POST "http://localhost:8000/videos/upload" \
  -F "file=@your-animation.mp4" \
  -F "author=Designer Name" \
  -F "source=Dribbble"
```

### 3. Check Status
```bash
# List all videos
curl "http://localhost:8000/videos/"

# Get specific video
curl "http://localhost:8000/videos/{video_id}"
```

### 4. API Documentation
Visit: **http://localhost:8000/docs** for interactive Swagger UI

---

## What Happens When You Upload?

1. **Upload** (2-5 seconds)
   - Video saved to `uploads/`
   - Metadata extracted (duration, fps, resolution)
   - Database record created
   - Task queued

2. **Scene Detection** (10-30 seconds)
   - PySceneDetect analyzes video
   - Identifies scene changes
   - Creates segments

3. **Frame Extraction** (5-15 seconds)
   - ffmpeg extracts 3 key frames per segment
   - Frames saved to `frames/{video_id}/segment_XXXX/`

4. **AI Analysis** (20-60 seconds per segment)
   - Gemini analyzes each frame set
   - Generates 20-parameter description
   - JSON response with structured data

5. **Embedding Generation** (1-2 seconds per segment)
   - OpenAI creates vector embeddings
   - Stored in PostgreSQL with pgvector

6. **Complete!**
   - Video status: `completed`
   - Segments searchable
   - Ready for Phase 2 search implementation

---

## File Structure After Processing

```
aibot-video/
├── uploads/
│   └── {video-uuid}.mp4              # Original video
├── frames/
│   └── {video-uuid}/
│       ├── segment_0000/
│       │   ├── frame_000.jpg         # Key frame 1
│       │   ├── frame_001.jpg         # Key frame 2
│       │   └── frame_002.jpg         # Key frame 3
│       ├── segment_0001/
│       │   └── ...
│       └── ...
```

---

## Monitoring & Debugging

### Check Services
```bash
# All services
docker-compose ps

# PostgreSQL
docker-compose logs postgres

# Redis
docker-compose logs redis

# Qdrant
docker-compose logs qdrant
```

### Database
```bash
# Connect to PostgreSQL
docker exec -it aibot_postgres psql -U aibot -d aibot_video

# View videos
SELECT id, filename, status, duration FROM videos;

# View segments
SELECT video_id, segment_index, animation_type, usage_context FROM segments;
```

### Celery
```bash
# View active tasks
celery -A app.tasks.video_tasks inspect active

# View task stats
celery -A app.tasks.video_tasks inspect stats
```

---

## Common Issues

### ffmpeg not found
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### Port already in use
```bash
# Change port in docker-compose.yml or stop conflicting service
sudo lsof -i :5432  # Check what's using PostgreSQL port
```

### Celery not processing
```bash
# Check Redis connection
redis-cli ping

# Restart Redis
docker-compose restart redis

# Check task queue
redis-cli
> LLEN celery
```

### Out of memory
```bash
# Reduce concurrent workers
celery -A app.tasks.video_tasks worker --concurrency=2

# Or process smaller videos
```

---

## Performance Tips

### For Large Videos (>100MB)
- Increase `MAX_VIDEO_SIZE_MB` in .env
- Adjust `SCENE_THRESHOLD` for fewer segments
- Reduce `MAX_FRAMES_PER_SEGMENT`

### For Faster Processing
- Use Gemini Flash model: `GEMINI_MODEL=gemini-2.0-flash-exp`
- Reduce frame extraction: `MAX_FRAMES_PER_SEGMENT=1`
- Increase Celery workers: `--concurrency=4`

### For Better Quality
- Use Gemini Pro: `GEMINI_MODEL=gemini-2.5-pro`
- Extract more frames: `MAX_FRAMES_PER_SEGMENT=5`
- Lower scene threshold: `SCENE_THRESHOLD=20.0`

---

## Next: Phase 2

Phase 1 is complete! Now you can move to Phase 2:

### Implement Search
- [ ] Qdrant collection setup
- [ ] Vector similarity search
- [ ] Filter by parameters (animation_type, style, industry)
- [ ] Ranking and reranking
- [ ] Search API endpoint

### Build Chatbot
- [ ] Natural language query understanding
- [ ] Context-aware recommendations
- [ ] Clarification questions
- [ ] Example-based search

See **README.md** for full Phase 2 roadmap.

---

## API Keys Required

**OpenAI** (for embeddings):
- Get at: https://platform.openai.com/api-keys
- Add to .env: `OPENAI_API_KEY=sk-...`

**Google Gemini** (for video analysis):
- Get at: https://ai.google.dev/
- Add to .env: `GEMINI_API_KEY=...`

---

## Support

- 📖 **Full docs**: README.md
- 🐛 **Issues**: Check logs in docker-compose
- 💬 **API docs**: http://localhost:8000/docs

---

**Ready to process your first video? Start the services and upload! 🎬**
