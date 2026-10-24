#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R335 的变异表：十一把刀钉 HTML 预览这条新通道（M973…M983）。

R335 做的事（用户点名："让右侧预览窗口支持 html 预览"）：详情区多了一条 HTML 渲染通道 ——
判定（`DetailRenderPolicy`）、消毒（`HtmlSanitizer`）、渲染（`NSAttributedString(html:)`）、
以及"渲染出来的墨必须跟着表面走"（`applySurfaceInk`，看图腿量出来的那一族）。
它和 Markdown 那条的**区别**不是排版，而是"喂进去的是别人写的可执行文档"，
而本产品至今没有任何出网通道 ⇒ 前几把刀全部打在"通道会不会替用户做他没点头的事"上，
后两把打在"画出来的东西读不读得出来"上。

  M973 产品：渲染器拿到的是**没消毒**的原文        ⇒ 残留判据与夹具前提必须一起红
  M974 产品：删掉"除 href 外任何带 URL 的属性都去掉"那条兜底 ⇒ `data-src` 回来，残留判据必须红
  M975 产品：正文缓存键丢掉渲染器身份              ⇒ "同一段字节换渲染器"那一格必须红
  M976 产品：载荷不再优先（Markdown 猜测盖过声明）  ⇒ 真值表必须红
  M977 尺：把字节上限抬到预算之外                  ⇒ 斜率判据必须红（它量的是现读斜率，不是常量）
  M978 产品：渲染**只抹不设**（第一版的形状）        ⇒ "正文没有颜色属性"那一格必须红
  M979 产品：正文墨换成固定黑                      ⇒ "两档解析成同一个 RGB"那一格必须红
  M980 产品：字号只搬正文不搬标题                  ⇒ 层级比那半句必须红（它钉的是"另一种坏法"）
  M981 产品：整步不搬（因子写死 1）                ⇒ 正文档 == 产品那一档必须红
  M982 产品：文件那一路退回只认 Markdown            ⇒ html 文件的提示语与混排那一格必须红
  M983 产品：提示语的载荷参数退回常量              ⇒ 「两支回答必须不一样」那一格必须红

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r335.py [M973 … M977]
（十一把全打在 Sources 上；M975 打在视图文件那一行，其余十把走判据卷那一格。
 像素那一格（`testHtmlRenderedBodyInkIsReadable`）不在这里跑：它自己拍两档×两夹具，
 一轮 4 张帧 ≈ 12s，而它要红的那两种坏法 M978/M979 在属性串那一层就先红了。）
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0"
POLICY = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                      "Utilities", "DetailRenderPolicy.swift")
SANITIZER = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                         "Utilities", "HtmlPreview.swift")
BUDGET = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                      "Utilities", "HtmlPreview.swift")
TEXTVIEW = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                        "Views", "ChineseTextContextMenu.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

PIPE_CELL = u"HtmlPreviewPolicyTests|HtmlSanitizerTests|HtmlPreviewPipelineTests"  # 三个类同文件
PAIR_CELL = u"UICaptureTests/testHtmlRenderedPairDiffersOnTheSurface"

# ① 渲染器拿到没消毒的原文 ⇒ 残留判据必须红（这一刀是"消毒在不在渲染路径上"的唯一证人）。
NEEDLE_973 = u"        case .html: return HtmlSanitizer.renderableHTML(source)"
REPL_973 = u"        case .html: return source"

# ② 删掉兜底那条 ⇒ `data-src="https://…"` 这类"名字不在名单里、值里带 URL"的属性回来。
NEEDLE_974 = u"""        replace(urlValuedAttrs)
        replace(dataAttrs)"""
REPL_974 = u"""        replace(dataAttrs)"""

# ③ 缓存键丢掉渲染器身份 ⇒ 同一段字节换渲染器时切了个空操作（屏幕上什么都没发生）。
NEEDLE_975 = u"        let key = renderer.cacheKeyPrefix + source"
REPL_975 = u"        let key = source"

# ④ 载荷不再优先 ⇒ "来源 App 的声明"被"对投影的猜测"盖掉。
NEEDLE_976 = u"""    static func wantsHtmlRendering(text: String, htmlPayloadBytes: Int) -> Bool {
        if htmlPayloadBytes > 0 { return true }
        return looksLikeHtmlDocument(text)
    }"""
REPL_976 = u"""    static func wantsHtmlRendering(text: String, htmlPayloadBytes: Int) -> Bool {
        if MarkdownParsingPolicy.offersRendering(forText: text) { return false }
        if htmlPayloadBytes > 0 { return true }
        return looksLikeHtmlDocument(text)
    }"""

# ⑤ 上限抬到预算之外 ⇒ 那一格量的是**现读斜率**，所以它红不是因为常量变了，
#    而是"按这台机器的斜率，这个上限会按住主线程多久"越过了仓库自己那条预算。
NEEDLE_977 = u"    static let maximumBytes = 128 * 1024"
REPL_977 = u"    static let maximumBytes = 64 * 1024 * 1024"

# ⑥ 产品：渲染只**抹**色不**设**色 ⇒ "有一段正文没有颜色属性"必须红。
#    这一刀钉的是 R335 那次自曝：第一版 `stripBakedInk` 就是只抹不设，属性串那一格全绿
#    （它判的是"颜色属性一个都不许留"，而"没留"恰恰是它要防的形状），帧上正文仍是黑的 ——
#    现读 8779 颗 RGB(0,0,0) 落在 luma=30 的表面上 ⇒ 对比 1.26:1。
NEEDLE_978 = u"""        var runs: [(range: NSRange, isLink: Bool)] = []
        attributed.enumerateAttribute(.link, in: full) { linkValue, range, _ in
            runs.append((range, linkValue != nil))
        }"""
REPL_978 = u"""        var runs: [(range: NSRange, isLink: Bool)] = []
        out.enumerateAttribute(.link, in: full) { _, _, _ in }"""

# ⑦ 产品：正文墨换成固定黑 ⇒ "两档解析成同一个 RGB"必须红（这一支就是缺陷本体本身）。
NEEDLE_979 = u"    static var surfaceBodyInk: NSColor { MarkdownPresentation.bodyColor }"
REPL_979 = u"    static var surfaceBodyInk: NSColor { NSColor.black }"

# ⑧ 产品：字号只搬正文、不搬标题 ⇒ "层级比"那一条必须红。
#    这一刀刻意**不**打"完全没搬"（那一刀会被第一条断言抓到而抓不到层级），
#    因为层级那半句是这格独有的承诺：只把正文调大 = 标题被压平 = 另一种坏法。
NEEDLE_980 = u"            let scaled = NSFont(descriptor: font.fontDescriptor, size: font.pointSize * factor)"
REPL_980 = u"            let scaled = NSFont(descriptor: font.fontDescriptor," \
          u" size: font.pointSize == base ? target : font.pointSize)"

# ⑨ 产品：整步不搬（因子写死 1）⇒ "正文档 == 产品那一档"必须红。
NEEDLE_981 = u"        let factor = target / base"
REPL_981 = u"        let factor: CGFloat = 1"

# ⑩ 产品：文件那一路"是哪一种渲染器"退回只认 Markdown ⇒ 混排数出来那一格与提示语那格必须红。
#    这一刀钉的是 R335 第二版真正修掉的那句假话：`.html` 文件的提示语写着 Markdown。
NEEDLE_982 = u"        if HtmlPreviewPolicy.isHtmlFile(url) { return .html }"
REPL_982 = u"        if HtmlPreviewPolicy.isHtmlFile(url) { return .markdown }"

# ⑪ 产品：提示语的载荷参数退回常量 ⇒ "两支回答必须不一样"那一格必须红。
#    这是**函数有两个分支而调用点只喂一个常量**那一族的钉子：帧与属性串都看不见它。
NEEDLE_983 = u"        case .html: return HtmlPreviewPolicy.controlHelp(hasPayload: htmlPayload)"
REPL_983 = u"        case .html: return HtmlPreviewPolicy.controlHelp(hasPayload: false)"

ARMS = [
    ("M973", u"产品：渲染器拿到没消毒的原文 ⇒ 残留判据必须红", POLICY,
     NEEDLE_973, REPL_973, u"testRenderedSourceIsAlwaysTheSanitizedOne", PIPE_CELL),
    ("M974", u"产品：删掉『任何带 URL 的属性都去掉』那条兜底 ⇒ data-src 回来，判据必须红", SANITIZER,
     NEEDLE_974, REPL_974, u"testEveryLoadableOrExecutableConstructIsGone", PIPE_CELL),
    ("M975", u"产品：正文缓存键丢掉渲染器身份 ⇒ 换渲染器成了空操作，那一格必须红", TEXTVIEW,
     NEEDLE_975, REPL_975, u"testSwitchingRendererOnTheSameBytesRepaints", PIPE_CELL),
    ("M976", u"产品：载荷不再优先（Markdown 猜测盖过声明）⇒ 真值表必须红", SANITIZER,
     NEEDLE_976, REPL_976, u"testThePrecedenceIsTheWholePoint", PIPE_CELL),
    ("M977", u"尺：把字节上限抬到预算之外 ⇒ 现读斜率那一格必须红", BUDGET,
     NEEDLE_977, REPL_977, u"testTheByteCeilingIsDerivedFromTheMeasuredSlope", PIPE_CELL),
    ("M978", u"产品：渲染只抹不设 ⇒ 「正文没有颜色属性」那一格必须红（第一版的形状）", POLICY,
     NEEDLE_978, REPL_978, u"testRenderedHtmlInkFollowsTheAppearance", PIPE_CELL),
    ("M979", u"产品：正文墨换成固定黑 ⇒ 「两档同色」那一格与权威那两条必须红", POLICY,
     NEEDLE_979, REPL_979, u"testRenderedHtmlInkFollowsTheAppearance", PIPE_CELL),
    ("M980", u"产品：字号只搬正文不搬标题 ⇒ 层级比那半句必须红", POLICY,
     NEEDLE_980, REPL_980, u"testRenderedHtmlBodySitsOnTheAppTypeScale", PIPE_CELL),
    ("M981", u"产品：整步不搬（因子写死 1）⇒ 正文档那一格必须红", POLICY,
     NEEDLE_981, REPL_981, u"testRenderedHtmlBodySitsOnTheAppTypeScale", PIPE_CELL),
    ("M982", u"产品：文件那一路退回只认 Markdown ⇒ 混排那一格与 html 文件提示语必须红", POLICY,
     NEEDLE_982, REPL_982, u"testTheHelpFollowsTheEntryNotJustTheRenderer", PIPE_CELL),
    ("M983", u"产品：提示语的载荷参数退回常量 ⇒ 「两支必须不一样」那一格必须红", POLICY,
     NEEDLE_983, REPL_983, u"testTheHelpFollowsTheEntryNotJustTheRenderer", PIPE_CELL),
]


SNAPSHOT = {}
_MISSING = object()


def sh(cmd):
    p = subprocess.run(cmd, cwd=PKG, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.decode("utf-8", "replace")


def read(path):
    with open(path, encoding="utf-8") as h:
        return h.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as h:
        h.write(text)


def run_cell(filter_name):
    """红不红只准由 **XCTest 的汇总行**说，不许由"日志里有没有 error: 字样"说。

    第一版就是那么判的，于是基线被判成 RED 而 17 格全绿 —— 成因是产品自己会往
    stderr 倒系统噪声（`CoreData: error: …AddressBook…`，本机每次跑都有）。
    这一族有名字：**结果通道本身会坏**（读到的字符串不等于结论）。
    """
    out = sh(["env", "-u", "SDKROOT", "swift", "test", "--filter", filter_name])
    executed = re.findall(r"Executed (\d+) tests, with (\d+) failures", out)
    if not executed:
        return (True, "?", out)                      # 一行汇总都没有 ⇒ 编译没过 / 根本没跑
    n, fails = executed[-1]
    red = int(fails) > 0 or "Test Suite 'Selected tests' failed" in out
    return (red, n, out)


def main(argv):
    picked = [a for a in ARMS if not argv or a[0] in argv]
    if not picked:
        print(u"ARG_ERROR 认不出臂号：" + u" ".join(argv))
        return 2
    # 基线不绿 ⇒ 后面每一朵 CAUGHT 都不说明任何事（先量地板，再落刀）。
    print(u"===== 基线（未落刀）")
    baseline_ok = True
    for cell in sorted(set(a[6] for a in picked)):
        red, n, out = run_cell(cell)
        print(u"BASELINE %s %s Executed=%s" % (cell, u"RED" if red else u"green", n))
        if red:
            baseline_ok = False
            print(out[-1500:])
    if not baseline_ok:
        print(u"PRECHECK_FAILED 基线不绿，这一轮的 CAUGHT 一律不作数")
        return 1

    caught = 0
    last_mtime = 0
    for a in ARMS:
        SNAPSHOT.setdefault(a[2], read(a[2]))
    for arm, desc, path, needle, repl, expect, cell in picked:
        text = read(path)
        hits = text.count(needle)
        if hits != 1:
            print(u"%s NOT_RUN 锚点命中 %d 次（要 1 次）：%s" % (arm, hits, path))
            continue
        write(path, text.replace(needle, repl))
        # 回读磁盘自证：落下去的就是这一刀（改了又被换回去 ⇒ NOT_RUN，不许记 CAUGHT）
        if read(path).count(repl) != 1:
            print(u"%s NOT_RUN 落刀后回读不匹配" % arm)
            write(path, text)
            continue
        # mtime 必须**严格递增**：同长度变异 + 同一秒还原，工具链会继续执行旧字节码。
        stamp = os.path.getmtime(path)
        if stamp <= last_mtime:
            os.utime(path, (time.time() + 2, time.time() + 2))
        last_mtime = os.path.getmtime(path)
        red, n, out = run_cell(cell)
        if n == u"?":
            # 编译不过 ⇒ 这一刀本身坏了（不是判据没牙）。记 NOT_RUN，绝不记 CAUGHT。
            print(u"%s NOT_RUN 变异之后编译不过：%s" % (arm, out.strip().splitlines()[-1][:160]))
            write(path, text)
            continue
        ok = red and (expect in out)
        if ok:
            caught += 1
            print(u"%s CAUGHT %s（Executed=%s）红在：%s" % (arm, desc, n, expect))
        else:
            print(u"%s %s %s —— 期望红在 %s，实得 Executed=%s"
                  % (arm, u"MISMATCH" if red else u"PASSED", desc, expect, n))
            print(out[-1200:])
        write(path, text)
        if read(path) != text:
            print(u"%s RESTORE_DIRTY 还原没回到原文" % arm)
            return 1

    # 还原干不干净 = **与落刀前那份快照逐字相等**。
    # 第一版判的是"needle 还在、repl 不在"，而 M974 的 repl 是 needle 的一部分
    # （删一行 ⇒ 剩下那行仍然含 repl）⇒ 它把一次干净的还原报成 RESTORE_CLEAN=no。
    clean = all(read(a[2]) == SNAPSHOT.get(a[2], _MISSING) for a in ARMS)
    print(u"CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(picked), u"yes" if clean else u"no"))
    if caught == len(picked) and clean:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
