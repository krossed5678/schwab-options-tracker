#!/bin/bash

# Schwab Options Tracker - Quick Setup Script
echo "🚀 Setting up Schwab Options Tracker..."

# Check Python version
python_version=$(python --version 2>&1 | grep -o '[0-9]\.[0-9]')
if [ "$(echo "$python_version >= 3.9" | bc)" -eq 1 ]; then
    echo "✅ Python $python_version detected"
else
    echo "❌ Python 3.9+ required. Current version: $python_version"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.template .env
    echo "⚠️ Please edit .env file with your Schwab API credentials"
else
    echo "✅ .env file already exists"
fi

# Create tokens directory
mkdir -p tokens

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Schwab API credentials"
echo "2. Run: streamlit run main.py"
echo "3. Complete OAuth authentication in the web interface"
echo ""
echo "For detailed instructions, see README.md"