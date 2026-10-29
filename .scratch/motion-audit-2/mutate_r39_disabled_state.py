#!/usr/bin/env python3
"""R39 变异对照：禁用态与失败回执这两件新东西，各该咬一次。

  M177 产品：`if let message` 那整段回执不画      ⇒ 红在**差值对照**（"要么没画"）与**天花板**
     （那一行没画 ⇒ 布局把下一颗开关的标签顶进这块矩形 ⇒ 读到标题档）。
     第一版这里预期的是"框贴到空白上了"（墨地板），实测**不对**：整行消失时布局会收上来，
     框里不是空白而是别人的字 ⇒ 这条也记进账本（判据的预期红要实测，不许推理）。
  M178 产品：去掉那颗开关的 `.disabled(!isSupported)` ⇒ "禁用淡得不够"必须红
  M179 产品：`setEnabled` 的 catch 里把 message 置 nil ⇒ 模型层那句回执用例 + 帧两边都红
  M180 产品：`verifyApplied` 读完不回比（恒通过）    ⇒ 真值表里两格"该抛的没抛"必须红（`did not throw`）
  M181 判据：失败回执那张夹具改名（帧消失）          ⇒ 必须红在"没有对象"，不许静默少判一档
  M182 判据：把失败回执的探针框挪到空白处            ⇒ 必须红在"框贴到空白上了"（证明这条框有牙齿）

M177/M182 是同一对：一个证明"回执不画会红"，一个证明"框贴错也会红"。
少了 M182，M177 的红可能来自任何一块墨，而 M182 把红限定在"这一块"上。

R39b 加的两支（CI 第一次跑就红在"runner 拍不出设置页"上，于是补了机器前提；
机器前提本身是一张免检牌，所以它自己也要被咬两次）：
  M183 「三张里只画出一部分」被折成环境问题      ⇒ 真值表那一格必须红
  M184 机器前提恒成立（不管几张有墨都记未运行）  ⇒ "全有墨必须判"那一格必须红
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
VIEW = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SettingsView.swift")
MODEL = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Managers/LoginItemSettings.swift")
SHOTS = "/tmp/r39-mut-shots"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

FILTER = ("UICaptureTests/(testDisabledToggleAndFailureReceiptAreVisible"
          "|testSettingsDrawabilityTruthTable"
          "|testCaptionTextStaysOnTheSecondaryTier)|LoginItemSettingsTests")

# R384 重钉：失败回执改用 `lastActionFailed` 决定颜色，整块针跟着当前源码走。
RECEIPT_BLOCK = """                        if let message = loginItemSettings.message {
                            // R492：失败回执只有红字，没有错误图标；横幅/回执都有图标，
                            // 这一行补一枚警示三角，正常的不支持说明不加。
                            HStack(spacing: 4) {
                                if loginItemSettings.lastActionFailed, loginFailureIconVisible {
                                    Image(systemName: "exclamationmark.triangle.fill")
                                        .font(.system(size: VisualGlyph.badge, weight: .semibold))
                                        .foregroundStyle(loginFailureStyle)
                                }
                                Text(message)
                                    .font(settingsHelperFont)
                                    // R384：失败回执用错误色，与「本机不支持」的静态说明分开
                                    // （快捷键页的非法录制回执也是红字；同一套状态语言）。
                                    // 判据是坐标无关的：失败帧里有红色文字像素、说明帧里没有。
                                    .foregroundStyle(loginItemSettings.lastActionFailed
                                                     ? loginFailureStyle
                                                     : AnyShapeStyle(.secondary))
                            }
                            .settingsHelperAxis()
                        }"""
DISABLED_SEAM = "                            .disabled(!loginItemSettings.isSupported)"
CATCH_MESSAGE = '            message = enabled ? "开机启动开启失败，请稍后重试。" : "开机启动关闭失败，请稍后重试。"'
VERIFY_APPLIED = """        let applied = readBack()
        guard applied == enabled else { throw LoginItemSettings.Error.loginItemNotApplied }"""
FAILED_FIXTURE = 'results.append(Fixture("settings-general-login-failed", NSSize(width: 720, height: 540)) {'
FAILED_PROBE = """        InkProbe(fixture: "settings-general-login-failed",
                 what: "回执「开机启动开启失败，请稍后重试。」（macOS 12 上 AppleScript 静默失败）",
                 rect: CGRect(x: 150, y: 135.5, width: 560, height: 11)),"""
PARTIAL_ARM = "        return .partial(drawn)"
NONE_ARM = "        if drawn == 0 { return .noneDrawn }"

MUTATIONS = [
    ("M177", "产品：那句回执整段不画", VIEW, RECEIPT_BLOCK,
     "                        // MUTANT：回执不画（原来在 `if let message` 后面）",
     "要么没画"),
    ("M178", "产品：禁用标签颜色也恒 primary", VIEW,
     """                            Text("开机启动")
                                .foregroundStyle(loginItemSettings.isSupported
                                                 ? AnyShapeStyle(.primary)
                                                 : AnyShapeStyle(.secondary))""",
     """                            Text("开机启动")
                                .foregroundStyle(AnyShapeStyle(.primary))  // MUTANT：禁用也主色""",
     "淡得不够"),
    ("M179", "产品：失败时把 message 置 nil（回到“什么都不说”）", MODEL, CATCH_MESSAGE,
     "            message = nil  // MUTANT",
     "只能靠用户自己猜"),
    ("M180", "产品：写完读回但不比较（恒通过）", MODEL, VERIFY_APPLIED,
     "        let applied = readBack()\n        _ = applied  // MUTANT：不比对 ⇒ 静默失败重新变成“看起来成功”",
     "did not throw"),
    ("M181", "判据：失败回执那张帧没了（夹具改名）", HARNESS, FAILED_FIXTURE,
     'results.append(Fixture("settings-general-login-failedX", NSSize(width: 720, height: 540)) {',
     "禁用态判据失去对象"),
    ("M182", "判据：失败回执的探针框挪到空白处", HARNESS, FAILED_PROBE,
     """        InkProbe(fixture: "settings-general-login-failed",
                 what: "回执「开机启动开启失败，请稍后重试。」（macOS 12 上 AppleScript 静默失败）",
                 rect: CGRect(x: 150, y: 400.0, width: 560, height: 11)),""",
     "框贴到空白上了"),
    # R39b：CI 第一次跑就红在"这一台拍不出设置页"上 ⇒ 补了机器前提。机器前提本身是新的免检牌，
    # 所以它自己也要有两支变异：一张坏帧被当成环境问题（M183）、以及"永远算环境问题"（M184）。
    ("M183", "判据：把「只画出一部分」折成「环境问题」", HARNESS, PARTIAL_ARM,
     "        return .noneDrawn  // MUTANT：某一帧坏了也被当成拍不出",
     "只画出一部分不是环境问题"),
    ("M184", "判据：机器前提恒成立（这条判据在这台机器上永不判）", HARNESS, NONE_ARM,
     "        return .noneDrawn  // MUTANT：不管几张有墨都记未运行",
     "机器前提就成了免检牌"),
]


def run():
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=2400)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    verdicts = [l for l in lines if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return "DID-NOT-RUN（整批 skip）", out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    if "error:" in out and not failed:
        return "BROKEN-MUTATION", out, []
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def apply(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"注入中止：那段话出现 {n} 次，不是 1 次 —— 电池与代码脱节\n  {old[:120]}")
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(text.replace(old, new))
    return text


def restore(path, original):
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(original)
    return open(path, encoding="utf-8").read() == original


def main():
    wanted = set(sys.argv[1:])
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：" + code + "\n" + out[-900:])
    print("预检 OK（未变异时这批全绿）")
    results = []
    for mid, desc, path, old, new, needle in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        code, out, failed = run()
        right = needle in out
        ok = restore(path, original)
        results.append((mid, code, "yes" if right else "NO", "yes" if ok else "NO",
                        ",".join(f.split(".")[-1] for f in failed)))
        print(f"{mid} {desc} ⇒ {code} 红得对={right} 红在 {failed}")
        if code != "CAUGHT" or not right:
            print(out[-900:])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[1] != "CAUGHT"]
    wrong = [r for r in results if r[2] != "yes"]
    dirty = [r for r in results if r[3] != "yes"]
    print(f"未被抓到={len(bad)}  红得不对={len(wrong)}  还原不干净={len(dirty)}")
    if dirty:
        raise SystemExit("RESTORE_CLEAN=no")
    if bad or wrong:
        raise SystemExit(f"MUTATION_UNCAUGHT={len(bad) + len(wrong)}")


if __name__ == "__main__":
    main()
