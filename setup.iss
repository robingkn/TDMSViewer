[Setup]
AppName=TDMS Viewer
AppVersion=1.0
DefaultDirName={autopf}\TDMSViewer
DefaultGroupName=TDMS Viewer
OutputDir=Output
OutputBaseFilename=TDMSViewerInstaller
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\TDMSViewer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\TDMS Viewer"; Filename: "{app}\TDMSViewer.exe"
Name: "{commondesktop}\TDMS Viewer"; Filename: "{app}\TDMSViewer.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"
