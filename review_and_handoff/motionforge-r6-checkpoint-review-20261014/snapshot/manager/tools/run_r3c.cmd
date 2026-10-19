@echo off
cd /d C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long
"C:\Users\Admin\Documents\Codex\work\mfv1\runtime\video14b\venv\Scripts\python.exe" -B manager\tools\dispatch_long.py manager\packets\LONG01_R3c.md MF-DEMO-LONG-01 "tasks\MF-DEMO-LONG-01" "tasks\MF-DEMO-LONG-01\worker_R3c.log" "manager\LONG01_receipt_R3c.json" --resume 20261007_234033_cc0b6d --max-turns 80 --max-tokens 16384 >> manager\r3c_stdout.log 2>&1
