Unicode True
!include "MUI2.nsh"
!define APPNAME "NOMIKO"
!define VERSION "0.9.17"
!define MUI_ICON "..\assets\NOMIKO.ico"
!define MUI_UNICON "..\assets\NOMIKO.ico"
Name "${APPNAME} ${VERSION} Stable"
OutFile "NOMIKO-Setup-0.9.17.exe"
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
 ; Assemble the complete app next to the destination BEFORE touching the
 ; installed Qt files. A locked previous DLL must never produce a mixed build.
 StrCpy $R8 "$INSTDIR.__incoming"
 StrCpy $R9 "$INSTDIR.__rollback"
 ClearErrors
 RMDir /r "$R8"
 IfFileExists "$R8\*.*" incoming_locked 0
 ClearErrors
 RMDir /r "$R9"
 IfFileExists "$R9\*.*" rollback_locked 0
 ClearErrors
 CreateDirectory "$R8"
 IfErrors staging_failed
 SetOutPath "$R8"
 ClearErrors
 File /r "..\dist\NOMIKO\*"
 File /oname=NOMIKO.ico "..\assets\NOMIKO.ico"
 IfErrors staging_failed
 IfFileExists "$R8\NOMIKO.exe" stage_ready staging_failed
 stage_ready:
 ; SetOutPath changes the NSIS working directory. Leave the incoming folder
 ; before renaming it: Windows will not move a directory used as CWD.
 SetOutPath "$TEMP"
 ; Never change the running install in place. Renaming an in-use directory
 ; can fail safely; in that case abort without modifying the old installation.
 StrCpy $R7 0
 IfFileExists "$INSTDIR\*.*" backup_existing begin_commit
 backup_existing:
 ClearErrors
 Rename "$INSTDIR" "$R9"
 IfErrors install_locked
 StrCpy $R7 1
 begin_commit:
 ClearErrors
 Rename "$R8" "$INSTDIR"
 IfErrors commit_failed
 Goto install_complete
 commit_failed:
 ; Restore the old install if the final rename was blocked.
 StrCmp $R7 1 0 commit_error
 ClearErrors
 Rename "$R9" "$INSTDIR"
 IfErrors restore_failed
 commit_error:
 MessageBox MB_OK|MB_ICONSTOP "NOMIKO could not finish replacing the application folder. Your previous version was restored. Close NOMIKO and QtWebEngineProcess or restart Windows, then retry." /SD IDOK
 SetErrorLevel 2
 Abort
 restore_failed:
 MessageBox MB_OK|MB_ICONSTOP "NOMIKO installation stopped. Your prior files are retained at $R9. Restart Windows and restore this folder before trying again." /SD IDOK
 SetErrorLevel 2
 Abort
 install_locked:
 MessageBox MB_OK|MB_ICONSTOP "NOMIKO is still running or its Qt files are locked. The old installation was not changed. Close NOMIKO and QtWebEngineProcess, or restart Windows, then retry." /SD IDOK
 SetErrorLevel 2
 Abort
 incoming_locked:
 MessageBox MB_OK|MB_ICONSTOP "NOMIKO could not remove an earlier staging folder: $R8. Restart Windows and try again." /SD IDOK
 SetErrorLevel 2
 Abort
 rollback_locked:
 MessageBox MB_OK|MB_ICONSTOP "NOMIKO's rollback folder is locked: $R9. Restart Windows and try again." /SD IDOK
 SetErrorLevel 2
 Abort
 staging_failed:
 MessageBox MB_OK|MB_ICONSTOP "NOMIKO could not extract the new browser files. Your existing installation has not been changed." /SD IDOK
 SetErrorLevel 2
 Abort
 install_complete:
 ; A rollback copy is retained until the next upgrade; user profile data
 ; is NEVER inside this folder (%APPDATA%\NOMIKO is separate).
 SetOutPath "$INSTDIR"
 WriteUninstaller "$INSTDIR\Uninstall.exe"
 IfErrors commit_error

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
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\NOMIKO" "DisplayName" "NOMIKO ${VERSION} Stable"
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
