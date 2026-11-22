#!/usr/bin/env bash
# ==============================================================================
# PBL6 - SCRIPT KHỞI CHẠY TẤT CẢ CÁC SERVICE KÈM LOG THEO MÀU
# ==============================================================================

# Định dạng màu sắc ANSI
BOLD='\033[1m'
NC='\033[0m' # No Color
CLR_ACCOUNT='\033[1;36m'      # Cyan
CLR_CONTENT='\033[1;32m'      # Green
CLR_LEARNING='\033[1;33m'     # Yellow
CLR_PAYMENT='\033[1;35m'      # Magenta
CLR_NOTIF='\033[1;34m'        # Blue
CLR_FRONTEND='\033[1;37m'     # White/Bold
CLR_INFO='\033[0;36m'
CLR_SUCCESS='\033[0;32m'
CLR_WARN='\033[0;33m'
CLR_ERR='\033[0;31m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

echo -e "${BOLD}${CLR_INFO}======================================================================${NC}"
echo -e "${BOLD}🚀 KHỞI ĐỘNG HỆ THỐNG TỰ HỌC TIẾNG ANH PBL6 (MICROSERVICES & FRONTEND)${NC}"
echo -e "${BOLD}${CLR_INFO}======================================================================${NC}"

# 1. Tìm đường dẫn công cụ uv và node/npm
UV=""
if command -v uv &>/dev/null; then
  UV="uv"
elif [ -f "$HOME/.local/bin/uv" ]; then
  UV="$HOME/.local/bin/uv"
elif [ -f "/Users/admin/.local/bin/uv" ]; then
  UV="/Users/admin/.local/bin/uv"
else
  echo -e "${CLR_ERR}❌ Không tìm thấy công cụ 'uv'. Vui lòng cài đặt uv hoặc thêm vào PATH.${NC}"
  exit 1
fi

NPM=""
if command -v npm &>/dev/null; then
  NPM="npm"
elif [ -f "/usr/local/bin/npm" ]; then
  NPM="/usr/local/bin/npm"
else
  echo -e "${CLR_ERR}❌ Không tìm thấy 'npm'. Vui lòng cài đặt Node.js/npm.${NC}"
  exit 1
fi

# 2. Dọn dẹp các tiến trình cũ đang chiếm cổng nếu có
echo -e "${CLR_INFO}🔍 Kiểm tra và giải phóng các cổng (3000, 8001 - 8005)...${NC}"
PORTS=(3000 8001 8002 8003 8004 8005)
for port in "${PORTS[@]}"; do
  pids=$(lsof -ti :"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo -e "   ${CLR_WARN}⚠️ Cổng $port đang bị chiếm bởi PID $pids. Đang giải phóng...${NC}"
    echo "$pids" | xargs kill -9 2>/dev/null || true
  fi
done

# Làm rỗng các tệp log cũ để hiển thị log phiên mới
> "$LOG_DIR/account.log"
> "$LOG_DIR/content.log"
> "$LOG_DIR/learning.log"
> "$LOG_DIR/payment.log"
> "$LOG_DIR/notification.log"
> "$LOG_DIR/frontend.log"

# Mảng lưu trữ PID để dọn dẹp khi thoát
PIDS=()
TAIL_PIDS=()

# Hàm xử lý dọn dẹp khi người dùng nhấn Ctrl+C hoặc tắt script
cleanup() {
  echo ""
  echo -e "${CLR_WARN}🛑 Nhận tín hiệu dừng (Ctrl+C). Đang tắt tất cả các service...${NC}"

  # Dừng các tiến trình tail log
  for tpid in "${TAIL_PIDS[@]}"; do
    kill "$tpid" 2>/dev/null || true
  done

  # Dừng các tiến trình service
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill -15 "$pid" 2>/dev/null || true
    fi
  done

  # Đợi nhẹ rồi giải phóng triệt để cổng
  sleep 1
  for port in 3000 8001 8002 8003 8004 8005; do
    lsof -ti :"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
  done

  rm -f "$LOG_DIR"/*.pid 2>/dev/null || true
  echo -e "${CLR_SUCCESS}✅ Toàn bộ hệ thống đã được dừng an toàn!${NC}"
  exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 3. Khởi chạy 5 Backend Microservices
echo -e "${CLR_INFO}⚙️  Đang khởi động 5 Backend Services...${NC}"

# Account Service (Port 8001)
(
  cd "$ROOT_DIR/Backend/services/account"
  exec "$UV" run uvicorn account.main:app --host 0.0.0.0 --port 8001
) > "$LOG_DIR/account.log" 2>&1 &
PID_ACCOUNT=$!
PIDS+=("$PID_ACCOUNT")
echo "$PID_ACCOUNT" > "$LOG_DIR/account.pid"
echo -e "   ${CLR_ACCOUNT}● Account Service${NC}      đang khởi chạy trên cổng ${BOLD}8001${NC} (PID: $PID_ACCOUNT)"

# Content Service (Port 8002)
(
  cd "$ROOT_DIR/Backend/services/content"
  exec "$UV" run uvicorn content.main:app --host 0.0.0.0 --port 8002
) > "$LOG_DIR/content.log" 2>&1 &
PID_CONTENT=$!
PIDS+=("$PID_CONTENT")
echo "$PID_CONTENT" > "$LOG_DIR/content.pid"
echo -e "   ${CLR_CONTENT}● Content Service${NC}      đang khởi chạy trên cổng ${BOLD}8002${NC} (PID: $PID_CONTENT)"

# Learning Service (Port 8003)
(
  cd "$ROOT_DIR/Backend/services/learning"
  exec "$UV" run uvicorn learning.main:app --host 0.0.0.0 --port 8003
) > "$LOG_DIR/learning.log" 2>&1 &
PID_LEARNING=$!
PIDS+=("$PID_LEARNING")
echo "$PID_LEARNING" > "$LOG_DIR/learning.pid"
echo -e "   ${CLR_LEARNING}● Learning Service${NC}     đang khởi chạy trên cổng ${BOLD}8003${NC} (PID: $PID_LEARNING)"

# Payment Service (Port 8004)
(
  cd "$ROOT_DIR/Backend/services/payment"
  exec "$UV" run uvicorn payment.main:app --host 0.0.0.0 --port 8004
) > "$LOG_DIR/payment.log" 2>&1 &
PID_PAYMENT=$!
PIDS+=("$PID_PAYMENT")
echo "$PID_PAYMENT" > "$LOG_DIR/payment.pid"
echo -e "   ${CLR_PAYMENT}● Payment Service${NC}      đang khởi chạy trên cổng ${BOLD}8004${NC} (PID: $PID_PAYMENT)"

# Notification Service (Port 8005)
(
  cd "$ROOT_DIR/Backend/services/notification"
  exec "$UV" run uvicorn notification.main:app --host 0.0.0.0 --port 8005
) > "$LOG_DIR/notification.log" 2>&1 &
PID_NOTIF=$!
PIDS+=("$PID_NOTIF")
echo "$PID_NOTIF" > "$LOG_DIR/notification.pid"
echo -e "   ${CLR_NOTIF}● Notification Service${NC} đang khởi chạy trên cổng ${BOLD}8005${NC} (PID: $PID_NOTIF)"

# 4. Khởi chạy Frontend Next.js (Port 3000)
echo -e "${CLR_INFO}🌐 Đang khởi động Frontend (Next.js)...${NC}"
(
  cd "$ROOT_DIR/Frontend"
  exec "$NPM" run dev
) > "$LOG_DIR/frontend.log" 2>&1 &
PID_FRONTEND=$!
PIDS+=("$PID_FRONTEND")
echo "$PID_FRONTEND" > "$LOG_DIR/frontend.pid"
echo -e "   ${CLR_FRONTEND}● Frontend App${NC}         đang khởi chạy trên cổng ${BOLD}3000${NC} (PID: $PID_FRONTEND)"

# 5. Chờ các service sẵn sàng
echo ""
echo -e "${CLR_INFO}⏳ Đang đợi các service sẵn sàng lắng nghe kết nối...${NC}"
sleep 3

# Kiểm tra trạng thái các cổng
for port in "${PORTS[@]}"; do
  ready=false
  for i in {1..15}; do
    if lsof -i :"$port" &>/dev/null; then
      ready=true
      break
    fi
    sleep 1
  done
done

# 6. Hiển thị Dashboard thông tin hệ thống
echo ""
echo -e "${CLR_SUCCESS}======================================================================${NC}"
echo -e "${BOLD}${CLR_SUCCESS}🎉 TẤT CẢ CÁC SERVICE ĐÃ SẴN SÀNG HOẠT ĐỘNG!${NC}"
echo -e "${CLR_SUCCESS}======================================================================${NC}"
echo -e "  ${BOLD}🌐 Frontend Web App:${NC}       ${CLR_INFO}http://localhost:3000${NC}"
echo -e "  ${BOLD}👤 Account Service:${NC}        ${CLR_ACCOUNT}http://localhost:8001${NC}  (Swagger Docs: http://localhost:8001/docs)"
echo -e "  ${BOLD}📚 Content Service:${NC}        ${CLR_CONTENT}http://localhost:8002${NC}  (Swagger Docs: http://localhost:8002/docs)"
echo -e "  ${BOLD}🧠 Learning Service:${NC}       ${CLR_LEARNING}http://localhost:8003${NC}  (Swagger Docs: http://localhost:8003/docs)"
echo -e "  ${BOLD}💳 Payment Service:${NC}        ${CLR_PAYMENT}http://localhost:8004${NC}  (Swagger Docs: http://localhost:8004/docs)"
echo -e "  ${BOLD}🔔 Notification Service:${NC}   ${CLR_NOTIF}http://localhost:8005${NC}  (Swagger Docs: http://localhost:8005/docs)"
echo -e "${CLR_SUCCESS}======================================================================${NC}"
echo -e "  ${BOLD}📁 Thư mục Log độc lập:${NC}     $LOG_DIR/"
echo -e "  ${BOLD}🛑 Nhấn ${CLR_ERR}Ctrl + C${NC}${BOLD} bất cứ lúc nào để dừng toàn bộ hệ thống.${NC}"
echo -e "${CLR_SUCCESS}======================================================================${NC}"
echo -e "${CLR_INFO}📡 Bắt đầu stream realtime log từ tất cả các service (kèm nhãn màu):${NC}\n"

# 7. Stream log thời gian thực với tiền tố màu sắc rõ ràng
tail -n 0 -f "$LOG_DIR/account.log"      | awk -v clr="$CLR_ACCOUNT" '{print clr "[ACCOUNT]     \033[0m " $0; fflush()}' &
TAIL_PIDS+=($!)

tail -n 0 -f "$LOG_DIR/content.log"      | awk -v clr="$CLR_CONTENT" '{print clr "[CONTENT]     \033[0m " $0; fflush()}' &
TAIL_PIDS+=($!)

tail -n 0 -f "$LOG_DIR/learning.log"     | awk -v clr="$CLR_LEARNING" '{print clr "[LEARNING]    \033[0m " $0; fflush()}' &
TAIL_PIDS+=($!)

tail -n 0 -f "$LOG_DIR/payment.log"      | awk -v clr="$CLR_PAYMENT" '{print clr "[PAYMENT]     \033[0m " $0; fflush()}' &
TAIL_PIDS+=($!)

tail -n 0 -f "$LOG_DIR/notification.log" | awk -v clr="$CLR_NOTIF" '{print clr "[NOTIF]       \033[0m " $0; fflush()}' &
TAIL_PIDS+=($!)

tail -n 0 -f "$LOG_DIR/frontend.log"     | awk -v clr="$CLR_FRONTEND" '{print clr "[FRONTEND]    \033[0m " $0; fflush()}' &
TAIL_PIDS+=($!)

# Chờ đợi các tiến trình
wait

