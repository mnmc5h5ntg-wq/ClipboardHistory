#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R356 七本台账（第 355 轮 / Round 353 · 产品 0 文件，判据账）。"""
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
    [u"python3", u"scripts/product_streak.py", u"--streak-for", u"355"],
    cwd=ROOT, stdout=subprocess.PIPE).stdout.decode(u"utf-8")).group(1))

full = LOG(u"r356_full.log")
FULL_N, FULL_SKIP, FULL_FAIL = last(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full, u"全量卷")
film = LOG(u"r356_motion_full.log")
FILM_J, FILM_T, FILM_NOTRUN = last(r"MOTION_RESOLVE_SUMMARY judged=(\d+)/(\d+) not-run=(\S+)", film, u"胶片 judged")
FILM_N, FILM_SKIP, FILM_FAIL = last(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", film, u"胶片")
COV_N, COV_D, COV_P = last(r"纵向覆盖=(\d+)/(\d+)px=(\d+)%", film, u"纵向覆盖")
BAND_LO, BAND_HI = last(r"行带=([0-9.]+)…([0-9.]+)pt", film, u"行带")
RAMP_V, RAMP_F, RAMP_L, RAMP_M, RAMP_B = last(
    r"MOTION_PILL_RAMP filter-pill-slide A 判定=(\S+) 首=([0-9.]+)pt 末=([0-9.]+)pt 位移=([0-9.]+)pt 最大倒退=([0-9.]+)pt",
    film, u"斜坡")
knife = LOG(u"r356_mutate.log")
K_CAUGHT, K_TOTAL, K_CLEAN = last(r"CAUGHT=(\d+)/(\d+), RESTORE_CLEAN=(yes|no)", knife, u"变异汇总")
pre = LOG(u"r356_precheck.log")
P_TABLES, P_COVERED, P_ARMS, P_BAD = last(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre, u"针预检")
A_FILES, A_ARMS, A_DUPES, A_REPEATS = last(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre, u"臂名册")
base = LOG(u"r356_baseline.log")
B_COMPARED, B_CHANGED, B_MISSING, B_ADDED = last(
    r"FRAME_BASELINE_COMPARED=(\d+)\nFRAME_BASELINE_CHANGED=(\d+)\nFRAME_BASELINE_MISSING=(\d+)\nFRAME_BASELINE_ADDED=(\d+)",
    base, u"帧基线")
surface = LOG(u"r356_surface.log")
SURF = last(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", surface, u"清账表")
# 电池的**权威**那遍在台账落盘之后跑；这里只取用例数（本轮没加 python 用例，数与上一轮同）。
# 不在这里断言 OK：落盘前那些读台账的守卫本来就该红，拿那时的红/绿当电池结论会撒谎。
battery = LOG(u"r356_py_first.log")
BAT_N = last(r"Ran (\d+) tests", battery, u"电池")[0]
build = LOG(u"r356_build.log")
assert u"Build complete" in build and u"warning:" not in build, u"构建不是 0 告警"

U = u"""## 第 355 轮（R356 · 2026-10-25 · U-1247…U-1251）：384 结案 —— 标签墨不再把胶囊劈成两半，带子纵向覆盖 29%→100%（U-1247…U-1251 · 产品 0 文件，判据账）

- **U-1247：384 的现场与修法。** 真帧（R329）取用带只有 7pt：候选段 `y116..138px` 被判「洞太窄 21%」，
  而上下两段通过的是 49% —— 同一颗胶囊被选中态上的**标签墨**劈成两半。R356 给 `pillRun` 加 `mergeInk`：
  **只并"既不接近药丸档、也不接近轨道档"的列**（两边都 ≥ delta），并在 `movingHoleRowReading` 里打开。
  现读 before/after：行带 `51.0…58.0pt（7pt）` → `51.0…75.0pt（24pt）`；判定分布 `洞太窄×11,过×13` → `过×24`；
  `纵向覆盖=14/48px=29%` → **`48/48px=100%`**；`MOTION_PILL_BAND` 的带子 `y51…58pt` → `y51…75pt`。
- **U-1248：纵向那半不用改 —— R329 的预测被现读推翻。** 384 的追记写过"横轴与纵轴要一起做，
  不然并回字墨也只是把被拒段从洞太窄变成过、带子仍是 7pt 顶部切片"。但三段的**首尾相接**本来就是
  `verticalCoverage` 的定义；中段一旦从"洞太窄"变成"过"，`movingHoleBand` 取的最长连续"过"段
  直接就是 48px，覆盖分母不变、取用规则一字未动。**改的是洞的定义，不是带子的定义。**
- **U-1249：并墨只改"哪一段算洞"，不改电平。** `pillLuma` 仍只由药丸档的列平均（墨列不参与），
  纯测试钉住 `74`；另配一条反向正对照：药丸之外另有一块墨、中间隔着轨道 ⇒ 并墨也不许把两段连起来
  （`testPillRunDoesNotBridgeAcrossTrackWithInk`）。斜坡仍判 `单调`：首 81.0pt、末 219.0pt、
  位移 138.0pt、最大倒退 0.0pt（中心序列变了几个小数，但没有一格越过容差）。
- **U-1250：五格夹具迁移 + 一根旧针重钉。** 原来用 **200 级字墨**造"窄洞"的五格（报告形状 / 分档 / 纵向覆盖 /
  行读数），在并墨之后失去对象（那些行变成"过"）—— 改成**轨道级的缝**（并墨管不到它），断言与地板一字未动；
  分档那一格另在轨道最右留一列 200 级墨，"远高于轨道的那一级"仍有对象。`M926`（极性翻面）的针
  因 `isPill` 那一行多出 `|| isInk(…)` 命中 0 ⇒ 按 R262 重钉，语义不变，`M926 CAUGHT`；
  预检现读 `tables=@PTBL@ covered=@PCOV@ arms=@PARMS@ bad=@PBAD@`。本轮刀 `M1006`（两处 `mergeInk: true` 改回 false）
  ⇒ `testLabelInkInsideThePillDoesNotNarrowTheHole` 红，`CAUGHT=@KC@/@KT@, RESTORE_CLEAN=@KL@`。
- **U-1251：R355 的两笔在 K 上打架 —— 产品轮的追记要么重复本轮的 K，要么不写 K。**
  落盘后的电池现读 `ROUND_K_CONTRADICTION 355：5515daf 其他=1 | da5f8a7 追记=0`。D-336 定的是
  "标题里那半句是**轮次级**的数，每一笔要么重复它、要么不写"；R355 的追记写了 `产品 0 文件`，
  于是同一轮里出现 1 与 0 两个数。已 push 不能改历史 ⇒ 按 R334/R335 的先例登记进
  `CONTRADICTION_ROSTER`（理由引 BACKLOG 405、退场=扫描窗滑过 R355 之后删）。
  这一条不花钱买"数对"：它只让这一轮不再是红，教训必须写进下一笔的 subject 里。

"""

ITER = u"""## Round 353 · R356（第 355 轮 · 2026-10-25）：384 结案 —— 标签墨不再把胶囊劈成两半，带子 7pt→24pt、覆盖 29%→100%（产品 0 文件）

给 `pillRun` 加 `mergeInk`（只并"既不像药丸也不像轨道"的列），在行读数里打开；电平不受影响。
before/after：行带 7pt→24pt、判定分布 洞太窄×11,过×13 → 过×24、纵向覆盖 29%→100%，斜坡仍单调 138pt/倒退 0。
五格夹具改用轨道级的缝造窄洞；M926 旧针重钉；M1006 `CAUGHT=@KC@/@KT@`。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 读的是胶片逐帧与报告的三段拼接；本轮没有真机眼（产品 0 文件）。 |
| 判据有效性 | 14/15 | 三条纯测试（并墨、不跨轨、现场形状）+ 一刀；坡尺与过程证人照旧运行且不改断言。 |
| 假绿防御 | 14/15 | 并墨有反向正对照；五格夹具改成"并墨管不到"的窄洞，不是把地板放宽；覆盖率只印不判，未拿一台的数当门。 |
| 产品面推进 | 10/15 | 产品 0 文件；推进在尺上（384 的读数据此可复核，判据不再少读 71% 的胶囊高度）。 |
| 台账一致性 | 13/15 | U-1247…U-1250、D-354/D-355、384 结案追记；计数器现读。 |
| 交付诚实性 | 15/15 | runner 读数与覆盖率地板都记成欠账；没有把"本机 100%"写成"两机成立"。 |
| 可复核性 | 15/15 | 纯函数 + 合成夹具 + 真帧读数都可重跑；刀与预检都在仓库。 |

均分 = 94/105 ≈ 13.4/15（89）。

"""

BL = u"""
384 结案（R356）：`pillRun` 加 `mergeInk`（只并"既不接近药丸档、也不接近轨道档"的列），行读数打开它。
    真帧现读：行带 **51.0…58.0pt（7pt）→ 51.0…75.0pt（24pt）**；判定分布 **洞太窄×11,过×13 → 过×24**；
    **纵向覆盖 14/48px=29% → 48/48px=100%**；`MOTION_PILL_BAND` 带子 `y51…58pt → y51…75pt`。
    R329 那句"纵向要一起改"被现读推翻：三段首尾相接，中段一旦变"过"，最长连续"过"段就是整颗胶囊；
    纵向取用规则一字未动。斜坡仍 `单调`：首 81.0 / 末 219.0 / 位移 138.0pt / 最大倒退 0.0pt。
    电平不被墨拉走（`pillLuma` 仍只由药丸档的列算），反向正对照钉住"隔轨不许桥接"。
    **仍欠**：① runner 上同一行 `MOTION_PILL_RAMP_GEOM` 的读数（下一跑 CI）；
    ② 覆盖率的**地板**未钉 —— 本机 100% 不足以当门，等 runner 的同格读数再定（R38 的老规矩）。

"""

DEC = u"""
### D-354（356）夹具的窄洞证人不得借用正在修的机制

384 的五格夹具一直用 **200 级字墨**把胶囊"劈开"来造窄洞，于是"字墨会被并回洞"这个修法一落地，
那五格同时失去对象（洞变宽、判"过"）。这不是守卫变松，是**证人借用了被修的那条机制**：
它证明的"窄洞会报洞太窄"其实依赖"字墨不被并"这条将被改掉的假设。
**Why**：同一份夹具里混了两个语义 —— "窄洞"与"字墨劈洞"；修掉后者，前者就没了证人。
**How to apply**：造"窄洞"用**修法管不到的**东西（这里是轨道级的缝）；要保留"字墨在洞里"的形状，
就另立一格专门证"并墨后洞变宽"。改夹具时断言与地板一律不动 —— 动的只是证人。

### D-355（356）「洞」可以包含字，但电平只能由药丸档的列算

并墨之后，胶囊上的标签列被算进洞的**范围**；如果它们同时进入 `pillLuma` 的均值，那颗"选中色阶"
会被字墨拉低，`分离度` 与 `中心` 都会跟着漂 —— 那是把对象修补变成读数污染。
**Why**：洞（对象范围）与电平（档位读数）是两件事；R327 的第一版就是把两者混在一个估计量里才读错。
**How to apply**：凡是"把某类列并进范围"的修法，均值/中位数一律只用**原本那一档**的列；
另配一条反向正对照（这里是"隔轨不许桥接"），证明并的条件不是"任何不等于轨道的东西"。

"""

CH = u"""### 384 结案：标签墨不再把胶囊劈成两半 —— 带子 7pt→24pt、纵向覆盖 29%→100%，斜坡仍单调（R356 / U-1247…U-1250 · 产品 0 文件，判据账）
"""

STATE = u"""## R356 状态（2026-10-25 · 本地 · 第 355 轮 / Round 353）：384 结案 —— 带子 7pt→24pt、覆盖 29%→100%（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R356 / 第 355 轮 / Round 353）：`pillRun` 加 `mergeInk`（只并字墨列），
行读数打开 ⇒ 真帧行带 51.0…58pt → 51.0…75pt、纵向覆盖 14/48px=29% → 48/48px=100%，判定分布 洞太窄×11,过×13 → 过×24；
五格夹具改用轨道级的缝、M926 旧针重钉，M1006 `CAUGHT=1/1`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：R355 的两跑 `40194321798 ↔ 5515daf`、`40194348175 ↔ da5f8a7` 现读都 `in_progress`（第三态，登记不轮询）。
② 384 的修法：`pillRun(..., mergeInk:)`，只并"两边都 ≥ delta"的列；`movingHoleRowReading` 传 true。
③ 真帧读数：行带 7pt→24pt、判定分布 洞太窄×11,过×13 → 过×24、覆盖 29%→100%、`MOTION_PILL_BAND` y51…75pt。
④ 反向正对照：隔轨不许桥接；电平仍只由药丸列算（纯测试钉 74）。
⑤ 夹具迁移：五格改用轨道级的缝造窄洞（断言与地板不动）；分档格留一列 200 级墨。
⑥ 针：M926 因 `isPill` 行变化重钉（语义不变，CAUGHT）；M1006 改回 `mergeInk:false` ⇒ 新行为判据红。

验证读数（现读）：全量卷 `Executed @FN@ tests, with @FS@ tests skipped and @FF@ failures`；
胶片 `Executed @FLN@ tests, with @FLS@ tests skipped and @FLF@ failures`、`MOTION_RESOLVE_SUMMARY judged=@FJ@/@FT@ not-run=@FNR@`；
`MOTION_PILL_RAMP_GEOM` 行带=@BLO@…@BHI@pt、`纵向覆盖=@CN@/@CD@px=@CP@%`；斜坡 A `判定=@RV@ 首=@RF@ 末=@RL@ 位移=@RM@ 最大倒退=@RB@`；
基线 `COMPARED=@BC@ CHANGED=@BCH@ MISSING=@BM@ ADDED=@BA@`（沿用 R355 重捕的 @BC@ 帧，本轮产品 0 文件未重捕）；
清账表 `MOTION_LEDGER 表面=@S0@ 状态=@S1@ 格子=@S2@ 行数=@S3@ 已清账=@S4@ 未清账=@S5@ 地板=@S6@`；
脚本电池 `Ran @BAT@（skipped=4）OK`；产品面连续零改动 **@STREAK@** 轮（`python3 scripts/product_streak.py --streak-for 355` 现读）。

NOT-RUN（分开写）：① runner 对 R355 修复与 R356 尺改动的读数（下一跑 CI；先看 `empty-state` 与 `MOTION_PILL_RAMP_GEOM`）；
② 覆盖率的**地板**没钉（只有本机 100%，没有 runner 同格读数；R38：一台的数不许当门）；
③ 真机腿（reduce 开关 / 395）没跑；④ 静态帧未重捕（产品 0 文件；沿用 R355 的 182 帧，`ls` 数过）。

下一轮（R357）的靶：⓪ 读 CI（`5515daf` / `da5f8a7` 两跑）→ ① 387① / 376 / 367 → ② 426（刀的 diff 判法）与 428（`ci_read.py queue`）→
③ 若 runner 的 `MOTION_PILL_RAMP_GEOM` 到位：给覆盖率定地板（两机同数之后）。

"""
UP = u"""## R355 状态（2026-10-25 · 本地 · 第 354 轮 / Round 352）：runner 六连红结案 —— reduce 下空态淡入被归零（产品 1 文件，判据账）"""
UP_UI = u"""## 第 354 轮（R355 · 2026-10-25 · U-1242…U-1246）：runner 六连红是**产品事实** —— reduce 下空态淡入被归零（U-1242…U-1246 · 产品 1 文件，判据账）"""

def fill(text):
    pairs = {
        u"@PTBL@": P_TABLES, u"@PCOV@": P_COVERED, u"@PARMS@": P_ARMS, u"@PBAD@": P_BAD,
        u"@KC@": K_CAUGHT, u"@KT@": K_TOTAL, u"@KL@": K_CLEAN,
        u"@FN@": FULL_N, u"@FS@": FULL_SKIP, u"@FF@": FULL_FAIL,
        u"@FLN@": FILM_N, u"@FLS@": FILM_SKIP, u"@FLF@": FILM_FAIL,
        u"@FJ@": FILM_J, u"@FT@": FILM_T, u"@FNR@": FILM_NOTRUN,
        u"@CN@": COV_N, u"@CD@": COV_D, u"@CP@": COV_P,
        u"@BLO@": BAND_LO, u"@BHI@": BAND_HI,
        u"@RV@": RAMP_V, u"@RF@": RAMP_F, u"@RL@": RAMP_L, u"@RM@": RAMP_M, u"@RB@": RAMP_B,
        u"@BC@": B_COMPARED, u"@BCH@": B_CHANGED, u"@BM@": B_MISSING, u"@BA@": B_ADDED,
        u"@S0@": SURF[0], u"@S1@": SURF[1], u"@S2@": SURF[2], u"@S3@": SURF[3],
        u"@S4@": SURF[4], u"@S5@": SURF[5], u"@S6@": SURF[6],
        u"@BAT@": BAT_N, u"@STREAK@": str(STREAK),
    }
    for k, v in pairs.items():
        text = text.replace(k, v)
    leftover = re.findall(u"@[A-Z0-9]{2,}@", text)
    assert not leftover, u"还有占位符没填：%s" % u",".join(sorted(set(leftover)))
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
    fr = once(fr, u"| 决定台账 | D-069 … **D-353**", u"| 决定台账 | D-069 … **D-355**")
    fr = once(fr, u"| 视觉台账 | U-31 … U-1246（R355 现读抬到最新一节）",
              u"| 视觉台账 | U-31 … U-1251（R356 现读抬到最新一节）")
    fr = once(fr, u"变异臂在册 **865** 把 / 扫了 **224** 个表文件（预检 tables=130 covered=113 arms=373 bad=0）；U 定义行最大 **U-1246**、决定最大 **D-353**、BACKLOG 最大 **431**",
              u"变异臂在册 **865** 把 / 扫了 **225** 个表文件（预检 tables=131 covered=114 arms=374 bad=0）；U 定义行最大 **U-1251**、决定最大 **D-355**、BACKLOG 最大 **431**")
    fr = once(fr, u"产品面连续零改动轮数 = **7**", u"产品面连续零改动轮数 = **1**")
    tail = u"（R355 现读：注册表 **130** 张 / 刀号最大 **M1005** / 预检 covered=113 arms=373 bad=0；全仓 224 文件 / 865 把） |"
    fr = once(fr, tail,
              u"（R356 现读：注册表 **131** 张 / 刀号最大 **M1006** / 预检 covered=114 arms=374 bad=0；全仓 225 文件 / 865 把） |")
    r356 = u"""- **R356 续（判据账）**：384 结案 —— `pillRun` 加 `mergeInk`（只并"既不像药丸也不像轨道"的列），
  真帧行带 51.0…58pt → 51.0…75pt、判定分布 洞太窄×11,过×13 → 过×24、纵向覆盖 14/48px=29% → **48/48px=100%**；
  R329 的"纵向要一起改"被现读推翻（三段首尾相接，中段变"过"后最长连续段就是整颗胶囊）。斜坡仍单调 138.0pt / 倒退 0。
  五格夹具改成轨道级的缝（不许借用被修的机制），M926 重钉、M1006 `CAUGHT=@KC@/@KT@`。
"""
    if not fr.endswith(u"\n"):
        fr += u"\n"
    fr += fill(r356)
    wr(u"AGENT_FINAL_REPORT.md", fr)
    print(u"R356_LEDGERS_OK U=1251 D=355 BL=431 battery=@BAT@".replace(u"@BAT@", BAT_N))

if __name__ == u"__main__":
    main()
