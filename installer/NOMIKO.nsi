Unicode True
!include "MUI2.nsh"
!define APPNAME "NOMIKO"
!define VERSION "0.9.9"
!define MUI_ICON "..\assets\NOMIKO.ico"
!define MUI_UNICON "..\assets\NOMIKO.ico"
Name "${APPNAME} ${VERSION} Alpha"
OutFile "NOMIKO-Setup-0.9.9-alpha.exe"
InstallDir "$LOCALAPPDATA\Programs\NOMIKO"
RequestExecutionLevel user
SetCompressor /SOLID lzma
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
Section "NOMIKO browser" SEC_MAIN
 SetShellVarContext current
 SetOutPath "$INSTDIR"
 File /r "..\dist\NOMIKO\*"
 File /oname=NOMIKO.ico "..\assets\NOMIKO.ico"
 WriteUninstaller "$INSTDIR\Uninstall.exe"

 ; Per-user Windows 11 Default Apps registration (does NOT seize defaults).
 WriteRegStr HKCU "Software\Classes\NOMIKO.HTTP" "" "NOMIKO HTTP link"
 WriteRegStr HKCU "Software\Classes\NOMIKO.HTTP" "URL Protocol" ""
 WriteRegStr HKCU "Software\Classes\NOMIKO.HTTP\DefaultIcon" "" "$INSTDIR\NOMIKO.ico"
 WriteRegStr HKCU "Software\Classes\NOMIKO.HTTP\shell\open\command" "" '"$INSTDIR\NOMIKO.exe" "%1"'
 WriteRegStr HKCU "Software\Classes\NOMIKO.HTTPS" "" "NOMIKO HTTPS link"
 WriteRegStr HKCU "Software\Classes\NOMIKO.HTTPS" "URL Protocol" ""
 WriteRegStr HKCU "Software\Classes\NOMIKO.HTTPS\DefaultIcon" "" "$INSTDIR\NOMIKO.ico"
 WriteRegStr HKCU "Software\Classes\NOMIKO.HTTPS\shell\open\command" "" '"$INSTDIR\NOMIKO.exe" "%1"'
 WriteRegStr HKCU "Software\Classes\NOMIKO.HTML" "" "NOMIKO HTML document"
 WriteRegStr HKCU "Software\Classes\NOMIKO.HTML\DefaultIcon" "" "$INSTDIR\NOMIKO.ico"
 WriteRegStr HKCU "Software\Classes\NOMIKO.HTML\shell\open\command" "" '"$INSTDIR\NOMIKO.exe" "%1"'
 WriteRegStr HKCU "Software\NOMIKO\Capabilities" "ApplicationName" "NOMIKO"
 WriteRegStr HKCU "Software\NOMIKO\Capabilities" "ApplicationDescription" "NOMIKO private web browser for Windows 11"
 WriteRegStr HKCU "Software\NOMIKO\Capabilities\UrlAssociations" "http" "NOMIKO.HTTP"
 WriteRegStr HKCU "Software\NOMIKO\Capabilities\UrlAssociations" "https" "NOMIKO.HTTPS"
 WriteRegStr HKCU "Software\NOMIKO\Capabilities\FileAssociations" ".htm" "NOMIKO.HTML"
 WriteRegStr HKCU "Software\NOMIKO\Capabilities\FileAssociations" ".html" "NOMIKO.HTML"
 WriteRegStr HKCU "Software\RegisteredApplications" "NOMIKO" "Software\NOMIKO\Capabilities"
 WriteRegStr HKCU "Software\Clients\StartMenuInternet\NOMIKO" "" "NOMIKO"
 WriteRegStr HKCU "Software\Clients\StartMenuInternet\NOMIKO\DefaultIcon" "" "$INSTDIR\NOMIKO.ico"
 WriteRegStr HKCU "Software\Clients\StartMenuInternet\NOMIKO\shell\open\command" "" '"$INSTDIR\NOMIKO.exe"'
 WriteRegStr HKCU "Software\Clients\StartMenuInternet\NOMIKO\Capabilities" "ApplicationName" "NOMIKO"
 WriteRegStr HKCU "Software\Clients\StartMenuInternet\NOMIKO\Capabilities" "ApplicationDescription" "NOMIKO web browser"
 WriteRegStr HKCU "Software\Clients\StartMenuInternet\NOMIKO\Capabilities\UrlAssociations" "http" "NOMIKO.HTTP"
 WriteRegStr HKCU "Software\Clients\StartMenuInternet\NOMIKO\Capabilities\UrlAssociations" "https" "NOMIKO.HTTPS"
 WriteRegStr HKCU "Software\Clients\StartMenuInternet\NOMIKO\Capabilities\FileAssociations" ".htm" "NOMIKO.HTML"
 WriteRegStr HKCU "Software\Clients\StartMenuInternet\NOMIKO\Capabilities\FileAssociations" ".html" "NOMIKO.HTML"
 System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, p 0, p 0)'
 CreateDirectory "$SMPROGRAMS\NOMIKO"
 CreateShortCut "$SMPROGRAMS\NOMIKO\NOMIKO.lnk" "$INSTDIR\NOMIKO.exe" "" "$INSTDIR\NOMIKO.ico" 0
 CreateShortCut "$SMPROGRAMS\NOMIKO\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
 CreateShortCut "$DESKTOP\NOMIKO.lnk" "$INSTDIR\NOMIKO.exe" "" "$INSTDIR\NOMIKO.ico" 0
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NOMIKO" "DisplayName" "NOMIKO ${VERSION} Alpha"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NOMIKO" "DisplayIcon" "$INSTDIR\NOMIKO.ico"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NOMIKO" "UninstallString" '"$INSTDIR\Uninstall.exe"'
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NOMIKO" "InstallLocation" "$INSTDIR"
 WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NOMIKO" "NoModify" 1
 WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NOMIKO" "NoRepair" 1
SectionEnd
Section "Uninstall"
 SetShellVarContext current
 Delete "$DESKTOP\NOMIKO.lnk"
 Delete "$SMPROGRAMS\NOMIKO\NOMIKO.lnk"
 Delete "$SMPROGRAMS\NOMIKO\Uninstall.lnk"
 RMDir "$SMPROGRAMS\NOMIKO"
 DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NOMIKO"
 ; Only NOMIKO-specific registrations are removed; user defaults are untouched.
 DeleteRegValue HKCU "Software\RegisteredApplications" "NOMIKO"
 DeleteRegKey HKCU "Software\NOMIKO\Capabilities"
 DeleteRegKey HKCU "Software\Clients\StartMenuInternet\NOMIKO"
 DeleteRegKey HKCU "Software\Classes\NOMIKO.HTTP"
 DeleteRegKey HKCU "Software\Classes\NOMIKO.HTTPS"
 DeleteRegKey HKCU "Software\Classes\NOMIKO.HTML"
 System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, p 0, p 0)'
 RMDir /r "$INSTDIR"
 ; Preserve user browsing data at %APPDATA%\NOMIKO.
SectionEnd
