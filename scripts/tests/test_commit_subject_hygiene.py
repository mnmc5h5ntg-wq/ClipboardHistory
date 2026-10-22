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
# 基线 = 装这门之前的一笔；只查它**之后**的提交（历史里 c7b952f 那条残渣留在原地当证人，
# 由 BACKLOG 348 记名，不由这一支假装它不存在）。
BASELINE = "b1b43da"
RESIDUE = [u"<<'EOF'", u"<<-EOF", u"PLACEHOLDER", u"EOF )", u"EOF)"]
STATE_LINE = re.compile(u"^最后更新：\\d{4}-\\d{2}-\\d{2}（本地 · R(\\d+)", re.M)


def git(*args):
    proc = subprocess.Popen([u"git"] + list(args), cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.communicate()[0].decode(u"utf-8", u"replace"), proc.returncode


def check(messages, current_round, window=2):
    """返回问题列表（空 = 干净）。纯函数：判据与正对照走同一条路。"""
    problems = []
    for sha, subject in messages:
        for needle in RESIDUE:
            if needle in subject:
                problems.append((sha, u"COMMIT_SUBJECT_HEREDOC_RESIDUE",
                                 u"subject 里有 heredoc 残渣「%s」：%s" % (needle, subject[:80])))
        m = re.search(u"R(\\d{2,4})", subject)
        if not m:
            problems.append((sha, u"COMMIT_SUBJECT_NO_ROUND",
                             u"subject 里没有轮次标签 R<NNN>：" + subject[:80]))
            continue
        claimed = int(m.group(1))
        if not (current_round - window <= claimed <= current_round):
            problems.append((sha, u"COMMIT_SUBJECT_ROUND_OFF",
                             u"subject 写 R%d，而 STATE 现读当前轮是 R%d（允许往前 %d 轮）⇒ 标签是手抄的"
                             % (claimed, current_round, window)))
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

    def test_clean_subjects_pass_the_same_function(self):
        good = [(u"aaaa1111", u"R296 轮次台账（第 295 轮 / Round 293）补齐"),
                (u"bbbb2222", u"R295 起步：给 pillReading 的盲区装一颗能红的牙")]
        self.assertEqual([], check(good, 296))

    def test_baseline_is_reachable(self):
        out, rc = git(u"rev-list", u"--max-count=15", u"--format=%h", u"HEAD")
        self.assertEqual(0, rc, out[-200:])
        self.assertIn(BASELINE, out.split(),
                      u"基线 " + BASELINE + u" 不在最近 15 笔里 ⇒ 这一支的扫描范围无从界定（不许静默放行）")

    def test_recent_subjects_are_clean(self):
        state = io.open(os.path.join(ROOT, "AGENT_STATE.md"), encoding="utf-8").read()
        cur = STATE_LINE.findall(state)
        self.assertTrue(cur, u"STATE 里没有「最后更新 … R<NNN>」那一行 ⇒ 当前轮读不到，这一格没有对象")
        # AGENT_STATE.md 是**新轮在上**的顺序，所以当前轮要取**第一个**匹配；取末会读到最老那一节
        # （本轮现读撞过：取末得到 R258，于是三笔 R296 的提交全被误判成「标签是手抄的」）。
        current_round = int(cur[0])
        out, rc = git(u"log", u"--format=%h%x00%s", u"-n", u"15", u"HEAD")
        self.assertEqual(0, rc, out[-200:])
        rows = []
        seen_baseline = False
        for line in out.splitlines():
            if u"\0" not in line:
                continue
            sha, subject = line.split(u"\0", 1)
            if sha == BASELINE:
                seen_baseline = True
                break
            rows.append((sha, subject))
        self.assertTrue(seen_baseline, u"扫完 15 笔没遇到基线 " + BASELINE)
        self.assertTrue(rows, u"基线之后一笔都没有 ⇒ 空对账（COMPARED=0 的绿不算绿）")
        problems = check(rows, current_round)
        self.assertEqual([], problems, u"\n".join(u"%s %s %s" % p for p in problems))


if __name__ == "__main__":
    unittest.main()
