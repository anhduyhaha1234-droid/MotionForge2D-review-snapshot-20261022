@echo off
cd /d C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long
"C:\Users\Admin\Documents\Codex\work\mfv1\runtime\video14b\venv\Scripts\python.exe" -B manager\tools\dispatch_long.py manager\packets\LONG01_C1_identity5m.md MF-DEMO-LONG-01 "tasks\MF-DEMO-LONG-01" "tasks\MF-DEMO-LONG-01\worker_C1.log" "manager\LONG01_receipt_C1.json" --resume 20261007_234033_cc0b6d --max-turns 80 --max-tokens 16384 >> manager\c1_stdout.log 2>&1
