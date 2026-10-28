#!/usr/bin/env python3
"""R33 变异对照：说明段探针表的"前提"与通用页说明段的"归属"，两半各有一支电池。

七支（M141–M147）：
  M141 把一条说明段探针的框挪到开关标签那一行      ⇒ 必须红在**天花板**那条（前提破了），不许红在地板上
  M142 产品里把一段说明提到 `.primary`             ⇒ 同上：这条探针命名的是一个 `.secondary` 位点
  M143 产品里把一段说明降到 `.tertiary`            ⇒ 必须红在**地板**那条（R27 的原缺陷形状）
  M144 把组内间距 `captionGap` 从 3 改回 8         ⇒ 归属判据红（说明段与上下两颗开关一样远）
  M145 只把 U-55 的**顺序**改回去（保留分组间距）  ⇒ 红在"判了几段"那条：两段被并成一段
  M146 把量尺的档位边界 150 挪进说明簇里（110）     ⇒ 真值表红在"说明带里冒出标题档像素"
  M147 把 NOT-RUN 判别臂的 gate 抬到 250（永远读不到墨）⇒ 判据必须红在"一条都没判成"，不许安静地全绿

模板四件套：剔 SDKROOT、预检不许把 skip 读成绿、还原比自抓的字节、读失败消息确认红得对。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILES = {
    "settings": os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SettingsView.swift"),
    "harness": os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"),
}
SHOTS = "/tmp/r33-mut-shots"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

TIER = "UICaptureTests/testCaptionTextStaysOnTheSecondaryTier"
HUG = "UICaptureTests/testSettingsCaptionSitsCloserToItsOwnToggle"
TRUTH = "UICaptureTests/testRowTierProfileSeparatesCaptionFromTitle"

CAPTION_BLOCK = """                        Text("暂停时仍在推进系统剪贴板的变更计数，所以恢复后不会补记一条暂停期间的旧内容；已入库的历史不受影响。")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .settingsHelperAxis()"""
OCR_GROUP = """                    VStack(alignment: .leading, spacing: SettingsViewLayout.captionGap) {
                        Toggle("识别截图文字用于搜索", isOn: ocrSearchEnabled)
                        Text("关闭后不再对新入库的图片做文字识别，历史里已有的识别结果保持不变。")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .settingsHelperAxis()
                    }"""
RTF_GROUP = """                    VStack(alignment: .leading, spacing: SettingsViewLayout.captionGap) {
                        Toggle("保留富文本格式（RTF / HTML）", isOn: $preserveRichText)
                        Text("打开后从 Word、Pages、邮件里复制的文字会连格式一起存，粘回去保留加粗与链接。"
                            + "代价是历史存档明显变大（单条最多 384KB），默认关闭；"
                            + "导出与导入只带纯文本。")
                            .font(.system(size: VisualFont.meta))
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                            .settingsHelperAxis()
                    }"""
# RTF 组去掉收尾那行 `}`，好把 OCR 的说明段插进组内（M145 的变异体要的是"合法但错"的代码）
RTF_HEAD = "\n".join(RTF_GROUP.split("\n")[:-1])
OCR_TEXT = """                        Text("关闭后不再对新入库的图片做文字识别，历史里已有的识别结果保持不变。")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .settingsHelperAxis()"""
M145_MUTANT = RTF_HEAD + "\n" + OCR_TEXT + "\n                    }\n" \
    + '                    Toggle("识别截图文字用于搜索", isOn: ocrSearchEnabled)'

MUTATIONS = [
    ("M141", "说明段探针的框挪到开关标签那一行", "harness",
     'rect: CGRect(x: 150, y: 200, width: 560, height: 12))',
     'rect: CGRect(x: 150, y: 141, width: 560, height: 12))',
     TIER, "只可能是框套到了标题/正文那一档上"),
    ("M142", "产品把一段说明提到 .primary", "settings",
     CAPTION_BLOCK,
     CAPTION_BLOCK.replace(".foregroundStyle(.secondary)", ".foregroundStyle(.primary)"),
     TIER, "只可能是框套到了标题/正文那一档上"),
    ("M143", "产品把一段说明降到 .tertiary", "settings",
     CAPTION_BLOCK,
     CAPTION_BLOCK.replace(".foregroundStyle(.secondary)", ".foregroundStyle(.tertiary)"),
     TIER, "它比系统说明文字那一档淡了"),
    ("M144", "组内间距从 3 改回 8（说明段与两颗开关等距）", "settings",
     "    static let captionGap: CGFloat = 3",
     "    static let captionGap: CGFloat = 8",
     HUG, "差不多远"),
    ("M145", "只把 U-55 的顺序改回去（保留分组间距）", "settings",
     OCR_GROUP + "\n\n" + RTF_GROUP,
     M145_MUTANT,
     HUG, "这段说明不跟着任何开关"),
    ("M146", "档位边界挪进说明簇里（150 → 110）", "harness",
     "                               tierSplit: Int = 150) -> [(yPx: Int, maxDeviation: Int,",
     "                               tierSplit: Int = 110) -> [(yPx: Int, maxDeviation: Int,",
     TRUTH, "冒出"),
    # R386：`gate: 8` 那次调用早已被重构成 `inkContrast`（没有 gate 参数），
    # 盘上剩下的唯一 `gate: 8` 属于另一条 tier-profile 探针，抬到 250 只会让它 **skip**、不会红 ——
    # 同义坏法换成「探针一条都不判」：judged 停在 0，`judged >= 3` 那条地板必须红。
    ("M147", "NOT-RUN 判别臂一条都不判（循环取 prefix(0)）", "harness",
     "            for probe in Self.captionInkProbes {\n"
     "                guard let fixture = fixtures(appearance: appearance)\n"
     "                    .first(where: { $0.name == probe.fixture }) else {\n"
     '                    return XCTFail("找不到夹具 \\(probe.fixture) ⇒ \\(probe.what) 这条探针没有对象")\n',
     "            for probe in Self.captionInkProbes.prefix(0) {   // MUTANT：一条都不判\n"
     "                guard let fixture = fixtures(appearance: appearance)\n"
     "                    .first(where: { $0.name == probe.fixture }) else {\n"
     '                    return XCTFail("找不到夹具 \\(probe.fixture) ⇒ \\(probe.what) 这条探针没有对象")\n',
     TIER, "一条都没判成"),
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

    print("=== 预检（不注入任何变异，三条判据都必须绿）===", flush=True)
    ok = True
    for test in (TIER, HUG, TRUTH):
        verdict, out = run(test)
        print(f"  {test:66s} {verdict}", flush=True)
        if verdict != "ESCAPED":
            ok = False
            print((out.splitlines() or [""])[-1][:220], flush=True)
    if not ok:
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
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
            reason = "对  「" + hit[0].strip()[-160:] + "」" if hit else f"!! 红得不对（找不到「{expect}」）"
        if verdict == "DID-NOT-RUN":
            first = [l for l in out.splitlines() if "error:" in l][:1]
            reason = "  " + (first[0][:150] if first else "")
        if verdict == "ESCAPED":
            reason = "!! 变异全绿通过 ⇒ 判据没盖住这条路"
        results.append((mid, verdict, title, reason))
        print(f"{mid}: {verdict} {title} {reason}", flush=True)

    print("\n=== R33 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}  {reason}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
