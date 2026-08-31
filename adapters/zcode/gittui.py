"""gittui — zcode git 的 textual 全屏 TUI（视图层）。

仅本文件依赖 textual；所有 git 语义与解析走 gitcore。面板切换 + 键盘绑定，
内容区上方列表、下方详情（diff），底部状态栏实时显示分支/上游/变更/冲突。
"""
from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import DataTable, Footer, Header, Input, Static

from . import gitcore

# 面板定义：键 + 名称 + 方法后缀
PANELS = [
    ("1", "状态", "status"),
    ("2", "差异", "diff"),
    ("3", "提交", "commit"),
    ("4", "日志", "log"),
    ("5", "分支", "branch"),
    ("6", "储藏", "stash"),
    ("7", "远端", "remote"),
    ("8", "进阶", "advanced"),
]


class Sidebar(Static):
    """左侧面板列表，高亮当前面板。"""

    def render(self) -> str:
        current = getattr(self.app, "panel_index", 0)
        lines = []
        for i, (key, name, _) in enumerate(PANELS):
            mark = "▶" if i == current else " "
            lines.append(f"{mark} {key} {name}")
        return "\n".join(lines)


class GitApp(App):
    """zcode git 全屏 TUI。"""

    TITLE = "zcode git"
    CSS = """
    Sidebar {
        width: 12;
        border-right: solid $primary;
        padding: 0 1;
        background: $panel;
    }
    #content {
        width: 1fr;
        height: 1fr;
    }
    #detail {
        height: 14;
        border-top: solid $primary-darken-1;
        padding: 0 1;
    }
    #statusbar {
        height: 1;
        background: $primary-darken-1;
        color: $text;
    }
    #hint {
        height: 2;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("q", "quit", "退出"),
        ("tab", "next_panel", "下一面板"),
        ("space", "toggle_stage", "暂存/取消"),
        ("a", "stage_all", "全选暂存"),
        ("d", "discard", "丢弃更改"),
        ("c", "commit", "提交"),
        ("o", "ours", "保留本地"),
        ("t", "theirs", "保留远端"),
        ("p", "stash_pop", "stash pop"),
        ("question_mark", "help", "帮助"),
    ]

    def __init__(self):
        super().__init__()
        self.panel_index = 0
        self.root: Path | None = None
        self._row_keys: list[str] = []  # 与 DataTable 行同步的 key 列表

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Sidebar()
            with Vertical():
                yield DataTable(id="content", cursor_type="row", zebra_stripes=True)
                yield Static(id="detail", markup=False)
        yield Static(id="statusbar")
        yield Static(id="hint")
        yield Footer()

    def on_mount(self) -> None:
        root = gitcore.find_git_root()
        if root is None:
            self._statusbar().update("不在 git 仓库内（按 q 退出）")
            self._hint().update("请在 git 仓库目录下运行 zcode git")
            return
        self.root = root
        self._refresh()

    # ---- 通用 ----
    def _table(self) -> DataTable:
        return self.query_one("#content", DataTable)

    def _detail(self) -> Static:
        return self.query_one("#detail", Static)

    def _statusbar(self) -> Static:
        return self.query_one("#statusbar", Static)

    def _hint(self) -> Static:
        return self.query_one("#hint", Static)

    def _current_key(self) -> str | None:
        table = self._table()
        if table.row_count == 0:
            return None
        idx = table.cursor_row
        return self._row_keys[idx] if idx < len(self._row_keys) else None

    def _refresh(self) -> None:
        if self.root is None:
            return
        self._refresh_statusbar()
        name = PANELS[self.panel_index][2]
        self._detail().update("")
        getattr(self, f"_show_{name}")()

    def _refresh_statusbar(self) -> None:
        state, files = gitcore.git_status(self.root)
        parts = [f"[{state.branch}]"]
        if state.upstream:
            parts.append(f"上游 {state.upstream}")
        if state.ahead or state.behind:
            parts.append(f"↑{state.ahead} ↓{state.behind}")
        parts.append(f"变更 {len(files)}")
        if state.conflicts:
            parts.append(f"冲突 {len(state.conflicts)}")
        self._statusbar().update("  ".join(parts))

    def _hint_for(self, text: str) -> None:
        self._hint().update(text)

    # ---- 各面板 ----
    def _show_status(self) -> None:
        table = self._table()
        table.clear(columns=True)
        table.add_columns("状态", "路径")
        self._row_keys = []
        state, files = gitcore.git_status(self.root)
        for f in sorted(files, key=lambda x: (not x.staged, x.path)):
            if f.conflicted:
                mark = "UU"
            elif f.untracked:
                mark = "??"
            elif f.staged:
                mark = "M "
            else:
                mark = " M"
            table.add_row(mark, f.path, key=f.path)
            self._row_keys.append(f.path)
        self._hint_for("空格 暂存/取消 · a 全选 · d 丢弃 · c 提交 · 回车 看 diff · Tab 切面板 · q 退出")

    def _show_diff(self) -> None:
        table = self._table()
        table.clear(columns=True)
        table.add_columns("状态", "路径")
        self._row_keys = []
        _, files = gitcore.git_status(self.root)
        for f in sorted(files, key=lambda x: x.path):
            table.add_row("U" if f.conflicted else "M", f.path, key=f.path)
            self._row_keys.append(f.path)
        self._hint_for("回车 查看所选文件 diff")

    def _show_commit(self) -> None:
        table = self._table()
        table.clear(columns=True)
        table.add_columns("状态", "路径")
        self._row_keys = []
        _, files = gitcore.git_status(self.root)
        staged = [f for f in files if f.staged]
        if not staged:
            self._detail().update("（暂存区为空，先在「状态」面板空格暂存文件）")
        for f in staged:
            table.add_row("M ", f.path, key=f.path)
            self._row_keys.append(f.path)
        self._hint_for("c 提交暂存区 · 回车 查看 diff")

    def _show_log(self) -> None:
        table = self._table()
        table.clear(columns=True)
        table.add_columns("哈希", "作者", "日期", "说明")
        self._row_keys = []
        for c in gitcore.git_log(self.root):
            table.add_row(c.hash[:7], c.author, c.date, c.subject, key=c.hash)
            self._row_keys.append(c.hash)
        self._hint_for("回车 查看该提交详情")

    def _show_branch(self) -> None:
        table = self._table()
        table.clear(columns=True)
        table.add_columns("", "分支", "上游")
        self._row_keys = []
        for b in gitcore.git_branches(self.root):
            mark = "*" if b.is_current else " "
            tag = "本地" if b.is_local else "远程"
            table.add_row(mark, f"{b.name} ({tag})", b.upstream or "", key=b.name)
            self._row_keys.append(b.name)
        self._hint_for("回车 检出该分支")

    def _show_stash(self) -> None:
        table = self._table()
        table.clear(columns=True)
        table.add_columns("引用", "说明")
        self._row_keys = []
        for e in gitcore.git_stash_list(self.root):
            table.add_row(e.ref, e.message, key=e.ref)
            self._row_keys.append(e.ref)
        self._hint_for("p 弹出并应用 · 回车 应用")

    def _show_remote(self) -> None:
        table = self._table()
        table.clear(columns=True)
        table.add_columns("远端", "地址")
        self._row_keys = []
        code, out = gitcore.run_git(self.root, ["remote", "-v"])
        for line in out:
            if line.strip():
                parts = line.split()
                table.add_row(parts[0], parts[1] if len(parts) > 1 else "", key=parts[0])
                self._row_keys.append(parts[0])
        self._hint_for("暂只读展示，远端操作请用 zcode git push/pull/fetch")

    def _show_advanced(self) -> None:
        table = self._table()
        table.clear(columns=True)
        table.add_columns("操作", "说明")
        self._row_keys = []
        for op, desc in [
            ("rebase", "交互式变基"),
            ("cherry-pick", "遴选提交"),
            ("tag", "标签管理"),
            ("reset", "重置（soft/mixed/hard）"),
            ("revert", "还原提交"),
        ]:
            table.add_row(op, desc, key=op)
            self._row_keys.append(op)
        self._hint_for("进阶操作请用 zcode git <rebase|cherry-pick|tag|reset|revert>")

    # ---- 详情（diff）----
    def _show_detail_diff(self, target: str | None, staged: bool = False) -> None:
        text = gitcore.git_diff(self.root, target=target, staged=staged)
        self._detail().update(text if text else "（无差异）")

    # ---- 事件 ----
    def on_data_table_row_selected(self, event) -> None:
        """回车：按面板显示详情或执行操作。"""
        if self.root is None:
            return
        key = self._current_key()
        name = PANELS[self.panel_index][2]
        if name == "status":
            self._show_detail_diff(key)
        elif name == "diff":
            self._show_detail_diff(key)
        elif name == "commit":
            self._show_detail_diff(key, staged=True)
        elif name == "log":
            text = gitcore.git_diff(self.root, target=None, staged=False)
            # 提交详情：用 git show
            code, out = gitcore.run_git(self.root, ["show", "--stat", "--format=fuller", key])
            self._detail().update("\n".join(out) if code == 0 else "（无详情）")
        elif name == "branch":
            if key:
                gitcore.run_git(self.root, ["checkout", key])
                self._refresh()
        elif name == "stash":
            ref = key.split(":")[0] if key else ""
            if ref:
                gitcore.run_git(self.root, ["stash", "apply", ref])
                self._refresh()

    # ---- 按键 ----
    def action_next_panel(self) -> None:
        self.panel_index = (self.panel_index + 1) % len(PANELS)
        self._refresh()

    def action_toggle_stage(self) -> None:
        if self.root is None or self.panel_index != 0:
            return
        key = self._current_key()
        if not key:
            return
        state, files = gitcore.git_status(self.root)
        f = next((x for x in files if x.path == key), None)
        if f is None:
            return
        if f.staged:
            gitcore.run_git(self.root, ["reset", "HEAD", "--", key])
        else:
            gitcore.run_git(self.root, ["add", "--", key])
        self._refresh()

    def action_stage_all(self) -> None:
        if self.root is None:
            return
        gitcore.run_git(self.root, ["add", "-A"])
        self._refresh()

    def action_discard(self) -> None:
        if self.root is None or self.panel_index != 0:
            return
        key = self._current_key()
        if not key:
            return
        gitcore.run_git(self.root, ["checkout", "--", key])
        self._refresh()

    def action_commit(self) -> None:
        if self.root is None:
            return

        def do_commit(msg: str | None) -> None:
            if msg and msg.strip():
                code, out = gitcore.git_commit(self.root, msg.strip())
                if code == 0:
                    self._refresh()
                else:
                    self._detail().update("\n".join(out[-10:]))

        self.push_screen(Input(placeholder="提交消息（回车确认）"), do_commit)

    def action_ours(self) -> None:
        """冲突解决：保留本地版本。"""
        if self.root is None:
            return
        key = self._current_key()
        if not key:
            return
        state, _ = gitcore.git_status(self.root)
        if key in state.conflicts:
            gitcore.run_git(self.root, ["checkout", "--ours", "--", key])
            gitcore.run_git(self.root, ["add", "--", key])
            self._refresh()

    def action_theirs(self) -> None:
        """冲突解决：保留远端版本。"""
        if self.root is None:
            return
        key = self._current_key()
        if not key:
            return
        state, _ = gitcore.git_status(self.root)
        if key in state.conflicts:
            gitcore.run_git(self.root, ["checkout", "--theirs", "--", key])
            gitcore.run_git(self.root, ["add", "--", key])
            self._refresh()

    def action_stash_pop(self) -> None:
        if self.root is None or self.panel_index != 5:
            return
        gitcore.run_git(self.root, ["stash", "pop"])
        self._refresh()

    def action_help(self) -> None:
        self._hint_for("空格=暂存 · a=全选 · d=丢弃 · c=提交 · o/t=冲突选本地/远端 · p=stash pop · Tab=切面板 · 回车=详情 · q=退出")


def main() -> None:
    GitApp().run()


if __name__ == "__main__":
    main()
