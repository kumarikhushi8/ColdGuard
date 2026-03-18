#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}"
cat << 'EOF'
   ___      _     _  ____                     _
  / __\___| | __| |/ ___|_   _  __ _ _ __ __| |
 / /  / _ \ |/ _` | |  _| | | |/ _` | '__/ _` |
/ /__| (_) | | (_| | |_| | |_| | (_| | | | (_| |
\____/\___/|_|\__,_|\____|\__,_|\__,_|_|  \__,_|

  Cold Chain Intelligence Platform
EOF
echo -e "${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
  echo -e "${RED}Docker not found. Install from https://docker.com${NC}"
  exit 1
fi

if ! docker compose version &> /dev/null; then
  echo -e "${RED}Docker Compose V2 not found.${NC}"
  exit 1
fi

# Optional: set Anthropic key for multilingual alerts
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo -e "${YELLOW}⚠  ANTHROPIC_API_KEY not set — alerts will not be translated.${NC}"
  echo -e "   Export it: export ANTHROPIC_API_KEY=sk-ant-..."
  echo ""
fi

echo -e "${GREEN}Starting ColdGuard...${NC}"
docker compose up --build -d

echo ""
echo -e "${GREEN}Waiting for services to be healthy...${NC}"
sleep 8

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ColdGuard is running!${NC}"
echo ""
echo -e "  Dashboard  →  ${YELLOW}http://localhost:5173${NC}"
echo -e "  API docs   →  ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "  Database   →  ${YELLOW}localhost:5432${NC} (coldguard/coldguard_secret)"
echo ""
echo -e "  Logs:  docker compose logs -f"
echo -e "  Stop:  docker compose down"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
