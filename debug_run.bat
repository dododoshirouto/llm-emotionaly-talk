@echo on
chcp 65001
echo Starting debug run... > debug_output.txt
echo Time: %TIME% >> debug_output.txt

echo Checking Python Version... >> debug_output.txt
venv\Scripts\python.exe --version >> debug_output.txt 2>&1

echo. >> debug_output.txt
echo Running main.py... >> debug_output.txt
venv\Scripts\python.exe -u src\main.py >> debug_output.txt 2>&1

echo. >> debug_output.txt
echo Done. >> debug_output.txt
