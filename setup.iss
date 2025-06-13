[Setup]
AppName=TDMSViewer
AppVersion=1.0
DefaultDirName={pf}\TDMSViewer
DefaultGroupName=TDMSViewer
OutputDir=Output
OutputBaseFilename=TDMSViewerSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\TDMSViewerApp.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\TDMSViewer"; Filename: "{app}\TDMSViewerApp.exe"
Name: "{group}\Uninstall TDMSViewer"; Filename: "{uninstallexe}"
