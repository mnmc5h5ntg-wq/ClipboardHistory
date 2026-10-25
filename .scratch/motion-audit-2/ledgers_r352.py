#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R352 七本台账（第 351 轮 / Round 349 · 产品 0 文件，判据账）。"""
import io, os, re, subprocess
ROOT = u"/Users/wangziyi/Codex_Project0"
rd = lambda n: io.open(os.path.join(ROOT, n), encoding="utf-8").read()
wr = lambda n, t: io.open(os.path.join(ROOT, n), u"w", encoding="utf-8").write(t)
def once(t, a, b):
    assert t.count(a) == 1, u"锚点命中 %d：%.60s" % (t.count(a), a)
    return t.replace(a, b, 1)

out = subprocess.run([u"python3", u"scripts/product_streak.py", u"--streak-for", u"351"],
                     cwd=ROOT, stdout=subprocess.PIPE).stdout.decode(u"utf-8")
STREAK = int(re.search(u"streak=(\\d+)", out).group(1))

U = u"""## 第 351 轮（R352 · 2026-10-25 · U-1229…U-1232）：§8 的十二个洞是退役验证器留下的 —— 退役它们，留出处（U-1229…U-1232 · 产品 0 文件，判据账）

- **U-1229：十二格的成因找到了。** `ledger_rows.py` 的 ROWS 要 `BUILD_EXIT` / `TEST_EXIT` / `PROBE_EXIT` /
  `CAPTURE_EXIT` / `FRAMES_EXIT` / `PY_EXIT` / `MUT_EXIT` / `LEDGER_EXIT` / `VIS_EXIT` / `CONTAIN_EXIT` /
  `SUMMARY_MISSING` / `VERIFY_OK` 十二个键；而现在的 `scripts/round_verify.sh` 只打**一行**
  `ROUND_VERIFY build_warnings=… swift_executed=… swift_failures=… frames=… baseline_changed=… dmg=… installed_version=… dir=…`。
  那套多步验证器已经不在了 ⇒ 十二格长期是"!! 日志里没有这一格"。**洞是真的，但成因不是手抄偷懒。**
- **U-1230：处置是退役（不是放宽）。** ROWS 换成一行 `("验证流水线", r"^ROUND_VERIFY .*")`，并在表上方写明
  这十二格为什么退役、出处是 BACKLOG 397。§8 从此每一格都有真读数 —— 格少了，但没有一格是洞。
- **U-1231：新守卫（`test_ledger_rows_keys`）两次读错对象，都是它自己红出来的。** ① 先要求"`echo ROUND_VERIFY`
  恰好一处"，可早退那一行（`ABORTED_AT_WARNING_GATE`）也算一处 ⇒ 读到 2；改成取**最后**一处。
  ② 又把 `key=$VAR` 用负向前瞻排除掉了 —— 验证器打的全是 `key=$变量` 形状 ⇒ 读到 **0** 个键，红线是"太少了"。
  两处都是"尺没对上对象"（D-341 一族），不是判据没牙。
- **U-1232：电池与全量。** 脚本电池 `Ran 648（skipped=4）OK`（比上一轮多 2 格：本守卫两格）；
  这一轮没有产品代码改动（`swift` 侧未跑 —— 上一轮的 1025 格仍是本树最近一次全量证据）。

"""

ITER = u"""## Round 349 · R352（第 351 轮 · 2026-10-25）：§8 的十二个洞退役，留出处（产品 0 文件）

ROWS 要的十二个键属于一套已经不在的多步验证器；`round_verify.sh` 现在只打一行。退役那十二格、只搬这一行，
并加一条守卫：表里的键必须在验证器的总结论行里。守卫自己两次读错对象（早退行、`$VAR` 形状），都当场红出来。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 9/15 | 本轮无像素改动；理由写在这里而不是留空。 |
| 判据有效性 | 13/15 | 守卫查两件事（键在验证器那一行里、退役带 BACKLOG 编号），两条都能红。 |
| 假绿防御 | 14/15 | 十二格是"退役"不是"填数"；没有为了让 §8 好看去手抄。 |
| 产品面推进 | 6/15 | 产品 0 文件。 |
| 台账一致性 | 13/15 | U-1229…U-1232 四条、D-349、397 结案追记；计数器现读抄。 |
| 交付诚实性 | 15/15 | 守卫两次误判都写进 U-1231；"swift 侧本轮未跑"也写明。 |
| 可复核性 | 13/15 | 一条 `unittest scripts.tests.test_ledger_rows_keys` 即可复核。 |

均分 ≈ 11.9/15（83/105）。
"""

BL = u"""
397 结案（R352）：十二格的成因是**验证器换了形状** —— `round_verify.sh` 现在只打一行
    `ROUND_VERIFY build_warnings=… swift_failures=… frames=… baseline_changed=… dmg=… installed_version=… dir=…`，
    而 ROWS 还在要旧多步验证器的十二个键。处置：退役那十二格（表上方写明出处），§8 只搬这一行；
    新增 `scripts/tests/test_ledger_rows_keys.py` 对账"表里的键必须在验证器总结论行里"，并要求退役注明 BACKLOG 编号。
    **留给后来**：§8 从 12 洞变成 1 格，不是判据变松 —— 那一格的键与验证器现在由门钉在一起。
"""

DEC = u"""
### D-349（352）§8 里的洞先问"那份日志还在不在"：不在就退役并留出处，不许挂着手抄的数

R352 现读：`ledger_rows.py` 的十二格要的是旧多步验证器的键，而 `round_verify.sh` 早已只打一行 —— 洞是真的，
成因是**形状换了**。处置是退役那十二格（注明 BACKLOG 397）+ 只搬现在那一行 + 一条对账守卫；
不是手抄十二个数把表格填满（那是 R99 那一族的假绿）。
**How to apply**：看到"这一格长期没有值"，先查**产出它的那份日志还在不在**；不在就退役并写出处，
在就修搬运口。两条之外没有第三条路（手抄与留白都不是）。
"""

CH = u"""### §8 的十二个洞退役：验证器早换成一行 `ROUND_VERIFY`，搬运表还在要旧键（R352 / U-1229…U-1232 · 产品 0 文件，判据账）
"""

STATE = u"""## R352 状态（2026-10-25 · 本地 · 第 351 轮 / Round 349）：§8 的十二个洞退役（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R352 / 第 351 轮 / Round 349）：ROWS 要的十二个键属于一套已不在的多步验证器，
退役那十二格、§8 只搬 `ROUND_VERIFY` 一行，并加一条"键必须在验证器总结论行里"的对账守卫（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：三跑按首读登记（只登记不轮询，R140）。
② 读两边：ROWS 十二键 vs `round_verify.sh` 只打一行（含 `build_warnings=` / `swift_failures=` / `frames=` …）。
③ 退役十二格（表上方写明成因与出处 BACKLOG 397），§8 改搬 `^ROUND_VERIFY .*`。
④ 新增 `scripts/tests/test_ledger_rows_keys.py` 两格（键的对账 + 退役必须带 BACKLOG 编号）。
⑤ 守卫自己两次红在"读错对象"上（早退行、`key=$VAR`），都改掉并写进 U-1231。

验证读数（现读）：`ROWS` 现读一行（"验证流水线"）；守卫 `Ran 2 tests OK`；脚本电池 `Ran 648（skipped=4）OK`；
产品面连续零改动 **{streak}** 轮（`python3 scripts/product_streak.py --streak-for 351` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 本轮没跑 `swift test`（产品 0 文件，上一次全量 1025 格仍是本树最近证据）；
② 无刀（没有产品改动可打，判据改动由守卫自身两格覆盖）；③ 真机腿没跑。

下一轮（R353）的靶：⓪ 读三跑 CI 配对 → ① 动效主线 390（内容与胶囊的落点差，胶片已有 after 读数）→
② 384 / 387① / 376 / 367 → ③ 426 的退场（刀的 diff 判法）。

"""

def main():
    s = rd(u"AGENT_UI_AUDIT.md"); a = u"## 第 350 轮（R351 · 2026-10-25 · U-1224…U-1228）"
    i = s.find(a); assert i > 0; wr(u"AGENT_UI_AUDIT.md", s[:i] + U + s[i:])
    s = rd(u"AGENT_VISUAL_ITERATION.md"); wr(u"AGENT_VISUAL_ITERATION.md", s.rstrip(u"\n") + u"\n\n" + ITER)
    s = rd(u"AGENT_BACKLOG.md"); wr(u"AGENT_BACKLOG.md", s.rstrip(u"\n") + u"\n" + BL)
    s = rd(u"AGENT_DECISIONS.md"); wr(u"AGENT_DECISIONS.md", s.rstrip(u"\n") + u"\n" + DEC)
    s = rd(u"CHANGELOG.md"); s = once(s, u"## [Unreleased]\n", u"## [Unreleased]\n\n" + CH); wr(u"CHANGELOG.md", s)
    s = rd(u"AGENT_STATE.md"); h = u"## R351 状态（2026-10-25 · 本地 · 第 350 轮 / Round 348）"
    assert s.count(h) == 1
    wr(u"AGENT_STATE.md", s.replace(h, STATE.replace(u"{streak}", u"%d" % STREAK) + h, 1))
    r = rd(u"AGENT_FINAL_REPORT.md")
    r = once(r, u"U-31 … U-1228（R351 现读抬到最新一节）", u"U-31 … U-1232（R352 现读抬到最新一节）")
    r = once(r, u"| 决定台账 | D-069 … **D-348**", u"| 决定台账 | D-069 … **D-349**")
    r = once(r, u"U 定义行最大 **U-1228**、决定最大 **D-348**、BACKLOG 最大 **426**",
             u"U 定义行最大 **U-1232**、决定最大 **D-349**、BACKLOG 最大 **426**")
    r = once(r, u"完整名单以 `AGENT_STATE.md` 的 R351 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R352 节 ② 为准")
    r = re.sub(u"产品面连续零改动轮数 = \\*\\*\\d+\\*\\*（现读", u"产品面连续零改动轮数 = **%d**（现读" % STREAK, r, count=1)
    r = r.rstrip(u"\n") + u"""
- **R352 续（判据账）**：§8 的十二个洞退役 —— `round_verify.sh` 早已只打一行 `ROUND_VERIFY`；
  ROWS 改搬那一行，并加一条"键必须在验证器总结论行里"的对账守卫（`Ran 648`）。
""" + u"\n"
    wr(u"AGENT_FINAL_REPORT.md", r)
    print(u"R352_LEDGERS_OK streak=%d" % STREAK)

if __name__ == u"__main__":
    main()
