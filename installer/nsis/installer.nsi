!include "MUI2.nsh"

Name "Android TV Remote"
OutFile "AndroidTVRemote-Installer.exe"
InstallDir "$PROGRAMFILES\\AndroidTVRemote"
RequestExecutionLevel admin

!define ICON "${PROJECT_DIR}\\resources\\icon32.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

Section "Install"
  SetOutPath "$INSTDIR"
  ; Copy all files from the application folder
  File /r "${PROJECT_DIR}\\dist\\AndroidTVRemote\\*"

  ; Create a desktop shortcut
  CreateShortCut "$DESKTOP\\Android TV Remote.lnk" "$INSTDIR\\AndroidTVRemote.exe" "" "$INSTDIR\\resources\\icon32.ico"

  ; Optionally create a Start Menu shortcut
  CreateDirectory "$SMPROGRAMS\\Android TV Remote"
  CreateShortCut "$SMPROGRAMS\\Android TV Remote\\Android TV Remote.lnk" "$INSTDIR\\AndroidTVRemote.exe" "" "$INSTDIR\\resources\\icon32.ico"

SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\\AndroidTVRemote.exe"
  RMDir /r "$INSTDIR"
  Delete "$DESKTOP\\Android TV Remote.lnk"
  Delete "$SMPROGRAMS\\Android TV Remote\\Android TV Remote.lnk"
  RMDir "$SMPROGRAMS\\Android TV Remote"
SectionEnd