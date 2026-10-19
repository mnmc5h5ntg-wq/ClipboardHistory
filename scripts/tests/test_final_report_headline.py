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


# R235 补记 / BACKLOG 266 的那格：报告里「最后一次动到 Sources/ 的轮次」**以前只靠手抄**，
# 于是它停在 R205 连着九轮说假话（那期间动了 R225 / R230 / R234 / R235 四次源码），而标题闸门完全不管它。
# 现在把它接进同一支现读仪器：真相由 `git log` 给，报告只是**声称**，两边不符就红，并点名两边各是什么。
SOURCES_CELL = re.compile(u'最后一次动到 `Sources/` 的轮次.*?\\*\\*R(\\d+)\\*\\*（commit `([0-9a-f]{7,40})`）')
SOURCES_PATH = u'ClipboardHistory/Sources'


def live_sources(n=1):
    """最近 n 笔动到源码的提交 [(sha, R 或 None, subject)]；git 不在/读不到就抛（不许静默通过）。"""
    import subprocess
    out = subprocess.Popen(
        ['git', '-C', REPO, 'log', '-%d' % n, '--format=%h%x09%s', '--', SOURCES_PATH],
        stdout=subprocess.PIPE).communicate()[0].decode('utf-8', 'replace')
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition(u'\t')
        m = re.search(u'（R(\\d+)', subject) or re.search(u'\\bR(\\d+)', subject)
        rows.append((sha.strip(), int(m.group(1)) if m else None, subject))
    return rows


def sources_problems(text, rows):
    problems = []
    c = SOURCES_CELL.search(text)
    if not c:
        problems.append(('FINAL_REPORT_SOURCES_CELL_UNPARSEABLE',
                         u'报告里读不到「最后一次动到 Sources/ 的轮次」那一格的 **R<NNN>**（commit `<sha>`）形状 ⇒ 这一格无从对账'))
        return problems
    claimed_round, claimed_sha = int(c.group(1)), c.group(2)
    if not rows:
        problems.append(('FINAL_REPORT_SOURCES_LIVE_EMPTY',
                         u'`git log -- %s` 一笔都没读到 ⇒ 对照数是空的，不许当成通过' % SOURCES_PATH))
        return problems
    live_sha, live_round, subject = rows[0]
    if not claimed_sha.startswith(live_sha[:7]) and not live_sha.startswith(claimed_sha[:7]):
        problems.append(('FINAL_REPORT_SOURCES_CELL_STALE',
                         u'那一格写 commit `%s`，而 git 说最近动源码的是 `%s`（%s）⇒ 动过源码却没刷这张格'
                         % (claimed_sha, live_sha, subject[:48])))
    elif live_round is None:
        problems.append(('FINAL_REPORT_SOURCES_COMMIT_ROUND_UNPARSEABLE',
                         u'最近那笔源码提交 `%s` 的标题里读不出 R 号 ⇒ 只能对 sha、对不了轮次：%s'
                         % (live_sha, subject[:48])))
    elif claimed_round != live_round:
        problems.append(('FINAL_REPORT_SOURCES_CELL_STALE',
                         u'那一格写 R%d，而 commit `%s` 的标题说自己属于 R%d ⇒ 两边有一边抄错'
                         % (claimed_round, live_sha, live_round)))
    return problems


class FinalReportSourcesCellTests(unittest.TestCase):
    """这一格是纯手抄、没有 LAG 容差挡着 ⇒ 必须逐字对 git。"""

    def test_the_sources_cell_agrees_with_git(self):
        self.assertEqual([], sources_problems(read(REPORT), live_sources(3)),
                         u'「最后一次动到 Sources/ 的轮次」与 git 不同源')

    def test_a_stale_sources_cell_is_named(self):
        """正对照：把 sha 换成**上一笔**动源码的提交 ⇒ 必须点名（换个数它不响 ⇒ 这一格是假的）。"""
        rows = live_sources(3)
        if len(rows) < 2:
            self.skipTest(u'仓库里动到 Sources 的提交不足两笔 ⇒ 这一格造不出对照')
        text = read(REPORT)
        stale = SOURCES_CELL.sub(u'最后一次动到 `Sources/` 的轮次 **R0**（commit `%s`）' % rows[1][0], text, count=1)
        self.assertNotEqual(stale, text, u'锚点漂了：报告里没有那一格')
        codes = [c for c, _ in sources_problems(stale, rows)]
        self.assertIn('FINAL_REPORT_SOURCES_CELL_STALE', codes)
        missing = SOURCES_CELL.sub(u'最后一次动到 Sources 的轮次（这一格故意没有形状）', text, count=1)
        self.assertIn('FINAL_REPORT_SOURCES_CELL_UNPARSEABLE',
                      [c for c, _ in sources_problems(missing, rows)],
                      u'形状被改掉时不许静默通过')


if __name__ == '__main__':
    unittest.main()
