!include "MUI2.nsh"

!ifndef VERSION
  !define VERSION "0.0.0"
!endif

Name "SUNROOM"
OutFile "SUNROOM-${VERSION}-Windows-Setup.exe"
InstallDir "$PROGRAMFILES64\SUNROOM"
InstallDirRegKey HKLM "Software\SUNROOM" "Install_Dir"
RequestExecutionLevel admin
Unicode True

; %ProgramData%\SUNROOM\bin — where the MCP bridge is installed. See the Install
; section for why it is not under $INSTDIR.
Var McpBinDir

; UI settings. The icon is staged next to this script at build time.
!define MUI_ABORTWARNING
!define MUI_ICON "${__FILEDIR__}\sunroom_icon.ico"
!define MUI_UNICON "${__FILEDIR__}\sunroom_icon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    ; SUNROOM, ONNX Runtime, and the OpenMP runtime dynamically link the
    ; Microsoft Visual C++ v14 runtime. A clean consumer Windows installation
    ; is not guaranteed to have it, so bootstrap the Microsoft-signed package
    ; before placing SUNROOM on disk. $PLUGINSDIR is removed automatically when
    ; setup exits; the shared runtime itself remains serviceable by Windows.
    SetOutPath "$PLUGINSDIR"
    File "${__FILEDIR__}\vc_redist.x64.exe"
    DetailPrint "Installing Microsoft Visual C++ Runtime..."
    StrCpy $0 "-1"
    ClearErrors
    ExecWait '"$PLUGINSDIR\vc_redist.x64.exe" /install /quiet /norestart' $0
    IfErrors vc_redist_failed
    IntCmp $0 0 vc_redist_ok
    ; 1638 (ERROR_PRODUCT_VERSION): an equal/newer v14 runtime is installed.
    IntCmp $0 1638 vc_redist_ok
    ; 3010 (ERROR_SUCCESS_REBOOT_REQUIRED): installation succeeded.
    IntCmp $0 3010 vc_redist_reboot
    Goto vc_redist_failed

vc_redist_reboot:
    SetRebootFlag true
    Goto vc_redist_ok

vc_redist_failed:
    MessageBox MB_ICONSTOP|MB_OK \
        "Microsoft Visual C++ Runtime installation failed (exit code $0). SUNROOM was not installed."
    Abort

vc_redist_ok:
    SetOutPath $INSTDIR
    ; ${__FILEDIR__} resolves to the directory of this .nsi at compile time, so
    ; the installer builds correctly regardless of makensis's working directory.
    File "${__FILEDIR__}\SUNROOM.exe"
    File "${__FILEDIR__}\mgd_doc_icon.ico"
    File /nonfatal "${__FILEDIR__}\magda_plugin_scanner.exe"

    ; The MCP bridge goes to %ProgramData%\SUNROOM\bin, NOT $INSTDIR.
    ; An MCP host is configured with its absolute path and launches it itself,
    ; and hosts differ on whether that string is an argv array or something they
    ; split on whitespace. The default $INSTDIR is "C:\Program Files\SUNROOM", so
    ; for the splitters the space breaks the command. %ProgramData% is a fixed
    ; name on every supported Windows and carries no user name, making it
    ; space-free regardless of who is logged in.
    ;
    ; The bridge does not need to sit beside SUNROOM: it locates a running
    ; instance through the discovery record under %APPDATA%\SUNROOM, not by
    ; relative path. SetShellVarContext is restored straight away so the Start
    ; Menu and Desktop shortcuts below stay per-user as before.
    SetShellVarContext all
    StrCpy $McpBinDir "$APPDATA\SUNROOM\bin"
    SetShellVarContext current

    SetOutPath "$McpBinDir"
    File /nonfatal "${__FILEDIR__}\magda-mcp.exe"
    SetOutPath $INSTDIR

    ; Upgrading in place over an install that predates the move: the copy left
    ; in $INSTDIR is never used again, and leaving it invites someone to
    ; configure a host with the path that has the space in it.
    Delete "$INSTDIR\magda-mcp.exe"

    ; All runtime DLLs staged next to SUNROOM.exe: ONNX Runtime (a load-time app
    ; dependency) and libxml2 + its transitive deps (DAWproject XSD validation).
    ; Windows only searches the exe's directory, so these must sit next to
    ; SUNROOM.exe. The release staging step asserts the critical DLLs are present,
    ; so this fails loudly upstream if one goes missing.
    File "${__FILEDIR__}\*.dll"

    ; Localization JSON files - StringTable looks for them next to SUNROOM.exe
    SetOutPath "$INSTDIR\lang"
    File /r "${__FILEDIR__}\lang\*.*"
    SetOutPath $INSTDIR

    ; Controller profiles + Lua scripts - registry probes
    ; <exe>/controllers/profiles and LuaScriptStore probes
    ; <exe>/controllers/scripts. File /r preserves both subdirs.
    SetOutPath "$INSTDIR\controllers"
    File /r "${__FILEDIR__}\controllers\*.*"
    SetOutPath $INSTDIR

    ; Faust standard libraries - FaustResources passes <exe>/faustlibraries to
    ; libfaust as the -I include path, so import("stdfaust.lib") resolves. Uses
    ; \* (not \*.*) because the tree carries extensionless files (Makefile etc).
    SetOutPath "$INSTDIR\faustlibraries"
    File /r "${__FILEDIR__}\faustlibraries\*"
    SetOutPath $INSTDIR

    ; Runtime Faust effects - FaustResources scans <exe>/faust_dsp to build the
    ; loader picker. These are discovered, not embedded, so without this the
    ; installed build shows an empty starter list.
    SetOutPath "$INSTDIR\faust_dsp"
    File /r "${__FILEDIR__}\faust_dsp\*"
    SetOutPath $INSTDIR

    ; Stock drumkit templates - DrumkitManager reads <exe>/drumkits to seed the
    ; user's Drumkits folder on first launch.
    SetOutPath "$INSTDIR\drumkits"
    File /r "${__FILEDIR__}\drumkits\*"
    SetOutPath $INSTDIR

    ; DAWproject XSD schemas - DawProjectValidator validates import/export
    ; against <exe>/dawproject/Project.xsd and MetaData.xsd. Without these the
    ; validator falls back to the baked-in build-tree source path, which does
    ; not exist on an end-user machine, and every DAWproject import fails.
    SetOutPath "$INSTDIR\dawproject"
    File /r "${__FILEDIR__}\dawproject\*"
    SetOutPath $INSTDIR

    ; Audio-to-MIDI model - TranscriptionService loads
    ; <exe>/models/basic_pitch.onnx for "Transcribe to MIDI". Without it the
    ; feature is unavailable on installed machines (dev builds resolve the
    ; source-tree fallback, which hides the gap).
    SetOutPath "$INSTDIR\models"
    File /r "${__FILEDIR__}\models\*"
    SetOutPath $INSTDIR

    ; Guided studio sounds, coach guide, and the local worker. The app looks
    ; for these in <exe>\Sunroom. Without them Create still runs, but the sound
    ; shelf and coach knowledge are empty on an installed machine.
    SetOutPath "$INSTDIR\Sunroom"
    File /r "${__FILEDIR__}\Sunroom\*"
    SetOutPath $INSTDIR

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\SUNROOM"
    CreateShortcut "$SMPROGRAMS\SUNROOM\SUNROOM.lnk" "$INSTDIR\SUNROOM.exe"
    CreateShortcut "$SMPROGRAMS\SUNROOM\Uninstall SUNROOM.lnk" "$INSTDIR\Uninstall.exe"

    ; Desktop shortcut
    CreateShortcut "$DESKTOP\SUNROOM.lnk" "$INSTDIR\SUNROOM.exe"

    ; Registry for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SUNROOM" \
        "DisplayName" "SUNROOM"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SUNROOM" \
        "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SUNROOM" \
        "DisplayVersion" "${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SUNROOM" \
        "Publisher" "Conceptual Machines"
    WriteRegStr HKLM "Software\SUNROOM" "Install_Dir" "$INSTDIR"

    ; File association for .mgd files
    WriteRegStr HKCR ".mgd" "" "SUNROOM.Project"
    WriteRegStr HKCR "SUNROOM.Project" "" "SUNROOM Project"
    WriteRegStr HKCR "SUNROOM.Project\shell\open\command" "" '"$INSTDIR\SUNROOM.exe" "%1"'
    WriteRegStr HKCR "SUNROOM.Project\DefaultIcon" "" "$INSTDIR\mgd_doc_icon.ico"

    ; Notify shell of file association change
    System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, i 0, i 0)'
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\SUNROOM.exe"
    Delete "$INSTDIR\mgd_doc_icon.ico"
    Delete "$INSTDIR\magda_plugin_scanner.exe"
    ; Installs predating the move to %ProgramData% put the bridge here.
    Delete "$INSTDIR\magda-mcp.exe"
    Delete "$INSTDIR\*.dll"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR\lang"
    RMDir /r "$INSTDIR\controllers"
    RMDir /r "$INSTDIR\faustlibraries"
    RMDir /r "$INSTDIR\faust_dsp"
    RMDir /r "$INSTDIR\drumkits"
    RMDir /r "$INSTDIR\dawproject"
    RMDir /r "$INSTDIR\models"
    RMDir /r "$INSTDIR\Sunroom"
    RMDir "$INSTDIR"

    ; The MCP bridge, out under %ProgramData%. Both RMDirs are non-recursive on
    ; purpose: SUNROOM\bin goes only if the bridge was all it held, and SUNROOM
    ; only if nothing else has since been written there.
    SetShellVarContext all
    Delete "$APPDATA\SUNROOM\bin\magda-mcp.exe"
    RMDir "$APPDATA\SUNROOM\bin"
    RMDir "$APPDATA\SUNROOM"
    SetShellVarContext current

    Delete "$SMPROGRAMS\SUNROOM\*.*"
    RMDir "$SMPROGRAMS\SUNROOM"
    Delete "$DESKTOP\SUNROOM.lnk"

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SUNROOM"
    DeleteRegKey HKLM "Software\SUNROOM"

    ; Remove file association
    DeleteRegKey HKCR ".mgd"
    DeleteRegKey HKCR "SUNROOM.Project"
    System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, i 0, i 0)'
SectionEnd
