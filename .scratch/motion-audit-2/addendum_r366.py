#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R366 追记：R365 的覆盖地板在 runner 上被签下（24/24=100%），以及成对号。"""
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


st = rd(u"AGENT_STATE.md")
st = once(st,
          u"① ⓪ CI：`96da5a7`（R362）与 `35d8e76`（R361 追记）都已 **success**；"
          u"`563c0ed`（40201333483）与 R363/R364 的几跑仍在队里。",
          u"① ⓪ CI：`96da5a7`（R362）、`35d8e76`（R361 追记）、`543b3a5`（R364 追记）都已 **success**；"
          u"`563c0ed`（40201333483）也 **success**（见追记）；"
          u"`452f5a3`（40201480169）与 `cc9eb1e`（40202177926）仍在队里（只登记不轮询）。")
r365_head = (u"## R365 状态（2026-10-25 · 本地 · 第 364 轮 / Round 362）：384 的覆盖地板 —— "
             u"两机 100% 落成 ≥90% 的会红判据（产品 0 文件，判据账）")
add = (
    u"**R366 追记（runner 读数，现读）**：`563c0ed`（`40201333483`，带本轮地板的那一跑）**success** —— "
    u"`MOTION_PILL_RAMP_GEOM … 候选段=y52..76px 高24px 判=过 洞宽=49% 取用=y52..76px 纵向覆盖=24/24px=100%`，"
    u"新地板 `≥0.90` 在 runner 上**被签下**（与本地 48/48 是同一个比例，分母 24↔48）；"
    u"`motion suite exit: 0 executed: 68`、`judged=4/4 not-run=-`、`ASSERTION_RED 0`。\n"
    u"同跑的 `MOTION_NOT_RUN=reduce-motion-on …（采样≈27ms 可分帧=7）` 仍是 431 的产品行为那一半。"
    u"成对号：`563c0ed ↔ 40201333483`（concluded success）、`452f5a3 ↔ 40201480169`（in_progress）、"
    u"`cc9eb1e ↔ 40202177926`（in_progress）。\n\n")
st = once(st, r365_head, add + r365_head)
wr(u"AGENT_STATE.md", st)

bl = rd(u"AGENT_BACKLOG.md")
bl_tail = (u"    删臂的回读从此也判「盘上恰好等于预期 diff」（旧判法只证针没了）。单针表里 **9 张** 在新判法上；"
           u"多针表与其余历史表未动。")
bl_add = (bl_tail + u"\n\n"
          u"384 的 runner 验收（R366 追记）：`563c0ed`（`40201333483`）绿跑现读 "
          u"`纵向覆盖=24/24px=100%`、`judged=4/4`、`ASSERTION_RED 0`\n"
          u"    ⇒ `pillBandCoverageFloor = 0.90` 在两台机器上都被签下（本机 48/48、runner 24/24，同一个比例）。"
          u"这一格从「结案时的读数」变成「两机都会红的判据」。")
bl = once(bl, bl_tail, bl_add)
wr(u"AGENT_BACKLOG.md", bl)

rp = rd(u"AGENT_FINAL_REPORT.md")
anchor = (u"- **R366 续（判据账）**：426 第四批 —— r312 迁到 `single_substitution_lands`（只换回读那一行），"
          u"三臂重跑 `3/3` 全 CAUGHT；\n"
          u"  两把删臂的回读从「针没了」升成「盘上恰好等于预期 diff」，红线仍在 895/881 两行的期望格子上。")
rp = once(rp, anchor, anchor + u"\n"
          u"- **R366 追记（runner）**：`563c0ed` 绿跑现读 `纵向覆盖=24/24px=100%`、`judged=4/4`、"
          u"`ASSERTION_RED 0` ⇒ 0.90 地板两机都签下。")
wr(u"AGENT_FINAL_REPORT.md", rp)
print(u"R366_ADDENDUM_OK")
