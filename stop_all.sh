#!/usr/bin/env bash
# ==============================================================================
# PBL6 - SCRIPT DỪNG TOÀN BỘ CÁC SERVICE
# ==============================================================================

# Định dạng màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"

echo -e "${YELLOW}🛑 Đang dừng toàn bộ các service của hệ thống PBL6...${NC}"

# 1. Dừng theo file PID nếu có
if [ -d "$LOG_DIR" ]; then
  for pid_file in "$LOG_DIR"/*.pid; do
    if [ -f "$pid_file" ]; then
      pid=$(cat "$pid_file" 2>/dev/null || true)
      service_name=$(basename "$pid_file" .pid)
      if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo -e "   ${BLUE}→${NC} Đang dừng service ${YELLOW}$service_name${NC} (PID: $pid)..."
        kill -15 "$pid" 2>/dev/null || true
      fi
      rm -f "$pid_file"
    fi
  done
fi

# 2. Giải phóng triệt để các cổng nếu còn tiến trình chiếm dụng
PORTS=(3000 8001 8002 8003 8004 8005)
for port in "${PORTS[@]}"; do
  pids=$(lsof -ti :"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo -e "   ${RED}→ Giải phóng cổng $port (PIDs: $pids)...${NC}"
    echo "$pids" | xargs kill -9 2>/dev/null || true
  fi
done

# 3. Dừng các tiến trình tail log còn sót lại
pkill -f "tail -n 0 -f .*logs/" 2>/dev/null || true

echo -e "${GREEN}==============================================================${NC}"
echo -e "${GREEN}✅ Tất cả các service đã được dừng và giải phóng cổng sạch sẽ!${NC}"
echo -e "${GREEN}==============================================================${NC}"

