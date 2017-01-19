CALL venv\Scripts\activate.bat

pyinstaller -F --clean --add-data dependencies;dependencies --noupx gui.py