#!/usr/bin/env bash
# Zcode 跨平台技能安装脚本（Layer 0 交付物）
# 以 ~/.agents/skills（跨工具事实标准）为主目标，平台原生目录做双保险。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
ZCODE_HOME="${ZCODE_HOME:-$HOME/.zcode}"

MODE="global"
PROJECT_DIR=""
UNINSTALL=0
ALL_PLATFORMS=0

usage() {
    cat <<EOF
Zcode 跨平台技能安装脚本

用法:
  bash scripts/install.sh                 全局安装（~/.agents/skills + 已存在的平台原生目录）
  bash scripts/install.sh --project <dir> 项目级安装（<dir>/.agents/skills）
  bash scripts/install.sh --all-platforms 强制创建全部 8 个平台原生目录（双保险）
  bash scripts/install.sh --uninstall     卸载（仅删除指向本仓库的软链）

选项:
  --project <dir>   项目级安装
  --all-platforms   强制在 8 个平台原生目录都建软链
  --uninstall       卸载
  -h, --help        显示帮助
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project) MODE="project"; PROJECT_DIR="$2"; shift 2 ;;
        --all-platforms) ALL_PLATFORMS=1; shift ;;
        --uninstall) UNINSTALL=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "未知参数: $1" >&2; usage; exit 1 ;;
    esac
done

[[ -d "$SKILLS_DIR" ]] || { echo "错误: 找不到技能目录 $SKILLS_DIR" >&2; exit 1; }

# 收集技能（跳过 _ 开头目录；技能名须匹配 opencode 约束 ^[a-z0-9]+(-[a-z0-9]+)*$）
mapfile -t SKILLS < <(find "$SKILLS_DIR" -mindepth 1 -maxdepth 1 -type d -not -name "_*" -printf "%f\n" | sort)

link_skill() {
    # $1 = 目标技能目录（如 ~/.agents/skills）
    local target="$1"
    mkdir -p "$target"
    local name src dst
    for name in "${SKILLS[@]:-}"; do
        src="$SKILLS_DIR/$name"
        dst="$target/$name"
        if [[ -e "$dst" || -L "$dst" ]]; then
            if [[ -L "$dst" && "$(readlink "$dst")" == "$src" ]]; then
                echo "  ✓ $name 已链接（跳过）"
            else
                echo "  ⚠ $dst 已存在且非本仓库链接，跳过"
            fi
        else
            ln -s "$src" "$dst"
            echo "  ✓ 链接 $name → $dst"
        fi
    done
}

unlink_skill() {
    local target="$1"
    local name dst
    for name in "${SKILLS[@]:-}"; do
        dst="$target/$name"
        if [[ -L "$dst" && "$(readlink "$dst")" == "$SKILLS_DIR/$name" ]]; then
            rm "$dst"
            echo "  ✓ 移除 $dst"
        fi
    done
}

# 平台原生技能目录（与 zcode/cli.py 的 PLATFORMS 保持一致）
PLATFORM_DIRS=(
    "$HOME/.claude/skills"
    "$HOME/.cursor/skills"
    "$HOME/.codex/skills"
    "$HOME/.gemini/skills"
    "$HOME/.config/opencode/skills"
    "$HOME/.kimi-code/skills"
    "$HOME/.pi/agent/skills"
    "$HOME/.reasonix/skills"
)

write_config() {
    mkdir -p "$ZCODE_HOME"
    local config="$ZCODE_HOME/config"
    if [[ ! -f "$config" ]]; then
        cat > "$config" <<EOF
# Zcode 本地配置（首次安装自动生成）
default_profile = "local-qwen3.6-35b"
memory_dir = "$ZCODE_HOME/memory"
skill_repo = "$REPO_ROOT"
EOF
        echo "  已生成配置: $config"
    else
        echo "  配置已存在，保留: $config"
    fi
}

install_cli() {
    # 全局 CLI 包装器: 任何目录直接 `zcode`（依赖 zcode 包已装入 python3 环境）
    local bindir="$HOME/.local/bin"
    mkdir -p "$bindir"
    local wrapper="$bindir/zcode"
    cat > "$wrapper" <<EOF
#!/bin/sh
# Zcode CLI 包装器（install.sh 生成）。若 python3 环境未装 zcode 包，先:
#   python3 -m pip install -e "$REPO_ROOT/adapters"
exec python3 -m zcode.cli "\$@"
EOF
    chmod +x "$wrapper"
    echo "  ✓ 已安装 CLI 包装器: $wrapper（任何目录直接 \`zcode\`）"
    if ! command -v python3 >/dev/null 2>&1; then
        echo "  ⚠ 未找到 python3，请先安装 Python 3.10+ 后重跑"
    elif ! python3 -c "import zcode" >/dev/null 2>&1; then
        echo "  ⚠ zcode 包未装入 python3 环境，先执行: python3 -m pip install -e '$REPO_ROOT/adapters'"
    fi
}

main() {
    if [[ $UNINSTALL -eq 1 ]]; then
        echo "== Zcode 卸载 =="
        if [[ "$MODE" == "project" ]]; then
            [[ -n "$PROJECT_DIR" ]] || { echo "错误: --project 需要目录参数" >&2; exit 1; }
            local pdir
            pdir="$(realpath -m "$PROJECT_DIR")/.agents/skills"
            echo "[项目级] 卸载: $pdir"
            unlink_skill "$pdir"
        else
            unlink_skill "$HOME/.agents/skills"
            local d
            for d in "${PLATFORM_DIRS[@]}"; do
                unlink_skill "$d"
            done
        fi
        echo "完成。~/.zcode/config 保留（含既有配置，如需删除请手动移除）。"
        exit 0
    fi

    echo "== Zcode 技能安装 =="

    if [[ "$MODE" == "project" ]]; then
        [[ -n "$PROJECT_DIR" ]] || { echo "错误: --project 需要目录参数" >&2; exit 1; }
        local dir
        dir="$(realpath -m "$PROJECT_DIR")/.agents/skills"
        echo "[项目级] 安装到: $dir"
        link_skill "$dir"
        echo "完成。项目级 .agents/skills 覆盖: opencode / Kimi Code / Pi / Cursor / Gemini / Reasonix"
        exit 0
    fi

    echo "[1/2] 主目标 ~/.agents/skills（跨工具事实标准: opencode/Kimi Code/Pi/Cursor/Reasonix）"
    link_skill "$HOME/.agents/skills"

    echo "[2/2] 平台原生目录双保险（仅已存在的目录）"
    local d
    for d in "${PLATFORM_DIRS[@]}"; do
        if [[ -d "$d" ]]; then
            echo "  → $d 存在，补软链"
            link_skill "$d"
        else
            if [[ $ALL_PLATFORMS -eq 1 ]]; then
                echo "  → $d 不存在，强制创建"
                link_skill "$d"
            else
                echo "  · $d 未安装（跳过；可用 --all-platforms 强制创建）"
            fi
        fi
    done

    echo "[3/4] 写入本地配置"
    write_config

    echo "[4/4] 安装全局 CLI（任意目录直接 \`zcode\`）"
    install_cli

    echo "== 完成 =="
}

main
