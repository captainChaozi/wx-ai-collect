#!/usr/bin/bash

if [ "$RUN" = "celery" ]; then
    echo "运行celery"
    celery -A app.celery_app worker 
else
    echo "欢迎来到Flask"
    gunicorn app:app -b 0.0.0.0:80 
fi
