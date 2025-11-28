#!/bin/bash
# 使用Debug模式启动FilePulse服务器

echo "=== FilePulse Debug启动 ==="
echo ""
echo "配置："
echo "  MAX_FILE_SIZE: ${MAX_FILE_SIZE:-从.env读取}"
echo "  DEBUG: true (详细日志已启用)"
echo ""
echo "启动服务器..."
echo ""

DEBUG=true MAX_FILE_SIZE="${MAX_FILE_SIZE:-200MB}" uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
