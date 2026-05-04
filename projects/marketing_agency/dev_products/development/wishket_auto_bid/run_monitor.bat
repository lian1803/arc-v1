@echo off
cd /d "%~dp0"
python orchestrator.py monitor >> run_log.txt 2>&1
