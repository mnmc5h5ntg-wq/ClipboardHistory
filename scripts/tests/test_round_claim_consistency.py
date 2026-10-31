#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R340 / BACKLOG 405 的第二半：把回顾尺 `review_round_claims.py` 变成电池里**会红**的门。

为什么要有它（405 记的现读）：一轮通常有两笔以上（代码半 / 代码半补 / 账半 / 追记），
每笔标题都带着「第 N 轮 / Round M · 产品 K 文件」。这半句在**一轮内部**必须说同一件事
（K = 本轮的产品面文件数，`scripts/product_streak.py` 也是从"代码半"那一笔并集派生的），
可 R336 回顾时现读到两轮在自我打脸：R334 是 代码半=2 / 账半=0，R335 是 7 / 7 / 代码半补=0。
尺当时造好了，但**它只在人肯跑的那一步有效** —— 这就是 D-333 那条"回顾要有两种仪器"里
缺的第二种：窗口守卫。本文件就是那第二种。

判什么（四格，各拦一种坏法）：
  ① 正对照：合成的矛盾标题必须被 `leftovers` 点名 —— 否则这把尺今天看不见红；
  ② 名单不是免票：把例外名单清空之后，同一份合成数据必须**照样红**（R298 那一课的形状）；
  ③ 真历史：现行 subject 形状启用之后的每一轮，K 必须只有一个数，且没有"带 K 却没有轮次身份"的笔；
  ④ 每条豁免都要能在 `AGENT_BACKLOG.md` 里查到，且理由里必须写"什么时候删"。

它**不判**"这一轮的 K 与 git 派生的是否相同" —— 那一半是 `review_commit_claims.py` 与
`product_streak.py --check` 的活（同一件事只留一处权威）。
"""
import importlib.util
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"review_round_claims.py")
BACKLOG = os.path.join(ROOT, u"AGENT_BACKLOG.md")


def _load():
    spec = importlib.util.spec_from_file_location(u"review_round_claims", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)     # 脚本有 __main__ 闸门，import 不会跑 git
    return mod


R = _load()

# ── 例外名单：**只买"不红"，买不到"数对"**；每一条都要能在 BACKLOG 里查到，且写明退场 ──
CONTRADICTION_ROSTER = {
    u"334": u"R334 两笔给了两个 K（代码半=2 / 账半=0）。已 push 不能改历史 ⇒ 登记，BACKLOG 405。"
            u"退场：扫描窗滑过 R334 之后必须删这一条。",
    u"335": u"R335 的「代码半补」写 0（那一笔确实 0 个产品文件），而本轮的轮次级数是 7。"
            u"这正是 D-336 立定义之前两种语义并存的形状。已 push ⇒ 登记，BACKLOG 405。"
            u"退场：扫描窗滑过 R335 之后必须删这一条。",
    u"355": u"R355 的主笔写 产品 1 文件、追记写 产品 0 文件（那一笔确实 0 个产品文件）—— 已 push 不能改历史 ⇒ 登记，BACKLOG 405。"
            u"教训：产品轮的追记要么重复本轮的 K、要么不写 K（R356 的 U-1251）。"
            u"退场：扫描窗滑过 R355 之后必须删这一条。",
    u"498": u"R498 是 AGENT_STATE 的最后更新锚点，不是轮次身份：`SUBJECT` 用前导 `R<num>` 分组，"
            u"于是 05771dc（第 497 轮，K=1）、52f4172（第 502 轮，K=1）与 0beac05（第 505 轮，K=2）"
            u"被并成一组。已 push 不能改历史 ⇒ 登记，BACKLOG 611。"
            u"退场：`parse_rows` 改成优先读「第 N 轮」之后必须删这一条，并复跑本文件的正对照。",
}
UNPARSED_ROSTER = {
    u"fb2cea0": u"R339 那一笔的 subject 是旧形状 `Round 336: …（… 产品 3 文件…）`，"
                u"带着 K 却没有可解析的轮次身份 ⇒ 本尺看不见它（同一处自伤的第二次，"
                u"另一面记在 test_commit_subject_hygiene 的 NO_LABEL_ROSTER）。"
                u"登记理由：BACKLOG 416。退场：扫描窗滑过之后必须删。",
    u"3ebc7fc": u"R510 的产品笔标题中段带空格（`策略 + 最小窗…`），`SUBJECT` 的 `(\S+?)` 跨不过 ⇒ "
                u"带 K 却认不出轮次；已 push 不能改历史。登记理由：BACKLOG 616。"
                u"退场：`SUBJECT` 中段改成 `(.+?)` 并复跑合成正对照之后必须删这一条。",
    u"f85aa21": u"R519 的产品笔标题中段带空格（`GitHub 项目主页`），`SUBJECT` 的 `(\S+?)` 跨不过 ⇒ "
                u"带 K 却认不出轮次；已 push 不能改历史。登记理由：BACKLOG 616。"
                u"退场：`SUBJECT` 中段改成 `(.+?)` 并复跑合成正对照之后必须删这一条。",
}


def _roster_problems(roster, field, backlog_text):
    u"""纯函数：名单里每一条引用的 BACKLOG 号必须真存在；理由里必须写"退场"。"""
    out = []
    for key in sorted(roster):
        reason = roster[key]
        nums = re.findall(u"BACKLOG (\\d{2,4})", reason)
        if not nums:
            out.append((key, field, u"豁免理由没引用任何 BACKLOG 条目 ⇒ 自我批准"))
        for n in nums:
            if not re.search(u"(?m)^\\*\\*%s\\. " % n, backlog_text):
                out.append((key, field, u"理由引用的 BACKLOG %s 在台账里查不到" % n))
        if u"退场" not in reason:
            out.append((key, field, u"豁免没写退场条件 ⇒ 它会变成一条没人复查的放宽"))
    return out


def _real_window():
    # R501：扫描窗原来写死 `-n 400`，本轮累计提交把 cutoff（R334 的 5d1c246）挤出了窗外，
    # 于是 `slice_since` 抛「cutoff 不在 git log 里」。窗必须**由 cutoff 派生**而不是猜一个笔数：
    # 从 cutoff 的父提交到 HEAD 的闭区间，既保证起点可见，也不会把 cutoff 之前的老形状放进来。
    cutoff = R.SHAPE_CUTOFF
    log = subprocess.run([u"git", u"log", u"%s^..HEAD" % cutoff, u"--format=%H%x09%s"],
                         cwd=ROOT, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT).stdout.decode(u"utf-8", u"replace")
    window = R.slice_since(log)
    by_round, unparsed, scanned = R.parse_rows(u"\n".join(window))
    return by_round, unparsed, scanned


SYNTH = u"\n".join([
    u"aaaa111\tR900 代码半（第 899 轮 / Round 896 · 产品 7 文件，动效主线）：一句话",
    u"bbbb222\tR900 账半（第 899 轮 / Round 896 · 产品 0 文件，判据账）：一句话",
    u"cccc333\tRound 897: 旧形状的一笔（U-1…U-9 · 产品 3 文件，动效主线）",
    u"dddd444\tR901 代码半（第 900 轮 / Round 897 · 产品 2 文件，动效主线）：干净的一笔",
])


class RoundClaimConsistency(unittest.TestCase):
    def test_positive_control_names_a_contradiction_and_an_unparsed_subject(self):
        by_round, unparsed, scanned = R.parse_rows(SYNTH)
        self.assertEqual(4, scanned, u"四行带 TAB 的合成数据都要被扫到（少一行就是扫描器漏读）")
        bad = R.find_inconsistent(by_round)
        self.assertEqual([u"900"], [r[0] for r in bad],
                         u"R900 两笔给出 7 与 0 ⇒ 必须被点名（没点名就是尺坏了）")
        self.assertEqual([u"cccc333"], [u[0] for u in unparsed],
                         u"旧形状那笔带着「产品 3 文件」却没有轮次身份 ⇒ 必须进未识别，不许静默消失")
        left = R.leftovers(by_round, unparsed)
        self.assertEqual(2, len(left), u"名单空着的时候两条都必须红：%s" % (left,))
        self.assertEqual(sorted([u"ROUND_K_CONTRADICTION", u"K_WITHOUT_ROUND_IDENTITY"]),
                         sorted(x[1] for x in left))

    def test_the_roster_is_not_a_free_pass(self):
        u"""名单**只剔掉它点名的那一条**：登记了轮次矛盾，未识别那一笔必须还在红。"""
        by_round, unparsed, _ = R.parse_rows(SYNTH)
        only_round = R.leftovers(by_round, unparsed, ok_rounds=set([u"900"]), ok_shas=set())
        self.assertEqual([(u"cccc333", u"K_WITHOUT_ROUND_IDENTITY")],
                         [(x[0], x[1]) for x in only_round],
                         u"登记 R900 不该顺手放过没登记的 cccc333")
        both = R.leftovers(by_round, unparsed, ok_rounds=set([u"900"]),
                           ok_shas=set([u"cccc333"]))
        self.assertEqual([], both, u"两条都登记之后才该安静下来")
        # 反方向：把 sha 写错一个字符就必须照样红（名单是按身份对的，不是"有条目就行"）
        typo = R.leftovers(by_round, unparsed, ok_rounds=set([u"900"]),
                           ok_shas=set([u"cccc33x"]))
        self.assertEqual(1, len(typo), u"sha 打错一位还放过 ⇒ 名单成了橡皮图章：%s" % (typo,))

    def test_recent_rounds_do_not_contradict_themselves(self):
        by_round, unparsed, scanned = _real_window()
        self.assertGreaterEqual(scanned, 10,
                                u"扫描窗只 %d 笔 ⇒ 分母太小，这一格是空对账（R140）" % scanned)
        self.assertGreaterEqual(len(by_round), 3,
                                u"只认出 %d 轮 ⇒ 解析器或 cutoff 坏了，别把『没红』读成『没问题』"
                                % len(by_round))
        left = R.leftovers(by_round, unparsed,
                           ok_rounds=set(CONTRADICTION_ROSTER), ok_shas=set(UNPARSED_ROSTER))
        self.assertEqual([], [(a, b, c[:70]) for a, b, c in left],
                         u"现行 subject 形状之后仍有轮次自我打脸，或带 K 却认不出身份的笔")

    def test_the_cutoff_is_a_real_commit_and_a_bogus_one_raises(self):
        # R501：与 `_real_window` 同一个窗源（cutoff^..HEAD），不再用写死的笔数。
        log = subprocess.run([u"git", u"log", u"%s^..HEAD" % R.SHAPE_CUTOFF, u"--format=%H%x09%s"],
                             cwd=ROOT, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT).stdout.decode(u"utf-8", u"replace")
        window = R.slice_since(log)
        self.assertTrue(window[-1].startswith(R.SHAPE_CUTOFF),
                        u"窗起那一笔必须是 cutoff 本身，否则窗口是猜的")
        with self.assertRaises(ValueError):
            R.slice_since(u"1111111\tR1 代码半（第 1 轮 · 产品 0 文件）：x", cutoff=u"cafe1234")

    def test_exemptions_are_cited_in_the_ledger_and_can_expire(self):
        u"""豁免不许自我批准：每条都要引用一条**真存在**的 BACKLOG 条目，并写明退场。"""
        text = io.open(BACKLOG, encoding=u"utf-8").read()
        problems = (_roster_problems(CONTRADICTION_ROSTER, u"CONTRADICTION_ROSTER", text) +
                    _roster_problems(UNPARSED_ROSTER, u"UNPARSED_ROSTER", text))
        self.assertEqual([], problems,
                         u"每一条豁免都要引用一条真存在的 BACKLOG 条目并写明退场：%s" % (problems,))
        # 名单为空时上面那格恒不报 —— 那是对的（没有需要解释的东西）；
        # 但真历史那一格必须**仍然**扫到提交，否则"清空名单"就等于把门关掉（R298 同一课）。
        by_round, _, scanned = _real_window()
        self.assertGreaterEqual(len(by_round), 3,
                                u"扫描窗里没有轮次 ⇒ 这一格已经退化成恒真：%d 笔" % scanned)
        # 正对照：引用一个不存在的 BACKLOG 号，就必须被 `_roster_problems` 点名
        fake = _roster_problems({u"999": u"随便一条豁免，BACKLOG 999999。退场：永不过期"},
                                u"CONTRADICTION_ROSTER", text)
        self.assertEqual(1, len(fake), u"引用查无条目却没被抓住 ⇒ 这一格是只印不拦的读数：%s" % (fake,))
        # 正对照：没写退场的豁免也要被抓
        noexp = _roster_problems({u"999": u"引用 BACKLOG 405 但没写什么时候删"},
                                 u"CONTRADICTION_ROSTER", text)
        self.assertEqual(1, len(noexp), u"缺退场条件的豁免必须被点名：%s" % (noexp,))


if __name__ == u"__main__":
    unittest.main()
