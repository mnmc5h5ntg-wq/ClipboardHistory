#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R42 的 CI 追认写进四份台账（原文照抄 runner 的读数，不写结论外的东西）。"""
import io

CI = '''**CI 已读（run 38511570267 / job 115681039121，12m45s，15 步全 ✓）**：
第 5 步 `Executed 726 tests, with 36 tests skipped and 0 failures`；第 7 步闸门
`passed=25 skipped=9 failed=0 有名字的红=0 NOT_RUN=8 ⇒ ok`（与 R41 那次逐字相同 ⇒ 本轮一条红都没新增）；
第 11 步 `Ran 83 tests`；第 13 步夹具集闸 `COMPARED=112 / MISSING=0 / ADDED=0`；第 15 步 `SMOKE_OK=1`。

**本轮唯一一条动效数字上的好消息在第 10 步**：
`motion floor: executed=24  MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-` ⇒ `MOTION_FLOOR_OK=4/4`。
覆盖率地板在 runner 上**四条全判到**，而本机同一把尺只判 1/3（抓帧时钟更粗，BACKLOG 里记着）。
这不证明回执在淡 —— 那四条不是这一族的 —— 但它把"CI 上看不到动效"这句老话削掉了一半：
**能被看见的那四件在跑**，而回执这一族量不到是**尺的通道问题**（淡入活在 presentation 层），不是没人跑。
'''


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new)
    io.open(path, "w", encoding="utf-8").write(text)


patch("AGENT_UI_AUDIT.md", [
    ("变异 **M194–M198** 五支全 CAUGHT、`未被抓到=0 红得不对=0 还原不干净=0`。\n**CI 待读**。",
     "变异 **M194–M198** 五支全 CAUGHT、`未被抓到=0 红得不对=0 还原不干净=0`。\n" + CI),
])

patch("AGENT_VISUAL_ITERATION.md", [
    ("脚本 83 全绿、变异 M194–M198 五支全 CAUGHT（`未被抓到=0 红得不对=0 还原不干净=0`）。\n**CI 待读**。",
     "脚本 83 全绿、变异 M194–M198 五支全 CAUGHT（`未被抓到=0 红得不对=0 还原不干净=0`）。\n" + CI),
])

patch("AGENT_STATE.md", [
    ("- **CI 待读**。\n- **下一步（R43）**",
     "- **CI 已读**：run 38511570267 **整作业 success**（12m45s，15 步全 ✓）—— 第 5 步 "
     "`Executed 726 tests / 36 skipped / 0 failures`、第 7 步闸门 `有名字的红=0 NOT_RUN=8 ⇒ ok`、"
     "第 13 步 `COMPARED=112 / MISSING=0 / ADDED=0`、第 15 步 `SMOKE_OK=1`。\n"
     "  **第 10 步是本轮唯一一条动效数字上的好消息**：`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-` "
     "⇒ `MOTION_FLOOR_OK=4/4` —— 覆盖率地板在 runner 上四条全判到（本机同一把尺只判 1/3）。"
     "它不证明回执在淡，但它把「CI 上看不到动效」这句老话削掉了一半：能被看见的那四件在跑，"
     "回执这一族量不到是**尺的通道**问题（presentation 层），不是没人跑。\n"
     "- **下一步（R43）**"),
])

patch("AGENT_FINAL_REPORT.md", [
    ("  同一族（两台机器的读数不能互当判据）第四次遇到 |",
     "  同一族（两台机器的读数不能互当判据）第四次遇到 |\n"
     "  **R42 补**：run 38511570267 **整作业 success**（12m45s，15 步全 ✓）—— `Executed 726 tests / "
     "36 skipped / 0 failures`、闸门 `有名字的红=0 NOT_RUN=8 ⇒ ok`、`SMOKE_OK=1`。"
     "**动效覆盖率地板第一次在 runner 上判满**：`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-` "
     "⇒ `MOTION_FLOOR_OK=4/4`（本机同一把尺 1/3，抓帧时钟更粗）⇒ 「CI 看不到动效」这句老话现在只剩一半："
     "能被看见的都在跑，量不到的那一族（纯淡入）是**通道**问题不是**执行**问题 |"),
])
print("四份台账已写入 R42 的 CI 追认")
