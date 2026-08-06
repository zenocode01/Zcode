#!/usr/bin/env bash
# git 危险命令守卫（pre-commit 示例钩子）
# 作用：阻止提交中混入危险 git 命令的"提交信息/脚本内容"。
# 注意：pre-commit 只能拦截提交；push 类操作需 pre-push 钩子（后续补充）。
set -euo pipefail

DANGEROUS_PATTERNS=(
    "git push[^a-z]"
    "git reset --hard"
    "git clean -f"
    "git clean -fd"
    "git branch -D"
)

fail=0
# 检查暂存内容（新增/修改的文本文件）中是否含危险命令
while IFS= read -r file; do
    if grep -Eqi "${DANGEROUS_PATTERNS[*]}" "$file" 2>/dev/null; then
        echo "⚠ 检测到危险 git 命令模式: $file" >&2
        fail=1
    fi
done < <(git diff --cached --name-only --diff-filter=ACM)

if [[ $fail -eq 1 ]]; then
    echo "已阻止提交：请移除危险命令后重试（push/reset --hard/clean -f/branch -D）" >&2
    exit 1
fi

echo "pre-commit: 安全检查通过"
