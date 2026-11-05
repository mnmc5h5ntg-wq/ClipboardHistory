# -*- coding: utf-8 -*-
"""R587 / 靶 B + 顺账：档位词表只许有一份真值；印出来的选项必须真存在。

三件事各自会红（都不靠注释）：
① python 仪器里**再出现第二份档位词表声明** ⇒ 红并点名文件与行。本轮把
   `hover_two_state_diff.py` 的 `TIERS`、`frame_baseline.py` 的 `(?:light|dark)` 正则、
   `frame_recording_proof.py` 的 `("light","dark")` 循环全部收成 `scripts/tier_vocabulary.py` 一份。
② 两侧对同一帧名必须给出**同一个档**（按段解析 vs 倍率正则里那一段）。
③ `substring_tier`（子串法）**不参与任何判定** —— 由 AST 签，不由注释签。

顺账那一笔：印给读者的**成句命令**（`python3 某脚本.py …`）里每个 `--选项`，必须真被那个脚本的参数表
或手写 argv 解析认得，脚本路径本身也要存在。措辞里多一个字母就是空头支票
（R586 ⑨·7 已复发过一次 ⇒ 本轮做成守卫，不再逐条追记）。
规则收窄的原因不是省事：按"print 里任何 `--x`"判会在两处**把存在的读成不存在**——
`ci_red_stability.py` 没有 argparse（它手写 `if args[0] == …`）、`create_issues.py` 的 `add_argument(`
与旗标换了行。今天全仓 scripts/ 里这样的成句命令只有 1 条（`frame_baseline.py` 自己那条出路），
守卫的范围是**每一支脚本**，不是那一条。

扫描范围为什么是 AST 而不是文本行：本轮第一版扫文本行，结果把我自己写的**注释**
「倍率解析里的 `(?:light|dark)` 由它现推」判成第二份声明 —— 那是守卫读错了对象
（R580 那一课：读到 1 要区分「对象在」与「字面在」）。AST 里没有注释，docstring 也能按位置摘出去。
"""
from __future__ import annotations

import ast
import io
import os
import re
import sys
import unittest
from pathlib import Path

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(REPO, "scripts")
sys.path.insert(0, REPO)

from scripts.tier_vocabulary import TIERS, tier_alternation, tier_from_name  # noqa: E402

PAIR_RX = re.compile(r"\(\?:light\|dark\)|\(light\|dark\)")
ALLOWED_DECL_FILE = "tier_vocabulary.py"


def docstring_lines(tree):
    """所有 docstring 占的行号（它们不是代码，不该被当成声明）。"""
    lines = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None) or []
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            d = body[0].value
            lines.update(range(d.lineno, (getattr(d, "end_lineno", None) or d.lineno) + 1))
    return lines


def vocabulary_decls(path):
    """返回该文件里**代码层面**声明了档位词表的位置（元组字面量、TIERS 赋值、正则片段）。"""
    tree = ast.parse(io.open(path, encoding="utf-8").read(), filename=path)
    docs = docstring_lines(tree)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.lineno in docs:
                continue
            if PAIR_RX.search(node.value):
                hits.append(u"%s:%d 正则片段 %s" % (os.path.basename(path), node.lineno, node.value[:48]))
        if isinstance(node, ast.Tuple):
            vals = [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if set(vals) == {u"light", u"dark"}:
                hits.append(u"%s:%d 元组字面量 %r" % (os.path.basename(path), node.lineno, tuple(vals)))
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "TIERS":
                    hits.append(u"%s:%d 重新赋值 TIERS" % (os.path.basename(path), node.lineno))
    return hits


def live_scripts():
    for name in sorted(os.listdir(SCRIPTS)):
        if name.endswith(".py"):
            yield os.path.join(SCRIPTS, name)


class TierVocabularySingleSourceTests(unittest.TestCase):
    def test_no_live_script_declares_its_own_tier_vocabulary(self):
        bad = []
        for path in live_scripts():
            if os.path.basename(path) == ALLOWED_DECL_FILE:
                continue
            bad.extend(vocabulary_decls(path))
        self.assertEqual([], bad,
                         u"档位词表又出现第二份代码层面的声明（加一档时其中一份会静默失效）：\n"
                         + u"\n".join(bad))

    def test_scanner_spots_a_second_declaration(self):
        """正对照：扫描器必须认得出它要防的那三种形状，否则上面那条绿灯是空的。"""
        self.assertTrue(vocabulary_decls(os.path.join(SCRIPTS, ALLOWED_DECL_FILE)),
                        u"连 tier_vocabulary.py 自己的声明都认不出 ⇒ 扫描器坏了")
        import tempfile
        samples = [u"TIERS = ('light', 'dark')\n",
                   u"import re\nRX = r'-(?:light|dark)\\.png$'\n",
                   u"import re\nRX = re.compile(r'(light|dark) 底')\n",
                   u"for shade in ('light', 'dark'):\n    pass\n"]
        for s in samples:
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
                f.write(s)
                name = f.name
            try:
                self.assertTrue(vocabulary_decls(name), u"这一行认不出来：%s" % s.strip())
            finally:
                os.unlink(name)

    def test_docstring_mention_is_not_counted_as_a_declaration(self):
        """反面对照：注释/docstring 里出现那三种形状**不算**声明（本轮真实撞过一次）。"""
        import tempfile
        src = (u'"""这里解释正则里的 (?:light|dark) 是由词表现推的。"""\n'
               u"# 注释里也写一次 (light|dark)\n"
               u"X = 1\n")
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(src)
            name = f.name
        try:
            self.assertEqual([], vocabulary_decls(name))
        finally:
            os.unlink(name)

    def test_both_sides_agree_on_every_frame_name(self):
        """按段解析（判定用）与倍率正则里那一段必须给同一个档 ⇒ 词表一份才推得动。"""
        # 名单里只放**带逻辑尺寸段**的名字（现读语料全部是这一形状）。没有尺寸段的那种名字倍率正则匹配不到，
        # 由 `test_frame_baseline.ScaleDistributionTests.test_sizeless_frame_names_are_counted_not_silently_skipped`
        # 用**合成**名字单独签 —— 注意那是合成形状，现读语料里并没有这种名字。
        names = [u"detail-0-text-720x520-dark.png", u"detail-text-highlight-720x520-dark.png",
                 u"quickpick-typed-no-highlight-420x300-dark.png", u"glass-pill-120x232-light.png",
                 u"heatmap-cell-strip-still-90x140-dark.png"]
        # 产品里那条正则的档位段是**非捕获**的（它只要尺寸），这里为了对账另建一条捕获版；
        # 上一稿我写了 `m.group(2)` —— 那是高度 520，不是档位。测试自己也会读错对象，
        # 所以这一格断言的是「两侧给同一个档」，不是「两侧用同一条正则」。
        rx = re.compile(r"-(\d+)x(\d+)-(%s)\.png$" % tier_alternation())
        for name in names:
            m = rx.search(name)
            self.assertTrue(m, name)
            self.assertEqual(m.group(3), tier_from_name(name), name)

    def test_tier_alternation_is_derived_not_copied(self):
        self.assertEqual((u"light", u"dark"), TIERS)
        self.assertEqual(u"light|dark", tier_alternation())


class SubstringTierContainmentTests(unittest.TestCase):
    """`substring_tier` 只许出现在报表里 —— 它现在不参与判定这件事得有人签。"""

    HOVER = os.path.join(SCRIPTS, "hover_two_state_diff.py")

    def function_body(self, tree, name):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return node
        raise AssertionError(u"找不到函数 %s ⇒ 形状变了，这一格该红不该绿" % name)

    def test_measure_uses_segment_parse_not_substring(self):
        tree = ast.parse(io.open(self.HOVER, encoding="utf-8").read(), filename=self.HOVER)
        body = self.function_body(tree, "measure")
        called = {n.func.id for n in ast.walk(body) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertIn("frame_tier", called, u"判定函数不再走按段解析 ⇒ R586 那一支被撤了")
        self.assertNotIn("substring_tier", called, u"判定函数调了子串法 ⇒ 上一轮修好的东西又回到判定里")

    def test_substring_tier_has_exactly_one_caller(self):
        callers = []
        for path in live_scripts():
            src = io.open(path, encoding="utf-8").read()
            if "substring_tier" not in src:
                continue
            tree = ast.parse(src, filename=path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                        and node.func.id == "substring_tier":
                    callers.append(u"%s:%d" % (os.path.basename(path), node.lineno))
        self.assertEqual(1, len(callers),
                         u"子串法的调用点应当只剩报表那一处（tier_collide 计数），现在是 %s" % callers)


class SwiftSideVocabularyCountTests(unittest.TestCase):
    """靶 B 的**边界**证人（BACKLOG 661）：python 侧那一份真值管不到 Swift 捕获侧。

    为什么这一格必须存在：本轮把 python 侧收成一份真值之后，账上很容易写出一句假的「全仓只有一份」。
    捕获侧（`UICaptureHarness.swift` 里 `for tag in ["light", "dark"]` 若干处）本轮一字未动 —— 那是派单红线。
    所以这里不拦、不改，只做一件事：**把处数现数出来**，并证明这个计数器认得出两种顺序的写法
    （只认 `["light","dark"]` 的计数器在有人写成 `["dark","light"]` 时会读成 0 ⇒ 那才是"全仓只有一份"
    这种假声明的来源）。数字本身交给台账现抄，不在这里钉死（钉死了就变成"改一处要回来改测试"）。
    """

    HARNESS = os.path.join(REPO, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",
                           "UICaptureHarness.swift")
    RX = re.compile(r'for\s+\w+\s+in\s+\[\s*"light"\s*,\s*"dark"\s*\]')
    RX_REVERSED = re.compile(r'for\s+\w+\s+in\s+\[\s*"dark"\s*,\s*"light"\s*\]')

    def test_the_swift_side_declarations_are_counted_by_two_orders(self):
        src = io.open(self.HARNESS, encoding="utf-8").read()
        n = len(self.RX.findall(src)) + len(self.RX_REVERSED.findall(src))
        self.assertGreater(n, 0,
                           u"Swift 侧一处档位声明都读不到 ⇒ 计数对象没了（它换了写法或文件搬了），"
                           u"这条绿灯是空的")
        # 两条正则各自命中数相加 == 一个"任意顺序"的合并计数 ⇒ 顺序差不会把某一边漏掉
        merged = len(re.findall(r'for\s+\w+\s+in\s+\[\s*"(?:light|dark)"\s*,\s*"(?:light|dark)"\s*\]', src))
        self.assertEqual(merged, n, u"两种顺序各自数(%d)与合并数(%d)不等 ⇒ 有第三种写法漏在中间" % (n, merged))

    def test_counter_recognises_a_reordered_declaration(self):
        """正对照：`["dark","light"]` 也必须被认出，否则计数器会在改名那天读成 0。"""
        self.assertEqual(1, len(self.RX_REVERSED.findall('for tag in ["dark", "light"] {')))
        self.assertEqual(1, len(self.RX.findall('for shade in ["light","dark"] {')))


class PrintedCommandParsesTests(unittest.TestCase):
    """顺账（R587）：**印给读者的每一条命令**必须能被它自己点到的那个脚本解析。

    上一稿这一节只对账两个脚本，判据是「print 里出现的每个 `--x` 都要在该脚本的 add_argument 里」。
    本轮把它扩到 scripts/ 每一支，扩的过程本身就挖出两处**尺读错对象**（都在真仓库里，不是假设）：
      · `ci_red_stability.py` 根本没有 argparse，它手写 `if args[0] == "--from-file"`
        ⇒ 按旧判据，那一条真旗标会被判成空头支票；
      · `create_issues.py` 的 `add_argument(` 与旗标**换行分开**写
        ⇒ 旧正则抓不到，真旗标同样会被读成"不存在"。
    两种坏法的形状相同：**把存在的读成不存在**。所以这一版做四件事：
      ① 范围＝scripts/ 下每一支会 print 的脚本（不是点名两个）；
      ② 只认「`python3 <某脚本.py> <尾巴>`」这种**成句的命令** —— 消息里顺口提一句
        `swift test --filter` 不是对本脚本参数表的承诺，把它算进来就是给将来的假红留门；
      ③ 一个脚本的真旗标 = add_argument（容忍换行）∪ 代码里**整条字面量就是一个 `--x`** 的那些
        （手写 argv 解析走这一支；注释与句子中的旗标不是字面量整体，不会被误收）；
      ④ 命令点到的脚本路径必须真存在 —— 印错文件名和印错旗标是同一种空头支票。
    """

    CMD_RX = re.compile(r"python3\s+(\S+\.py)([^`\n]*)")
    FLAG_RX = re.compile(r"(--[a-z][a-z0-9-]+)")

    def printed_texts(self, path):
        """每个 print 调用**合成一条**文本（隐式拼接在 AST 里本就是一个 Constant，
        多参数按空格接）——按字面量逐条扫会把一条命令劈成两截，那是漏判不是红。"""
        tree = ast.parse(io.open(path, encoding="utf-8").read(), filename=path)
        out = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                parts = []
                for arg in node.args:
                    for lit in ast.walk(arg):
                        if isinstance(lit, ast.Constant) and isinstance(lit.value, str):
                            parts.append(lit.value)
                if parts:
                    out.append(u" ".join(parts))
        return out

    def real_flags(self, path):
        src = io.open(path, encoding="utf-8").read()
        flags = set(re.findall(r'add_argument\(\s*(?:"|\')(--[a-z][a-z0-9-]*)', src))
        tree = ast.parse(src, filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if re.match(r"^--[a-z][a-z0-9-]+$", node.value):
                    flags.add(node.value)      # 手写 argv 解析：`if args[0] == "--from-file"`
        return flags

    def test_every_printed_command_parses_in_the_script_it_names(self):
        bad = []
        for path in live_scripts():
            for text in self.printed_texts(path):
                for script, tail in self.CMD_RX.findall(text):
                    target = os.path.join(REPO, script)
                    if not os.path.exists(target):
                        bad.append(u"%s 印了不存在的脚本 %s" % (os.path.basename(path), script))
                        continue
                    unknown = sorted(set(self.FLAG_RX.findall(tail)) - self.real_flags(target))
                    for opt in unknown:
                        bad.append(u"%s 印的 `%s … %s` 里 %s 不被 %s 的参数表认（可用：%s）"
                                   % (os.path.basename(path), script, tail.strip()[:40], opt,
                                      os.path.basename(script), sorted(self.real_flags(target))))
        self.assertEqual([], bad, u"印给读者的命令是空头支票：\n" + u"\n".join(bad))

    def test_scanner_sees_the_two_real_handlings(self):
        """正/负对照：真存在的两种写法必须被认成"存在"，否则上面那条绿灯是假的。"""
        self.assertIn(u"--from-file", self.real_flags(os.path.join(SCRIPTS, "ci_red_stability.py")))
        self.assertIn(u"--confirm-release-publish",
                      self.real_flags(os.path.join(SCRIPTS, "create_issues.py")))
        self.assertIn(u"--for-machine", self.real_flags(os.path.join(SCRIPTS, "frame_baseline.py")))

    def test_scanner_spots_a_nonexistent_option(self):
        """正对照：这一格也要能红 —— 上一轮的错值就是这个形状（M1552 钉的正是它）。"""
        known = self.real_flags(os.path.join(SCRIPTS, "frame_baseline.py"))
        self.assertIn(u"--for-machine", known)
        _script, tail = self.CMD_RX.findall(
            u"出路 跑 `python3 scripts/frame_baseline.py update <帧目录> --for-machin` 即可")[0]
        self.assertEqual([u"--for-machin"], sorted(set(self.FLAG_RX.findall(tail)) - known))

    def test_scanner_spots_a_nonexistent_script(self):
        """正对照：文件名印错也是空头支票，这一支同样要红。"""
        hits = self.CMD_RX.findall(u"跑 `python3 scripts/frame_base.py update X` 即可")
        self.assertEqual(1, len(hits))
        self.assertFalse(os.path.exists(os.path.join(REPO, hits[0][0])))


if __name__ == "__main__":
    unittest.main()
