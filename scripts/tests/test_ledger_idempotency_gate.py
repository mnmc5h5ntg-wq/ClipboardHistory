# -*- coding: utf-8 -*-
"""R594 靶 4①：台账写手的幂等证人 —— 这一卷判的是**守卫自己**（含一次真重放）。

来历：贴纸不幂等是第四次（R303/R562/R580/R593），而 R593 那次是电池到盘上之后才抓到的。
所以这里不许只测正则形状：三块临时仓库、三个假写手（幂等 / 每跑追加一行 / 直接崩），
**真跑** `main()` 并看它给的结论。
"""
from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import ledger_idempotency_gate as g  # noqa: E402

BOOKS = g.BOOKS


IDEMPOTENT_WRITER = u'''# -*- coding: utf-8 -*-
import io, os, sys
root = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(root, "AGENT_STATE.md")
t = io.open(p, encoding="utf-8").read()
if u"## R900 状态" in t:
    print("IDEMPOTENT：已在盘上 ⇒ 不写")
    sys.exit(0)
io.open(p, "w", encoding="utf-8").write(u"## R900 状态（略）\\n" + t)
print("WROTE")
'''

APPENDING_WRITER = u'''# -*- coding: utf-8 -*-
import io, os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AGENT_UI_AUDIT.md")
t = io.open(p, encoding="utf-8").read()
io.open(p, "w", encoding="utf-8").write(t + u"\\n再来一行（这一支就是不幂等的形状）")
print("WROTE 每次追加")
'''

CRASHING_WRITER = u'''# -*- coding: utf-8 -*-
raise SystemExit(3)
'''


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="r594-idem-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        for book in BOOKS:
            io.open(os.path.join(self.dir, book), "w", encoding="utf-8").write(
                u"# %s\\n正文\\n" % book)
        subprocess.check_call([u"git", u"init", u"-q", self.dir])
        subprocess.check_call([u"git", u"-C", self.dir, u"add", u"--"] + list(BOOKS))
        subprocess.check_call([u"git", u"-C", self.dir, u"-c", u"user.email=t@t",
                               u"-c", u"user.name=t", u"commit", u"-q", u"-m", u"base"])

    def writer(self, body, name="writer.py"):
        path = os.path.join(self.dir, name)
        io.open(path, "w", encoding="utf-8").write(body)
        return name

    def replay(self, name):
        out = io.StringIO()
        real = sys.stdout
        sys.stdout = out
        try:
            rc = g.main([u"--writer", name, u"--repo", self.dir])
        finally:
            sys.stdout = real
        return rc, out.getvalue()


class ReplayTest(Sandbox):
    def test_an_idempotent_writer_passes_and_the_replay_is_real(self):
        name = self.writer(IDEMPOTENT_WRITER)
        rc0, _ = self.replay(name)
        self.assertEqual(0, rc0, u"第一次落盘必须成功（否则第二次的「没改」是假的）")
        rc, text = self.replay(name)
        self.assertEqual(0, rc, text)
        self.assertIn(u"改动本=0", text, u"重放没改任何一本 ⇒ 这一支给的就是这个读数：%s" % text)

    def test_a_writer_that_appends_is_named_book_by_book(self):
        name = self.writer(APPENDING_WRITER, u"appender.py")
        rc, text = self.replay(name)
        self.assertEqual(1, rc, u"每跑追加一行的写手必须红：%s" % text)
        self.assertIn(u"AGENT_UI_AUDIT.md", text, u"红话要点名是哪本：%s" % text)

    def test_a_crashing_replay_is_not_read_as_clean(self):
        name = self.writer(CRASHING_WRITER, u"crash.py")
        rc, text = self.replay(name)
        self.assertEqual(2, rc, u"重放崩了 ⇒ 没判，不许读成「第二次没改所以幂等」：%s" % text)
        self.assertIn(u"那一趟在重放里退出", text)
        self.assertNotIn(u"RESULT=ok", text)

    def test_a_missing_writer_is_not_run_not_pass(self):
        rc, text = self.replay(u"no_such_writer.py")
        self.assertEqual(2, rc, u"读不到写手 ⇒ 不判：%s" % text)
        self.assertIn(u"not-run", text)


class GuardHygieneTest(unittest.TestCase):
    def test_the_reader_selftest_rings(self):
        self.assertTrue(g.selftest(), u"重放两次判不出差别 ⇒ 这一支是假门")

    def test_diff_rounds_distinguishes_the_two_shapes(self):
        good = dict((b, (u"m", 0)) for b in BOOKS)
        bad = dict(good)
        bad[BOOKS[0]] = (u"n", 3)
        self.assertEqual(u"ok", g.diff_rounds(good, good))
        self.assertEqual(u"red", g.diff_rounds(good, bad))
