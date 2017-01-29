; Dienstplanextraktor.nsi
;
; This script is based on example1.nsi, but it remember the directory, 
; has uninstall support and (optionally) installs start menu shortcuts.
;
; It will install Dienstplanextraktor into a directory that the user selects,

;--------------------------------

!include MUI2.nsh

!insertmacro MUI_LANGUAGE "English"

; The name of the installer
Name "Dienstplanextraktor"

; The file to write
OutFile "Dienstplanextraktor.exe"

; The default installation directory
InstallDir $PROGRAMFILES\Dienstplanextraktor

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\Dienstplanextraktor" "Install_Dir"

; Request application privileges for Windows Vista
RequestExecutionLevel admin

;--------------------------------

; Pages

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------

; The stuff to install
Section "Core (required)"

  SectionIn RO
  
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  
  ; Put file there

  File /r ".\dist\gui\*"
  
  ; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\Dienstplanextraktor "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dienstplanextraktor" "DisplayName" "Dienstplanextraktor"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dienstplanextraktor" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dienstplanextraktor" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dienstplanextraktor" "NoRepair" 1
  WriteUninstaller "uninstall.exe"
  
SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\Dienstplanextraktor"
  CreateShortcut "$SMPROGRAMS\Dienstplanextraktor\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortcut "$SMPROGRAMS\Dienstplanextraktor\Dienstplanextraktor.lnk" "$INSTDIR\gui.exe" "" "$INSTDIR\gui.exe" 0
  
SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dienstplanextraktor"
  DeleteRegKey HKLM SOFTWARE\NSIS_Dienstplanextraktor

  ; Remove files and uninstaller
  RMDir /r "$INSTDIR\*"

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\Dienstplanextraktor\*.*"

  ; Remove directories used
  RMDir "$SMPROGRAMS\Dienstplanextraktor"
  RMDir "$INSTDIR"

SectionEnd
