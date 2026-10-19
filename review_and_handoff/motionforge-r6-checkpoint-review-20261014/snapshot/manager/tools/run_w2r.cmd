@echo off
cd /d C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long
"C:\Users\Admin\Documents\Codex\work\mfv1\runtime\video14b\venv\Scripts\python.exe" -B manager\tools\dispatch_long.py manager\packets\LONG01_W2.md MF-DEMO-LONG-01 "tasks\MF-DEMO-LONG-01" "tasks\MF-DEMO-LONG-01\worker_W2r.log" "manager\LONG01_receipt_W2r.json" --resume 20261005_235131_0caeab --max-turns 1000 --max-tokens 131072 >> manager\w2r_stdout.log 2>&1
