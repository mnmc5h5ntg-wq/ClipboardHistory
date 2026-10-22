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
STATE = os.path.join(REPO, 'AGENT_STATE.md')
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


def round_from_subject(subject):
    """从 commit 标题抠归属轮次：**开头的徽章说了算**，正文里的引用不算。

    为什么单独做成一个函数并配已知答案的格子：R260 的标题是
    `R260 代码半（第 259 轮 / Round 257）：…（R259 自己写下的形状警告）…`，
    旧顺序先找 `（R(\\d+)` ⇒ 它先撞上正文里那句引用，把这笔提交说成属于 R259，
    于是「最后一次动到 Sources/ 的轮次」这一格红在一张**没写错**的账上。
    引用赢过署名，是尺的错，不是账的错。
    """
    m = (re.match(u'^R(\\d+)', subject) or re.search(u'（R(\\d+)', subject)
         or re.search(u'\\bR(\\d+)', subject))
    return int(m.group(1)) if m else None


def live_sources(n=1, repo=None):
    """最近 n 笔动到源码的提交 [(sha, R 或 None, subject)]；git 不在/读不到就抛（不许静默通过）。"""
    import subprocess
    out = subprocess.Popen(
        ['git', '-C', repo or REPO, 'log', '-%d' % n, '--format=%h%x09%s', '--', SOURCES_PATH],
        stdout=subprocess.PIPE).communicate()[0].decode('utf-8', 'replace')
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition(u'\t')
        rows.append((sha.strip(), round_from_subject(subject), subject))
    return rows


def is_shallow(repo=None):
    """仓库是不是浅clone（浅 ⇒ 边界提交的 diff 对着空树，路径历史不可解析）。读不出就抛，不许静默通过。"""
    import subprocess
    out = subprocess.Popen(
        ['git', '-C', repo or REPO, 'rev-parse', '--is-shallow-repository'],
        stdout=subprocess.PIPE).communicate()[0].decode('utf-8', 'replace').strip()
    if out not in (u'true', u'false'):
        raise RuntimeError(u'`git rev-parse --is-shallow-repository` 读出 %r ⇒ 历史深度无从判定' % out)
    return out == u'true'


def sources_gate(shallow, rows, text, round_n=None):
    """把"这一格能不能判"和"判出来是什么"分成两句说（R242 / BACKLOG 278）。

    浅历史上 `git log -- <路径>` 只会给边界那一笔，而那一笔的 diff 对着空树 ⇒ 它**必然**被读成
    「最近动过 Sources/ 的提交」。于是 STALE 这句话在浅 clone 上没有对象：既不能说台账错了，
    也不能说它对了，只能具名 skip。返回 ('skip', 原因) 或 ('judge', problems)。
    """
    if shallow:
        return ('skip', u'浅clone（fetch-depth=1）里路径历史不可解析 ⇒ HEAD 会被读成答案，'
                        u'这一格在 runner 上没有对象（ci.yml 已改 fetch-depth: 50）')
    return ('judge', sources_problems(text, rows, round_n))


def ledger_round(repo=None):
    """台账当前的最大节号（`AGENT_UI_AUDIT.md` 的「## 第 N 轮」）。读不到就抛，不许静默放行。"""
    import io as _io
    import os as _os
    path = _os.path.join(repo or REPO, "AGENT_UI_AUDIT.md")
    with _io.open(path, encoding="utf-8") as h:
        found = [int(x) for x in re.findall(u"(?m)^## 第 (\\d+) 轮", h.read())]
    if not found:
        raise RuntimeError(u"%s 里解析不到任何「## 第 N 轮」节 ⇒ as-of 口径没有参照" % path)
    return max(found)


def as_of(rows, round_n):
    """第 round_n 轮的那一格该对哪一笔提交：标签 ≤ round_n 的**最近一笔**动过源码的提交。

    为什么必须有这一层（R300 现读，与 355 同一族）：本仓库一轮常拆成"代码半 + 台账半"两笔，
    代码半先落地时 `git log -1 -- Sources` 已经指向**下一轮**那一笔，而台账最大节还停在上一轮。
    拿"此刻最新"去判上一轮写对的格，会把没写错的账判成 STALE —— 于是每次动产品都必须在
    "写台账之前"那一跑里红着，或者逼着人把两半塞成一笔。改成 as-of 之后两半谁先落都不红。

    `round_n` 与 `rows` 里的标签**同为 R 号**（调用方负责把「第 N 轮」换成 R 号：R_n = 第 n−1 轮）。
    """
    picked = [(sha, label, subject) for sha, label, subject in rows
              if label is not None and label <= round_n]
    return picked[0] if picked else None


def sources_problems(text, rows, round_n=None):
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
    if round_n is not None:
        picked = as_of(rows, round_n)
        if picked is None:
            return [(u'FINAL_REPORT_SOURCES_NO_COMMIT_AS_OF',
                     u'标签 ≤ 第 %d 轮的源码提交一笔都没有 ⇒ as-of 口径没有分界，'
                     u'这一格不许拿"此刻最新"凑数' % round_n)]
        rows = [picked] + [r for r in rows if r is not picked]
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

    def test_the_commit_badge_wins_over_a_citation_in_the_subject(self):
        """已知答案的三格：归属号必须来自**开头的徽章**，正文里的引用不许赢过署名。

        这一格是 R260 现读撞上的：标题写成 `R260 代码半（第 259 轮 / Round 257）：…（R259 自己写下的…）`，
        旧尺先找 `（R(\\d+)` ⇒ 撞上正文里那句引用，把一笔 R260 的提交判成 R259，
        于是这张格红在一份**没写错**的账上。修法是排优先级，不是把账改回去。
        """
        self.assertEqual(260, round_from_subject(
            u'R260 代码半（第 259 轮 / Round 257）：亮档按下与选中糊成一档 —— 尺的按步骤切片同笔落地（R259 自己写下的形状警告）'))
        self.assertEqual(253, round_from_subject(u'R253（第 252 轮 / Round 250）：抬量'))
        self.assertEqual(242, round_from_subject(u'收尾：（R242 新开）'))   # 没有开头徽章时才退到旧形状
        self.assertIsNone(round_from_subject(u'没有轮次徽章的一笔'))

    def test_the_sources_cell_agrees_with_git(self):
        # 40 笔而不是 3 笔：as-of 口径要能往回找到"标签 ≤ 台账最大节"的那一笔
        # 单位换算要说死：本仓库 R_n = 第 n−1 轮（STATE 的标题行就是这么配的），
        # 而 `AGENT_UI_AUDIT.md` 的节号是「第 N 轮」，git 那侧的标签是 R 号 ⇒ as-of 要拿 R 号比。
        shallow, rows, round_n = is_shallow(), live_sources(40), ledger_round() + 1
        # 结论行排在能力闸门之前（R85：闸门先响就没有读数可读了）
        mode, detail = sources_gate(shallow, rows, read(REPORT), round_n)
        print(u'SOURCES_CELL_HISTORY 浅=%s 对照数=%d 头笔=%s as_of第%d轮=%s 处置=%s'
              % (shallow, len(rows), rows[0][0] if rows else u'无', round_n,
                 (as_of(rows, round_n) or (u'无',))[0], mode))
        if mode == 'skip':
            self.skipTest(u'%s —— 这一格在浅历史上不许给台账定罪（BACKLOG 278）' % detail)
        self.assertEqual([], detail, u'「最后一次动到 Sources/ 的轮次」与 git 不同源：%s' % detail)

    def test_as_of_ignores_a_commit_from_a_round_the_ledger_has_not_reached(self):
        """正对照：代码半先落地时，"此刻最新"那一笔属于**还没写账**的那一轮 ⇒ 不许拿它判上一轮的格。

        两半各判一次：as-of 上一轮 ⇒ 账是对的（无 problems）；as-of 到那一笔自己的轮次 ⇒ 必须 STALE。
        这一格钉的就是 R300 撞到的那个形状：不改成 as-of，每次动产品都会"写台账之前必然红一次"。
        """
        ahead = (u'aaa1111', 299, u'R300 代码半（第 299 轮 / Round 297）：动了产品')
        old = (u'2f8b1e0', 290, u'R290 代码半（第 289 轮 / Round 287）：上一笔产品改动')
        rows = [ahead, old]
        cell = (u'| 最后一次动到 `Sources/` 的轮次 | **R290**（commit `2f8b1e0`）—— 现读 1 个文件。|')
        self.assertEqual([], sources_problems(cell, rows, 298),
                         u'as-of 第 298 轮时，账写 R290 是对的，却被判成 STALE ⇒ 过滤没生效')
        detail = sources_problems(cell, rows, 299)
        self.assertEqual(1, len(detail), u'as-of 到第 299 轮却不判这张格 ⇒ 这一格被写成了恒真')
        self.assertEqual(u'FINAL_REPORT_SOURCES_CELL_STALE', detail[0][0], detail)
        # 一笔都挑不出来时必须响，不许退回"此刻最新"
        self.assertEqual([u'FINAL_REPORT_SOURCES_NO_COMMIT_AS_OF'],
                         [k for k, _ in sources_problems(cell, rows, 100)])

    def test_a_shallow_history_must_not_be_allowed_to_judge(self):
        """浅历史是**真造一颗合成小仓库**判的（`git init` + 两笔 + `file://` 上 `--depth 1` 克隆），
        不是嘴上说说：那种历史上只读到边界那一笔，而边界那笔**根本没动源码**却被报成"最近动过
        Sources/ 的提交" ⇒ 「STALE」在浅历史上只能是尺的假话。
        闸门那一支被摘掉（`if shallow:` 变恒假）时这一格必须红（M801 就是这一刀）。
        两边各判一次：全历史的 origin 必须判得出"只有一笔动过源码"，浅克隆必须只读到 HEAD。
        （第一版是克隆本仓库 —— `.git` 220 MB，一格把电池拖成 4 分钟，才改成合成仓库。）"""
        import subprocess, tempfile, shutil, os
        devnull = open(os.devnull, 'wb')
        d = tempfile.mkdtemp(prefix='sources_shallow_')
        try:
            origin = os.path.join(d, 'origin')
            os.makedirs(os.path.join(origin, SOURCES_PATH))
            os.makedirs(os.path.join(origin, 'ClipboardHistory', 'Docs'))

            def git(root, *args):
                subprocess.check_call(['git', '-C', root] + list(args),
                                      stdout=devnull, stderr=devnull)
            git(origin, 'init', '-q')
            git(origin, 'config', 'user.email', 'x@x.invalid')
            git(origin, 'config', 'user.name', 'x')
            io.open(os.path.join(origin, SOURCES_PATH, 'a.swift'), 'w', encoding='utf-8').write(u'1\n')
            git(origin, 'add', '-A')
            git(origin, 'commit', '-q', '-m', u'第一笔（R1）：动了源码')
            io.open(os.path.join(origin, 'ClipboardHistory', 'Docs', 'n.md'), 'w',
                    encoding='utf-8').write(u'只动文档\n')
            git(origin, 'add', '-A')
            git(origin, 'commit', '-q', '-m', u'第二笔（R2）：一笔都没动源码')
            self.assertFalse(is_shallow(origin), u'刚造的对照仓库应当是全历史')
            full = live_sources(3, origin)
            print(u'SOURCES_CELL_SYNTH 全历史对照数=%d 头笔标题=%s'
                  % (len(full), full[0][2][:20] if full else u'无'))
            self.assertEqual(1, len(full),
                             u'全历史下「动过源码的提交」只该读到第一笔，读到 %s ⇒ pathspec 没生效' % full)
            self.assertEqual(1, full[0][1], u'第二笔没动源码，头笔的轮次应当是 R1：%s' % (full,))

            shallow = os.path.join(d, 'shallow')
            subprocess.check_call(['git', 'clone', '--depth', '1', '-q', 'file://' + origin, shallow],
                                  stdout=devnull, stderr=devnull)
            self.assertTrue(is_shallow(shallow),
                            u'`git clone --depth 1` 造出来的居然不是浅仓库 ⇒ 这一格没有对象'
                            u'（走本地路径会被忽略，必须 file://）')
            rows = live_sources(3, shallow)
            head = subprocess.Popen(['git', '-C', shallow, 'rev-parse', '--short=7', 'HEAD'],
                                    stdout=subprocess.PIPE).communicate()[0].decode().strip()
            print(u'SOURCES_CELL_SHALLOW 对照数=%d 头笔=%s HEAD=%s（HEAD 那一笔其实没动源码）'
                  % (len(rows), rows[0][0] if rows else u'无', head))
            self.assertEqual(1, len(rows), u'浅历史上只该读到边界那一笔：%s' % (rows,))
            self.assertEqual(head, rows[0][0],
                             u'浅历史上「最近动源码的提交」应当恰好是 HEAD —— 若不是，'
                             u'下面那条 skip 保护的就不是同一件事')
            mode, detail = sources_gate(True, rows, read(REPORT))
            self.assertEqual('skip', mode,
                             u'浅历史仍去判（%s）⇒ 这一格会对台账说假话' % (detail,))
            mode_full, detail_full = sources_gate(False, live_sources(3, origin), read(REPORT))
            self.assertEqual('judge', mode_full, u'全历史上这一格必须有处置，不许一律 skip')
        finally:
            devnull.close()
            shutil.rmtree(d, ignore_errors=True)

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

NOTE_RX = re.compile(u"（R\\d+ 现读抬到最新一节）")
STILL_OPEN_RX = re.compile(u"(?m)^- \\*\\*仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 (R\\d+) 节 ② 为准）\\*\\*")


def count_derivation_notes(line):
    """U 格那一行里有几条「（Rnnn 现读抬到最新一节）」注记。"""
    return len(NOTE_RX.findall(line))


class LedgerPointerTests(unittest.TestCase):
    """R303：报告里两处**指针**必须各自指向当下，而不是每轮再贴一张贴纸。

    本轮量到的两种坏法都是我自己写的生成器造成的：
    ① §1 的 U 格每轮 `re.subn(u"U-31 … U-\\d+", ...)` 只吃数字，括号里的派生注记留在那里，
       于是攒成「（R303 现读…）（R302 现读…）（R301 现读…）」五连 —— 数字是对的，句子是烂的；
    ② §13 的「仍开（…以 `AGENT_STATE.md` 的 Rnnn 节 ② 为准）」指针，本轮因为一次按行号的
       手术把 `PREV_TAG → R_TAG` 那行 re.sub 切掉了 ⇒ 报告指着**上一轮**的 STATE 节。
    两条都是「账看起来更新过，其实指向过期对象」——比没更新更坏（R88 那一族）。
    """

    def test_positive_control_two_notes_are_counted_not_eyeballed(self):
        self.assertEqual(2, count_derivation_notes(
            u"U-31 … U-994（R303 现读抬到最新一节）（R302 现读抬到最新一节）"))
        self.assertEqual(1, count_derivation_notes(u"U-31 … U-994（R303 现读抬到最新一节）"))
        self.assertEqual(0, count_derivation_notes(u"U-31 … U-994"))

    def test_the_u_cell_carries_exactly_one_derivation_note(self):
        text = io.open(REPORT, encoding=u"utf-8").read()
        hits = [l for l in text.split(u"\n") if u"U-31 … U-" in l]
        self.assertEqual(1, len(hits), u"U 格那一格应当只在 §1 出现一次，读到 %d 处" % len(hits))
        self.assertEqual(1, count_derivation_notes(hits[0]),
                         u"§1 的 U 格上堆了多条派生注记 ⇒ 生成器的替换不是幂等的：" + hits[0][:120])

    def test_still_open_bullet_points_at_the_newest_state_section(self):
        text = io.open(REPORT, encoding=u"utf-8").read()
        m = STILL_OPEN_RX.search(text)
        self.assertIsNotNone(m, u"读不到 §13 的「仍开（…为准）」bullet 标签形状 ⇒ 这一格无从判定，红")
        state = io.open(STATE, encoding=u"utf-8").read()
        newest = (re.findall(u"(?m)^## (R\\d{3}) 状态", state) or [None])[0]
        self.assertIsNotNone(newest, u"STATE 里读不到任何 `## Rnnn 状态` 节")
        self.assertEqual(newest, m.group(1),
                         u"§13 的仍开名单指着 %s 节，而 STATE 最新一节是 %s ⇒ 指针过期，"
                         u"读者会去翻上一轮的账" % (m.group(1), newest))

