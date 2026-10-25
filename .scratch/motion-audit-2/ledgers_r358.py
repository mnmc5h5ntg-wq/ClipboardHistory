#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R358 七本台账（第 357 轮 / Round 355 · 产品 0 文件，判据账）。"""
import io, os, re, subprocess
ROOT = u"/Users/wangziyi/Codex_Project0"
rd = lambda n: io.open(os.path.join(ROOT, n), encoding="utf-8").read()
wr = lambda n, t: io.open(os.path.join(ROOT, n), u"w", encoding="utf-8").write(t)
LOG = lambda n: io.open(os.path.join(u"/tmp", n), encoding="utf-8", errors="replace").read()

def once(t, a, b):
    assert t.count(a) == 1, u"锚点命中 %d：%.60s" % (t.count(a), a)
    return t.replace(a, b, 1)

def last(pat, text, what):
    found = list(re.finditer(pat, text))
    assert found, u"没解析到 %s" % what
    return found[-1].groups()

STREAK = int(re.search(u"streak=(\\d+)", subprocess.run(
    [u"python3", u"scripts/product_streak.py", u"--streak-for", u"357"],
    cwd=ROOT, stdout=subprocess.PIPE).stdout.decode(u"utf-8")).group(1))
full = LOG(u"r358_full.log")
FULL_N, FULL_SKIP, FULL_FAIL = last(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full, u"全量卷")
ab = LOG(u"r358_ab.log")
AB = last(r"MOTION_SCENARIO_AB_SUMMARY 场景=(\d+) 同=(\d+) 漂=(\d+) 敏感=(\d+) 换对象=(\d+) 粒度不可比=(\d+)", ab, u"A/B 汇总")
MAG = last(r"有变化=(\d+) 亮臂更大=(\d+) 暗臂更大=(\d+) 比值暗除亮=([0-9.]+)…([0-9.]+)", ab, u"墨量方向")
pre = LOG(u"r358_precheck.log")
P_TABLES, P_COVERED, P_ARMS, P_BAD = last(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre, u"针预检")
A_FILES, A_ARMS = last(r"ARM_TOTAL files=(\d+) arms=(\d+)", pre, u"臂名册")
battery = LOG(u"r358_py.log")
BAT_N = last(r"Ran (\d+) tests", battery, u"电池")[0]
assert re.search(r"^OK \(skipped=4\)$", battery, re.M), u"电池不是 OK"
build = LOG(u"r358_build.log")
assert u"Build complete" in build and u"warning:" not in build, u"构建不是 0 告警"

U = u"""## 第 357 轮（R358 · 2026-10-25 · U-1255…U-1257）：387① 落地 —— 墨量只印不判，色档 A/B 从「敏感=8」收到「同=11 / 漂=1」（U-1255…U-1257 · 产品 0 文件，判据账）

- **U-1255：判词只由两颗面积尺做，墨量差仍逐颗印。** `appearanceDependenceVerdict` 的 `rel` 从
  `max(首末面积, 动过并集, 首末墨量)` 收回 `max(首末面积, 动过并集)`；墨量两个参数保留（调用点与打印同源），
  但函数里 `_ = (inkDark, inkLight)` 明写「判词不许读它们」。同一次本机 A/B 现读：
  **`场景=@S@ 同=@N@ 漂=@D@ 敏感=@T@ 换对象=@F@ 粒度不可比=@G@`**（改前是 `同=1 漂=3 敏感=8`）；
  墨量那颗自己的分布没动：`有变化=@M0@ 亮臂更大=@M1@ 暗臂更大=@M2@ 比值暗除亮=@M3@…@M4@` ——
  11 颗全在同一侧，那个色档级系统偏移还在，只是它现在**只是读数**。
  ⇒ R326 那 8 颗"敏感"几乎全部由偏移抬起来；两颗面积尺说这些场景的**变化形状**在两档里是同一件事。
- **U-1256：测试随之改写，两把刀各自咬住。** 纯函数格 ⑥ 从"墨量必须抬成敏感"改成"墨量差 40% 仍判同"；
  新加 ⑥b 用本机现场数（`detailSameKind` 首末 4.7% / 并集 4.4% / 墨量 89.1% ⇒ 同）；
  `testEndpointAreaIsBlindToInkMagnitudeButTheVerdictIsNot` 改名成 `…AndTheVerdictNoLongerUsesIt`，
  ③ 的期望从"敏感"翻成"同"（② 仍断言墨量读出 40% 的深浅，盲区与读数都留着）。
  `mutate_r326.M944` 的旧针是三项 max（已不在盘上）⇒ 按 R262 重钉成"只丢并集"（它原本要证的
  "取较大者这一半有牙"不变），`M944 CAUGHT=1/1`；新刀 `M1007` 把墨量塞回 max ⇒ 词表格红，`CAUGHT=1/1`。
  预检现读 `tables=@PT@ covered=@PC@ arms=@PA@ bad=@PB@`、`files=@AF@ arms=@AA@`。
- **U-1257：唯一那颗「漂」是 emptyState，而且它现在有逐颗读数。** 首末 0.2261 对 0.2304（1.9%），
  并集 0.2139 对 0.2304（**7.2%**），墨量 0.0881 对 0.1776（只印）；7.2% 落在 5–25% ⇒ 漂、登记不钉。
  这是第一颗被两颗面积尺判成"漂"的场景：它的**变化面积**随色档差 7%，而 8 颗原来那批是 1–5%。
  仍欠：runner 的同格读数（下一跑 CI 的 `MOTION_SCENARIO_AB_SUMMARY`），两机同数之前不给它钉色档、也不改 5%/25% 的线。

"""

ITER = u"""## Round 355 · R358（第 357 轮 · 2026-10-25）：387① 落地 —— 墨量只印不判，色档 A/B 收到 同=11/漂=1（产品 0 文件）

`appearanceDependenceVerdict` 的判词收回两颗面积尺；墨量仍逐颗印、全局方向行不变。
本机同一次 A/B：`同=11 漂=1 敏感=0`（改前 同=1 漂=3 敏感=8）；唯一漂=emptyState（并集 7.2%）。
M944 重钉、M1007 新刀，双 `CAUGHT=1/1`；全量 1030/48skip/0，电池 `Ran @BAT@`。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 10/15 | 本轮对象是两档色档的逐颗读数，不是屏幕帧；没有真机眼（产品 0 文件）。 |
| 判据有效性 | 14/15 | 两把刀各钉一侧（丢并集 / 塞回墨量），词表与分界仍由同一颗纯函数出。 |
| 假绿防御 | 14/15 | 墨量仍有逐颗读数与全局方向行；"同=11"不是把尺关掉，而是把带偏移的轴从判词里拿掉。 |
| 产品面推进 | 8/15 | 产品 0 文件；推进在"色档依赖的分类不再由偏移决定"。 |
| 台账一致性 | 13/15 | U-1255…U-1257、D-357、387① 结案；计数器现读。 |
| 交付诚实性 | 15/15 | runner 同格读数仍欠；唯一"漂"没有被洗成"同"，也没有被钉。 |
| 可复核性 | 15/15 | 一条测试命令 + 两把刀；改前/改后计数都在账上。 |

均分 = 89/105 ≈ 12.7/15（85）。

"""

BL = u"""
387① 结案（R358）：按 R328 的①把墨量那颗从判词里拿出去 —— `rel = max(首末面积, 动过并集)`；
    墨量仍逐颗印（`MOTION_SCENARIO_AB` 的 墨暗/墨亮）与全局方向行（`MOTION_SCENARIO_AB_MAGNITUDE`）都没动。
    本机同一次 A/B 改前/改后：`同=1 漂=3 敏感=8` → **`同=11 漂=1 敏感=0`**；墨量 11/11 亮臂更大（比值 0.11…0.94）照旧。
    ⇒ 那 8 颗"敏感"是偏移抬起来的，不是"这条判据换档会说不同的话"；两颗面积尺判它们为"同"。
    唯一漂 = emptyState（首末 1.9%、并集 7.2%），登记不钉。
    **仍欠**：① runner 上同一 A/B 的读数（下一跑 CI，`MOTION_SCENARIO_AB_SUMMARY`）；
    ② 386 的"5%/25% 两条线该在哪"仍未标定（现在输入不再带偏移，但它仍是拍上去的线）；
    ③ emptyState 的 7.2% 是面积的色档差还是阈值附近的计数差，没拆（要逐帧像素对照）。

"""

DEC = u"""
### D-357（358）读数可以带偏移，判词不许吃偏移

R326 让三颗通道无关的量一起取 max，其中墨量差带着一个**色档级系统偏移**：本机 11/11、runner 11/11
都是亮臂更大，偏移大小随机器走（比值 0.11…0.94 对 0.72…0.99），runner 两跑自己还会翻一格。
于是 8 颗场景被抬成"敏感"，而它们的两颗面积尺读的是"同" —— 分类几乎完全由"这颗尺带多少偏移"决定。
R358 把墨量从判词里拿出去（仍逐颗印、仍有全局方向行），A/B 从 `敏感=8` 收到 `同=11 漂=1`。
**Why**：一颗带系统性偏移的读数能做"这台机器差多少"的证据，不能做"这条判据换档会不会说不同的话"的判词；
把两者混在一起，判词就会被偏移量而不是被产品行为决定。
**How to apply**：跨条件分类的输入只许用**与条件无关的形状量**（这里：动过的像素集合/面积）；
带偏移的量要保留成读数（逐颗印 + 全局方向），并写清它为什么不能当判词。要让它重新有判词资格，
先给出偏移的**可减形式**（R327/R328 已证：常数偏移在两跑之间不成立）。

"""

CH = u"""### 色档 A/B 的判词收回两颗面积尺：墨量只印不判，敏感=8 → 同=11 / 漂=1（387① 结案）（R358 / U-1255…U-1257 · 产品 0 文件，判据账）
"""

STATE = u"""## R358 状态（2026-10-25 · 本地 · 第 357 轮 / Round 355）：387① 落地 —— 墨量只印不判，色档 A/B 收到 同=11/漂=1（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R358 / 第 357 轮 / Round 355）：`appearanceDependenceVerdict` 的判词收回两颗面积尺，
墨量仍逐颗印；本机同一次 A/B `同=11 漂=1 敏感=0`（改前 同=1 漂=3 敏感=8），唯一漂=emptyState 并集 7.2%；
M944 重钉 + M1007 新刀双 CAUGHT；全量 1030/48skip/0、电池 655（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：R356 两跑与 R357 一跑仍 `in_progress`（`queue` 现读；只登记不轮询）。
② 387①：判词 `rel` 从三项 max 收回 `max(首末面积, 动过并集)`；墨量保留为读数（有 `_ = (inkDark, inkLight)` 的明证）。
③ 重跑本机 A/B：`同=11 漂=1 敏感=0`；墨量方向 11/11 亮臂更大（0.11…0.94）⇒ 偏移在读数里、不在判词里。
④ 测试改写：纯函数 ⑥ 翻成"墨量不抬判定"、新 ⑥b 用现场数；盲区测试改名并把 ③ 的期望翻成"同"。
⑤ M944 旧针腐烂 ⇒ 重钉成"只丢并集"（语义不变，CAUGHT）；新刀 M1007 把墨量塞回 max ⇒ 词表格红。

验证读数（现读）：全量卷 `Executed @FN@ tests, with @FS@ tests skipped and @FF@ failures`；构建 0 告警；
A/B `场景=@S@ 同=@N@ 漂=@D@ 敏感=@T@ 换对象=@F@ 粒度不可比=@G@`；墨量 `有变化=@M0@ 亮臂更大=@M1@ 暗臂更大=@M2@ 比值=@M3@…@M4@`；
预检 `tables=@PT@ covered=@PC@ arms=@PA@ bad=@PB@`、`files=@AF@ arms=@AA@`；脚本电池 `Ran @BAT@（skipped=4）OK`；
基线/胶片本轮未重跑（产品与尺的渲染路径都没动，沿用 R356 的 1030/68/182）；产品面连续零改动 **@STREAK@** 轮。

NOT-RUN（分开写）：① runner 上的 A/B 同格读数（下一跑 CI）；② 386 的 5%/25% 两条线仍未标定；
③ emptyState 的 7.2% 是"面积随色档"还是"阈值附近计数"，没拆；④ 真机腿没跑。

下一轮（R359）的靶：⓪ 用 `queue`/`steps` 读 `df35274` / `6a0258a` / `78f7551`（若结案：R355 的 empty-state 是否 judged、
R356 的 `MOTION_PILL_RAMP_GEOM` 行带/覆盖）→ ① 376 的第二通道或 367（表自己声明针）→ ② 426（刀的 diff 判法）→
③ 若有 runner 同格：386 的两条线标定。

"""
UP_UI = u"""## 第 356 轮（R357 · 2026-10-25 · U-1252…U-1254）：读 CI 的第三态有名字了 —— `queue` 子命令（U-1252…U-1254 · 产品 0 文件，判据账）"""
UP = u"""## R357 状态（2026-10-25 · 本地 · 第 356 轮 / Round 354）：读 CI 的第三态有名字了 —— queue 子命令（产品 0 文件，判据账）"""

def fill(text):
    pairs = {u"@S@": AB[0], u"@N@": AB[1], u"@D@": AB[2], u"@T@": AB[3], u"@F@": AB[4], u"@G@": AB[5],
             u"@M0@": MAG[0], u"@M1@": MAG[1], u"@M2@": MAG[2], u"@M3@": MAG[3], u"@M4@": MAG[4],
             u"@PT@": P_TABLES, u"@PC@": P_COVERED, u"@PA@": P_ARMS, u"@PB@": P_BAD,
             u"@AF@": A_FILES, u"@AA@": A_ARMS,
             u"@FN@": FULL_N, u"@FS@": FULL_SKIP, u"@FF@": FULL_FAIL,
             u"@BAT@": BAT_N, u"@STREAK@": str(STREAK)}
    for k, v in pairs.items():
        text = text.replace(k, v)
    leftover = re.findall(u"@[A-Z0-9]{2,}@", text)
    assert not leftover, u"还有占位符：%s" % u",".join(sorted(set(leftover)))
    return text

def main():
    ui = rd(u"AGENT_UI_AUDIT.md")
    ui = once(ui, UP_UI, fill(U) + UP_UI)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    if not it.endswith(u"\n"):
        it += u"\n"
    wr(u"AGENT_VISUAL_ITERATION.md", it + fill(ITER))

    bl = rd(u"AGENT_BACKLOG.md")
    if not bl.endswith(u"\n"):
        bl += u"\n"
    wr(u"AGENT_BACKLOG.md", bl + fill(BL))

    de = rd(u"AGENT_DECISIONS.md")
    if not de.endswith(u"\n"):
        de += u"\n"
    wr(u"AGENT_DECISIONS.md", de + fill(DEC))

    ch = rd(u"CHANGELOG.md")
    ch = once(ch, u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + fill(CH) + u"\n")
    wr(u"CHANGELOG.md", ch)

    st = rd(u"AGENT_STATE.md")
    before = st.count(u"\n## R")
    st = once(st, UP, fill(STATE) + UP)
    wr(u"AGENT_STATE.md", st)
    st2 = rd(u"AGENT_STATE.md")
    assert UP in st2 and st2.count(u"\n## R") == before + 1, u"STATE 轮换后上一轮标记丢了或层数不对"

    fr = rd(u"AGENT_FINAL_REPORT.md")
    fr = once(fr, u"| 决定台账 | D-069 … **D-356**", u"| 决定台账 | D-069 … **D-357**")
    fr = once(fr, u"| 视觉台账 | U-31 … U-1254（R357 现读抬到最新一节）",
              u"| 视觉台账 | U-31 … U-1257（R358 现读抬到最新一节）")
    fr = once(fr, u"U 定义行最大 **U-1254**、决定最大 **D-356**",
              u"U 定义行最大 **U-1257**、决定最大 **D-357**")
    fr = once(fr, u"预检 tables=131 covered=114 arms=374 bad=0",
              u"预检 tables=132 covered=115 arms=375 bad=0")
    fr = once(fr, u"产品面连续零改动轮数 = **2**", u"产品面连续零改动轮数 = **3**")
    fr = once(fr, u"`AGENT_STATE.md` 的 R357 节 ② 为准", u"`AGENT_STATE.md` 的 R358 节 ② 为准")
    tail = u"（R357 现读：注册表 **131** 张 / 刀号最大 **M1006** / 预检 covered=114 arms=374 bad=0；全仓 225 文件 / 865 把） |"
    fr = once(fr, tail,
              u"（R358 现读：注册表 **132** 张 / 刀号最大 **M1007** / 预检 covered=115 arms=375 bad=0；全仓 226 文件 / 865 把） |")
    bullet = u"""- **R358 续（判据账）**：387① 结案 —— 色档 A/B 的判词收回两颗面积尺，墨量只印不判；
  本机同一次 A/B `同=1 漂=3 敏感=8` → **`同=11 漂=1 敏感=0`**（唯一漂=emptyState 并集 7.2%）；
  墨量方向 11/11 亮臂更大照旧。M944 重钉 + M1007 双 `CAUGHT=1/1`；全量 1030/48skip/0、电池 @BAT@。
"""
    if not fr.endswith(u"\n"):
        fr += u"\n"
    fr += fill(bullet)
    wr(u"AGENT_FINAL_REPORT.md", fr)
    print(u"R358_LEDGERS_OK U=1257 D=357 battery=@BAT@".replace(u"@BAT@", BAT_N))

if __name__ == u"__main__":
    main()
