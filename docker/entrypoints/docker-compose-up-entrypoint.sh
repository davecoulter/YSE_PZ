#!/usr/bin/env bash
set -e
cd /app

bash /app/Entrypoints/wait-for-it.sh yse_db:3306 --timeout=120 &&
echo "**** LET'S GO GAMERS! ****" &&
gunicorn YSE_PZ.wsgi:application --bind 0.0.0.0:8000 &&
#gunicorn /Users/rfoley/YSE_PZ/YSE_PZ.wsgi:application --bind 0.0.0.0:8000 &&
bash /app/Entrypoints/wait-for-it.sh yse_nginx:80 --timeout=30 || true

#python3 manage.py collectstatic --noinput &&

#echo "***** SLEEP FOR 30 seconds... *****"; sleep 30;
#python3 manage.py runserver 0.0.0.0:8000
#python manage.py makemigrations &&
#python manage.py migrate &&
#python manage.py loaddata setup_survey_data.yaml &&
#python manage.py loaddata setup_filter_data.yaml &&
#python manage.py loaddata setup_catalog_data.yaml &&
#python manage.py loaddata setup_test_transient.yaml &&
#python manage.py loaddata setup_tasks.yaml &&
#python manage.py loaddata setup_status.yaml &&
#python manage.py loaddata setup_test_task_register.yaml &&
#gunicorn app.wsgi:application --bind 0.0.0.0:8000
