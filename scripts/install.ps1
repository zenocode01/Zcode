# install.ps1 — Zcode 跨平台安装（Windows 主安装；Linux/macOS 也可用）
# 功能镜像 scripts/install.sh:
#   1. 技能软链到 ~/.agents/skills（跨工具事实标准）
#   2. 全局 CLI: zcode.cmd / zcode.ps1 包装器（调 python -m zcode.cli）
#   3. 用户 PATH 注册 + ~/.zcode/config 本地配置
# 依赖: Python 3.10+（py 或 python 在 PATH）

$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }

$isWin = ($env:OS -eq "Windows_NT")
$src = Split-Path $PSScriptRoot -Parent   # 仓库根（PSScriptRoot 是 scripts/）
$skillsSrc = Join-Path $src "skills"
$agentsSkills = Join-Path $HOME ".agents/skills"
$zcodeHome = Join-Path $HOME ".zcode"
$binDir = Join-Path $HOME ".local/bin"

Write-Info "Zcode 跨平台安装"
Write-Info "  源码: $src"
Write-Info "  技能目标: $agentsSkills"
Write-Info "  CLI 目录: $binDir"

# ---------- 1. 技能安装（Windows: Junction 免管理员；失败退复制；Unix: 软链） ----------
if (-not (Test-Path $skillsSrc)) { throw "找不到技能目录 $skillsSrc" }
New-Item -ItemType Directory -Path $agentsSkills -Force | Out-Null

$skillNames = @(Get-ChildItem -Path $skillsSrc -Directory | Where-Object { -not $_.Name.StartsWith("_") } | ForEach-Object { $_.Name })

foreach ($name in $skillNames) {
  $dstSkill = Join-Path $agentsSkills $name
  if (Test-Path $dstSkill) {
    Write-Info "  · $name 已存在（跳过）"
    continue
  }
  $ok = $false
  if ($isWin) {
    # Junction 不需要管理员权限；失败则整目录复制
    try {
      New-Item -ItemType Junction -Path $dstSkill -Target (Join-Path $skillsSrc $name) -ErrorAction Stop | Out-Null
      $ok = $true
    } catch {
      Copy-Item -Path (Join-Path $skillsSrc $name) -Destination $dstSkill -Recurse -Force
      $ok = $true
    }
  } else {
    try {
      New-Item -ItemType SymbolicLink -Path $dstSkill -Target (Join-Path $skillsSrc $name) -ErrorAction Stop | Out-Null
      $ok = $true
    } catch {
      Copy-Item -Path (Join-Path $skillsSrc $name) -Destination $dstSkill -Recurse -Force
      $ok = $true
    }
  }
  Write-Ok "  ✓ 已安装技能: $name"
}

# ---------- 2. 全局 CLI 包装器 ----------
New-Item -ItemType Directory -Path $binDir -Force | Out-Null
$pythonCmd = "python"
if (Get-Command py -ErrorAction SilentlyContinue) { $pythonCmd = "py" }

# zcode.cmd（cmd / git-bash 可用）
$cmdWrapper = "@echo off`r`n$pythonCmd -m zcode.cli %*`r`n"
Set-Content -Path (Join-Path $binDir "zcode.cmd") -Value $cmdWrapper -Encoding ASCII

# zcode.ps1（PowerShell 可用）
$psWrapper = "#!/usr/bin/env pwsh`n$pythonCmd -m zcode.cli `$args`n"
Set-Content -Path (Join-Path $binDir "zcode.ps1") -Value $psWrapper -Encoding UTF8

if (-not $isWin) {
  # Unix 再加无扩展名 sh 包装器
  $shWrapper = "#!/bin/sh`nexec $pythonCmd -m zcode.cli `"`$@`"`n"
  $zcodeSh = Join-Path $binDir "zcode"
  Set-Content -Path $zcodeSh -Value $shWrapper -Encoding ASCII -NoNewline
  if (Get-Command chmod -ErrorAction SilentlyContinue) { & chmod +x $zcodeSh }
}
Write-Ok "  ✓ 已创建 CLI 包装器: zcode.cmd / zcode.ps1$(if (-not $isWin) { ' / zcode' })"

# ---------- 3. PATH 注册（Windows 用户 PATH;Unix 检查 .local/bin） ----------
if ($isWin) {
  $curPath = [Environment]::GetEnvironmentVariable("Path", "User")
  if ($curPath -notlike "*$binDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$binDir;$curPath", "User")
    Write-Ok "  已把 $binDir 加入用户 PATH（新开终端生效）"
  }
} else {
  Write-Info "  提示: 若 zcode 命令不可用，把 $binDir 加入 PATH"
}

# ---------- 4. 本地配置 ----------
New-Item -ItemType Directory -Path $zcodeHome -Force | Out-Null
$config = Join-Path $zcodeHome "config"
if (-not (Test-Path $config)) {
  @"
default_profile = "local-qwen3.6-35b"
memory_dir = "$zcodeHome/memory"
skill_repo = "$src"
"@ | Set-Content -Path $config -Encoding UTF8
  Write-Ok "  已生成配置: $config"
} else {
  Write-Info "  配置已存在，保留: $config"
}

# ---------- 5. zcode 包检查 ----------
Write-Info "  检查 zcode 包..."
& $pythonCmd -c "import zcode" 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Warn "  ⚠ zcode 包未装入 Python 环境，请先执行:"
  Write-Warn "     $pythonCmd -m pip install -e '$src/adapters'"
} else {
  Write-Ok "  ✓ zcode 包可用"
}

Write-Ok ""
Write-Ok "✓ Zcode 安装完成"
Write-Ok "  命令: zcode ticket init <项目> | zcode skills list | zcode ticket context"
Write-Ok "  提示: 新开终端后 zcode 全局可用；已有项目嵌入用 zcode ticket init --existing ."
