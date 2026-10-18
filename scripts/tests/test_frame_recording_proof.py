# -*- coding: utf-8 -*-
"""`scripts/frame_recording_proof.py` 的自测（R147 / BACKLOG 177 收尾那一格）。

判据不许只在作者本机的一次脚本运行里成立过 —— 那是 R145 当时的状态（"录制态那一圈进了帧"
只由一次性测量作证）。这里把它的**判定函数**钉住：合成的两帧各自走到该走的那个出口，
所以真产物哪天不再画那一圈，会红的是一格电池，不是我的眼睛。

正对照全部在临时目录里现造（不写共享绝对路径、不复用上一遍的 PNG）：
`idle` = 灰底 + 灰药丸；`recording` = 同一张 + 一圈高色度描边。四格分别拆掉判据的四条轴。
"""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import scripts.frame_recording_proof as proof
from scripts.frame_recording_proof import (BBOX_MAX_HEIGHT, DELTA_FLOOR, EDGE_FLOOR,
                                           PillowMissing, judge, main, measure)

# R154 / CI run 39118582249 · STEP[8]（U-515）：runner 的 python 3.14 没装 Pillow，
# 这一整个文件原先在**导入期**就 ImportError ⇒ discover 收到一条
# `ERROR: test_frame_recording_proof (unittest.loader._FailedTest)`，
# 报出来的话是"这个测试模块导不进来"，而真实成因是"这台机器没装那个库"（与 R143 的
# `No module named pytest` 同一族：一个错的解释盖住一次环境差异）。
# 现在：需要 PIL 的那几格响成**带名字的 skip**（既不是静默通过、也不是永久红），
# 而"没有 PIL 时这台机器该怎么收场"由 `NoPillowExitTests` 在**两种**解释器上各自判一次。
try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    Image = None
    HAS_PILLOW = False
PILLOW_REASON = ("这台解释器没装 Pillow ⇒ 合成帧造不出来，这一格**没量过**"
                 "（runner 的 python 3.14 就是这样；本机 3.9 有 PIL，照跑）")

SIZE = (400, 200)
BG = (235, 235, 235)
PILL = (215, 215, 215)
RING = (0, 122, 255)          # 强调蓝：高色度，与亮度档无关
PILL_BOX = (100, 60, 300, 140)   # 160×40 太小：它的 delta 只有 711，会被真产物尺寸的地板拦住（第一版就是这么红的）


def base_frame():
    image = Image.new("RGB", SIZE, BG)
    image.paste(PILL, PILL_BOX)
    return image


def ring_frame(box=PILL_BOX, thickness=5, skip_edge=None):
    image = base_frame()
    left, top, right, bottom = box
    for offset in range(thickness):
        if skip_edge != "上":
            for x in range(left, right + 1):
                image.putpixel((x, top + offset), RING)
        if skip_edge != "下":
            for x in range(left, right + 1):
                image.putpixel((x, bottom - offset), RING)
        if skip_edge != "左":
            for y in range(top, bottom + 1):
                image.putpixel((left + offset, y), RING)
        if skip_edge != "右":
            for y in range(top, bottom + 1):
                image.putpixel((right - offset, y), RING)
    return image


@unittest.skipUnless(HAS_PILLOW, PILLOW_REASON)
class SyntheticTruthTableTests(unittest.TestCase):
    def judge_of(self, recording):
        tmp = tempfile.mkdtemp(prefix="r147-frame-")
        try:
            idle_path = os.path.join(tmp, "idle.png")
            rec_path = os.path.join(tmp, "recording.png")
            base_frame().save(idle_path)
            recording.save(rec_path)
            reading = measure(idle_path, rec_path)
            lines, ok = judge(reading, "synthetic")
            return "\n".join(lines), ok, reading
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def testRingPassesAndIsProven(self):
        text, ok, _ = self.judge_of(ring_frame())
        self.assertTrue(ok, "画了整圈还不许说成立：" + text)
        self.assertIn("FRAME_STATE_PROVES_RECORDING=synthetic", text)

    def testIdenticalPairIsNoDifference(self):
        text, ok, _ = self.judge_of(base_frame())
        self.assertFalse(ok, "两帧一模一样却给了名字 = 判据没牙：" + text)
        self.assertIn("FRAME_STATE_NO_DIFF", text)

    def testMissingOneEdgeIsNamed(self):
        for edge in ("上", "下", "左", "右"):
            text, ok, _ = self.judge_of(ring_frame(skip_edge=edge))
            self.assertFalse(ok, "断了一条 %s 边必须红（环不是一团）：%s" % (edge, text))
            self.assertIn("FRAME_STATE_EDGE_MISSING=%s=" % edge, text,
                          "要说出断的是哪条边，不能只说『不成立』：" + text)

    def testFaintRingFallsBelowTheDeltaFloor(self):
        """合成样本的环要与真产物同一量级（地板是从真帧推的）。

        只画两个角 ⇒ 包围盒与四边都可能像样，但"多出来的高色度"不够 ⇒ 由 delta 那一格拦住。"""
        image = base_frame()
        left, top, right, bottom = PILL_BOX
        for corner in ((left, top), (right, bottom)):
            for x in range(corner[0], min(SIZE[0], corner[0] + 6)):
                for y in range(corner[1], min(SIZE[1], corner[1] + 6)):
                    image.putpixel((x, y), RING)
        text, ok, reading = self.judge_of(image)
        self.assertLess(reading["delta"], DELTA_FLOOR, "样本本身没到地板，这一格才有意义")
        self.assertIn("FRAME_STATE_DELTA_BELOW_FLOOR", text, text)

    def testOverflowIsRefused(self):
        """整窗铺满描边 ⇒ "不喧宾夺主"这条不成立，必须由包围盒那一格拦住。"""
        text, ok, _ = self.judge_of(ring_frame(box=(2, 2, SIZE[0] - 3, SIZE[1] - 3),
                                               thickness=BBOX_MAX_HEIGHT))
        self.assertFalse(ok, "外溢到整窗还判成立 = 尺量错了对象：" + text)
        self.assertIn("FRAME_STATE_BBOX_OVERFLOW", text, text)

    def testFloorsAreBelowTheRealRingButAboveZero(self):
        """地板不能比真环的读数还高（那会红得没道理），也不能低到 0（那就拦不住"没画"）。"""
        _, _, reading = self.judge_of(ring_frame())
        self.assertGreater(reading["delta"], DELTA_FLOOR)
        for name in ("上", "下", "左", "右"):
            self.assertGreaterEqual(reading["edges"][name], EDGE_FLOOR * 3,
                                    "合成环的某条边只比地板高一点点 ⇒ 地板贴边，换个尺寸就会假红")


class CliTests(unittest.TestCase):
    def testMissingFramesAreNotSilent(self):
        """读不到帧 ⇒ `NOT_RUN` + 退出码 1：没量过与量了没问题在账上必须长得不一样。"""
        tmp = tempfile.mkdtemp(prefix="r147-cli-")
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main([tmp])
            self.assertEqual(1, code, out.getvalue())
            self.assertIn("FRAME_STATE_NOT_RUN", out.getvalue())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class NoPillowExitTests(unittest.TestCase):
    """没有 Pillow 时这支尺该怎么收场 —— 这两格**不依赖 PIL**，所以在 runner 上也算数。

    R154 那一朵红的形状：环境差异（runner 的 python 没装 Pillow）被报成了一条关于代码的结论
    （「这个脚本在这台解释器上构造不出来」）。修完之后要把两件事分开钉住：
    ① 构造期不需要 PIL ⇒ `--help` 在任何解释器上都得是 0；
    ② 测量期读不到 PIL ⇒ 必须响成**带名字的 NOT-RUN** 且退出码 1，不许洗成"那一圈没问题"。
    """

    SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "frame_recording_proof.py")

    def _hide_pillow_env(self, tmp):
        """造一个假 `PIL` 包住真的：子进程里 `from PIL import Image` 必抛 ImportError。"""
        stub_dir = os.path.join(tmp, "no-pil")
        os.makedirs(os.path.join(stub_dir, "PIL"))
        with io.open(os.path.join(stub_dir, "PIL", "__init__.py"), "w",
                     encoding="utf-8") as handle:
            handle.write("raise ImportError('simulated: this interpreter has no Pillow')\n")
        env = dict(os.environ)
        env["PYTHONPATH"] = stub_dir + os.pathsep + env.get("PYTHONPATH", "")
        return env

    def test_help_builds_parser_without_pillow(self):
        tmp = tempfile.mkdtemp(prefix="r154-help-")
        try:
            env = self._hide_pillow_env(tmp)
            proc = subprocess.run([sys.executable, self.SCRIPT, "--help"],
                                  capture_output=True, text=True, timeout=30, env=env)
            self.assertEqual(0, proc.returncode,
                             "没有 PIL 就连 --help 都跑不出来 ⇒ 构造期依赖没搬干净：\n"
                             + (proc.stderr or "")[-400:])
            self.assertNotIn("Traceback", proc.stderr, proc.stderr[-400:])
            self.assertIn("frames_dir", proc.stdout, "help 文本要还在（说明真跑到 argparse 了）")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_missing_pillow_is_a_named_not_run_and_exit_one(self):
        """帧在、PIL 没 ⇒ `FRAME_STATE_NOT_RUN=pillow` + 退出码 1。

        正对照的形状：这一格喂的是**空文件**，尺连像素都没碰到就该收口；
        如果哪天这条出口被写成 return 0（"读不到就当没问题"），红的是这一格。"""
        tmp = tempfile.mkdtemp(prefix="r154-nopil-")
        original = proof._load_pil
        try:
            for shade in ("light", "dark"):
                with io.open(os.path.join(tmp, "settings-shortcuts-720x540-%s.png" % shade),
                             "wb") as handle:
                    handle.write(b"")
                with io.open(os.path.join(tmp, "settings-shortcuts-recording-720x540-%s.png" % shade),
                             "wb") as handle:
                    handle.write(b"")

            def raise_missing():
                raise PillowMissing("simulated: no Pillow")

            proof._load_pil = raise_missing
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main([tmp])
            text = out.getvalue()
            self.assertEqual(1, code, "读不到 PIL 却给了 0 ⇒ 把「我没量过」洗成了「量了没问题」：" + text)
            self.assertIn("FRAME_STATE_NOT_RUN=pillow", text, text)
            self.assertNotIn("FRAME_STATE_PROVES_RECORDING", text,
                             "没 PIL 还打出「这一圈成立」＝伪造验证：" + text)
        finally:
            proof._load_pil = original
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
