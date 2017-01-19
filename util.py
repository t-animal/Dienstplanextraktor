import os, sys

def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


_curDir = os.path.dirname(os.path.abspath(__file__))
if sys.platform.startswith("linux"):
    _PDFTOTEXT = which("pdftotext")
    if _PDFTOTEXT is None:
        _PDFTOTEXT = _curDir + "/dependencies/pdftotext"
elif sys.platform.startswith("win"):
    _PDFTOTEXT = which("pdftotext.exe")
    if _PDFTOTEXT is None:
        _PDFTOTEXT = _curDir + "/dependencies/texlive/bin/win32/pdftotext.exe"
else:
    _PDFTOTEXT = which("pdftotext")
    if _PDFTOTEXT is None:
        print("Your platform is not supported (missing pdftotext). Sorry.")
        sys.exit(1)


if sys.platform.startswith("linux"):
    _PDFLATEX = which("pdflatex")
    if _PDFLATEX is None:
        _PDFLATEX = _curDir + "/dependencies/pdflatex"
elif sys.platform.startswith("win"):
    _PDFLATEX = which("pdflatex.exe")
    if _PDFLATEX is None:
        _PDFLATEX = _curDir + "/dependencies/texlive/bin/win32/pdflatex.exe"
else:
    _PDFLATEX = which("pdflatex")
    if _PDFLATEX is None:
        print("Your platform is not supported (missing pdflatex). Sorry.")
        sys.exit(1)


if sys.platform.startswith("linux"):
    home_dir = os.path.expanduser('~')
    _CONFIG_DIR = os.path.join(home_dir, '.config/dienstplanextraktor/')
elif sys.platform.startswith("win"):
    _CONFIG_DIR = os.path.join(os.environ['APPDATA'], 'dienstplanextraktor')
else:
    print("Your platform is not supported (no idea where to put the config). Sorry.")
    sys.exit(1)


if sys.platform.startswith("linux"):
    _LAYOUT_PARAM = "-layout"
elif sys.platform.startswith("win"):
    _LAYOUT_PARAM = "-table"
else:
    _LAYOUT_PARAM = "-layout"


if sys.platform.startswith('win'):
    import ctypes

    def hideConsole():
        """
        Hides the console window in GUI mode. Necessary for frozen application, because
        this application support both, command line processing AND GUI mode and theirfor
        cannot be run via pythonw.exe.
        """

        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd != 0:
            ctypes.windll.user32.ShowWindow(whnd, 0)
            # if you wanted to close the handles...
            #ctypes.windll.kernel32.CloseHandle(whnd)

    def showConsole():
        """Unhides console window"""
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd != 0:
            ctypes.windll.user32.ShowWindow(whnd, 1)


if sys.platform.startswith("win"):
    import win32api
    import win32print

    def printing(filename, printer = None):
        win32api.ShellExecute(0, "print", filename,
                                '/d:"%s"' % win32print.GetDefaultPrinter() if printer is None else printer, ".", 0)
elif sys.platform.startswith("linux"):
    import subprocess

    def printing(filename, printer = None):
        lpr = subprocess.Popen(["lpr"] + (["-P" + printer] if printer else []), stdin=subprocess.PIPE)
        with open(filename, "rb") as file:
            tmp = file.read(1024)
            while len(tmp) > 0:
                lpr.stdin.write(tmp)
                tmp = file.read(1024)
            lpr.stdin.close()
else:
    print("Your platform is not supported (no idea how to print). Sorry.")
    sys.exit(1)