# -*- coding: utf-8 -*-
"""R236 台账补丁：刀号跨表撞号（电池第一跑就红）⇒ 三刀改号 M789/M790/M791 并**重跑**，账要跟着改。

顺序不许换：改号 → 重跑变异（真读数见 /tmp/r236_mutate_renamed.log）→ 才动这几本账。
每个 old 串必须在所属文件里**恰好出现一次**，否则抛错不落盘（事务性，与 R147 的规矩同一条）。
"""
import io
import os

REPO = u"/Users/wangziyi/Codex_Project0"

EDITS = [
    # ---------------- AGENT_UI_AUDIT.md ----------------
    (u"AGENT_UI_AUDIT.md",
     u"：13 那棵的墨第一次有**两轴**会红的判据 —— M787 从 ESCAPED 关成 CAUGHT",
     u"：13 那棵的墨第一次有**两轴**会红的判据 —— R235 那枚 ESCAPED 的 M787（同一处变异，本轮重编号 M790）关成 CAUGHT"),
    (u"AGENT_UI_AUDIT.md",
     u"三刀各自只红在自己那一格（`--log` 逐条列名）：M786→",
     u"三刀各自只红在自己那一格（`--log` 逐条列名，名字由仪器自己印、非空）：M789→"),
    (u"AGENT_UI_AUDIT.md",
     u"M787（就地钉蓝）→`testDismissRowLabelRoutesThroughTheSeam`、M788（钉进缝里）→",
     u"M790（就地钉蓝 = R235 那枚 ESCAPED 的 M787 同一处变异）→`testDismissRowLabelRoutesThroughTheSeam`、M791（钉进缝里）→"),
    (u"AGENT_UI_AUDIT.md",
     u"，264 的 ESCAPED 就地关成 CAUGHT。",
     u"，264 的 ESCAPED 就地关成 CAUGHT。\n"
     u"  **刀号改过并且重跑过**（不是只改账）：第一版这张表把三刀登成 M786 / M787 / M788，而 M786 / M787 属于\n"
     u"  `mutate_r235.py` 那张表 ⇒ 脚本电池 `test_mutate_arm_registry` 当场红\n"
     u"  （`AssertionError: 跨表撞号：{'M786': ['mutate_r235', 'mutate_r236'], 'M787': [...]}`）。规矩是**刀号跨表唯一**：\n"
     u"  一个号要能指向唯一一个形状，沿用上一轮的号 = 让两个不同的东西共享身份。本轮改成 M789 / M790 / M791 后\n"
     u"  重跑（`/tmp/r236_mutate_renamed.log`：三行 `R236_KNIFE ... CAUGHT` + `CAUGHT=3 / ESCAPED=0 / NOT_RUN=0 / RESTORE_CLEAN=yes`），\n"
     u"  上面那三个红名就是这个通道的产物。"),

    # ---------------- AGENT_VISUAL_ITERATION.md ----------------
    (u"AGENT_VISUAL_ITERATION.md",
     u"三刀分别红在各自那一格 ⇒ **CAUGHT=3 / ESCAPED=0 / NOT_RUN=0 / RESTORE_CLEAN=yes**，M787 关成 CAUGHT。",
     u"三刀分别红在各自那一格 ⇒ **CAUGHT=3 / ESCAPED=0 / NOT_RUN=0 / RESTORE_CLEAN=yes**，M790 关成 CAUGHT\n"
     u"（三刀登记号 M789 / M790 / M791 —— 第一版撞了 `mutate_r235.py` 的 M786 / M787，被脚本电池钉住后**改号重跑**，\n"
     u"不是把旧号借来用一次）。"),

    # ---------------- AGENT_DECISIONS.md ----------------
    (u"AGENT_DECISIONS.md",
     u"附则：仪器打印的\"红名\"列若为空串，那条读数按不存在记账（见 U-759）。",
     u"附则：仪器打印的\"红名\"列若为空串，那条读数按不存在记账（见 U-759）。第二条附则：**刀号跨表唯一** ——\n"
     u"本轮第一版沿用 R235 的 M786 / M787，被 `scripts/tests/test_mutate_arm_registry.py` 判红；改号 M789 / M790 / M791\n"
     u"之后**重跑变异**才落账。借上一轮的号 = 让两个不同形状共享一个身份，下一轮读到那个号就不知道在问哪一行代码。"),

    # ---------------- AGENT_BACKLOG.md ----------------
    (u"AGENT_BACKLOG.md",
     u"**264 追记（R236 结案）：缝做了，两轴各一条判据、各一刀 —— M787 由 ESCAPED 关成 CAUGHT**",
     u"**264 追记（R236 结案）：缝做了，两轴各一条判据、各一刀 —— M787 那一处变异（重编号 M790）由 ESCAPED 关成 CAUGHT**"),
    (u"AGENT_BACKLOG.md",
     u"M786 CAUGHT（在岗证人，红在 12 那棵的行为轴）、M787 CAUGHT（就地钉蓝 ⇒ 结构轴）、M788 CAUGHT（钉进缝里 ⇒ 行为轴），\n"
     u"ESCAPED=0 / NOT_RUN=0 / RESTORE_CLEAN=yes。",
     u"M789 CAUGHT（在岗证人，红在 12 那棵的行为轴）、M790 CAUGHT（就地钉蓝 ⇒ 结构轴）、M791 CAUGHT（钉进缝里 ⇒ 行为轴），\n"
     u"ESCAPED=0 / NOT_RUN=0 / RESTORE_CLEAN=yes（三枚都是重跑后的号：原先借了 `mutate_r235.py` 的 M786 / M787，"
     u"被脚本电池的跨表撞号守卫钉红）。"),

    # ---------------- AGENT_STATE.md ----------------
    (u"AGENT_STATE.md",
     u"—— M787 由 ESCAPED 关成 CAUGHT，而画面一字未动",
     u"—— R235 那枚 ESCAPED（M787，本轮同一处变异重编号 M790）关成 CAUGHT，而画面一字未动"),
    (u"AGENT_STATE.md",
     u"：M786→12 那棵的在岗证人、M787→结构轴、\nM788→行为轴",
     u"：M789→12 那棵的在岗证人、M790→结构轴、\nM791→行为轴"),

    # ---------------- AGENT_FINAL_REPORT.md ----------------
    (u"AGENT_FINAL_REPORT.md",
     u"三刀 M786 / M787 / M788 **各红在自己那一格**",
     u"三刀 M789 / M790 / M791 **各红在自己那一格**（第一版撞了 `mutate_r235.py` 的 M786 / M787 ⇒ 脚本电池的跨表撞号守卫钉红，改号后**重跑**）"),
]


def main():
    loaded = {}
    for name, old, new in EDITS:
        text = loaded.get(name)
        if text is None:
            path = os.path.join(REPO, name)
            text = io.open(path, encoding="utf-8").read()
            loaded[name] = text
        count = text.count(old)
        if count != 1:
            raise SystemExit(u"锚点命中 %d 次（要恰好 1 次）：%s <- %r" % (count, name, old[:70]))
        loaded[name] = text.replace(old, new, 1)

    # CHANGELOG：把本轮那条 bullet 升成**标题行**（`^### .*（R236 / `），
    # 因为 `test_round_batch_consistency` 读的是结构而不是散文（R143 起，M655 那一刀钉的正是这件事）。
    cl = loaded.setdefault(
        u"CHANGELOG.md",
        io.open(os.path.join(REPO, u"CHANGELOG.md"), encoding="utf-8").read())
    start = cl.index(u"- R236（第 235 轮 / Round 233 / U-757…U-760 / D-221）：")
    end = cl.index(u"\n", start)
    old_line = cl[start:end]
    new_block = (
        u"### 判据与缝：13 那棵 SwiftUI 树的 dismiss 行墨第一次有**两轴**会红的判据（R236 / U-757…U-760 / D-221 · 产品 1 文件，画面一字未动）\n"
        u"\n"
        u"- 墨与文案收成一条可读的缝（`dismissRowInk` + `dismissRowLabel()`），判据 `MenuBarSwiftUIDismissRowInkTests` 三格："
        u"尺自对照 / 行为轴（钉进缝里 ⇒ 两档 × 4.5 与 3.0 地板必须红）/ 结构轴（绕过缝就地钉色 ⇒ 必须红）。"
        u"变异三刀 M789 / M790 / M791 CAUGHT=3 / ESCAPED=0 / NOT_RUN=0 / RESTORE_CLEAN=yes ⇒ "
        u"R235 那枚 ESCAPED 的 M787（同一处变异，本轮号 M790）就地关成 CAUGHT，BACKLOG 264 结案。"
        u"画面不变（重捕 162 帧 `CHANGED=0 / MISSING=0`）⇒ 这是一笔**不改变画面的可证伪性**改动。\n"
        u"- 仪器自己的两处坏（本轮实测并修）：变异表的「红名」列被 `split(\"]\")[-1]` 恒取成空串（U-759，本轮修成 `[-2]` 并要非空）；"
        u"三刀第一版借用了 `mutate_r235.py` 的 M786 / M787 ⇒ 脚本电池 `test_mutate_arm_registry` 判红，"
        u"改号之后**重跑**变异而不是只改账。"
    )
    loaded[u"CHANGELOG.md"] = cl[:start] + new_block + cl[end:]

    for name, text in loaded.items():
        path = os.path.join(REPO, name)
        io.open(path, "w", encoding="utf-8").write(text)
        print(u"写了 %s" % name)


if __name__ == u"__main__":
    main()
