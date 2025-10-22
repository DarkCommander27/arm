!include "MUI2.nsh"
!include "FileFunc.nsh"

; App information - VERSION is defined when calling makensis
!ifndef VERSION
  !define VERSION "1.0.0"
!endif
!define APPNAME "Android TV Remote"
!define COMPANYNAME "DarkCommander27"
!define DESCRIPTION "Remote control for Android TV devices"
!define HELPURL "https://github.com/DarkCommander27/arm"
!define UPDATEURL "https://github.com/DarkCommander27/arm/releases"
!define ABOUTURL "https://github.com/DarkCommander27/arm"

; Define the output file and installer settings
Name "${APPNAME}"
OutFile "AndroidTVRemote-${VERSION}-Installer.exe"
InstallDir "$PROGRAMFILES\\${APPNAME}"
RequestExecutionLevel admin
InstallDirRegKey HKLM "Software\\${APPNAME}" "Install_Dir"

!define ICON "${PROJECT_DIR}\\resources\\icon32.ico"
!define MUI_ICON "${ICON}"
!define MUI_UNICON "${ICON}"

; Define the UI pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${PROJECT_DIR}\\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Define languages
!insertmacro MUI_LANGUAGE "English"

; Default section - main program installation
Section "Android TV Remote" SecMain
  SectionIn RO
  SetOutPath "$INSTDIR"
  
  ; Copy all files from the application folder
  File /r "${PROJECT_DIR}\\dist\\AndroidTVRemote\\*"
  
  ; Write uninstaller
  WriteUninstaller "$INSTDIR\\uninstall.exe"
  
  ; Write registry keys for uninstaller
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayName" "${APPNAME}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "UninstallString" "$\"$INSTDIR\\uninstall.exe$\""
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\\uninstall.exe$\" /S"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "Publisher" "${COMPANYNAME}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "HelpLink" "${HELPURL}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayIcon" "$INSTDIR\\resources\\icon32.ico"
  
  ; Get estimated size
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "EstimatedSize" "$0"
SectionEnd

; Desktop shortcut section
Section "Desktop Shortcut" SecDesktop
  CreateShortCut "$DESKTOP\\${APPNAME}.lnk" "$INSTDIR\\AndroidTVRemote.exe" "" "$INSTDIR\\resources\\icon32.ico"
SectionEnd

; Start menu shortcuts section
Section "Start Menu Shortcuts" SecStartMenu
  CreateDirectory "$SMPROGRAMS\\${APPNAME}"
  CreateShortCut "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk" "$INSTDIR\\AndroidTVRemote.exe" "" "$INSTDIR\\resources\\icon32.ico"
  CreateShortCut "$SMPROGRAMS\\${APPNAME}\\Uninstall.lnk" "$INSTDIR\\uninstall.exe" "" "$INSTDIR\\uninstall.exe"
SectionEnd

; Descriptions
LangString DESC_SecMain ${LANG_ENGLISH} "Install the main application files."
LangString DESC_SecDesktop ${LANG_ENGLISH} "Create a shortcut on your desktop."
LangString DESC_SecStartMenu ${LANG_ENGLISH} "Create shortcuts in your Start Menu."

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_SecDesktop)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} $(DESC_SecStartMenu)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Uninstaller
Section "Uninstall"
  ; Remove files and folders
  Delete "$INSTDIR\\AndroidTVRemote.exe"
  RMDir /r "$INSTDIR"
  
  ; Remove shortcuts
  Delete "$DESKTOP\\${APPNAME}.lnk"
  Delete "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk"
  Delete "$SMPROGRAMS\\${APPNAME}\\Uninstall.lnk"
  RMDir "$SMPROGRAMS\\${APPNAME}"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}"
  DeleteRegKey HKLM "Software\\${APPNAME}"
SectionEnd