' FluxaVision 崩溃自恢复启动器
' 以隐藏窗口启动 FluxaVision.exe，异常崩溃时自动重启，用户主动退出时停止。
' 由开机自启项（HKCU\Run）启动。
' 卸载时安装包会写入 data\.launcher_shutdown 标记文件，通知本启动器退出。

Dim shell, fso, appDir, exePath, shutdownFile, ret

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
appDir = fso.GetParentFolderName(WScript.ScriptFullName)
exePath = appDir & "\FluxaVision.exe"
shutdownFile = appDir & "\data\.launcher_shutdown"

Do
    ' 检测卸载关机标记
    If fso.FileExists(shutdownFile) Then
        fso.DeleteFile shutdownFile, True
        Exit Do
    End If
    
    ' 以隐藏窗口(WinStyle=0)启动，等待进程退出
    ret = shell.Run("""" & exePath & """", 0, True)
    
    If ret = 0 Then
        ' exit code 0 = 用户主动退出（托盘点击"退出"）
        Exit Do
    Else
        ' exit code <> 0 = 异常崩溃，5秒后自动重启
        WScript.Sleep 5000
    End If
Loop

Set fso = Nothing
Set shell = Nothing
