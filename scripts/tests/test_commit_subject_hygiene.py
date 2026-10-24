#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R297 / BACKLOG 348：给「写台账与提交」这件事本身装一格会红的对账。

为什么要有这一支（都是本轮**真栽过**的三种形态，不是假想）：

· `c7b952f` 的 commit subject 被一个写坏的 heredoc 咬了 —— 正文里混进 `<<'EOF' PLACEHOLDER EOF )`，
  树是对的、消息是垃圾，而**没有任何判据会红**。
· 同一轮往 `AGENT_BACKLOG.md` 追加追记，第一次因 heredoc 里的 python 没带 `PYTHONUTF8=1` 而整批
  SyntaxError 拒绝 —— 脚本电池那一步**仍然绿**，因为它不读那一格。「台账没写上」与「台账写对了」同形。
· 再一轮把轮次号写成 296/294，会让曲线跳号；台账里的轮次标签靠手抄，抄错了没人管（R271 那一课）。

这一支只管**提交消息**那一格（其余两格记在 348 里，由后续轮补）：
① 不许有 heredoc 残渣；② subject 里的轮次标签必须与 `AGENT_STATE.md` 现读的当前轮同源
（允许是当前轮或往前数两轮，因为代码半与账半常跨笔），不许是一个平空出现的数。

判据形状：先跑**纯函数** `check()`，正对照喂它一条伪造消息（不许拿被搜的串自己拼正则那条老坑：
伪造串与判据读的是同一个量），再跑真历史。基线 `BASELINE` 必须在最近 15 笔里找得到 ——
找不到就红（证据指针不许指不到东西，R140 那一族）。
"""
import io
import os
import re
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 基线 = 装这门之前的一笔；只查它**之后**的提交。
# R298 现读的腐烂：这条原本写 `b1b43da`，落地不到一天就滑出了 15 笔窗口 ⇒ 两格红（基线找不到 + 扫描没有对象）。
# 这不是判据错了，是**窗口长度与提交速率**没对上：本仓库一轮常出 3~8 笔，15 笔撑不过两天。
# 因此基线要按轮轮换（每轮台账落地时把它推到本轮第一笔），而「基线不在窗口内」必须继续红而不是静默放行 ——
# 这一格本身就是 348 的第四格：锚点腐烂的检测已经有了，缺的是自动轮换（记在 348 追记里）。
# 基线**不写死 sha**：写死就会腐烂 —— 今天实测，`b1b43da` 落地不到一天滑出 15 笔窗口，两格红 + 一条级联红
# （本仓库一轮常出 3~8 笔，固定窗口撑不过两天）。改成自定位：基线 = **引入这一支判据的那一笔提交**，
# 扫描范围是「它自己 + 之后所有笔」。这样窗口永远跟着判据的生日走，既不腐烂也不空转，
# 而「扫不到任何一笔」仍然会红（生日那一笔至少要在，缺了说明尺坏了）。
THIS_FILE = os.path.basename(__file__)


def round_at(sha):
    """那一笔提交**自己的树**里 STATE 的当前轮（STATE 新轮在上 ⇒ 取第一个匹配）。

    不许退回工作树：工作树只有一份，历史里的每一笔都得向它对齐，那就是拿今天的尺量昨天的笔。
    """
    out, rc = git(u"show", sha + u":AGENT_STATE.md")
    if rc != 0:
        return None
    found = STATE_LINE.findall(out)
    return int(found[0]) if found else None


def baseline_sha():
    out, rc = git(u"log", u"--diff-filter=A", u"--format=%H", u"--reverse", u"--",
                  u"scripts/tests/" + THIS_FILE)
    self_ok = rc == 0 and out.split()
    if not self_ok:
        return None
    return out.split()[0]


BASELINE = None  # 运行时由 baseline_sha() 现取；留着这个名字给读代码的人一个线索


def birth_short():
    sha = baseline_sha()
    return None if sha is None else sha[:7]


def scan_args():
    """扫描范围 = 判据生日那一笔（含）之后。生日之前不判（那时这门还不存在）。"""
    sha = baseline_sha()
    if sha is None:
        return None
    return [u"log", u"--format=%h%x00%s", sha + u"~1..HEAD"]
# 在册例外：**只能登记「标签比台账新」的那一类**（代码半先于轮次账），每条都要写清由哪一轮补账。
# 这一格故意要求名单**恰好等于**实际命中的那些 sha —— 多一笔未登记的超前标签仍然红，
# 而在册的那笔若哪天不再出现在扫描范围里也不会被忘记（放宽必须成对，R74 那一课）。
AHEAD_ROSTER = {
    # R324 现读（BACKLOG 382）：07acf2e 是 R324 的代码半，而它自己的树里 STATE 的当前轮仍是 R322 ——
    # 根因不是手抄，是 R323 那一节整节没写 identity 行（`^最后更新：…（本地 · R<NNN>`），
    # 于是 current_round() 静默停了一轮，把这一笔从「超前 1（设计允许）」推成「超前 2（该红）」。
    # 同笔已补写 R323 的 identity 行并要求 R324 起必带；这条豁免按 sha 键，扫描窗滑过就必须删（test_roster_must_retire）。
    u"07acf2e": u"R324 代码半先于轮次账（根因：R323 的 STATE 节缺 identity 行，BACKLOG 382）",
}
# 在册例外（**第二张**）：已 push、历史改不了的"subject 里根本没有轮次标签"。
# 为什么不并进 `AHEAD_ROSTER`：那张只给"标签比台账新"这一类（代码半先于轮次账），
# 混在一张里，"这条豁免只买得到代码半"那句约束就没了 —— 两类违规的**退场条件**也不同：
# 超前标签在台账落地后自动消失，而无标签的笔只能等扫描窗滑过。
# R334 现读：117f45d（R333 代码半）照的是 Skill 里那份过期形状 `Round 330: …`，
# 既没有 `R<NNN>` 也没有「第 N 轮」⇒ `COMMIT_SUBJECT_NO_ROUND` + `product_streak` 同时红。
# 已 push ⇒ 不许 amend、不许 force-push（那是替别人重写历史）⇒ 只能登记（BACKLOG 398）。
NO_LABEL_ROSTER = {
    u"117f45d": u"R333 代码半的 subject 没有轮次标签（照的是 Skill 里过期的 `Round <r>:` 形状）；"
                u"已 push 不能改历史 ⇒ 登记豁免，BACKLOG 398。"
                u"退场：扫描窗滑过这笔之后必须删（`product_streak` 那一半由下一笔产品提交自动治好）",
}

# 名单已清空（R298 台账落地 ⇒ 当前轮就是 R298，那两笔超前标签不再需要豁免）。
# 这一格要求：名单为空时 `test_recent_subjects_are_clean` 仍必须真扫到提交（它扫的是区间里的每一笔，
# 不是「名单空 ⇒ 跳过」），否则清空名单就等于把门一起关掉。
RESIDUE = [u"<<'EOF'", u"<<-EOF", u"PLACEHOLDER", u"EOF )", u"EOF)"]
STATE_LINE = re.compile(u"^最后更新：\\d{4}-\\d{2}-\\d{2}（本地 · R(\\d+)", re.M)


def git(*args):
    proc = subprocess.Popen([u"git"] + list(args), cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.communicate()[0].decode(u"utf-8", u"replace"), proc.returncode


def roster_problems(roster, backlog_text):
    """纯函数：每一条具名豁免都必须能在 BACKLOG 里被查得到。

    为什么需要这一格（R298 现读的教训）：豁免名单是我自己写的，写进测试文件就等于「自我批准」——
    没有第二处账，下一轮加一条豁免时没人看得见它被谁批过。要求每条 sha 在 `AGENT_BACKLOG.md`
    里出现一次，就是让放宽必须留下**人类会读的那份**痕迹（R74：放宽要成对；D-279：豁免要能退场）。
    名单为空时这里恒不报（那是对的：没有需要解释的东西），但正对照那一格保证机制不是空的。
    """
    out = []
    for sha in sorted(roster):
        if sha not in backlog_text:
            out.append((sha, u"ROSTER_NOT_IN_LEDGER",
                        u"豁免在册但 BACKLOG 里查不到这笔 sha ⇒ 放宽没有人类可读的登记"))
    return out


def check(messages, rounds, window=2, ahead_allowed=1):
    """返回问题列表（空 = 干净）。纯函数：判据与正对照走同一条路。

    `rounds` 是 sha → **那一笔提交当时**的当前轮（R299 现读的腐烂：原来这里收一个全局 current_round，
    而扫描范围从判据生日一路到 HEAD，于是每推一轮，历史里那些「R296 代码半」就自动变成超前/落后的假红 ——
    拿今天的尺量昨天的笔，红的是尺。改成按笔取轮：每笔与**它自己那一棵树里的 STATE** 对账）。
    收 int 也可以（正对照与合成用例走这条路）：那种情况下所有行都用同一个轮次。
    """
    problems = []
    for sha, subject in messages:
        current_round = rounds if isinstance(rounds, int) else rounds.get(sha)
        if current_round is None:
            problems.append((sha, u"COMMIT_SUBJECT_ROUND_UNKNOWN",
                             u"取不到那一笔提交当时的当前轮 ⇒ 这一格不许静默放行（算不出来必须响，R102）"))
            continue
        for needle in RESIDUE:
            if needle in subject:
                problems.append((sha, u"COMMIT_SUBJECT_HEREDOC_RESIDUE",
                                 u"subject 里有 heredoc 残渣「%s」：%s" % (needle, subject[:80])))
        m = re.search(u"R(\\d{2,4})", subject)
        if not m:
            # 只有**登记过**的 sha 能走这条路（`test_roster_entries_must_be_registered_in_the_ledger`
            # 要求每条都在 BACKLOG 里查得到，而正对照 `cafe1234` 不在任何名单里、照样红）。
            if sha in NO_LABEL_ROSTER:
                continue
            problems.append((sha, u"COMMIT_SUBJECT_NO_ROUND",
                             u"subject 里没有轮次标签 R<NNN>：" + subject[:80]))
            continue
        claimed = int(m.group(1))
        # 方向规矩（R299 现读，两笔 f78b6ac / efeca29 是证人）：**代码半常先于本轮的轮次账** ——
        # 那一笔自己的 STATE 还停在上一轮，而 subject 已经写本轮，这是本仓库的既有形状，不是手抄错。
        # 所以往前只许 1 轮（本轮），往后允许 window 轮（补记与台账半）。
        # 这条不是豁免名册：它是一条有方向的界，写错成 R7 / R999 照样红（正对照钉着）。
        if not (current_round - window <= claimed <= current_round + ahead_allowed):
            if sha in AHEAD_ROSTER:
                continue      # 在册例外：代码半先于轮次账，由 AHEAD_ROSTER 那一格要求它退场
            problems.append((sha, u"COMMIT_SUBJECT_ROUND_OFF",
                             u"subject 写 R%d，而那一笔自己的 STATE 里当前轮是 R%d"
                             u"（只许超前 %d 轮、落后 %d 轮）⇒ 标签是手抄的"
                             % (claimed, current_round, ahead_allowed, window)))
    return problems


class CommitSubjectHygiene(unittest.TestCase):
    def test_positive_control_has_teeth(self):
        """正对照：残渣与平空轮次标签都必须被点名 —— 否则这一支是只印不拦的读数。"""
        bad = [(u"deadbeef", u"R999 修一处东西 <<'EOF' PLACEHOLDER EOF )"),
               (u"cafe1234", u"这一笔没有轮次标签"),
               (u"beef5678", u"R7 台账落盘")]
        found = check(bad, 296)
        kinds = sorted(set(k for _, k, _ in found))
        self.assertEqual([u"COMMIT_SUBJECT_HEREDOC_RESIDUE", u"COMMIT_SUBJECT_NO_ROUND",
                          u"COMMIT_SUBJECT_ROUND_OFF"], kinds, found)
        # 按笔取轮那条路也要有牙：拿今天的当前轮去判历史笔会假红，而**读不到当时的轮**必须红。
        hist = [(u"aa000001", u"R296 代码半：某处修法")]
        self.assertEqual([], check(hist, {u"aa000001": 298}),
                         u"历史笔与它自己当时的轮（298）同域，却被今天的尺判成红 ⇒ 按笔取轮没生效")
        self.assertEqual([(u"aa000001", u"COMMIT_SUBJECT_ROUND_UNKNOWN")],
                         [(sha, kind) for sha, kind, _ in check(hist, {u"aa000001": None})],
                         u"读不到当时的当前轮却静默放行 ⇒ 这一格没有对象也算绿（不许）")
        # 界本身要有方向：超前 1 轮合法（代码半先于轮次账），超前 2 轮必须红。
        self.assertEqual([], check([(u"aa000002", u"R299 代码半")], {u"aa000002": 298}),
                         u"代码半那笔超前一轮被拦 ⇒ 这条界与本仓库的落盘顺序不符")
        self.assertEqual([(u"aa000003", u"COMMIT_SUBJECT_ROUND_OFF")],
                         [(sha, kind) for sha, kind, _ in check([(u"aa000003", u"R301 代码半")],
                                                               {u"aa000003": 298})],
                         u"超前 3 轮却放行 ⇒ 把界写成免检了")

    def test_clean_subjects_pass_the_same_function(self):
        good = [(u"aaaa1111", u"R296 轮次台账（第 295 轮 / Round 293）补齐"),
                (u"bbbb2222", u"R295 起步：给 pillReading 的盲区装一颗能红的牙")]
        self.assertEqual([], check(good, 296))

    def test_roster_must_retire(self):
        """在册的豁免必须仍然用得上：它的 sha 若已不在扫描范围内，这条豁免就该被删掉。

        放宽不许留着不退场（R74：放宽要成对）—— 否则扫描窗口滑过去之后，这一格会变成
        一条永久有效的空白豁免，下一笔超前标签就能借它蒙过去。
        """
        if not AHEAD_ROSTER and not NO_LABEL_ROSTER:
            return
        args = scan_args()
        self.assertIsNotNone(args, u"判据的生日提交查不到 ⇒ 豁免退场判据没有对象")
        out, rc = git(u"log", u"--format=%h", args[-1])
        self.assertEqual(0, rc, out[-200:])
        in_range = set(out.split()) | {birth_short()}
        stale = sorted((set(AHEAD_ROSTER) | set(NO_LABEL_ROSTER)) - in_range)
        self.assertEqual([], stale,
                         u"这些 sha 已不在扫描范围里，豁免要删掉：" + ", ".join(stale))

    def test_roster_entries_must_be_registered_in_the_ledger(self):
        """每一条豁免都要在 `AGENT_BACKLOG.md` 里查得到 —— 名单是我自己写的，不能自我批准。"""
        backlog = io.open(os.path.join(ROOT, "AGENT_BACKLOG.md"), encoding="utf-8").read()
        self.assertEqual([], roster_problems(AHEAD_ROSTER, backlog),
                         u"在册豁免没在账里登记：放宽必须留下人类会读的那份痕迹（R74 / D-279）")
        self.assertEqual([], roster_problems(NO_LABEL_ROSTER, backlog),
                         u"第二张名单里的豁免没在账里登记 ⇒ 同一件事（R334 现读 117f45d 走的就是这张）")
        # 每条理由都必须**指得回一个真条目**：只写 sha 不算登记（下一轮没人知道该由谁补账）。
        for roster in (AHEAD_ROSTER, NO_LABEL_ROSTER):
            for sha, why in roster.items():
                cited = re.findall(u"BACKLOG (\\d{2,4})", why)
                self.assertTrue(cited, u"%s 的豁免理由没引用 BACKLOG 条目：%s" % (sha, why[:60]))
                for n in cited:
                    self.assertIn(u"**%s. " % n, backlog,
                                  u"%s 的豁免引用了 BACKLOG %s，可账上没有这一条" % (sha, n))
        # 正对照：造一条没登记的豁免 ⇒ 必须被点名（名单为空时这一格仍然有牙）
        forged = {u"deadbeef": u"伪造的豁免"}
        found = roster_problems(forged, backlog)
        # 逐字段判，不许拿 found 自己当期望（同形 assert 恒真 = 没判，R146 那一课）
        self.assertEqual(1, len(found), u"造一条未登记的豁免却不点名 ⇒ 这一格是恒真的")
        self.assertEqual(u"deadbeef", found[0][0])
        self.assertEqual(u"ROSTER_NOT_IN_LEDGER", found[0][1])
        self.assertIn(u"BACKLOG", found[0][2])

    def test_baseline_is_reachable(self):
        b = baseline_sha()
        self.assertIsNotNone(b, u"查不到引入这一支的提交 ⇒ 扫描范围无从界定（不许静默放行）")
        out, rc = git(u"rev-list", b + u"~1..HEAD")
        self.assertEqual(0, rc, out[-200:])
        self.assertTrue(out.split(), u"生日之后一笔都没有 ⇒ 空对账，这一格没有对象")

    def test_recent_subjects_are_clean(self):
        args = scan_args()
        self.assertIsNotNone(args, u"判据的生日提交查不到 ⇒ 这一格没有对象")
        out, rc = git(*args)
        self.assertEqual(0, rc, out[-200:])
        rows = []
        for line in out.splitlines():
            if u"\0" not in line:
                continue
            sha, subject = line.split(u"\0", 1)
            rows.append((sha, subject))
        self.assertIn(birth_short(), [r[0] for r in rows],
                      u"扫描范围里连判据自己的生日那一笔都不到 ⇒ 范围算错了")
        self.assertTrue(rows, u"基线之后一笔都没有 ⇒ 空对账（COMPARED=0 的绿不算绿）")
        # 每一笔与它自己那棵树里的当前轮对账；读不到就红（fail-closed，见 round_at）
        rounds = {sha: round_at(sha) for sha, _ in rows}
        self.assertTrue(any(v is not None for v in rounds.values()),
                        u"扫描范围里没有任何一笔能读到当时的当前轮 ⇒ 尺没有对象")
        problems = check(rows, rounds)
        self.assertEqual([], problems, u"\n".join(u"%s %s %s" % p for p in problems))


if __name__ == "__main__":
    unittest.main()
