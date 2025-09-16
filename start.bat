@echo off
TITLE LiangZiXuanGu AI Agent

echo Starting LiangZiXuanGu AI Agent...
echo Activating virtual environment and launching Streamlit app...

:: Activate the virtual environment and run the main python script
call venv\Scripts\activate && streamlit run src/main.py

pause
