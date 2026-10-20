# -*- coding: utf-8 -*-
"""两态差尺的判据卷（R241 / BACKLOG 273）—— `scripts/hover_two_state_diff.py` 的两个口径与三道闸门。

**不覆盖管线**：这一卷钉的是尺本身（两个估计量各算各的、闸门在缺证据时必须红），
它不给产品定罪。产品那一档的读数来自真帧卷（`CLIPBOARD_HISTORY_UI_SHOTS`）与 251 的逐位点比较，
本卷只保证那把尺在**任何机器、不需要任何帧**的情况下都不会把自己演成一出绿。

为什么必须单独有这一卷（273 的三条承重）：
  ① 两个估计量不许互冒充 —— `band_mean` 会被未变像素稀释、`per_pixel` 是控件局部。
     R239 那次就是拿稀释过的数去对历史账里没稀释的数，差点改了不该改的 `VisualFill.hover`。
     所以这里造两块**已知形状**的合成帧：一块"整带都变了"（两数必须相等）、
     一块"带里只有两个点变了"（两数必须差得远）。
  ② 闸门不能是摆设 —— 缺正对照、空名单、覆盖率低于地板、帧尺寸不符，四种都必须 rc≠0；
     而"干净的一跑"必须 rc=0（两向证人，否则闸门可能是恒红的死码）。
  ③ 期望值不许心算 —— 下面每个字面数都由手算推出（推导写在注释里），
     跑出来的数若与手算不符，那是尺坏了，不是把期望改成读数。
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(REPO, "scripts", "hover_two_state_diff.py")

try:
    from PIL import Image
except ImportError:                                       # 与 252 同一族：缺库要能被点名，不许静默绿
    Image = None

_ruler = None
_load_error = None
if Image is not None:
    _spec = importlib.util.spec_from_file_location("hover_two_state_diff", SCRIPT)
    try:
        _ruler = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_ruler)
    except Exception as exc:                              # pragma: no cover - 只在本机之外可能命中
        _load_error = str(exc)

NO_PIL = Image is None
NO_RULER = _ruler is None
NO_PIL_OR_RULER = NO_PIL or NO_RULER

BG, LIT = 30, 80   # 两个灰阶：BG 与本机暗档平涂背景同量级，LIT 是"亮一档"

# 手算的两个期望值（公式与尺一致：ratio=(max/255+0.05)/(min/255+0.05)）
#   80 vs 30 ⇒ (0.3137254902+0.05)/(0.1176470588+0.05) = 0.3637254902/0.1676470588 = 2.16959 ⇒ 2.17
RATIO_LIT_VS_BG = 2.17
#   稀释带：hover 带内均值 = (2×80 + 8×30)/10 = 40 ⇒ (0.1568627451+0.05)/0.1676470588 = 1.23393 ⇒ 1.234
RATIO_DILUTED = 1.234


def block(x0, y0, w, h, grey):
    return [(x0 + i, y0 + j, grey) for i in range(w) for j in range(h)]


def write_frame(dirpath, name, size, spots=(), fill=BG):
    im = Image.new("RGB", size, (fill, fill, fill))
    for x, y, grey in spots:
        im.putpixel((x, y), (grey, grey, grey))
    im.save(os.path.join(dirpath, name + ".png"))


class RulerTestCase(unittest.TestCase):
    """合成帧目录的公共底座：每格自己的临时目录，绝不跨格复用（R91 那一族）。"""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="hover_ruler_")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def add(self, name, size=(10, 10), spots=()):
        write_frame(self.dir, name, size, spots)

    def clean_pair(self, size=(20, 20)):
        """一整块 10×10 亮档 ⇒ 100 个变化像素（够正对照的 MIN_CHANGED=50）。"""
        self.add("pill-hover-20x20-dark", size, block(0, 0, 10, 10, LIT))
        self.add("pill-20x20-dark", size)

    def cli(self, extra=(), shots_env=None):
        env = dict(os.environ)
        env.pop("CLIPBOARD_HISTORY_UI_SHOTS", None)
        if shots_env is not None:
            env["CLIPBOARD_HISTORY_UI_SHOTS"] = shots_env
        args = [sys.executable, SCRIPT] + list(extra)
        proc = subprocess.run(args, capture_output=True, text=True, env=env)
        return proc.returncode, proc.stdout


@unittest.skipIf(NO_PIL, "缺 PIL：这一格在本机与 runner 上都要能被点名（252 的形状）")
class EstimatorTests(RulerTestCase):
    def test_a_fully_changed_band_makes_the_two_estimators_agree(self):
        self.add("pill-hover-10x10-dark", spots=block(0, 0, 2, 5, LIT))
        self.add("pill-10x10-dark")
        m = _ruler.measure(self.dir, "pill-hover-10x10-dark", "pill-10x10-dark")
        self.assertEqual(10, m["changed"], "Δ>4 的像素应当是 2×5=10 个（合成帧是我造的，数错就是尺的像素门槛坏了）")
        self.assertEqual(10.0, m["share"])
        self.assertEqual((0, 0, 2, 5), m["bbox"])
        self.assertEqual(RATIO_LIT_VS_BG, m["band_mean"], "整带都变了 ⇒ 带内均值就是 80:30，手算 2.17")
        self.assertEqual(RATIO_LIT_VS_BG, m["per_pixel"], "逐点中位数与带内均值在这一块上必须同值")

    def test_unchanged_pixels_dilute_band_mean_but_not_per_pixel(self):
        # 变化带横跨整行（x=0..9, y=5）而只有两端真的变了 ⇒ 带内 8 个未变像素进分母。
        self.add("pill-hover-10x10-dark", spots=[(0, 5, LIT), (9, 5, LIT)])
        self.add("pill-10x10-dark")
        m = _ruler.measure(self.dir, "pill-hover-10x10-dark", "pill-10x10-dark")
        self.assertEqual(2, m["changed"])
        self.assertEqual((0, 5, 10, 6), m["bbox"], "包围盒要把两端都圈进来，否则稀释就无从发生")
        self.assertEqual(RATIO_DILUTED, m["band_mean"], "带内均值被 8 个未变像素拉到 40:30，手算 1.234")
        self.assertEqual(RATIO_LIT_VS_BG, m["per_pixel"], "变化像素逐点中位不看未变像素")
        self.assertLess(m["band_mean"], m["per_pixel"],
                        "两个口径不分开，R239 那种『拿稀释数对历史账』的错就还会再犯")

    def test_a_pair_that_did_not_change_reads_as_no_band_rather_than_zero_contrast(self):
        self.add("pill-10x10-dark")
        m = _ruler.measure(self.dir, "pill-10x10-dark", "pill-10x10-dark")
        self.assertEqual(0, m["changed"])
        self.assertIsNone(m["band_mean"], "没变化时不许编一个 1.0/0.0 出来 —— 缺席与为零是两回事（R99）")
        self.assertIsNone(m["per_pixel"])
        self.assertIsNone(m["bbox"])

    def test_frames_of_different_sizes_are_refused_not_measured(self):
        self.add("pill-hover-10x10-dark", size=(10, 10), spots=block(0, 0, 2, 5, LIT))
        self.add("pill-10x10-dark", size=(8, 12))
        self.assertIsNone(_ruler.measure(self.dir, "pill-hover-10x10-dark", "pill-10x10-dark"))

    def test_a_missing_frame_is_refused_not_zero(self):
        self.add("pill-10x10-dark")
        self.assertIsNone(_ruler.measure(self.dir, "pill-hover-10x10-dark", "pill-10x10-dark"))


@unittest.skipIf(NO_PIL, "缺 PIL：见上")
class PairingTests(RulerTestCase):
    def test_both_idle_spellings_are_recognised(self):
        # 仓库里两种形状同时存在：glass-pill（静置名没有 idle 段）与 segmented-filter（有）。
        self.add("pill-hover-10x10-dark", spots=block(0, 0, 2, 5, LIT))
        self.add("pill-10x10-dark")
        self.add("seg-hover-10x10-light", spots=block(0, 0, 2, 5, LIT))
        self.add("seg-idle-10x10-light")
        pairs, unpaired = _ruler.find_pairs(self.dir)
        self.assertEqual([], unpaired)
        self.assertEqual({("-dark", "pill-hover-10x10-dark", "pill-10x10-dark"),
                          ("-light", "seg-hover-10x10-light", "seg-idle-10x10-light")},
                         set(pairs))

    def test_a_hover_frame_without_a_still_twin_is_a_named_absence(self):
        # 这就是 251 的欠账形状：有悬停帧、没静置帧 ⇒ 两态对照不存在，要被点名而不是被跳过。
        self.add("row-favorite-hover-10x10-dark", spots=block(0, 0, 2, 5, LIT))
        pairs, unpaired = _ruler.find_pairs(self.dir)
        self.assertEqual([], pairs)
        self.assertEqual(["row-favorite-hover-10x10-dark"], unpaired)

    def test_the_real_shots_pair_at_least_as_well_as_the_registered_floor(self):
        """本机/runner 各自的地板：`HOVER_DIFF_MIN_PAIRS`（本机 R240 实测 6，未设时按 1）。"""
        shots = os.environ.get("CLIPBOARD_HISTORY_UI_SHOTS")
        if not shots or not os.path.isdir(shots):
            self.skipTest("通道缺席：CLIPBOARD_HISTORY_UI_SHOTS=%r 不存在 ⇒ 这一格只在本机重捕帧之后承重（R140：/tmp 会被清）" % (shots,))
        floor = int(os.environ.get("HOVER_DIFF_MIN_PAIRS", "1"))
        pairs, unpaired = _ruler.find_pairs(shots)
        self.assertGreaterEqual(len(pairs), floor,
                                "只配到 %d 对，低于地板 %d ⇒ 帧名形状漂了，上面的读数一律不算" % (len(pairs), floor))
        print("真帧配对=%d 无静置态=%d（本机 R240 实测 6/14）" % (len(pairs), len(unpaired)))


@unittest.skipIf(NO_PIL_OR_RULER, "缺 PIL 或尺加载失败（%s）：要能被点名，不许静默通过" % (_load_error or "PIL"))
class GateTests(RulerTestCase):
    def test_refuses_without_a_shots_channel(self):
        rc, out = self.cli()
        self.assertEqual(2, rc, "没有帧目录却 exit 0 ⇒ 这把尺会在 CI 上『什么都没量到』地绿过去")
        self.assertIn("HOVER_DIFF_REFUSED", out)

    def test_an_empty_pair_list_is_red_not_skipped(self):
        self.add("nothing-here-10x10-dark")           # 有 PNG，但一个 -hover 都没有
        rc, out = self.cli(["--shots", self.dir])
        self.assertEqual(1, rc)
        self.assertIn("HOVER_DIFF_EMPTY=1", out)
        self.assertNotIn("退出=0", out, "空名单不许打绿的那一行")

    def test_a_clean_run_with_both_controls_is_green(self):
        self.clean_pair()
        rc, out = self.cli(["--shots", self.dir, "--control", "pill-hover-20x20-dark,pill-20x20-dark"])
        self.assertEqual(0, rc, out)
        self.assertIn("HOVER_DIFF_NEG_CONTROL=OK", out)
        self.assertIn("HOVER_DIFF_POS_CONTROL=OK", out)
        self.assertIn("对=pill-hover-20x20-dark↔pill-20x20-dark", out,
                      "读数必须点名它量的是哪一对，否则两行同 bbox 数不清主语（R121 那一族）")

    def test_missing_positive_control_cannot_announce_resolvability(self):
        self.clean_pair()
        rc, out = self.cli(["--shots", self.dir])
        self.assertEqual(1, rc, "没给 --control 就 exit 0 ⇒ 『可分辨/不可分辨』会在没有参照的情况下被宣布")
        self.assertIn("POS_CONTROL=MISSING", out)

    def test_a_positive_control_that_shows_no_change_is_bad(self):
        self.clean_pair()
        self.add("pill-10x10-dark")
        rc, out = self.cli(["--shots", self.dir, "--control", "pill-10x10-dark,pill-10x10-dark"])
        self.assertEqual(1, rc)
        self.assertIn("POS_CONTROL=BAD", out, "正对照读不到已知变化 = 尺坏了，此时上面所有数都不作数")

    def test_the_coverage_floor_is_a_real_floor_and_only_that(self):
        self.clean_pair()
        ctl = ["--shots", self.dir, "--control", "pill-hover-20x20-dark,pill-20x20-dark"]
        rc_ok, _ = self.cli(ctl + ["--min-pairs", "1"])
        self.assertEqual(0, rc_ok, "地板设 1 时同一批帧必须绿 —— 否则下面那格的红是死码不是地板")
        rc_low, out_low = self.cli(ctl + ["--min-pairs", "2"])
        self.assertEqual(1, rc_low)
        self.assertIn("覆盖率本身要红", out_low)


@unittest.skipIf(NO_PIL, "缺 PIL：见上")
class InstrumentContractTests(RulerTestCase):
    def test_the_ruler_names_its_two_estimators_so_neither_can_be_cited_as_the_other(self):
        self.clean_pair()
        rc, out = self.cli(["--shots", self.dir, "--control", "pill-hover-20x20-dark,pill-20x20-dark"])
        self.assertEqual(0, rc, out)
        self.assertIn("带内均值=", out)
        self.assertIn("变化像素逐点中位=", out)
        # 负对照这一格必须真的两向：帧↔自身读出 0，否则"尺在量差"这句话没有证人。
        m = _ruler.measure(self.dir, "pill-hover-20x20-dark", "pill-hover-20x20-dark")
        self.assertEqual(0, m["changed"])

    def test_no_hard_coded_round_directory_in_the_ruler_itself(self):
        # 253 那条守卫扫全仓，这里只补一句尺自己的合同：路径只能来自通道参数。
        text = open(SCRIPT, encoding="utf-8").read()
        self.assertIn("CLIPBOARD_HISTORY_UI_SHOTS", text)
        self.assertNotIn(u"/" + u"tmp/shots_" + u"r1", text)


if __name__ == "__main__":
    unittest.main()
