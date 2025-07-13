@echo off
cd /d "%~dp0"
echo ===========================================
echo     GPT Classifier Batch Runner (v6)
echo ===========================================
echo.
echo 🔍 Scanning: batch_txts\
echo 💾 Writing to: mudroom_logs\[date]\
echo.

python gpt_classifier_enhanced_batch.py

echo.
echo ✅ Done. Check mudroom_logs\[date]\ for outputs.
pause