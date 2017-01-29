CALL venv\Scripts\activate.bat

pyinstaller -F --clean --add-data dependencies;dependencies -add-data lang;lang --noupx gui.py
pyinstaller --clean --add-data dependencies;dependencies -add-data lang;lang --noupx gui.py