param(
    [string]$BuildRoot = 'E:\Cache\NBA-Roster-Sync\release-build',
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [string]$Python = 'python',
    [string]$PyInstallerRoot = 'E:\Dev\Tools\PythonPackages\PyInstaller-6.22.3',
    [string]$InnoCompiler = ''
)
$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).ProviderPath
$buildFull = [IO.Path]::GetFullPath($BuildRoot)
$outputFull = [IO.Path]::GetFullPath($OutputDirectory)
if ($buildFull -eq $sourceRoot -or $outputFull -eq $sourceRoot) { throw '构建和输出目录应与源码目录分开。' }
$driveRoot = [IO.Path]::GetPathRoot($buildFull)
if (-not (Test-Path -LiteralPath $driveRoot)) { throw "构建盘不存在：$driveRoot；请显式指定可用位置。" }
$space = [IO.DriveInfo]::new($driveRoot)
if ($space.AvailableFreeSpace -lt 1GB) { throw '构建盘至少需要 1 GiB 可用空间，预计峰值小于 500 MiB。' }
New-Item -ItemType Directory -Path $buildFull,$outputFull,(Join-Path $buildFull 'tmp') -Force | Out-Null
$env:TEMP = Join-Path $buildFull 'tmp'
$env:TMP = $env:TEMP
$env:PYINSTALLER_CONFIG_DIR = Join-Path $buildFull 'pyinstaller-cache'
$env:PYTHONPYCACHEPREFIX = Join-Path $buildFull 'pycache'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
if (Test-Path -LiteralPath $PyInstallerRoot) { $env:PYTHONPATH = $PyInstallerRoot }
if (Test-Path -LiteralPath 'E:\Cache\pip') { $env:PIP_CACHE_DIR='E:\Cache\pip' }
& $Python (Join-Path $PSScriptRoot 'build_assets.py')
if ($LASTEXITCODE -ne 0) { throw '图标构建失败。' }
& $Python -m PyInstaller --noconfirm --clean --workpath (Join-Path $buildFull 'work') --distpath (Join-Path $buildFull 'dist') (Join-Path $sourceRoot 'packaging\windows.spec')
if ($LASTEXITCODE -ne 0) { throw 'Windows 打包失败。' }
& $Python (Join-Path $PSScriptRoot 'package_release.py') --build-root $buildFull --output $outputFull --prepare-only
if ($LASTEXITCODE -ne 0) { throw '分发许可收集失败。' }
$version = (Get-Content -LiteralPath (Join-Path $sourceRoot 'app_runtime.py') | Select-String "^VERSION = '([^']+)'").Matches.Groups[1].Value
if (-not $InnoCompiler) {
    $candidates=@('E:\Dev\Tools\InnoSetup\7.1.1\ISCC.exe',"${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe")
    $InnoCompiler=$candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $InnoCompiler) { throw '未找到共享 Inno Setup。请通过 -InnoCompiler 指向已有 ISCC.exe。' }
& $InnoCompiler "/DBuildRoot=$buildFull" "/DAppVersion=$version" (Join-Path $sourceRoot 'packaging\installer.iss')
if ($LASTEXITCODE -ne 0) { throw '安装包构建失败。' }
& $Python (Join-Path $PSScriptRoot 'package_release.py') --build-root $buildFull --output $outputFull
if ($LASTEXITCODE -ne 0) { throw '发布候选归档失败。' }
Write-Output "交付物已写入：$outputFull。没有安装工具、启动游戏或发布远程仓库。"
