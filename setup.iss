; ============================================================
;  XB-Dino-Game Inno Setup 安装包脚本
;  编译：ISCC.exe setup.iss  （或用 Inno Setup Compiler GUI 打开编译）
;  产物：installer/XB-Dino-Game-Setup-<版本>.exe
; ============================================================

#define MyAppName "XB-Dino-Game"
#define MyAppVer "1.0.0"
#define MyAppPublisher "Code-XB"
#define MyAppExeName "XB-Dino-Game.exe"
#define MyAppURL "https://github.com/Code-XB/XB-Dino-Game"

[Setup]
; 唯一标识（卸载/升级识别用，切勿更改）
AppId={{7C1E9A64-52F3-4B8E-9A7D-XBDINO10001}
AppName={#MyAppName}
AppVersion={#MyAppVer}
AppVerName={#MyAppName} {#MyAppVer}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
; 默认安装到 64 位 Program Files
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; 安装包图标与卸载程序图标
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
; 版本信息（资源管理器属性）
VersionInfoVersion={#MyAppVer}
VersionInfoProductVersion={#MyAppVer}
; 压缩与完整性
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; 64 位模式
ArchitecturesInstallIn64BitMode=x64compatible
; 允许普通用户安装到自己的目录（不强制管理员）
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=installer
OutputBaseFilename=XB-Dino-Game-Setup-{#MyAppVer}
; 卸载时保留用户最高分存档
UninstallFilesDir={app}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; 单文件主程序（Nuitka onefile 产物，图标已内嵌）
Source: "build\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 图标（应用目录留一份备用）
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; 用户手册
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; 开始菜单快捷方式
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
; 桌面快捷方式（可选勾选）
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
; 安装完成后可选择立即运行
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 清理日志类残留（保留 %APPDATA% 下的最高分存档）
Type: files; Name: "{app}\highscore.json"

[Messages]
; 覆盖部分提示文案
WelcomeLabel2=这将安装 [name/ver] 到您的电脑。%n%n一款使用 Python 完整复刻的 Google Chrome 小恐龙游戏，素材与音效均来自 Chromium 官方。
FinishedLabelNoIcons=安装完成！%n%n去跳起来吧（空格起跳，按下蹲）。
FinishedLabel=安装完成！%n%n去跳起来吧（空格起跳，按下蹲）。
