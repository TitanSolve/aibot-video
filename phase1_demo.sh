#!/bin/bash

echo "==================================="
echo "PHASE 1 DEMONSTRATION"
echo "==================================="

# Navigate to project directory
cd /home/ubuntu/Documents/aibot-video
source venv/bin/activate

# Kill existing processes
echo "Stopping existing services..."
pkill -9 -f "uvicorn app.main"
pkill -9 -f "celery.*video_tasks"
sleep 2

# Start FastAPI
echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &
FASTAPI_PID=$!
echo "FastAPI PID: $FASTAPI_PID"

# Wait for FastAPI to start
sleep 5

# Start Celery worker
echo "Starting Celery worker..."
celery -A app.tasks.video_tasks worker --loglevel=info --pool=solo > /tmp/celery.log 2>&1 &
CELERY_PID=$!
echo "Celery PID: $CELERY_PID"

# Wait for Celery to start
sleep 3

echo ""
echo "Services running:"
echo "  FastAPI: http://localhost:8000 (PID: $FASTAPI_PID)"
echo "  Celery Worker (PID: $CELERY_PID)"
echo ""

# Upload videos
echo "Uploading sample1.mp4 and sample2.mp4..."
python upload_test_videos.py /home/ubuntu/Documents/sample1.mp4 /home/ubuntu/Documents/sample2.mp4

echo ""
echo "==================================="
echo "To stop services, run:"
echo "  kill $FASTAPI_PID $CELERY_PID"
echo "==================================="
