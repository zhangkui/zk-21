@echo off
echo 启动 Celery Worker...
cd backend
celery -A aqua_platform worker --loglevel=info --pool=solo
