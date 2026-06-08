#!/usr/bin/env python3
"""Release-only helper for promoting curated local items to GitHub Issues.

During active development, issues and PRDs live under .scratch/. This script is
kept only for a deliberate release-preparation pass, after deciding which local
items should become public GitHub Issues.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

REPO = "mnmc5h5ntg-wq/ClipboardHistory"
GITHUB_API = "https://api.github.com"


def post(title, body, labels, *, token, repo=REPO):
    payload = json.dumps({"title": title, "body": body, "labels": labels}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{GITHUB_API}/repos/{repo}/issues",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "ClipboardHistory-release-helper",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API failed ({error.code}): {body[:200]}") from error

    if "number" not in data:
        raise RuntimeError(f"Unexpected response: {json.dumps(data, ensure_ascii=False)[:200]}")
    print(f"  ✅ #{data['number']} {title}")
    return data["number"]


def all_issues():
    return [
        ("搜索无结果时状态提示错误",
         "有记录但搜索无匹配时，侧边栏仍显示「暂无剪贴板历史」，应改为「无匹配结果」。\n\n"
         "修改: ContentView.swift 侧边栏空状态区分 entries.isEmpty 和 filteredEntries.isEmpty。\n\n"
         "```swift\nif manager.filteredEntries.isEmpty {\n    if manager.entries.isEmpty {\n        Text(\"暂无剪贴板历史\")\n    } else {\n        Text(\"无匹配结果\")\n    }\n}\n```",
         ["bug", "ui"]),

        ("边栏时间精确到秒导致频繁刷新",
         "边栏 .relative 时间每秒刷新，界面频繁跳动。\n\n"
         "期望: 边栏只显示 HH:mm 时刻；详情头部显示 yyyy-MM-dd HH:mm:ss。\n\n"
         "```swift\nText(entry.timestamp.formatted(.dateTime.hour().minute()))\n```",
         ["bug", "ui", "ux"]),

        ("清空全部按钮缺少危险动作样式与二次确认",
         "点击即清空，无确认，易误操作。应加红色样式 + Alert 确认。\n\n"
         "```swift\n.foregroundStyle(.red)\n.alert(\"清空全部记录\", isPresented: $showConfirm) {\n    Button(\"取消\", role: .cancel) {}\n    Button(\"清空\", role: .destructive) { manager.clearAll() }\n}\n```",
         ["enhancement", "ui", "ux"]),

        ("历史记录上限过低且无溢出提示",
         "上限 100 条偏少，超出时静默删除无提示。提升至 500 条，加溢出提示。",
         ["enhancement", "ux"]),

        ("右下角胶囊按钮缺少 Hover 动效",
         "GlassPill 悬停无反馈。应复用 GlassCircleButton 的 hover 放大+高亮逻辑。",
         ["enhancement", "ui"]),

        ("边栏标题「时间剪史」自动换行",
         "窄窗口下四个字折成两行。加 lineLimit(1) 和 fixedSize。\n\n"
         "```swift\nText(\"时间剪史\")\n    .lineLimit(1)\n    .fixedSize(horizontal: true, vertical: false)\n```",
         ["bug", "ui"]),

        ("图片缩略图样式不统一",
         "不同来源缩略图表现不一致：有些显示实际内容，有些是文件图标。统一样式：圆角 4pt、16x16、统一边框。",
         ["bug", "ui"]),

        ("搜索框省略号不规范",
         "「搜索历史…」使用了英文省略号，应为中文「……」。\n\n"
         "```swift\nTextField(\"搜索历史……\", text: ...)\n```",
         ["bug", "ui"]),

        ("顶部菜单未本地化且存在冗余项",
         "File/Edit/View 未汉化，部分菜单项为空或无意义。应汉化并清理。\n\n"
         "```swift\n.commands {\n    CommandGroup(replacing: .appInfo) {\n        Button(\"关于时间剪史\") { ... }\n    }\n}\n```",
         ["enhancement", "ui"]),

        ("Show All Tabs 菜单项无意义",
         "顶部菜单含 Show All Tabs，在非浏览器应用中无意义。应移除。\n\n"
         "```swift\nCommandGroup(replacing: .toolbar) {}\n```",
         ["bug"]),

        ("关于窗口信息贫乏",
         "关于弹框仅基本信息，应补充：版本号、作者、GitHub 链接、MIT License。",
         ["enhancement", "ui"]),

        ("右键菜单未汉化且含无关项",
         "文本右键菜单为英文且含无关项。应保留复制/全选/查找等必要项并汉化。",
         ["bug", "ui"]),
    ]


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Promote curated release items to GitHub Issues.")
    parser.add_argument("--repo", default=REPO, help="GitHub repo, for example owner/name")
    parser.add_argument(
        "--confirm-release-publish",
        action="store_true",
        help="Actually create GitHub Issues. Without this flag, only prints the planned items.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    issues = all_issues()
    if not args.confirm_release_publish:
        print("预演：不会创建 GitHub Issue。开发期请继续使用 .scratch/ 本地 markdown。")
        print("如确认要在 release 准备阶段发布这些 Issue，请添加 --confirm-release-publish。")
        for index, (title, _body, labels) in enumerate(issues, start=1):
            print(f"{index:02d}. {title} [{', '.join(labels)}]")
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("缺少 GITHUB_TOKEN。请只在 release 准备阶段通过环境变量提供 token。", file=sys.stderr)
        return 1

    print(f"在 {args.repo} 创建 Issue...\n")
    ok = 0
    for title, body, labels in issues:
        try:
            post(title, body, labels, token=token, repo=args.repo)
            ok += 1
        except Exception as e:
            print(f"  ❌ {title}: {e}")
    print(f"\n完成: {ok}/{len(issues)} 创建成功")
    return 0 if ok == len(issues) else 1


if __name__ == "__main__":
    raise SystemExit(main())
