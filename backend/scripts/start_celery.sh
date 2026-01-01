#!/bin/bash
# Celery Worker和Beat启动脚本
# 用于checkpoint分层存储迁移定时任务

set -e

# 切换到backend目录
cd "$(dirname "$0")/.."

# 激活虚拟环境(如果存在)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 设置Python路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# 启动Celery worker和beat
echo "启动Celery worker和beat..."
celery -A tasks.checkpoint_migration worker \
    --beat \
    --loglevel=info \
    --logfile=/var/log/ai-platform/celery-checkpoint-migration.log \
    --pidfile=/var/run/ai-platform/celery-checkpoint-migration.pid
