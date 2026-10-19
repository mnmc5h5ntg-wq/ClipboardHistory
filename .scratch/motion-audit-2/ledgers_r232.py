# -*- coding: utf-8 -*-
"""R232 的台账（补记形状）：258 第二处结案 —— 详情区那颗「原文 / 渲染」控件第一次有两态帧。

只写**追加型**的两本（BACKLOG 追记 + CHANGELOG 插在 [Unreleased] 之下）：本轮按补记落账
⇒ 不轮换 AGENT_STATE、不开新的 U/D 编号（那要连 ITERATION 的七维表与 U 区间一起写，预算不够；
半份账比没账更坏，所以把"没写哪几本"显式记进账里）。
数字全部现读、读不到就拒绝写盘：刀读数从 `mutate_r232.py` 那一跑的日志解析，
帧读数从 `frame_baseline.py compare` 现跑，全量卷从捕获/全量日志的 `Test Case` 行计数。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
SHOTS = '/tmp/shots_r232'
MUT_LOG = '/tmp/r232_mutate_run.log'
FULL_LOG = '/tmp/r232_fulltest.log'


def read(p):
    return io.open(os.path.join(ROOT, p) if not p.startswith('/') else p, encoding='utf-8').read()


def write(p, t):
    io.open(os.path.join(ROOT, p) if not p.startswith('/') else p, 'w', encoding='utf-8').write(t)


def die(why):
    print('LEDGERS_R232 refused: ' + why)
    sys.exit(1)


def sh(cmd):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    env.pop('SDKROOT', None)
    p = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


# ————————————————————— 读数（三本都要有来源）—————————————————————
if not os.path.isfile(MUT_LOG):
    die('刀日志不在：' + MUT_LOG + ' ⇒ 没跑过的刀不许写进账')
mt = read(MUT_LOG)
mstat = re.search(r'R232_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)', mt)
mclean = re.search(r'RESTORE_CLEAN=(\w+)', mt)
if not mstat or not mclean:
    die('刀读数解析失败：' + mt[-300:])
if mstat.group(3) != '0' or mstat.group(4) != '0' or mclean.group(1) != 'yes':
    die('刀这一跑不干净（ESCAPED/NOT_RUN/RESTORE 之一不为零）⇒ 先修刀再写账')
knives = 'R232_MUTATE 刀=%s CAUGHT=%s ESCAPED=%s NOT_RUN=%s｜RESTORE_CLEAN=%s' % (
    mstat.group(1), mstat.group(2), mstat.group(3), mstat.group(4), mclean.group(1))

if not os.path.isdir(SHOTS):
    die('帧目录不在：' + SHOTS + ' ⇒ 看图腿与帧对账都没有对象（空对账，R140）')
n_png = len([f for f in os.listdir(SHOTS) if f.endswith('.png')])
code, cmp_text = sh(['python3', 'scripts/frame_baseline.py', 'compare', SHOTS, '--against', 'working'])
if code != 0:
    die('帧对账返回非零：' + cmp_text[-200:])
mcmp = re.search(r'FRAME_BASELINE_COMPARED=(\d+)', cmp_text)
mchg = re.search(r'FRAME_BASELINE_CHANGED=(\d+)', cmp_text)
if not (mcmp and mchg):
    die('帧对账读数解析失败：' + cmp_text[:200])
compared, changed = int(mcmp.group(1)), int(mchg.group(1))
if compared == 0:
    die('COMPARED=0 ⇒ 空对账（R140）')
if changed != 0:
    die('CHANGED=%d ⇒ 本轮不打算把任何旧帧的像素洗进基线，先分辨再落账' % changed)
if n_png != compared:
    die('帧数与对账数不签字：目录里 %d 张 PNG，compare 报了 %d（两种口径不许互相作证）' % (n_png, compared))

if not os.path.isfile(FULL_LOG):
    die('全量卷日志不在：' + FULL_LOG)
ft = read(FULL_LOG)
passed = len(re.findall(r"Test Case '.*' passed", ft))
failed = len(re.findall(r"Test Case '.*' failed", ft))
skipped = len(re.findall(r"Test Case '.*' skipped", ft))
if failed != 0 or 'Test Suite ' + "'All tests' passed" not in ft:
    die('全量卷不干净：failed=%d，且没有 All tests passed 行' % failed)
if passed < 800:
    die('全量卷只数到 %d 条 passed ⇒ 掉档了（上一版是 863），不许当成跑过了' % passed)

# ————————————————————— 两本追加型台账 —————————————————————
BACKLOG_APPEND = u"""

## R231 补记第七笔（258 第二处结案：详情区那颗「原文 / 渲染」控件第一次有两态帧 · 2026-10-20）

- **病根**：`DetailView.MarkdownModeButton` 的悬停层在 R231 刚接进共享换算 `HoverInk.opacity`，
  但那只是**源码层的事实** —— 名册按**引用**计数，引用对而换算错（少一个色档出口）名册照样绿
  （R230 那朵 `233→228` 就是这么被抓到的）。"这一档灰对**它自己那片底**看不看得见"在像素上从来没有证人。
- **修法（产品 1 文件）**：摘 `private struct` → `struct`（夹具引用不到 `private`，先例 `SettingsSidebarRow`），
  接 `@Environment(\\.hoveredForCapture)`，把 `.fill(.primary.opacity(isHovered ? … : 0))` 提成 `hoverOpacity`
  —— 真实指针**或**取证通道点亮，两条汇到**同一个绘制分支**。**档位一字未改**（还是 `VisualFill.hover`）。
- **判据**：`modechip-hover-idle` / `modechip-hover-lit`（200×60、`contentMustFit`；族名另起，
  不撞那 7 处按 `hasPrefix("settings-")` 收对象的尺）+ `testModeChipHoverFillIsVisibleOnItsOwnSurface`
  四条断言（像素>400 / 两态不许同灰 / 比值压地板 / 空闲==同列上方背景）。
  矩形是**量出来的**：两档各自逐像素相减得到**同一条**差异带 px x166…233 / y78…105
  ⇒ pt `83.0…116.5 × 39.0…52.5`（33.5×13.5），与源码对得上才算归位
  （11pt 行高 + `padding(.horizontal, 6)` × 2 = 34pt、刻意无纵向 padding）。
- **读数**：亮 `255→220` 比值 **1.371**（地板 1.20）、暗 `30→52` 比值 **1.339**（地板 1.10），
  点亮像素 1281 / 1222 颗，两档空闲位都 == 同列上方背景（255 / 30）⇒ 取证通道没漏电。
  **这一档看得见，不为它开新的缺陷条目。** 顺带交出第二条产品事实：0.06 铺在白底只会到 240，
  读到的 220 只可能来自 R229 那个抬档出口 ⇒ 那一抬在**这颗控件**上真的落地了（以前只有注释撑着）。
- **看图腿真做**：两张 lit 帧（亮/暗）—— 药丸圆角完整、四边不贴字形、亮档比暗档更醒目，
  两档都还是"安静的行内动作"，不喧宾夺主 ⇒ 不加第二层效果。
- **刀**：%s（M779 摘产品侧出口 / M780 把夹具点亮写成 false；两刀都该红，都不许 skip）。
- **验证顺序**：构建 0 告警 → 新判据与 R231 那条一起跑（2 格 0 失败）→ 刀 → 重捕帧
  `COMPARED=%d CHANGED=0 ADDED=4`（旧帧哈希一条没动 ⇒ `hoveredForCapture` 为 nil 的产品路径像素零变化）
  → 基线同一笔 update（%d 帧）→ 全量卷 `passed=%d skipped=%d failed=%d`（All tests passed）
  → 换装本机 → 本台账 → 电池。
- **形状自曝**：本笔记按**补记**落账 ⇒ 不轮换 `AGENT_STATE.md`、不开新的 U/D 编号、
  也不给 `AGENT_VISUAL_ITERATION.md` 添整轮条目（那要连七维表与 U 区间一起写，本轮预算不够；
  半份账比没账更坏，所以在这里写明"没写哪几本"）。
- **仍未读**：R231 那四跑（5cf95fe→39319255032、f798ff8→39319908786、920c327→39321237675、
  e6c696b→39321432401）与本轮这一跑；下一轮第 ⓪ 条 = 读它们，并核对 `CI_PROFILE_OK` 的主语是不是 `github-runner`。
- **258 仍剩**第三处 `DetailView.swift:541`（`MultiFileRow`，同样还是 `private struct`，模式已验两遍）。
""" % (knives, compared, n_png, passed, skipped, failed)

CL_BLOCK = u"""### 详情区「原文 / 渲染」那颗控件的悬停档，第一次在像素上对账（R231 补记第七笔 / BACKLOG 258 第二处）

`MarkdownModeButton` 的悬停层在上一轮接进了共享换算，但"接进了"只有名册知道、帧上从来没有证人。
本轮摘掉 `private`、接上取证通道，两态各一张帧，四条断言各判一件事、谁也不替谁签字。
实测：亮 `255→220`（1.371:1，地板 1.20）、暗 `30→52`（1.339:1，地板 1.10），点亮像素 1281 / 1222 颗；
空闲那一帧的填充位与同列上方背景相等 ⇒ 取证通道没漏电。
**强度一字未改**，产品路径（没有指针）像素零变化：%d 帧对账 `CHANGED=0`、只多 4 张新帧。
两把刀（摘产品侧出口 / 把夹具点亮写成 false）都必须红，实测 `%s`。

""" % (compared, knives)

bl = read('AGENT_BACKLOG.md')
if u'R231 补记第七笔' in bl:
    die('BACKLOG 里已经有第七笔了 ⇒ 不许登记两次')
write('AGENT_BACKLOG.md', bl.rstrip('\n') + '\n' + BACKLOG_APPEND)

cl = read('CHANGELOG.md')
head, sep, rest = cl.partition(u'## [Unreleased]\n')
if not sep:
    die('CHANGELOG 找不到 [Unreleased] 锚点')
if u'BACKLOG 258 第二处' in cl:
    die('CHANGELOG 里已经有这一节了')
write('CHANGELOG.md', head + sep + CL_BLOCK + rest)

old = subprocess.run(['git', 'show', 'HEAD:CHANGELOG.md'], cwd=ROOT,
                     stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')
new = read('CHANGELOG.md').split('\n')
it = iter(new)
if not all(any(l == o for l in it) for o in old):
    die('CHANGELOG 的插入吃掉了 HEAD 里的行 ⇒ 这一本要回滚重跑')
print('LEDGERS_R232 ok｜BACKLOG+%d行 CHANGELOG+%d行｜frames=%d changed=%d｜全量卷 passed=%d skipped=%d failed=%d｜%s'
      % (BACKLOG_APPEND.count('\n'), CL_BLOCK.count('\n'), compared, changed,
         passed, skipped, failed, knives))
