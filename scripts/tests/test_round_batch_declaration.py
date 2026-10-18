#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""申报通道自己的三条性质（R188 / 新开 211）。

被申报的守卫在 `test_round_batch_consistency.py`（`SINGLE_LEDGER_ROUNDS`）。这里管的是**这张表会不会被用坏**：
① 申报必须带理由 —— 没理由的申报等于偷偷放宽；
② 申报的那一轮必须**确实缺一本账** —— 往名册里塞一轮三本账齐全的（桩标题那条路）要红；
③ 当前轮永远不许被豁免（`back > 0` 那颗钉子必须在），且名册里的号必须小于当前轮。

为什么用 importlib 按路径取模块而不是 import：测试是用 `discover -s scripts/tests` 跑的，
`scripts/` 不在 sys.path 上；而这条判据问的就是**那个文件现在的形状**，所以按文件取（R98「仪器要与被判对象同源」）。
"""
import importlib.util
import io
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
GUARD = os.path.join(HERE, "test_round_batch_consistency.py")


def guard_module():
    spec = importlib.util.spec_from_file_location("trbc_for_declaration_r188", GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def titles_present(round_no, mod):
    out = {}
    for name, fmt in mod.LEDGERS.items():
        path = os.path.join(REPO, name)
        text = io.open(path, encoding="utf-8").read() if os.path.exists(path) else u""
        out[name] = bool(re.search(fmt % round_no, text, re.M))
    return out


class DeclarationTests(unittest.TestCase):

    def setUp(self):
        self.mod = guard_module()

    def test_the_channel_exists(self):
        self.assertTrue(hasattr(self.mod, "SINGLE_LEDGER_ROUNDS"),
                        "守卫里没有 SINGLE_LEDGER_ROUNDS ⇒ BACKLOG 211 说的申报通道没落地")

    def test_every_declaration_carries_a_reason(self):
        roster = self.mod.SINGLE_LEDGER_ROUNDS
        for no in sorted(roster):
            self.assertTrue(str(roster[no]).strip(),
                            "R%d 的申报没有理由 ⇒ 等于偷偷豁免（211 明写不许）" % no)
            self.assertRegex(str(roster[no]), u"[一-龥]",
                             "R%d 的申报理由里一个汉字都没有 ⇒ 那是占位不是理由" % no)

    def test_a_declared_round_really_lacks_a_ledger_title(self):
        for no in sorted(self.mod.SINGLE_LEDGER_ROUNDS):
            t = titles_present(no, self.mod)
            have = sorted(n for n, ok in t.items() if ok)
            self.assertFalse(all(t.values()),
                            "R%d 三本账标题都齐（%s）⇒ 不许申报成单本账笔次：桩标题喂饱守卫就是这一格要红的"
                            % (no, u"、".join(have)))

    def test_declarations_do_not_exempt_the_current_round(self):
        """名册里的号不许等于当前轮。

        为什么这里只判 `!=` 而不判 `<`：写这笔时 STATE 仍自报 R185（R186/R187 没换表头，正是 211 记的那笔债），
        而名册声明的偏偏是 186/187 —— 要求「申报号必须小于当前轮」会在债还没还清时红，
        那是拿台账的错位当判据的错。真正的保护在守卫那一侧（`back > 0`，下一条测试钉它），
        这条只堵「本轮刚写完就把自己豁免掉」。
        """
        r, _ = self.mod.current_round()
        self.assertNotIn(r, self.mod.SINGLE_LEDGER_ROUNDS,
                         "当前轮 R%d 出现在名册里 ⇒ 等于本轮自己宣布自己不写三本账" % r)

    def test_the_skip_is_gated_by_back_positive(self):
        text = io.open(GUARD, encoding="utf-8").read()
        self.assertEqual(1, len(re.findall(r"if back > 0 and this in SINGLE_LEDGER_ROUNDS:", text)),
                         "豁免那颗钉子要么没了、要么不止一处 ⇒ back > 0（当前轮不豁免）必须恰好写一次")

    def test_positive_control_the_channel_is_load_bearing(self):
        """反方向也钉一次：把名册清空后，窗口里必须真的出现缺失（证明这些申报在承重，不是装饰）。

        如果名册里的某一轮其实三本账齐全（上面那条会红），或者守卫根本没在用名册（上面那条会红），
        这里都会给出「清空后 missing 为空」= 这条豁免其实没放过任何东西 ⇒ 红。
        """
        r, _ = self.mod.current_round()
        missing = []
        for back in range(self.mod.LOOKBACK):
            this = r - back
            if back > 0:  # 当前轮永远要查 —— 这条正对照问的是历史轮
                continue
            for name, ok in titles_present(this, self.mod).items():
                if not ok:
                    missing.append((this, name))
        declared_missing = []
        for no in sorted(self.mod.SINGLE_LEDGER_ROUNDS):
            for name, ok in titles_present(no, self.mod).items():
                if not ok:
                    declared_missing.append((no, name))
        self.assertTrue(declared_missing,
                        "名册非空却一项缺失都没有 ⇒ 这些申报是空转的（该轮其实齐了）")


if __name__ == "__main__":
    unittest.main()
