#ifndef BuildRoot
  #error BuildRoot is required
#endif
#ifndef AppVersion
  #define AppVersion "1.0.0-rc10"
#endif
[Setup]
AppId={{6EBED3CA-6192-471E-9373-1193AE3BD7B9}
AppName=Roster Beacon
AppVersion={#AppVersion}
AppPublisher=Roster Beacon contributors
DefaultDirName={localappdata}\Programs\Roster Beacon
DefaultGroupName=Roster Beacon
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#BuildRoot}\release
OutputBaseFilename=Roster-Beacon-{#AppVersion}-windows-x64-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Roster-Beacon.exe
LicenseFile=..\LICENSE
SetupIconFile=..\assets\app.ico
LanguageDetectionMethod=uilanguage

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopShortcut}"; GroupDescription: "{cm:ShortcutGroup}"

[CustomMessages]
chinesesimp.DesktopShortcut=创建桌面一键更新并启动快捷方式
english.DesktopShortcut=Create a desktop sync-and-launch shortcut
chinesesimp.ShortcutGroup=快捷方式：
english.ShortcutGroup=Shortcuts:
chinesesimp.Configure=配置 Roster Beacon
english.Configure=Configure Roster Beacon

[Files]
Source: "{#BuildRoot}\dist\Roster-Beacon\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
Type: files; Name: "{app}\NBA-Roster-Sync.exe"
Type: files; Name: "{app}\NBA-Roster-Sync-cli.exe"
Type: files; Name: "{app}\README.en.md"
Type: files; Name: "{autodesktop}\NBA Roster Sync.lnk"

[Icons]
Name: "{group}\Roster Beacon"; Filename: "{app}\Roster-Beacon.exe"
Name: "{group}\{cm:Configure}"; Filename: "{app}\Roster-Beacon.exe"; Parameters: "--settings"
Name: "{autodesktop}\Roster Beacon"; Filename: "{app}\Roster-Beacon.exe"; Parameters: "--launch"; Tasks: desktopicon

[Run]
Filename: "{app}\Roster-Beacon.exe"; Parameters: "--settings"; Description: "{cm:Configure}"; Flags: nowait postinstall skipifsilent
