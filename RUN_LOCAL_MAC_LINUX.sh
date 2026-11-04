#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python -m pip install -r requirements.txt
python seed_demo.py
printf 'Open http://127.0.0.1:8000\nStudent: student@demo.edu / StudentDemo123!\nAdmin: admin@demo.edu / AdminDemo123!\n'
uvicorn app:app --host 127.0.0.1 --port 8000
