# -*- coding: utf-8 -*-
"""R222 的守卫：最终报告的**标题格**必须与活账同源（它停过 R46 一次，U-264 记过；现在停在 R136）。

形状照 `test_final_report_claims.py`：把"报告说了什么"与"仓库现在是什么"分开成一个纯函数，
再用**伪造输入**证明它会红 —— 只印不拦的读数等于没有读数（R100）。
"""
import io
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
ITERATION = os.path.join(REPO, 'AGENT_VISUAL_ITERATION.md')
UI_AUDIT = os.path.join(REPO, 'AGENT_UI_AUDIT.md')


def read(path):
    return io.open(path, encoding='utf-8').read()


def live_counts():
    """活的对照数：从两本账自己读，不从报告读。"""
    it = read(ITERATION)
    rounds = [int(x) for x in re.findall(r'^## Round (\d+) · ', it, re.M)]
    ui = read(UI_AUDIT)
    u_ids = [int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)]
    return {
        'last_round': max(rounds),
        'u_max': max(u_ids),
    }


# 有界的落后，不是恒等：报告的刷新发生在**轮次台账之前**，写完台账它就又落后一轮。
# 所以这条守卫钉的是"不许落后超过一轮 / 一轮的 U 条目数"，而不是"必须逐字等于当下"。
# （第一版写的是恒等，结果本轮写完台账它自己就红了 —— 那是设计错，不是报告旧。）
LAG_ROUNDS = 1
LAG_U = 3


def headline_problems(text, live):
    """报告标题那一行与 §1 的两格，逐条对活账。返回 [(code, 说明)]。"""
    problems = []
    title = text.splitlines()[0] if text.splitlines() else ''
    m = re.search(r'R9–R(\d+)', title)
    if not m:
        problems.append(('FINAL_REPORT_TITLE_UNPARSEABLE',
                         u'标题里找不到 `R9–R<NNN>` 这一段形状 ⇒ 这一格无从对账'))
    else:
        claimed = int(m.group(1))
        if claimed > live['last_round']:
            problems.append(('FINAL_REPORT_HEADLINE_AHEAD',
                             u'标题写到 R%d，而 ITERATION 最新一节只有 Round %d ⇒ 报告在说一轮没发生的事'
                             % (claimed, live['last_round'])))
        elif live['last_round'] - claimed > LAG_ROUNDS:
            problems.append(('FINAL_REPORT_HEADLINE_STALE',
                             u'标题写到 R%s，而 AGENT_VISUAL_ITERATION 最新一节是 Round %d（允许落后 %d 轮）'
                             % (m.group(1), live['last_round'], LAG_ROUNDS)))
    u = re.search(r'U-31 … U-(\d+)', text)
    if not u:
        problems.append(('FINAL_REPORT_UCELL_UNPARSEABLE',
                         u'§1 里找不到 `U-31 … U-<NNN>` 那一格'))
    else:
        claimed_u = int(u.group(1))
        if claimed_u > live['u_max']:
            problems.append(('FINAL_REPORT_UCELL_AHEAD',
                             u'§1 的 U 上界写到 U-%d，而账里最大只有 U-%d' % (claimed_u, live['u_max'])))
        elif live['u_max'] - claimed_u > LAG_U:
            problems.append(('FINAL_REPORT_UCELL_STALE',
                             u'§1 的 U 上界写到 U-%s，而 AGENT_UI_AUDIT 里最大的是 U-%d（允许落后 %d 条）'
                             % (u.group(1), live['u_max'], LAG_U)))
    return problems


class FinalReportHeadlineTests(unittest.TestCase):
    """报告的标题格不许停在旧数（同一族在 U-264 记过一次，那次停在 R46）。"""

    def test_the_headline_cells_agree_with_the_live_ledgers(self):
        text = read(REPORT)
        live = live_counts()
        self.assertEqual([], headline_problems(text, live),
                         u'最终报告的标题格与活账不一致 ⇒ 见上面的说明')

    def test_a_stale_headline_is_named(self):
        """正对照：把标题改回旧值，守卫必须点名（改一个数它不响 ⇒ 这一格是假的）。"""
        text = read(REPORT)
        live = live_counts()
        forged = re.sub(r'R9–R\d+', u'R9–R%d' % (live['last_round'] - 7), text, count=1)
        self.assertNotEqual(forged, text, u'锚点漂了：标题里没有那一段形状')
        codes = [c for c, _ in headline_problems(forged, live)]
        self.assertIn('FINAL_REPORT_HEADLINE_STALE', codes)
        forged_u = re.sub(r'U-31 … U-\d+', u'U-31 … U-%d' % (live['u_max'] - 40), text, count=1)
        self.assertNotEqual(forged_u, text, u'锚点漂了：§1 里没有 U 那一格')
        self.assertIn('FINAL_REPORT_UCELL_STALE',
                      [c for c, _ in headline_problems(forged_u, live)])

    def test_an_unparseable_headline_is_red_not_silent(self):
        """反方向：形状被改掉（比如换了破折号）也不许静默通过。"""
        live = live_counts()
        codes = [c for c, _ in headline_problems(u'# 最终报告 · 没有那一段形状\n', live)]
        self.assertEqual(
            sorted(['FINAL_REPORT_TITLE_UNPARSEABLE', 'FINAL_REPORT_UCELL_UNPARSEABLE']),
            sorted(codes), u'读不到形状时给的是 %s ⇒ 不许当成通过' % codes)


if __name__ == '__main__':
    unittest.main()
