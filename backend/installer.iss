; ============================================================
; FluxAvision 客流统计系统 - Inno Setup 安装程序脚本
; ============================================================
; 编译方式: 使用 Inno Setup Compiler 打开此文件编译
; 下载地址: https://jrsoftware.org/isinfo.php
; ============================================================

; 从项目根目录的 VERSION 文件读取版本号
#define VERSION_FILE AddBackslash(SourcePath) + "..\VERSION"
#define VERSION_HANDLE
#expr VERSION_HANDLE = FileOpen(VERSION_FILE)
#define MyAppVersion FileRead(VERSION_HANDLE)
#expr FileClose(VERSION_HANDLE)

#define MyAppName "FluxAvision 客流统计系统"
#define MyAppPublisher "FluxAvision"
#define MyAppURL "http://127.0.0.1:15678"
#define MyAppExeName "FluxaVision.exe"
#define MyAppDescription "基于AI的客流统计与分析系统"
#define MyLauncherName "FluxaVision_launcher.vbs"

[Setup]
; ==================== 基本信息 ====================
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\FluxAvision
DefaultGroupName={#MyAppName}
OutputDir=..\installer_output
OutputBaseFilename=FluxAvision-Setup-v{#MyAppVersion}
SetupIconFile=assets\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

; ==================== 升级配置 ====================
UsePreviousAppDir=yes
UsePreviousGroup=yes
DirExistsWarning=auto

; ==================== 运行中应用处理 ====================
; 安装/卸载的进程清理由 InitializeSetup() 和 [UninstallRun] 处理

; ==================== 安装界面配置 ====================
WizardImageFile=assets\wizard.bmp
WizardSmallImageFile=assets\wizard-small.bmp
WizardSizePercent=120

; ==================== 卸载配置 ====================
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; ==================== 权限和兼容性 ====================
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "autostart"; Description: "开机自动启动"; GroupDescription: "启动:"
Name: "firewall"; Description: "添加防火墙规则"; GroupDescription: "网络:"

[Registry]
; ==================== 开机自启（使用 VBS 启动器，崩溃自动恢复）====================
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "FluxaVision"; ValueData: "wscript.exe ""{app}\{#MyLauncherName}"""; Tasks: autostart; Flags: uninsdeletevalue

[Files]
; ==================== 打包文件 ====================
; 主程序文件（从 PyInstaller dist/ 目录获取）
Source: "dist\FluxaVision\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; VBS 崩溃自恢复启动器
Source: "{#MyLauncherName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; ==================== 开始菜单快捷方式 ====================
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; ==================== 安装后执行 ====================
; 添加防火墙规则
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""FluxaVision"" dir=in action=allow program=""{app}\{#MyAppExeName}"" enable=yes protocol=tcp localport=8080"; Flags: runhidden waituntilterminated; Tasks: firewall
; 启动服务（直接启动 exe，VBS 启动器用于开机自启的崩溃恢复）
Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; ==================== 卸载前执行 ====================
; 写入关机标记（通知 VBS 启动器停止，不要重启进程）
Filename: "cmd"; Parameters: "/c echo 1 > ""{app}\data\.launcher_shutdown"""; Flags: runhidden; RunOnceId: "ShutdownMarker"
; 强制结束进程
Filename: "taskkill"; Parameters: "/F /IM FluxaVision.exe /T"; Flags: runhidden; RunOnceId: "KillProcess"
; 等待端口释放
Filename: "timeout"; Parameters: "/T 3 /NOBREAK"; Flags: runhidden; RunOnceId: "WaitRelease"
; 卸载开机自启（清理旧版注册的 exe 路径）
Filename: "{app}\{#MyAppExeName}"; Parameters: "--uninstall"; Flags: runhidden waituntilterminated; RunOnceId: "UninstallAutostart"
; 移除防火墙规则
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""FluxaVision"""; Flags: runhidden waituntilterminated; RunOnceId: "RemoveFirewall"

[UninstallDelete]
; ==================== 卸载时清理 ====================
; 清理应用自身创建的桌面快捷方式（.url 文件）
Type: files; Name: "{userdesktop}\FluxaVision *.url"
; 清理 VBS 启动器
Type: files; Name: "{app}\{#MyLauncherName}"
; 保留用户数据目录
Type: filesandordirs; Name: "{app}\data"; Check: not ShouldDeleteData

[Code]
// ==================== 自定义代码 ====================
var
  ResultCode: Integer;
  IsUpgrade: Boolean;
  OldVersion: String;

// ==================== 辅助函数 ====================
function ReadFileContent(const FileName: String): String;
var
  Lines: TArrayOfString;
begin
  Result := '';
  if FileExists(FileName) then
    if LoadStringsFromFile(FileName, Lines) then
      if GetArrayLength(Lines) > 0 then
        Result := Trim(Lines[0]);
end;

// ==================== 安装前准备 ====================
function InitializeSetup(): Boolean;
var
  KillCode: Integer;
begin
  // 清理前次残留的进程
  if Exec('taskkill', '/F /IM FluxaVision.exe /T', '', SW_HIDE, ewWaitUntilTerminated, KillCode) then
  begin
    if KillCode = 0 then
      Sleep(3000);
  end;
  Result := True;
end;

// ==================== 安装步骤回调 ====================
procedure CurStepChanged(CurStep: TSetupStep);
var
  VersionFile: String;
  MarkerFile: String;
  UpgradeLines: TArrayOfString;
begin
  if CurStep = ssInstall then
  begin
    // 检测是否为升级安装
    VersionFile := ExpandConstant('{app}\VERSION');
    OldVersion := ReadFileContent(VersionFile);
    IsUpgrade := (OldVersion <> '');

    if IsUpgrade then
      Log('检测到升级安装: 旧版本 ' + OldVersion + ' → 新版本 {#MyAppVersion}');
  end;

  if CurStep = ssPostInstall then
  begin
    if IsUpgrade then
    begin
      // 创建升级标记文件，应用启动时执行数据库迁移
      MarkerFile := ExpandConstant('{app}\data\.upgrade_marker');
      SetArrayLength(UpgradeLines, 2);
      UpgradeLines[0] := OldVersion;
      UpgradeLines[1] := '{#MyAppVersion}';
      SaveStringsToFile(MarkerFile, UpgradeLines, False);
      Log('升级标记文件已创建: ' + OldVersion + ' → {#MyAppVersion}');
    end;
  end;
end;

function ShouldDeleteData(): Boolean;
begin
  Result := False;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
  MsgBoxResult: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{app}\data');
    if DirExists(DataDir) then
    begin
      MsgBoxResult := MsgBox('是否删除所有数据（包括数据库和配置）？' + #13#10 + #13#10 +
        '选择"是"将永久删除所有数据。' + #13#10 +
        '选择"否"将保留数据目录。', mbConfirmation, MB_YESNO or MB_DEFBUTTON2);
      if MsgBoxResult = IDYES then
      begin
        DelTree(DataDir, True, True, True);
      end;
    end;
  end;
end;
