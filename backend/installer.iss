; ============================================================
; FluxAvision 客流统计系统 - Inno Setup 安装程序脚本
; ============================================================
; 编译方式: 使用 Inno Setup Compiler 打开此文件编译
; 下载地址: https://jrsoftware.org/isinfo.php
; ============================================================

#define MyAppName "FluxAvision 客流统计系统"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "FluxAvision"
#define MyAppURL "http://127.0.0.1:15678"
#define MyAppExeName "FluxaVision.exe"
#define MyAppDescription "基于AI的客流统计与分析系统"

[Setup]
; ==================== 基本信息 ====================
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
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
Name: "quicklaunchicon"; Description: "创建快速启动栏快捷方式"; GroupDescription: "快捷方式:"; Flags: unchecked
Name: "autostart"; Description: "开机自动启动"; GroupDescription: "启动:"
Name: "firewall"; Description: "添加防火墙规则"; GroupDescription: "网络:"

[Files]
; ==================== 打包文件 ====================
; 主程序文件（从 PyInstaller dist/ 目录获取）
Source: "dist\FluxaVision\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; ==================== 快捷方式 ====================
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; ==================== 安装后执行 ====================
; 安装开机自启动
Filename: "{app}\{#MyAppExeName}"; Parameters: "--install"; Flags: runhidden waituntilterminated; Tasks: autostart
; 添加防火墙规则
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""FluxaVision"" dir=in action=allow program=""{app}\{#MyAppExeName}"" enable=yes protocol=tcp localport=8080"; Flags: runhidden waituntilterminated; Tasks: firewall
; 启动服务
Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; ==================== 卸载前执行 ====================
; 卸载开机自启动
Filename: "{app}\{#MyAppExeName}"; Parameters: "--uninstall"; Flags: runhidden waituntilterminated; RunOnceId: "UninstallAutostart"
; 移除防火墙规则
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""FluxaVision"""; Flags: runhidden waituntilterminated; RunOnceId: "RemoveFirewall"

[UninstallDelete]
; ==================== 卸载时保留/删除 ====================
; 保留用户数据目录
Type: filesandordirs; Name: "{app}\data"; Check: not ShouldDeleteData

[Code]
// ==================== 自定义代码 ====================
var
  ResultCode: Integer;

function ShouldDeleteData(): Boolean;
begin
  // 默认保留数据，用户可选择删除
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
