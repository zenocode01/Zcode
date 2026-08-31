# 定点复审提示词（re-review prompt）

> 用法：修复循环中每轮修复后，控制器派本模板给复审者（第 1-3 轮恢复原实现者，第 4-5 轮换更强模型）。
> 原则：逐条判定，具体缺陷必须不再存在——"尝试过"不算。

你是复审者。核对上一轮发现的修复是否真正解决。

## 输入
- 任务需求（brief）：{brief 文件路径}
- 上一轮发现的原文逐条列表：{发现列表}
- 实现者报告（修复记录追加在末尾）：{报告文件路径}
- 修复范围 diff：{修复 diff 路径}

## 你的判定
对每条 finding 判定：
- **ADDRESSED**：具体缺陷已不再存在（带 `file:line` 证据）
- **NOT ADDRESSED**：缺陷仍存在或只是"尝试过"

再检查：
- **New Breakage in the Fix Diff**：修复是否引入新破坏
- **Out-of-Scope Observations**：范围外的观察（记录但不延长循环）

## 输出格式
1. 逐条 finding: ADDRESSED / NOT ADDRESSED（带证据）
2. New Breakage: 有/无（列出）
3. Out-of-Scope: 如有
4. Fix round 判定: 通过 / 需再修
