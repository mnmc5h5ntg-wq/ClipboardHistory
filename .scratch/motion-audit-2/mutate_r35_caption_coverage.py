#!/usr/bin/env python3
"""R35 变异对照：新点名的 9 处说明段（其余设置分区 + 详情 meta + 行内 meta）与覆盖规则。

  M152 把快捷键页那条探针的框挪到上面那行开关标签上   ⇒ 必须红在天花板（前提破了要说得出口）
  M153 产品把隐私页那句说明降到 `.tertiary`            ⇒ 必须红在地板（R27 那个形状）
  M154 从表里删掉快捷键页那条探针                      ⇒ 必须红在**覆盖规则**（"这一页一处都没点名"）
  M155 把"列表行第二行 meta"那条探针加回说明段表        ⇒ 必须红在**颜色域资格**那条：
        这一列压在 NSAppearanceNameVibrantLight/Dark 子树上，拍到的是合成**前**的像素。
        （这一支原本是"产品把 meta 降到 .tertiary"，它 **ESCAPED 过一次** —— 那次逃逸
         顺着查出来的不是框放错，而是整帧颜色域不同：侧栏 `.primary` 行标题最深 113，
         设置页同样声明 `.primary` 的标签最深 38。所以这条探针本来就不该在表里。）
  M156 把已登记的 vibrant 控件探针名单清空              ⇒ 名单那条必须红（盲区不许被忘掉）

模板四件套：剔 SDKROOT、预检不许把 skip 读成绿、还原比自抓的字节、读失败消息确认红得对。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILES = {
    "harness": os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"),
    "settings": os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SettingsView.swift"),
    "rows": os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift"),
}
SHOTS = "/tmp/r35-mut-shots"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
CAPTION = "UICaptureTests/testCaptionTextStaysOnTheSecondaryTier"
DOMAIN = "UICaptureTests/testProbesDoNotSitOnVibrantColumns"

SHORTCUT_PROBE = """        InkProbe(fixture: "settings-shortcuts", what: "快捷键页那一段说明（R28 修过它被截断，档也要钉住）",
                 rect: CGRect(x: 150, y: 275, width: 560, height: 10)),
"""
PRIVACY_CAPTION = """                    Text("启用后可提供更准确的推荐。")
                        .font(.caption)
                        .foregroundStyle(.secondary)"""
DETAIL_PROBE = """        InkProbe(fixture: "detail-0-text", what: "详情头部 meta（时间 · 大小 · 来源）",
                 rect: CGRect(x: 0, y: 36, width: 720, height: 12)),"""
SIDEBAR_PROBE = DETAIL_PROBE + """
        InkProbe(fixture: "sidebar-history", what: "列表行第二行 meta（时间/来源那一小条）",
                 rect: CGRect(x: 0, y: 164, width: 300, height: 12)),"""
DECLARED = """    static let vibrantResolvedControlProbes: Set<String> = [
        "sidebar-multi-select/批量操作按钮（侧栏工具排）",
    ]"""

MUTATIONS = [
    ("M152", "快捷键页探针的框挪到上面那行标签", "harness",
     SHORTCUT_PROBE,
     SHORTCUT_PROBE.replace("y: 275", "y: 117"),
     CAPTION, "只可能是框套到了标题/正文那一档上"),
    ("M153", "隐私页那句说明降到 .tertiary", "settings",
     PRIVACY_CAPTION,
     PRIVACY_CAPTION.replace(".foregroundStyle(.secondary)", ".foregroundStyle(.tertiary)"),
     CAPTION, "它比系统说明文字那一档淡了"),
    ("M154", "从表里删掉快捷键页那条探针（覆盖规则的对象）", "harness",
     SHORTCUT_PROBE, "",
     CAPTION, "这些设置分区在说明段表里"),
    ("M155", "把侧栏 meta 探针加回说明段表（它压在 vibrant 列上）", "harness",
     DETAIL_PROBE, SIDEBAR_PROBE,
     DOMAIN, "这些说明段探针压在 vibrant 子树上"),
    ("M156", "把已登记的 vibrant 控件探针名单清空", "harness",
     DECLARED, "    static let vibrantResolvedControlProbes: Set<String> = []",
     DOMAIN, "控件探针压在 vibrant 子树上的名单变了"),
]


def run(test_filter):
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    passed = [l for l in lines if "Test Case" in l and "passed" in l]
    failed = [l for l in lines if "Test Case" in l and " failed" in l]
    if not passed and not failed:
        return "DID-NOT-RUN", "整条被 skip：" + (lines[-1][:160] if lines else "")
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out


def main():
    only = [a for a in sys.argv[1:] if a.startswith("M")]
    originals = {k: open(v, encoding="utf-8").read() for k, v in FILES.items()}
    digests = {v: open(v, "rb").read() for v in FILES.values()}

    print("=== 预检（不注入任何变异，两条判据都必须绿）===", flush=True)
    for test in (CAPTION, DOMAIN):
        verdict, out = run(test)
        print(f"  {test:66s} {verdict}", flush=True)
        if verdict != "ESCAPED":
            print((out.splitlines() or [""])[-1][:220], flush=True)
            print("PREFLIGHT_FAILED ⇒ 一支都不注入", flush=True)
            return 2

    results = []
    for mid, title, key, needle, mutant, test, expect in MUTATIONS:
        if only and mid not in only:
            continue
        text = originals[key]
        got = text.count(needle)
        if got != 1:
            results.append((mid, "DID-NOT-RUN", title, f"needle 命中 {got} 次，期望 1 ⇒ 不注入"))
            print(f"{mid}: DID-NOT-RUN needle 命中 {got} 次", flush=True)
            continue
        path = FILES[key]
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text.replace(needle, mutant))
        try:
            verdict, out = run(test)
        except subprocess.TimeoutExpired:
            verdict, out = "DID-NOT-RUN", "timeout"
        finally:
            with open(path, "wb") as handle:
                handle.write(digests[path])
        reason = ""
        if verdict == "CAUGHT":
            hit = [l for l in out.splitlines() if expect in l][:1]
            reason = "对  「" + hit[0].strip()[-170:] + "」" if hit else f"!! 红得不对（找不到「{expect}」）"
        if verdict == "DID-NOT-RUN":
            first = [l for l in out.splitlines() if "error:" in l][:1]
            reason = "  " + (first[0][:160] if first else "")
        if verdict == "ESCAPED":
            reason = "!! 变异全绿通过 ⇒ 判据没盖住这条路"
        results.append((mid, verdict, title, reason))
        print(f"{mid}: {verdict} {title} {reason}", flush=True)

    print("\n=== R35 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}  {reason}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
