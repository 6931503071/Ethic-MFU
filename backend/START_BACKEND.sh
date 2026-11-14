#!/bin/bash

# ============================================
# AI Document Generator - Backend Startup
# ============================================

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║  🚀 Starting AI Document Generator Backend   ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

echo "📍 Running at: http://localhost:8050"
echo "🏥 Health Check: http://localhost:8050/health"
echo "📤 API Endpoint: POST http://localhost:8050/api/analysis/fill"
echo ""
echo "Press CTRL+C to stop"
echo ""

python standalone_server.py
