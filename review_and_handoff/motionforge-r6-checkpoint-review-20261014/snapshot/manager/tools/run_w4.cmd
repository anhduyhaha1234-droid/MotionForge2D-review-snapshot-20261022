@echo off
cd /d C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long
"C:\Users\Admin\Documents\Codex\work\mfv1\runtime\video14b\venv\Scripts\python.exe" -B manager\tools\dispatch_long.py manager\packets\LONG01_W4.md MF-DEMO-LONG-01 "tasks\MF-DEMO-LONG-01" "tasks\MF-DEMO-LONG-01\worker_W4.log" "manager\LONG01_receipt_W4.json" --max-turns 80 --max-tokens 16384 >> manager\w4_stdout.log 2>&1
