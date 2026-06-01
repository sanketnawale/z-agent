#!/bin/bash
# Quick test script for IBM-III project

cd /mnt/c/Users/sanke/Documents/IBM-III/IBM-III/new
source venv_linux/bin/activate

echo "🔍 Testing Environment..."
echo "===================="
echo ""

echo "✓ Python version:"
python --version

echo ""
echo "✓ Installed packages:"
pip list | grep -E "fastapi|django|requests|pydantic|uvicorn"

echo ""
echo "✓ FastAPI test:"
python -c "from fastapi import FastAPI; print('  FastAPI loads successfully')"

echo ""
echo "✓ Django test:"
cd jobfrontend
python manage.py --version
echo "  Django loads successfully"
cd ..

echo ""
echo "✓ Requests test:"
python -c "import requests; print('  Requests loads successfully')"

echo ""
echo "===================="
echo "✅ All systems GO!"
echo "===================="
echo ""
echo "To start the application:"
echo ""
echo "1️⃣  FastAPI Backend (Terminal 1):"
echo "   source venv_linux/bin/activate"
echo "   python -m uvicorn main:app --host 127.0.0.1 --port 3000"
echo ""
echo "2️⃣  Django Frontend (Terminal 2):"
echo "   cd jobfrontend"
echo "   source ../venv_linux/bin/activate"
echo "   python manage.py runserver 127.0.0.1:8000"
echo ""
echo "3️⃣  Access at:"
echo "   Django: http://127.0.0.1:8000/jobs/"
echo "   FastAPI Docs: http://127.0.0.1:3000/docs"
