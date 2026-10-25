#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""真机尺的「对象门」：拍到的像素必须属于它声称的那个窗口（R341 开）。

为什么要有它（R341 当场撞的）：屏幕解锁之后，同一条调用链拍到的是 **Numbers 的保存对话框**
（用户正在编辑的表格），`frame_ready` 只问「这一帧画完了没有」（≥3 档电平各占 ≥2%）⇒ 放行，
接着尺报 `no_band`（侧栏顶部没有一行过闸）—— 一个关于**产品**的假结论，而产品窗口根本不在前台。
这是「尺读的不是它声称的对象」那一族第四次（D-090 / 176 / 372 之后）。

判四格（每一格都能单独红）：
  ① 三态各自有名字，且三个输入给出三个不同的判（正对照：这函数不是恒绿）；
  ② 门真的接在 `main` 里（AST 查调用点），不是写了个函数没人用；
  ③ 拒绝时打的是 `REALSCREEN_NOT_RUN` 那一行，而不是继续往下判成 `no_band`；
  ④ 目标进程名（= 可执行名，不是显示名）在测试里写死一份字面量 —— 它若与模块常量漂开，这一格红。
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, u"scripts"))
import real_screen_filter_pill as T  # noqa: E402  与 test_sources_cell_second_source 同一写法

SRC_PATH = os.path.join(ROOT, u"scripts", u"real_screen_filter_pill.py")


class RealScreenCaptureIdentity(unittest.TestCase):
    def setUp(self):
        self.src = io.open(SRC_PATH, encoding=u"utf-8").read()

    def test_three_inputs_three_names_and_they_differ(self):
        ok = T.capture_identity(u"ClipboardHistoryApp")
        other = T.capture_identity(u"Numbers")
        unknown = T.capture_identity(None)
        self.assertEqual(ok, u"ok")
        self.assertEqual(other, u"occluded_not_frontmost")
        self.assertEqual(unknown, u"frontmost_unknown")
        # 正对照：三个输入不许塌成同一个判（恒绿的门比没有门更坏）
        self.assertEqual(len({ok, other, unknown}), 3)

    def test_target_name_is_the_products_ax_process_name(self):
        # 这一份字面量与模块常量分开写：`APP_PROCESS` 被人改坏时这一格红，而不是跟着改坏
        self.assertEqual(T.APP_PROCESS, u"ClipboardHistoryApp")
        self.assertEqual(T.capture_identity(u"ClipboardHistoryApp", u"ClipboardHistoryApp"), u"ok")

    def test_gate_is_wired_into_main_before_scanning(self):
        tree = ast.parse(self.src)
        mains = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == u"main"]
        self.assertEqual(len(mains), 1, u"main 应当恰好一个")
        called = set()
        for node in ast.walk(mains[0]):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called.add(node.func.id)
        self.assertIn(u"capture_identity", called, u"门写了却没人调用 = 没有门")
        self.assertIn(u"activate_and_wait", called, u"不推前台就截图 = 拍到别人的窗口")

    def test_refusal_path_is_named_not_no_band(self):
        # 拒绝那一支必须落在 REALSCREEN_NOT_RUN 上；`no_band` 只能作为「真的没有控件」的结论
        self.assertIn(u"REALSCREEN_NOT_RUN %s", self.src)
        idx = self.src.find(u"if gate != u\"ok\":")
        if idx < 0:
            idx = self.src.find(u"if gate != ")
        self.assertGreater(idx, 0, u"找不到对象门那一支")
        window = self.src[idx:idx + 400]
        self.assertIn(u"REALSCREEN_NOT_RUN", window)
        self.assertNotIn(u"no_band", window)


if __name__ == u"__main__":
    unittest.main()


class RealScreenPairShape(unittest.TestCase):
    u""""第二形状"：一个控件两段、选中段在左（R341 真机 107/80 那一格）。"""

    def test_light_pair_reads_pill_above_track(self):
        # 真机亮档那一趟的形状：页底 219 / 轨道 196 / 药丸 220。
        # 注意左端那 2 个采样点是**轨道露在药丸外面的窄边**（真机上 12..14pt 那一条）：
        # 没有它，左半与页底同档（220 vs 219）⇒ 容器从中间才开始，两段形状根本切不开 ——
        # 这也正是亮档本来就能被旧形状判出来的原因。
        prof = [(i, 196) for i in range(2)] + [(i, 220) for i in range(2, 40)] \
            + [(i, 196) for i in range(40, 80)]
        got = T.pair_split(prof, 219, 4, 2.0, T.DELTA)
        self.assertIsNotNone(got)
        self.assertEqual(got[u"pill"], 220)
        self.assertEqual(got[u"track"], 196)
        self.assertEqual(got[u"pill"] - got[u"track"], 24)

    def test_dark_pair_reads_selected_brighter_than_unselected(self):
        # 真机暗档那一趟的形状：页底 43 / 左(选中) 107 / 右(未选) 80
        prof = [(i, 107) for i in range(40)] + [(i, 80) for i in range(40, 80)]
        got = T.pair_split(prof, 43, 4, 2.0, T.DELTA)
        self.assertIsNotNone(got)
        self.assertEqual(got[u"pill"], 107)
        self.assertEqual(got[u"track"], 80)
        self.assertGreater(got[u"pill"] - got[u"track"], T.DELTA)

    def test_pair_refuses_shapes_it_cannot_read(self):
        # ① 不够宽（60pt < MIN_CONTAINER_PT）② 两半同档 ③ 整条都是页底
        narrow = [(i, 107) for i in range(15)] + [(i, 80) for i in range(15, 30)]
        self.assertIsNone(T.pair_split(narrow, 43, 4, 2.0, T.DELTA))
        same = [(i, 100) for i in range(80)]
        self.assertIsNone(T.pair_split(same, 43, 4, 2.0, T.DELTA))
        flat = [(i, 43) for i in range(80)]
        self.assertIsNone(T.pair_split(flat, 43, 4, 2.0, T.DELTA))

    def test_prefer_shape_keeps_the_old_ruler_when_both_exist(self):
        pill = {u"pill": 70, u"track": 52, u"hole_pt": 40, u"extent_pt": 300}
        pair = {u"pair": True, u"pill": 107, u"track": 80, u"hole_pt": 150,
                u"extent_pt": 320, u"solidity": 0.9}
        self.assertEqual(T.prefer_shape([pill, pair])[0], u"pill")
        self.assertEqual(T.prefer_shape([pair])[0], u"pair")
        self.assertEqual(T.prefer_shape([]), (None, None))
        # 两段形状没有 solidity 时也不许在比较里 KeyError（这一格是形状门自己的崩点）
        pair2 = dict(pair); pair2.pop(u"solidity")
        self.assertEqual(T.prefer_shape([pill, pair2])[0], u"pill")
