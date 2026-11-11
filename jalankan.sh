#!/bin/bash
cd ~/Downloads/UTS_AI_CV_v2
source venv/bin/activate
export CVKU_AI_MODE=remote
export CVKU_AI_URL="$1"
lsof -ti :5001 | xargs kill 2>/dev/null
python app.py
