@echo off
cd /d "%~dp0backend"
py -m pip install -r requirements.txt
py run.py
