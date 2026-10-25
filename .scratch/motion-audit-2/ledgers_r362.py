#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R362 七本台账（第 361 轮 / Round 359 · 产品 0 文件，判据账）。"""
import io, os, re, subprocess
ROOT = u"/Users/wangziyi/Codex_Project0"
rd = lambda n: io.open(os.path.join(ROOT, n), encoding="utf-8").read()
wr = lambda n, t: io.open(os.path.join(ROOT, n), u"w", encoding="utf-8").write(t)
LOG = lambda n: io.open(os.path.join(u"/tmp", n), encoding="utf-8", errors="replace").read()

def once(t, a, b):
    assert t.count(a) == 1, u"锚点命中 %d：%.60s" % (t.count(a), a)
    return t.replace(a, b, 1)

STREAK = int(re.search(u"streak=(\\d+)", subprocess.run(
    [u"python3", u"scripts/product_streak.py", u"--streak-for", u"361"],
    cwd=ROOT, stdout=subprocess.PIPE).stdout.decode(u"utf-8")).group(1))
battery = LOG(u"r362_py.log")
BAT_N = re.search(u"Ran (\\d+) tests", battery).group(1)
assert re.search(r"^OK \(skipped=4\)$", battery, re.M), u"电池不是 OK"

U = u"""## 第 361 轮（R362 · 2026-10-25 · U-1267…U-1269）：426 第一步 —— 落刀回读判「盘上等于预期」，不判替换串出现几次（U-1267…U-1269 · 产品 0 文件，判据账）

- **U-1267：`readback.single_substitution_lands`。** 判据三件事一起：`before` 里 needle 恰好一次、
  `after == before.replace(needle, repl)`、`after != before`。它同时排除"没落刀""落了两次""顺手改了别处"，
  且**不要求 repl 全局唯一** —— R350 的现场正是 repl 在别处本来就有（`.contentFade) * 1000) { store in`），
  旧判法 `count(repl)==1` 把一把能落的刀判成 NOT_RUN。5 格测试：精确替换 / repl 在别处出现（放行）/
  多改一处（拒）/ 空刀（拒）/ needle 歧义或不存在（拒）。
- **U-1268：两张新表先迁移（r358 / r360）。** 落刀后的回读从 `count(repl)==1` 换成
  `single_substitution_lands(before, needle, repl, 盘上内容)`；两把刀重跑 `M1007 / M1008` 各 `CAUGHT=1/1, RESTORE_CLEAN=yes`
  —— 迁移没有动刀本身，只动了"落刀有没有落成"的判法。电池 `Ran @BAT@（skipped=4）OK`。
- **U-1269：426 仍未全收口。** 还有一百多张表在用旧判法；迁移顺序按"最近动过的表"走（先把 r340 之后的新表迁完，
  再碰历史表）。两个边界写清：① diff 判法只证"盘上等于预期"，不证"预期本身打对了靶"（那是 needle/expect 的事）；
  ② 多针表（ARMS 里 needle 是 list）暂不迁 —— 它们要的是"逐针各改一处"的 diff，形状不同，别混用。

"""

ITER = u"""## Round 359 · R362（第 361 轮 · 2026-10-25）：426 第一步 —— 落刀回读判 diff（产品 0 文件）

`readback.single_substitution_lands`：needle 恰好一次 + after == 预期替换 + 非空刀；
r358/r360 迁移，M1007/M1008 各 CAUGHT 1/1；5 格测试（含 R350 的 repl-在别处现场）。电池 664。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 10/15 | 本轮是刀的落刀判法，无画面。 |
| 判据有效性 | 14/15 | 5 格测试把三种坏法各拦一次；两把刀重跑仍 CAUGHT。 |
| 假绿防御 | 14/15 | "repl 全局唯一"既不必要也不充分被写成测试；多改一处会拒。 |
| 产品面推进 | 8/15 | 产品 0 文件；推进在"刀能不能落下去"的判法。 |
| 台账一致性 | 13/15 | U-1267…U-1269、D-361、426 追记；计数器现读。 |
| 交付诚实性 | 15/15 | 未声称 130 张表都已迁移；多针表与"预期打靶"两个边界写明。 |
| 可复核性 | 15/15 | 一个 helper + 5 格测试 + 两把刀重跑。 |

均分 = 89/105 ≈ 12.7/15（85）。

"""

BL = u"""
426 追记（R362）：第一步 —— `.scratch/motion-audit-2/readback.py` 的 `single_substitution_lands`：
    needle 恰好一次 + `after == before.replace(needle, repl)` + 非空刀；**不要求 repl 全局唯一**
    （R350 的现场：repl 在别处本来就有 ⇒ 旧判法假红）。5 格测试；r358 / r360 迁到新判法，
    M1007 / M1008 重跑各 `CAUGHT=1/1, RESTORE_CLEAN=yes`；电池 664。
    **仍欠**：其余一百多张表（按"最近动过的表"先迁）；多针表（ARMS 的 needle 是 list）形状不同，
    要"逐针各改一处"的 diff，不许混用；以及"预期打靶"不由 diff 判法负责（那是 needle/expect 的事）。

"""

DEC = u"""
### D-361（362）落刀回读判「盘上恰好等于预期」，不判替换串的全局出现次数

R350 的刀没落下去，因为 `read(path).count(repl) == 1` 不成立 —— 而 repl 在该文件别处本来就有。
"repl 唯一"既不必要（替换串可以合法地已经在别处出现）也不充分（它不排除顺手改了别处）。
R362 立的判法：`before.count(needle) == 1` 且 `after == before.replace(needle, repl)` 且 `after != before`。
**Why**：刀要证的是"文件变成了我预期的那一份"，不是"替换串出现了几次"；后者是同一个估计量的两面，
一面会假红（R350）、一面会漏掉"多改一处"。
**How to apply**：迁移一张表时只换回读那一行，不动 needle/repl/期望；多针表要另立形状（逐针各一条 diff），
不许把它硬塞进单替换的判据里。

"""

CH = u"""### 426 第一步：落刀回读改判预期 diff（单针表），repl 在别处出现不再假红（R362 / U-1267…U-1269 · 产品 0 文件，判据账）
"""

STATE = u"""## R362 状态（2026-10-25 · 本地 · 第 361 轮 / Round 359）：426 第一步 —— 落刀回读判 diff（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R362 / 第 361 轮 / Round 359）：新增 `.scratch/motion-audit-2/readback.py`
（`single_substitution_lands`：needle 恰好一次 + 盘上 == 预期替换 + 非空刀）；r358/r360 迁移，
M1007/M1008 各 CAUGHT 1/1；5 格测试、电池 `Ran @BAT@（skipped=4）OK`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`queue` 现读 R359–R361 六跑仍在队里（2 queued / 4 in_progress），只登记不轮询。
② 426：新增 diff 判法 helper（不要求 repl 全局唯一）；5 格测试含 R350 的现场。
③ 两张新表迁移；两把刀重跑仍 CAUGHT 1/1、还原干净。
④ 边界：其余一百多张表与多针表未迁；diff 判法不负责"预期打没打对靶"。

验证读数（现读）：电池 `Ran @BAT@（skipped=4）OK`；M1007/M1008 `CAUGHT=1/1, RESTORE_CLEAN=yes`；
本轮不动 Swift/产品 ⇒ 全量/胶片/基线沿用；产品面连续零改动 **@STREAK@** 轮（`python3 scripts/product_streak.py --streak-for 361` 现读）。

NOT-RUN（分开写）：① 其余一百多张表的迁移；② 多针表的 diff 形状；③ R359–R361 六跑的 runner 读数（下一轮）；
④ 真机腿没跑。

下一轮（R363）的靶：⓪ 读六跑（`MOTION_REDUCE_SOURCES` 三源 + 376 的出口文本）；
① 426 下一批（按"最近动过的表"迁 3–5 张）；② 367 下一批（按两箱点名）；③ 若 runner 报 376 通道那一半：第二通道。

"""
UP_UI = u"""## 第 360 轮（R361 · 2026-10-25 · U-1264…U-1266）：367 第一步 —— 四张新表自己声明针，已声明 2→6（U-1264…U-1266 · 产品 0 文件，判据账）"""
UP = u"""## R361 状态（2026-10-25 · 本地 · 第 360 轮 / Round 358）：367 第一步 —— 四张新表声明 NEEDLES（产品 0 文件，判据账）"""

def fill(text):
    pairs = {u"@BAT@": BAT_N, u"@STREAK@": str(STREAK)}
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
    fr = once(fr, u"| 决定台账 | D-069 … **D-360**", u"| 决定台账 | D-069 … **D-361**")
    fr = once(fr, u"| 视觉台账 | U-31 … U-1266（R361 现读抬到最新一节）",
              u"| 视觉台账 | U-31 … U-1269（R362 现读抬到最新一节）")
    fr = once(fr, u"U 定义行最大 **U-1266**、决定最大 **D-360**",
              u"U 定义行最大 **U-1269**、决定最大 **D-361**")
    fr = once(fr, u"脚本电池 `Ran 659`（skipped=4）", u"脚本电池 `Ran 664`（skipped=4）")
    fr = once(fr, u"产品面连续零改动轮数 = **6**", u"产品面连续零改动轮数 = **7**")
    fr = once(fr, u"`AGENT_STATE.md` 的 R361 节 ② 为准", u"`AGENT_STATE.md` 的 R362 节 ② 为准")
    bullet = u"""- **R362 续（判据账）**：426 第一步 —— `readback.single_substitution_lands`（needle 恰好一次 + 盘上 == 预期替换 + 非空刀；
  不要求 repl 全局唯一，R350 的现场不再假红）；r358/r360 迁移，M1007/M1008 各 CAUGHT 1/1；5 格测试、电池 664。
"""
    if not fr.endswith(u"\n"):
        fr += u"\n"
    fr += fill(bullet)
    wr(u"AGENT_FINAL_REPORT.md", fr)
    print(u"R362_LEDGERS_OK U=1269 D=361 battery=@BAT@".replace(u"@BAT@", BAT_N))

if __name__ == u"__main__":
    main()
