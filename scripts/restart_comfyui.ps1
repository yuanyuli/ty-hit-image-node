param(
  [string]$ComfyRoot = "E:\ComfyUI_windows_portable-G314\ComfyUI"
)
$python = Join-Path (Split-Path $ComfyRoot) "python_embeded\python.exe"
$main = Join-Path $ComfyRoot "main.py"
if (!(Test-Path -LiteralPath $python)) { throw "找不到 ComfyUI Python: $python" }
if (!(Test-Path -LiteralPath $main)) { throw "找不到 ComfyUI main.py: $main" }
Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -eq $python -and $_.CommandLine -like "*ComfyUI*main.py*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Process -WindowStyle Hidden -FilePath $python -ArgumentList '-s',$main,'--windows-standalone-build','--disable-auto-launch','--preview-method','auto','--fast','fp16_accumulation','--cuda-malloc' -WorkingDirectory $ComfyRoot
Write-Output "ComfyUI 已按标准参数启动: $ComfyRoot"
