#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R354 七本台账（第 353 轮 / Round 351 · 产品 0 文件，判据账）。"""
import io, os, re, subprocess
ROOT = u"/Users/wangziyi/Codex_Project0"
rd = lambda n: io.open(os.path.join(ROOT, n), encoding="utf-8").read()
wr = lambda n, t: io.open(os.path.join(ROOT, n), u"w", encoding="utf-8").write(t)
def once(t, a, b):
    assert t.count(a) == 1, u"锚点命中 %d：%.60s" % (t.count(a), a)
    return t.replace(a, b, 1)
out = subprocess.run([u"python3", u"scripts/product_streak.py", u"--streak-for", u"353"],
                     cwd=ROOT, stdout=subprocess.PIPE).stdout.decode(u"utf-8")
STREAK = int(re.search(u"streak=(\\d+)", out).group(1))

U = u"""## 第 353 轮（R354 · 2026-10-25 · U-1237…U-1241）：尺进了仓库，390 的落点差第一次可复核 —— 1–2 帧（U-1237…U-1241 · 产品 0 文件，判据账）

- **U-1237：`scripts/filmstrip_frames.py` 进了仓库（427 的兑现）。** 拼贴网格**不写死**：按场景宽高比在
  `6×5 / 5×6 / 10×3 / …` 里挑最接近的一档，并把选中那一档打出来（`GRID … → 6×5 帧 300x520`）。
  两条序列：`INK`（内容带里比页底暗 20 级以上的像素数）与 `PILL`（控制带里最宽亮点段的中位 x，pt）。
- **U-1238：两条正对照都过。** `CONTROL_STEADY filter-pill-slide-关 … pill_landed=2 ok`（不演的那一臂第 2 帧就落定）；
  `CONTROL_DIFFER pill_first8_differs=True ok`（开A 与开B 前 8 帧的 PILL 不同）。`FILMSTRIP_FRAMES_RESULT=ok`。
- **U-1239：390 的 after 有了，而且差收窄到 1–2 帧。** 开A 的胶囊 `81,81,89,119,145,175,150,150…` ⇒ 落点 **6**；
  开B `81,81,89,119,145,172,189,150…` ⇒ 落点 **7**；两臂的 `INK` 都是 `688,688,688,683,19,0,0…`，内容到第 **5** 帧归零。
  也就是说：**内容与胶囊现在相差 1–2 帧**（≈20–40ms，帧中位 19.2–19.5ms），而 R328 的 before 是 6–7 对 12（差约 5 帧）。
  R348 把两半接成同一个动画之后，这个差收窄到一格以内是**预期**的；现在它有数。
- **U-1240：关臂的形状也读出来了。** `PILL 81,81,150…`（两格跳完，没有过程）、`INK 688,688,0…` —— 不演就是两帧。
  这一条是正对照的"另一半"：尺要能分辨"有过程"与"没有过程"。
- **U-1241：尺自己改了两处，都是它第一次跑就红出来的。** ① 稳态不能用"最后一格"——拼贴末三格是留白（`-1`），
  于是 `关` 被算成落点 27；改成取**非 -1 的众数**。② 落点不能是"第一次碰到稳态"——开A 会冲到 175 再回落，
  改成"**此后一直等于稳态**的第一帧"。③ differ 对照要比 **PILL** 不是 INK（两臂的行文字本来一样，R353 就是拿错通道）。

"""

ITER = u"""## Round 351 · R354（第 353 轮 · 2026-10-25）：尺进仓库，390 收窄到 1–2 帧（产品 0 文件）

`scripts/filmstrip_frames.py` 落地（网格自动识别 + INK/PILL 两条序列 + 两条正对照）。
after：开A 胶囊落点 6、开B 7，内容第 5 帧归零 ⇒ 差 1–2 帧；before（R328）是 6–7 对 12。两类对照都过。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 读的是三卷胶片的逐帧像素；没有整图看（这一轮的对象是序列）。 |
| 判据有效性 | 14/15 | 两条正对照（关臂落点 2、两臂 PILL 前 8 帧不同），而且尺自己三次读错对象都被抓出来。 |
| 假绿防御 | 15/15 | 稳态/落点/通道三处都改成可证伪的定义；`-1` 与过冲都不许混进落点。 |
| 产品面推进 | 7/15 | 产品 0 文件；但 390 从"不可复核"变成"有数且可重跑"。 |
| 台账一致性 | 13/15 | U-1237…U-1241 五条、D-351、390/427 结案追记；计数器现读抄。 |
| 交付诚实性 | 15/15 | 尺自己的三处错（末格当稳态、过冲当落点、拿错通道）都写在账上。 |
| 可复核性 | 15/15 | 尺在 `scripts/`，命令一行、两只环境变量都不需要。 |

均分 ≈ 13.0/15（91/105）。
"""

BL = u"""
390 结案（R354）：用 `scripts/filmstrip_frames.py` 重读三卷胶片（网格 6×5 的 300×520）：
    开A 胶囊 `81,81,89,119,145,175,150,150…` ⇒ 落点 **6**；开B `…172,189,150…` ⇒ 落点 **7**；
    两臂 INK `688,688,688,683,19,0…` ⇒ 内容第 **5** 帧归零。**内容与胶囊相差 1–2 帧**（≈20–40ms），
    而 before（R328）是 6–7 对 12（差约 5 帧）。R348 把两半接成同一个动画之后，这个差落在 1–2 帧内 ——
    两卷的浮点差异（开A 6 / 开B 7）来自过冲幅度不同，落点差 ≤1 帧。**这一单不再欠数。**

427 结案（R354）：`scripts/filmstrip_frames.py` 进了仓库 —— 网格按场景比自动选、INK/PILL 两条序列、
两条正对照（关臂落点 ≤2、开/开B 前 8 帧 PILL 不同）。R353 那两卷读不出来的原因分别写进了 U-1233/U-1234；
现在同一批文件用这支尺能读，且 `FILMSTRIP_FRAMES_RESULT=ok`。
"""

DEC = u"""
### D-351（354）"落点"的定义必须是「此后不再变」，且稳态取众数不取末值

R354 现读：拿"最后一格"当稳态时，拼贴末三格的留白（`-1`）把 `关` 算成落点 27；
拿"第一次碰到稳态"当落点，开A 的过冲（175）会被当成落定；拿 INK 当两臂差异的通道，两臂看起来一模一样。
三条都是同一个病：**定义没有写成"此后不再变"**。
**How to apply**：写"某条曲线落在第几帧"的判据时，① 稳态 = 非缺测值的众数；② 落点 = 此后一直等于稳态的第一帧
（过冲不算）；③ 两臂对照要先证明所选通道在两臂上真的不同（否则它测的是别的层）。
"""

CH = u"""### 胶片逐帧尺进仓库：390 的落点差收到 1–2 帧（before 约 5 帧），427 结案（R354 / U-1237…U-1241 · 产品 0 文件，判据账）
"""

STATE = u"""## R354 状态（2026-10-25 · 本地 · 第 353 轮 / Round 351）：尺进仓库，390 收窄到 1–2 帧（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R354 / 第 353 轮 / Round 351）：`scripts/filmstrip_frames.py` 落地（网格自动识别 +
INK/PILL 两条序列 + 两条正对照）；390 现读 开A 胶囊落点 6、开B 7、内容第 5 帧归零 ⇒ 差 1–2 帧（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：三跑按首读登记（只登记不轮询，R140）。
② 写 `scripts/filmstrip_frames.py`：网格按场景比自动选；INK（内容带暗像素数）与 PILL（控制带最宽亮点中位 x）。
③ 两条正对照：`关` 落点 2、开A/开B 的 PILL 前 8 帧不同 ⇒ `FILMSTRIP_FRAMES_RESULT=ok`。
④ 读 390：开A `81,81,89,119,145,175,150…`（落点 6）、开B `…172,189,150…`（落点 7）、INK 第 5 帧归零。
⑤ 尺自己三处错（末格当稳态、过冲当落点、拿 INK 当对照通道）都改掉并写进 U-1241。

验证读数（现读）：`CONTROL_STEADY … pill_landed=2 ok`、`CONTROL_DIFFER pill_first8_differs=True ok`、
`FILMSTRIP_FRAMES_RESULT=ok`；`INK 688,688,688,683,19,0…`（两臂同）；脚本电池
`Ran 648（skipped=4）OK`（沿用上一轮；本轮只加一支 `scripts/` 工具，未进电池）；
产品面连续零改动 **{streak}** 轮（`python3 scripts/product_streak.py --streak-for 353` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 新工具没进电池（它要`/tmp` 的胶片，属于"现场尺"，下一轮决定要不要把它接进捕获卷）；
② 无刀、无 swift 全量（产品 0 文件）；③ 真机腿没跑。

下一轮（R355）的靶：⓪ 读 CI 配对 → ① 384（胶囊带纵向覆盖 29%）→ ② 387① / 376 / 367 → ③ 426 的退场（刀的 diff 判法）
→ ④ 决定 `filmstrip_frames.py` 要不要接进捕获卷（接进去就要有它自己的正对照与地板）。

"""

def main():
    s = rd(u"AGENT_UI_AUDIT.md"); a = u"## 第 352 轮（R353 · 2026-10-25 · U-1233…U-1236）"
    i = s.find(a); assert i > 0; wr(u"AGENT_UI_AUDIT.md", s[:i] + U + s[i:])
    s = rd(u"AGENT_VISUAL_ITERATION.md"); wr(u"AGENT_VISUAL_ITERATION.md", s.rstrip(u"\n") + u"\n\n" + ITER)
    s = rd(u"AGENT_BACKLOG.md"); wr(u"AGENT_BACKLOG.md", s.rstrip(u"\n") + u"\n" + BL)
    s = rd(u"AGENT_DECISIONS.md"); wr(u"AGENT_DECISIONS.md", s.rstrip(u"\n") + u"\n" + DEC)
    s = rd(u"CHANGELOG.md"); s = once(s, u"## [Unreleased]\n", u"## [Unreleased]\n\n" + CH); wr(u"CHANGELOG.md", s)
    s = rd(u"AGENT_STATE.md"); h = u"## R353 状态（2026-10-25 · 本地 · 第 352 轮 / Round 350）"
    assert s.count(h) == 1
    wr(u"AGENT_STATE.md", s.replace(h, STATE.replace(u"{streak}", u"%d" % STREAK) + h, 1))
    r = rd(u"AGENT_FINAL_REPORT.md")
    r = once(r, u"U-31 … U-1236（R353 现读抬到最新一节）", u"U-31 … U-1241（R354 现读抬到最新一节）")
    r = once(r, u"| 决定台账 | D-069 … **D-350**", u"| 决定台账 | D-069 … **D-351**")
    r = once(r, u"U 定义行最大 **U-1236**、决定最大 **D-350**、BACKLOG 最大 **427**",
             u"U 定义行最大 **U-1241**、决定最大 **D-351**、BACKLOG 最大 **427**")
    r = once(r, u"完整名单以 `AGENT_STATE.md` 的 R353 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R354 节 ② 为准")
    r = re.sub(u"产品面连续零改动轮数 = \\*\\*\\d+\\*\\*（现读", u"产品面连续零改动轮数 = **%d**（现读" % STREAK, r, count=1)
    r = r.rstrip(u"\n") + u"""
- **R354 续（判据账）**：`scripts/filmstrip_frames.py` 进仓库（网格自动识别 + INK/PILL + 两条正对照）；
  390 现读 开A 胶囊落点 6 / 开B 7 / 内容第 5 帧归零 ⇒ 差 1–2 帧（before 约 5 帧）；427 结案。
""" + u"\n"
    wr(u"AGENT_FINAL_REPORT.md", r)
    print(u"R354_LEDGERS_OK")

if __name__ == u"__main__":
    main()
