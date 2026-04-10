#!/bin/bash
# Setup script for AI Video Animation Search System

echo "🎬 AI Video Animation Search - Setup Script"
echo "==========================================="

# Check if running from project root
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check Python version
echo "📋 Checking Python version..."
python3 --version || { echo "❌ Python 3 not found"; exit 1; }

# Check ffmpeg
echo "📋 Checking ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  ffmpeg not found. Installing..."
    sudo apt-get update && sudo apt-get install -y ffmpeg
else
    echo "✅ ffmpeg found"
fi

# Check Docker
echo "📋 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker not found. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
else
    echo "✅ Docker found"
fi

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - GEMINI_API_KEY"
else
    echo "✅ .env file already exists"
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from app.database import init_db; init_db(); print('✅ Database initialized')"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "   1. Edit .env file with your API keys"
echo "   2. Start the API server:"
echo "      uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo "   3. Start Celery worker (in another terminal):"
echo "      celery -A app.tasks.video_tasks worker --loglevel=info -Q video_processing"
echo "   4. Visit http://localhost:8000"
echo ""
echo "📖 Read README.md for more information"
