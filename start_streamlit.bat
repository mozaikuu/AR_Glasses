@echo off
REM Start the Streamlit app using the virtual environment

echo Activating virtual environment...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo Warning: Virtual environment not found at .venv\Scripts\activate.bat
    echo Make sure you have created and activated the virtual environment.
    pause
    exit /b 1
)

echo.
echo Starting Streamlit app...
streamlit run ui/app.py

pause

