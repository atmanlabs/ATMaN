$ErrorActionPreference='Stop'
$appTarget=Join-Path $env:LOCALAPPDATA 'Programs\AtmanSituationGym'
$buildSource=Join-Path $PSScriptRoot 'dist\ATMAN Situation Gym'
New-Item -ItemType Directory -Path $appTarget -Force | Out-Null
Copy-Item -Path (Join-Path $buildSource '*') -Destination $appTarget -Recurse -Force
$shellLink=New-Object -ComObject WScript.Shell
$desktopFolder=[Environment]::GetFolderPath('Desktop')
$startFolder=Join-Path ([Environment]::GetFolderPath('Programs')) 'ATMAN Situation Gym'
New-Item -ItemType Directory -Path $startFolder -Force | Out-Null
foreach ($shortcutPath in @((Join-Path $desktopFolder 'ATMAN Situation Gym.lnk'),(Join-Path $startFolder 'ATMAN Situation Gym.lnk'))) {
 $shortcut=$shellLink.CreateShortcut($shortcutPath)
 $shortcut.TargetPath=Join-Path $appTarget 'ATMAN Situation Gym.exe'
 $shortcut.WorkingDirectory=$appTarget
 $shortcut.Description='ATMAN live-stack scenario training with simulated tools'
 $shortcut.Save()
}
$uninstallText=@'
$ErrorActionPreference='Stop'
$target=Join-Path $env:LOCALAPPDATA 'Programs\AtmanSituationGym'
$expected=[IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\AtmanSituationGym'))
if ([IO.Path]::GetFullPath($target) -ne $expected -or (Split-Path $target -Leaf) -ne 'AtmanSituationGym') { throw 'Unexpected uninstall path' }
Get-Process -Name 'ATMAN Situation Gym' -ErrorAction SilentlyContinue | Stop-Process
Remove-Item -LiteralPath (Join-Path ([Environment]::GetFolderPath('Desktop')) 'ATMAN Situation Gym.lnk') -ErrorAction SilentlyContinue
$shortcutFolder=Join-Path ([Environment]::GetFolderPath('Programs')) 'ATMAN Situation Gym'
Remove-Item -LiteralPath (Join-Path $shortcutFolder 'ATMAN Situation Gym.lnk') -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $shortcutFolder -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\AtmanSituationGym' -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $target -Recurse -Force
# Preserve all training reports, traces, and live learned memories.
'@
Set-Content -LiteralPath (Join-Path $appTarget 'Uninstall.ps1') -Value $uninstallText -Encoding utf8
$regPath='HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\AtmanSituationGym'
New-Item -Path $regPath -Force | Out-Null
$props=@{DisplayName='ATMAN Situation Gym';DisplayVersion='1.0.0';Publisher='Local application for Operator';InstallLocation=$appTarget;DisplayIcon=(Join-Path $appTarget 'ATMAN Situation Gym.exe');UninstallString=('powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $appTarget 'Uninstall.ps1')+'"')}
foreach ($key in $props.Keys) { New-ItemProperty -Path $regPath -Name $key -Value $props[$key] -PropertyType String -Force | Out-Null }
Write-Output ('Installed: '+$appTarget)
Write-Output ('Desktop shortcut: '+(Join-Path $desktopFolder 'ATMAN Situation Gym.lnk'))
