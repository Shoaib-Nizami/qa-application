@echo off

rem Activate the virtual environment and keep the command prompt open
start cmd /k call "C:\Users\Muhammad Shoaib\venv_shoaib\Scripts\activate.bat"
call streamlit run app.py --server.port 8100
