#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R365 追记（第 364 轮 / Round 362）：runner 上的 376 收口文本 + 24/24 覆盖读数。

只动三本：STATE（⓪ 的成对号 + 追记段）、BACKLOG（376 结案 + 384 的 runner 读数）、
REPORT（§14 标题抬到 R365、两条续写、顺手把 R362 那条重复的 bullet 去掉）。
"""
import io
import os

ROOT = u"/Users/wangziyi/Codex_Project0"


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding=u"utf-8").read()


def wr(name, text):
    io.open(os.path.join(ROOT, name), u"w", encoding=u"utf-8").write(text)


def once(text, anchor, replacement):
    assert text.count(anchor) == 1, u"锚点命中 %d 次：%s" % (text.count(anchor), anchor[:80])
    return text.replace(anchor, replacement)


# ---------- AGENT_STATE.md ----------
st = rd(u"AGENT_STATE.md")
st = once(st,
          u"① ⓪ CI：`9d2c8a8`（R360 追记）已 **success**；R361–R364 六跑仍在队里（只登记不轮询）。",
          u"① ⓪ CI：`9d2c8a8`（R360 追记）已 **success**；R361–R364 六跑仍在队里（只登记不轮询）；"
          u"本轮 `563c0ed ↔ 40201333483`（queued、同 workflow 前面=4）。")
st_head = (u"## R364 状态（2026-10-25 · 本地 · 第 363 轮 / Round 361）：426 第三批 —— "
           u"三张表迁到 diff 回读（产品 0 文件，判据账）")
st_add = (
    u"**R365 追记（runner 读数，现读）**：`9d2c8a8`（R360 追记）那一跑 **success**，日志里第一次出现 376 的收口文本：\n"
    u"`MOTION_NOT_RUN=reduce-motion-on filter-pill-slide 三臂不可分（帧数与峰值全等（数组别处不同）：开A 帧数=1 峰值=0.9187 "
    u"开B 帧数=1 峰值=0.9187 关 帧数=1 峰值=0.9187） 采样≈17ms 可分帧=11 ⇒ reduce=on（catalog 真）⇒ "
    u"药丸按 431 归零是**产品行为**，这一半在 reduce 机器上判不了` —— 同一跑再印\n"
    u"`MOTION_REDUCE_SOURCES setting=true voiceOver=false catalog=true override=nil`，出口文本与三源读数在同一跑里对上；\n"
    u"`empty-state=3`、`judged=3/4 not-run=notice-banner`。同跑 `MOTION_PILL_RAMP_GEOM … 纵向覆盖=24/24px=100%`\n"
    u"⇒ 本轮的 0.90 地板在 runner 上第一次有数（但那一跑还没有这行断言；判词要等 `563c0ed`）。\n\n")
st = once(st, st_head, st_add + st_head)
wr(u"AGENT_STATE.md", st)

# ---------- AGENT_BACKLOG.md ----------
bl = rd(u"AGENT_BACKLOG.md")
bl_tail = (u"- **384 追记（R365 · 地板）**：并墨修法的覆盖已经写成会红的地板 `pillBandCoverageFloor = 0.90`"
           u"（本机 48/48、runner 24/24；关掉并墨 14/48=29%）。地板在 `testFilterPillRampIsMonotone` 里，"
           u"M1009 的红线是 6024 行的原文（U-1277）。结案 ≠ 钉住 —— 这一格现在两样都有。")
bl_add = (bl_tail + u"\n\n"
          u"376 结案（R365 追记）：`9d2c8a8`（R360 追记）绿跑现读\n"
          u"    `MOTION_NOT_RUN=reduce-motion-on filter-pill-slide 三臂不可分（帧数与峰值全等（数组别处不同）："
          u"开A 帧数=1 峰值=0.9187 开B 帧数=1 峰值=0.9187 关 帧数=1 峰值=0.9187） 采样≈17ms 可分帧=11 ⇒ "
          u"reduce=on（catalog 真）⇒ 药丸按 431 归零是**产品行为**，这一半在 reduce 机器上判不了`，\n"
          u"    同一跑 `MOTION_REDUCE_SOURCES setting=true voiceOver=false catalog=true override=nil` ⇒ "
          u"出口文本与三源读数在同一跑里对上：runner 上这朵是产品行为，不是通道限制。**判据面到此收口**。\n\n"
          u"384 的 runner 读数（R365 追记）：同一跑的 `MOTION_PILL_RAMP_GEOM … 纵向覆盖=24/24px=100%`"
          u" 与本机 48/48 是同一个比例；\n"
          u"    R365 的 0.90 地板要等 `563c0ed`（`40201333483`）那一跑才第一次在 runner 上被判。")
bl = once(bl, bl_tail, bl_add)
wr(u"AGENT_BACKLOG.md", bl)

# ---------- AGENT_FINAL_REPORT.md：§14 ----------
rp = rd(u"AGENT_FINAL_REPORT.md")
rp = once(rp,
          u"## 14. R299 → R364 这一段（R337 补写；R341 续到 341、R364 续到 364 —— 这份报告第三次差点停在几十轮之前）",
          u"## 14. R299 → R365 这一段（R337 补写；R341 续到 341、R365 续到 365 —— 这份报告第三次差点停在几十轮之前）")
# 去掉 R362 那条重复的 bullet（先写的那条短版；留下带 M1007/M1008 明细的那条）
dup = (u"- **R362 续（判据账）**：426 第一步 —— `readback.single_substitution_lands`（needle 恰好一次 + 盘上 == 预期替换 + 非空刀；\n"
       u"  不要求 repl 全局唯一，R350 的现场不再假红）；r358/r360 迁移，M1007/M1008 各 CAUGHT 1/1；5 格测试、电池 664。\n")
rp = once(rp, dup, u"")
anchor = (u"- **R364 追记（runner）**：`ff3deba` / `753fa5d` 两跑绿 —— 387① 的 A/B 在 runner 上与本机逐字同数\n"
          u"  （`同=11 漂=1 敏感=0`）；`MOTION_REDUCE_SOURCES setting=true voiceOver=false catalog=true override=nil`\n"
          u"  第一次出现在日志里，证实 runner 系统级 reduce-on（431 收口），同跑 `judged=4/4`。")
rp_add = (anchor + u"\n"
          u"- **R365 续（判据账）**：384 的修法有了自己的地板 —— `pillBandCoverageFloor = 0.90`，"
          u"本机 48/48、runner 24/24；\n"
          u"  M1009 关掉并墨 ⇒ 14/48=29%，红在 `testFilterPillRampIsMonotone` 6024 行的地板原文上，`RESTORE_CLEAN=yes`；"
          u"读不出覆盖走具名 skip。\n"
          u"- **R365 追记（runner）**：`9d2c8a8` 绿跑现读 `MOTION_NOT_RUN=reduce-motion-on …（三臂 1/1/1 帧、峰值 0.9187 全等）`"
          u"⇒ 376 收口；\n"
          u"  同跑 `纵向覆盖=24/24px=100%`、`MOTION_REDUCE_SOURCES setting=true`、`judged=3/4`。")
rp = once(rp, anchor, rp_add)
wr(u"AGENT_FINAL_REPORT.md", rp)

print(u"R365_ADDENDUM_OK")
