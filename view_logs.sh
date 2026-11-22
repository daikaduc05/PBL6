#!/usr/bin/env bash
# ==============================================================================
# PBL6 - XEM LOG TỪNG SERVICE HOẶC TOÀN BỘ
# Cách dùng:
#   ./view_logs.sh            -> Xem tất cả log
#   ./view_logs.sh account    -> Chỉ xem log của Account Service
#   ./view_logs.sh content    -> Chỉ xem log của Content Service
#   ./view_logs.sh learning   -> Chỉ xem log của Learning Service
#   ./view_logs.sh payment    -> Chỉ xem log của Payment Service
#   ./view_logs.sh notif      -> Chỉ xem log của Notification Service
#   ./view_logs.sh frontend   -> Chỉ xem log của Frontend
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"

TARGET="${1:-all}"

case "$TARGET" in
  account)
    echo "Đang theo dõi log: Account Service (logs/account.log)"
    tail -f "$LOG_DIR/account.log"
    ;;
  content)
    echo "Đang theo dõi log: Content Service (logs/content.log)"
    tail -f "$LOG_DIR/content.log"
    ;;
  learning)
    echo "Đang theo dõi log: Learning Service (logs/learning.log)"
    tail -f "$LOG_DIR/learning.log"
    ;;
  payment)
    echo "Đang theo dõi log: Payment Service (logs/payment.log)"
    tail -f "$LOG_DIR/payment.log"
    ;;
  notif|notification)
    echo "Đang theo dõi log: Notification Service (logs/notification.log)"
    tail -f "$LOG_DIR/notification.log"
    ;;
  frontend|next)
    echo "Đang theo dõi log: Frontend (logs/frontend.log)"
    tail -f "$LOG_DIR/frontend.log"
    ;;
  all)
    echo "Đang theo dõi tất cả log..."
    tail -f "$LOG_DIR"/*.log
    ;;
  *)
    echo "Lựa chọn không hợp lệ: $TARGET"
    echo "Các lựa chọn: all, account, content, learning, payment, notif, frontend"
    exit 1
    ;;
esac

