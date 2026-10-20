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
import re
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
# 同一个 80:30 在 **WCAG 线性口径**下的手算（仓库 1.20/1.10 那条地板就是这个口径）：
#   L(80)=((0.3137254902+0.055)/1.055)^2.4=0.080182，L(30)=((0.1176470588+0.055)/1.055)^2.4=0.012973
#   ⇒ (0.0801905+0.05)/(0.0129728+0.05)=0.1301905/0.0629728=2.067538 ⇒ 四舍五入 2.068
#   （期望值由独立算式现算，不许心算：第一版我手算成 2.067，被自己这一格红回来）
RATIO_LIT_VS_BG_WCAG = 2.068
# 亮档那一族（R243 / D-229 的真靶）：白底 255 上 alpha=0.085 的悬停层 ⇒ 合成灰 255×(1−0.085)=233.325
#   码值口径 (1.0+0.05)/(233/255+0.05)=1.05/0.9637254902=1.08951 ⇒ 1.090 —— **看着低于 1.20**
#   WCAG 口径  L(255)=1.0，L(233)=((233/255+0.055)/1.055)^2.4=0.814869
#              ⇒ 1.05/(0.814869+0.05)=1.05/0.864869=1.21405 ⇒ 1.214 —— **过地板**
WHITE, LIFT_085 = 255, 233
RATIO_LIGHT_HUFF_CODE = 1.090
RATIO_LIGHT_HUFF_WCAG = 1.214


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

    def add(self, name, size=(10, 10), spots=(), fill=BG):
        write_frame(self.dir, name, size, spots, fill)

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
        self.assertEqual(RATIO_LIT_VS_BG_WCAG, m["per_pixel_wcag"],
                         "同一对像素在 WCAG 线性口径下手算 2.067 ⇒ 两个口径不许互相当对方的证人")

    def test_the_light_hover_fill_clears_the_floor_only_in_the_floor_s_own_estimator(self):
        """R243 / D-229：这一格钉的是**别拿错口径给产品定罪**。

        白底上 alpha=0.085 的悬停层合成出 233，码值口径读 1.090、WCAG 口径读 1.214。
        仓库那条"亮档 ≥1.20"地板是 WCAG 口径（`UICaptureHarness.contrastRatio` 做了 2.4 次幂线性化），
        所以 1.090 < 1.20 这句话**不成立** —— R240 那次拦下改档、R243 又差点按它抬梯子，同一坑两种形状。
        两列同时断言：只断言一列的话，另一列被改坏就没人报。
        """
        write_frame(self.dir, "pill-hover-10x10-light", (10, 10), block(0, 0, 2, 5, LIFT_085), WHITE)
        write_frame(self.dir, "pill-10x10-light", (10, 10), (), WHITE)   # 平涂白底：亮档才是这一格的对象
        m = _ruler.measure(self.dir, "pill-hover-10x10-light", "pill-10x10-light")
        self.assertEqual(10, m["changed"])
        self.assertAlmostEqual(RATIO_LIGHT_HUFF_CODE, m["per_pixel"], places=3,
                               msg="码值口径应当复现 1.090（=1.05/0.9637254902）")
        self.assertAlmostEqual(RATIO_LIGHT_HUFF_WCAG, m["per_pixel_wcag"], places=3,
                               msg="WCAG 口径应当复现 1.214 ⇒ 地板按这个口径才有效")
        self.assertLess(m["per_pixel"], 1.20, "码值口径确实在 1.20 之下 —— 这正是假缺陷的来源")
        self.assertGreaterEqual(m["per_pixel_wcag"], 1.20,
                                "同一块填充在地板自己的口径里是过了的 ⇒ 不许按 1.09 改产品")

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
        self.assertIn("变化像素逐点中位(码值)=", out)
        self.assertIn("WCAG口径", out)
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

@unittest.skipIf(NO_PIL_OR_RULER, u"缺 PIL 或读不到尺：这两格要能被点名，不许静默通过")
class FloorVerdictTests(RulerTestCase):
    """地板判定必须只看 WCAG 那一列，且**底不平涂时不许判**（R244 / D-229 / BACKLOG 282）。"""

    def test_a_weak_light_hover_is_named_by_the_floor_verdict(self):
        """平涂白底上只抬到 245（alpha≈0.04）⇒ WCAG 1.090 < 1.20 ⇒ 必须点名并 exit 1。

        期望值现算（不心算）：L(245)=((245/255+0.055)/1.055)^2.4=0.91310 ⇒ 1.05/(0.91310+0.05)=1.09024。
        """
        self.add(u"pill-hover-20x20-light", (20, 20), block(0, 0, 10, 10, 245), WHITE)
        self.add(u"pill-20x20-light", (20, 20), (), WHITE)
        m = _ruler.measure(self.dir, u"pill-hover-20x20-light", u"pill-20x20-light")
        self.assertTrue(m[u"idle_flat"], u"整块平涂白底 ⇒ 这一格的对象是「底平」")
        self.assertEqual(1.090, m[u"per_pixel_wcag"], u"WCAG 现算 1.09024 ⇒ 四舍五入 1.090")
        self.assertEqual(u"低于地板", m[u"verdict"])
        rc, out = self.cli([u"--shots", self.dir,
                            u"--control", u"pill-hover-20x20-light,pill-20x20-light"])
        self.assertEqual(1, rc, u"平涂底上弱悬停被判低于地板却不 exit 1 ⇒ 地板只是装饰")
        self.assertIn(u"HOVER_DIFF_FLOOR_RED=1", out)

    def test_a_nonflat_base_is_reported_as_a_reading_not_a_verdict(self):
        """同一块弱填充放在**抖动底**上（250/255 棋盘，众数只占一半）⇒ 只报读数、不判、不红。

        这一格钉的是 R242 那台 runner 的形状：底不是平涂时「对底比值」没有单一的底可对，
        硬判就会造出跨机假红；但也不许因此把整行吞掉 —— 读数照打。
        """
        dither = [(x, y, WHITE) for y in range(10) for x in range(10) if (x + y) % 2 == 0]
        self.add(u"pill-hover-20x20-light", (20, 20), block(0, 0, 10, 10, 245), 250)
        self.add(u"pill-20x20-light", (20, 20), dither, 250)
        m = _ruler.measure(self.dir, u"pill-hover-20x20-light", u"pill-20x20-light")
        self.assertFalse(m[u"idle_flat"], u"棋盘底众数只占 50%% ⇒ 不该被当成平涂")
        self.assertLess(m[u"per_pixel_wcag"], 1.20,
                        u"这一格要的就是「数值上确实低于地板」—— 不然下一句断言没有对象")
        self.assertEqual(u"只报读数（底不平涂）", m[u"verdict"])
        rc, out = self.cli([u"--shots", self.dir,
                            u"--control", u"pill-hover-20x20-light,pill-20x20-light"])
        self.assertEqual(0, rc, u"底不平涂的那一格不许变成红（但读数必须照打）")
        self.assertNotIn(u"HOVER_DIFF_FLOOR_RED", out)
        self.assertIn(u"判定=只报读数", out)


# R252 / BACKLOG 297：**已登记的地板红名册**（欠账的账期，不是豁免）。
# 现读（/tmp/shots_r252，168 张，尺 退出=1）：`detail-3-files-row0-hover-720x520-light`
# 的悬停在 WCAG 口径下只有 1.171（地板 1.20）⇒ 多文件行在**亮档**的悬停墨淡到没有读者。
# 同一位暗档 1.257 过线；而"整列一起亮"那一对（detail-3-files-hover-*）两档都过线
# —— R251 那句"两档过线"是**归属没对上**造成的假绿（D-237 预言的正是这件事）。
# 双向对账：① 名册里的名字现在必须真的红（不红=名册过期）；② 现在红的必须在名册里（不在=新缺陷）。
# ⇒ 这张表只能被"修好产品"清空，不能被"再加一行"放宽。
KNOWN_FLOOR_RED = {
    'detail-3-files-row0-hover-720x520-light':
        u'亮档多文件行的悬停墨淡到没有读者（现读 1.171 < 1.20）；这是产品缺陷不是判据过严，'
        u'修法见 BACKLOG 297（按色档取墨，暗档 1.257 不动）',
}


@unittest.skipIf(NO_PIL_OR_RULER, u"缺 PIL 或读不到尺：这一格要能被点名")
class RealFrameFloorTests(RulerTestCase):
    """真帧那一格：把「亮档偏淡」这类候选缺陷变成**standing 判据**（R244 / BACKLOG 282）。

    帧目录由 `CLIPBOARD_HISTORY_UI_SHOTS` 给；不在就是具名 skip（NOT-RUN），
    不许把「没帧」读成「没问题」。正对照从帧名里现取，不写死 —— 写死的名字一漂，
    这一格就会在没有任何产品判断的情况下绿（R102 那一族）。
    """

    def setUp(self):
        RulerTestCase.setUp(self)          # 底座建自己的临时目录；这一格读的是真帧通道
        self.dir = os.environ.get(u"CLIPBOARD_HISTORY_UI_SHOTS")
        if not self.dir or not os.path.isdir(self.dir):
            self.skipTest(u"CLIPBOARD_HISTORY_UI_SHOTS 未设或目录不在 ⇒ 真帧地板那一格 NOT-RUN（不是通过）")

    def test_every_real_pair_clears_the_floor_or_is_named_nonflat(self):
        pairs, unpaired = _ruler.find_pairs(self.dir)
        if not pairs:
            self.skipTest(u"目录里没有「悬停↔静置」配对 ⇒ 这一格没有对象（帧目录=%s）" % self.dir)
        app, hover, idle = pairs[0]
        rc, out = self.cli([u"--shots", self.dir,
                            u"--control", u"%s,%s" % (hover, idle)])
        rows = re.findall(r"HOVER_DIFF (\S+) 对=(\S+) .*?判定=(\S+?) ", out)
        self.assertEqual(len(pairs), len(rows),
                         u"配到 %d 对却只解析到 %d 行判定 ⇒ 读数行形状漂了" % (len(pairs), len(rows)))
        ok_verdicts = (u"过线", u"只报读数（底不平涂）", u"低于地板")
        bad = [(a, p, v) for a, p, v in rows if v not in ok_verdicts]
        red = set(p.split(u"↔")[0] for _, p, v in rows if v == u"低于地板")
        print(u"HOVER_FLOOR_REAL 配对=%d 无静置态=%d 退出=%d 判定=%s" % (
            len(pairs), len(unpaired), rc,
            u','.join(u'%s:%s' % (p.split(u'↔')[0][:28], v) for _, p, v in rows)))
        self.assertEqual([], bad, u"有对的判定行读不出形状")
        self.assertEqual(set(KNOWN_FLOOR_RED), red,
                         u"地板红名册与现读不同源 ⇒ 名册过期（修好了没删）或出现了新缺陷（没登记）：\n"
                         u"  名册=%s\n  现读=%s" % (sorted(KNOWN_FLOOR_RED), sorted(red)))
        for name, why in KNOWN_FLOOR_RED.items():
            self.assertGreaterEqual(len(why), 20, u'%s 的理由不足 20 字 ⇒ 名册成了垃圾桶' % name)
        expected_rc = 1 if red else 0
        self.assertEqual(expected_rc, rc,
                         u"退出码应与名册一致（有登记的红=尺自己响，期望 1；空名册=期望 0）：%s" % out[-400:])
        print(u"HOVER_FLOOR_RED_KNOWN=%d 名册=%s 现读=%s 退出=%d" % (
            len(red), sorted(KNOWN_FLOOR_RED), sorted(red), rc))

