#!/bin/bash
# =================================================================
# Quick Database Migration Script
# =================================================================
# This script migrates database schemas and sample users to Railway
#
# Usage:
#   1. Edit the DATABASE_URL below
#   2. Run: ./QUICK_MIGRATE.sh
# =================================================================

# 🎨 Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   BDD Property Tracker - DB Migration     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# =================================================================
# 📝 STEP 1: Configure Database URL
# =================================================================
# Get this from Railway → Database → Connect → Public URL
# Format: postgresql://user:password@host:port/database

DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:PORT/railway"

# =================================================================
# ⚠️  SAFETY CHECK
# =================================================================
if [[ "$DATABASE_URL" == *"YOUR_PASSWORD"* ]]; then
    echo -e "${RED}❌ Error: Please edit this script and set your DATABASE_URL${NC}"
    echo -e "${YELLOW}   Line 23: DATABASE_URL=\"postgresql://...\"${NC}"
    echo ""
    echo "Get your URL from:"
    echo "  Railway → Database → Connect → Public URL (copy)"
    exit 1
fi

echo -e "${GREEN}✅ Database URL configured${NC}"
echo ""

# =================================================================
# 📂 STEP 2: Navigate to Server Directory
# =================================================================
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}📂 Working directory: $SCRIPT_DIR${NC}"
echo ""

# =================================================================
# 🐍 STEP 3: Activate Virtual Environment
# =================================================================
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Error: Virtual environment not found${NC}"
    echo "Please create it first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# =================================================================
# 📦 STEP 4: Create Database Tables
# =================================================================
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   STEP 1: Creating Database Tables        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}⚠️  WARNING: This will DROP all existing tables!${NC}"
echo -e "${YELLOW}   Press Ctrl+C within 5 seconds to cancel...${NC}"
echo ""
sleep 5

DATABASE_URL="$DATABASE_URL" python3 create_tables.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to create tables${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Database tables created successfully!${NC}"
echo ""

# =================================================================
# 👥 STEP 5: Create Sample Users
# =================================================================
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   STEP 2: Creating Sample Users           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

DATABASE_URL="$DATABASE_URL" python3 create_sample_users.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to create users${NC}"
    exit 1
fi

echo ""

# =================================================================
# 🎉 STEP 6: Success Message
# =================================================================
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Migration Complete! 🎉            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📋 What was created:${NC}"
echo "   ✅ 10 database tables"
echo "   ✅ 4 test users (see output above)"
echo ""
echo -e "${BLUE}🔐 Login credentials are displayed above${NC}"
echo -e "${YELLOW}   💾 Save them somewhere safe!${NC}"
echo ""
echo -e "${BLUE}📚 Next steps:${NC}"
echo "   1. Deploy your server to Railway"
echo "   2. Set environment variables in Railway"
echo "   3. Test login with the sample users"
echo ""
echo -e "${BLUE}📖 For more details, see:${NC}"
echo "   - DATABASE_MIGRATION_GUIDE.md"
echo "   - STAGING_CREDENTIALS.md (if this was staging)"
echo ""

