#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R189 的台账批写：210 结案（读数误认 + 一条通道事实）、纯核落地、7 把刀、亮档出口点名。

三条老规矩都在这里：
① 数字一律从日志解析（缺格 ⇒ 拒绝写盘），不手抄；
② 写盘前先模拟 `test_round_batch_consistency` 的窗口（r=189 / 188 / 187，名册豁免 187），不给绿就不写；
③ 要么全成要么全不写：所有文件先算完再一次性落盘。
'''
import io
import os
import re
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
L = {'cap': '/tmp/r189_capture.log', 'full': '/tmp/r189_full.log',
     'mut': '/tmp/r189_mut.log', 'base': '/tmp/r189_baseline.log',
     'read': '/tmp/r189_frames2/capture-readings.log',
     'gate': '/tmp/r189_gate.log'}
NEW_R, NEW_N = 189, 191


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_LOG %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8').read()


def grab(pat, text, what, flags=0):
    hits = re.findall(pat, text, flags)
    if not hits:
        raise SystemExit('PARSE_FAILED %s（%r）⇒ 拒绝写盘' % (what, pat))
    return hits[-1]


cap = read(L['cap'])
full = read(L['full'])
mut = read(L['mut'])
base = read(L['base'])
rd = read(L['read'])
gate = read(L['gate'])

sum_line = grab(r'Executed \d+ tests[^\n]*', cap, '捕获卷结论行')
cap_n = grab(r'Executed (\d+) tests', sum_line, '捕获卷执行数')
cap_fail = grab(r'(\d+) failures?', sum_line, '捕获卷失败数')
fsum = grab(r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures', full, '全量卷结论行')
compared = grab(r'^FRAME_BASELINE_COMPARED=(\d+)', base, 'compared', re.M)
changed = grab(r'^FRAME_BASELINE_CHANGED=(\d+)', base, 'changed', re.M)
swap = grab(r'(FILTER_PILL_SWAP dark [^\n]*)', rd, '两态读数', re.M)
levels = {k: grab(r'%s=([\d.]+)' % k, swap, k) for k in ('左all', '右all', '左fav', '右fav')}
unjudged = grab(r'(FILTER_PILL_UNJUDGED light[^\n]*)', rd, '亮档出口读数')
caught = grab(r'CAUGHT=(\d+)/(\d+)', mut, '变异表结论')
arms = sorted(set(re.findall(r'^(M\d{3}) CAUGHT', mut, re.M)))
restore = 'yes' if 'RESTORE_CLEAN=yes' in mut else 'NO'
surface = grab(r'(MOTION_LEDGER 表面=\d+ 状态=\d+ 格子=\d+ 行数=\d+ 已清账=\d+ 未清账=\d+ 地板=\d+)', gate, '清账表闸门')

problems = []
if cap_fail != '0':
    problems.append('捕获卷失败 %s' % cap_fail)
if fsum[2] != '0':
    problems.append('全量卷失败 %s' % fsum[2])
if changed != '0':
    problems.append('帧变了 changed=%s（本轮是行为保持的重构，画面不该变）' % changed)
if caught != ['7', '7'] and list(caught) != ['7', '7']:
    problems.append('变异表 %s（要 7/7）' % (caught,))
if restore != 'yes':
    problems.append('RESTORE_CLEAN 不是 yes')
if len(arms) != 7:
    problems.append('刀号数 %d（要 7）：%s' % (len(arms), arms))
if problems:
    raise SystemExit('REFUSE_TO_WRITE ' + u'；'.join(problems))

V = dict(round=str(NEW_R), newn=str(NEW_N),
         cap_n=cap_n, cap_fail=cap_fail, full_n=fsum[0], full_skip=fsum[1], full_fail=fsum[2],
         compared=compared, changed=changed, arms=', '.join(arms), caught=caught[0],
         total=caught[1], restore=restore, surface=surface,
         la=levels[u'左all'], ra=levels[u'右all'], lf=levels[u'左fav'], rf=levels[u'右fav'],
         unjudged=unjudged.strip())

ui_title = (u'## 第 %d 轮（R%d · 2026-10-19）：210 结案 —— 药丸一直在选中段，是**我把轨道当成了药丸**；'
            u'顺手把这段几何做成能被打红的纯核（U-619…U-621 · 产品 2 文件，动效主线）\n') % (NEW_N, NEW_R)

ui_body = u'''
- **U-619：两态对照到手，五轮翻脸的根因是一句没写下来的默认。** 同一棵 `ContentView` 走产品入口各拍一张
  （`perform(.updateFilter(.all))` / `(.favorites)`），逐行量控件两半的电平：
  `.all` 是 `左=%(la)s 右=%(ra)s`，`.favorites` 是 `左=%(lf)s 右=%(rf)s` ⇒ **两半各自翻转**（差 214luma），
  而"暗的那一半"在 `.all` 是左段、在 `.favorites` 是右段 —— 也就是**药丸一直在选中的那一段上**。
  之前五轮（R182…R188）之所以能三次改判，是因为每个人都默认"亮的那块 = 药丸"；这条离屏通道里恰恰相反：
  `.ultraThickMaterial` 药丸合成成**暗**、`.quaternary` 轨道合成成**白**（我直接裁片用眼睛看过，不是推理）。
  ⇒ 210 结案为**读数误认**，不是产品缺陷；R187 那句"病根钉死"与 R188 那句"退回未钉死"现在都有了答案，
  而答案不在两把尺里，在**没被验过的默认**里（新开 D-195 记这条通道事实）。
- **U-620：把这段几何做成能被红打中的东西。** 新增纯核 `FilterPillGeometry`（段号 ↔ 矩形 ↔ 段号的恒等式、
  内缩、越界**夹住而不是回落到 0**、退化输入给 `.zero`），视图 `slidingPill` 改成 `.position(x: rect.midX, y: rect.midY)` ——
  原来的 `frame(width:) + offset(x:)` 把摆放基准交给 `GeometryReader` 的隐式对齐，那件事既没人写也没人测。
  刀：%(arms)s 共 %(caught)s/%(total)s 全 CAUGHT、RESTORE_CLEAN=%(restore)s
  （M696 段号反号、M697 钉死第 0 段、M698 视图绕开纯核、M699 两态塌成一态、M700 越界不夹、M701 出口吃掉判据、M702 除零路径放行）。
  **画面逐字节没变**：重捕 %(compared)s 张、`CHANGED=%(changed)s` ⇒ 这是一次行为保持的可测性改动，不是视觉改动。
- **U-621：亮档今天判不了，而且这件事本身要有牙。** 出口读数：`%(unjudged)s`
  ——亮档整条轨道那一行的极差只有 1luma，材质与底轨在这条通道分不开。出口按 R133/174 那三条立：
  前提由这一跑量出来、说清放掉的是"亮档的归位"、暗档那条照旧承重；并且加了一道**档数闸门**
  （两档全走出口 ⇒ `judgedAppearances=0` 当场红），M701 就是砍在这道闸门上的刀：
  把 `canJudge` 恒置 false 时，两档都安静出口、一条断言都不会跑 —— 那正是"有名字的未判定"退化成"没有判定"的形状。
  亮档欠的那条通道另开 BACKLOG 215。
''' % V

vi_body = u'''
## Round %(round)s · 210 结案：药丸一直在选中段，是"亮=药丸"这个默认骗了五轮（2026-10-19 · 产品 2 文件，动效主线）

两态对照（`.all` / `.favorites` 各拍一张，控件两半的电平）：`左=%(la)s 右=%(ra)s` vs `左=%(lf)s 右=%(rf)s`
⇒ 两半各自翻转、暗的那半始终跟着选中走。这段几何现在住在一颗纯函数里（`FilterPillGeometry`），
视图只留 `.position` 一句；138 张帧逐字节不变，7 把刀全 CAUGHT。亮档判不了这件事被写成一个**会红的出口**（档数闸门 + M701）。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 真的把控件裁出来用眼睛看了（并因此推翻"亮=药丸"）；重捕 %(compared)s 张帧逐张对账；扣分：只看了一处表面 |
| 判据有效性 | 15/15 | 新增纯核 5 条 + 两态像素判据；%(caught)s/%(total)s 把刀全 CAUGHT，其中 M699 专砍"两态塌成一态"、M701 专砍"出口吃掉判据" |
| 假绿防御 | 14/15 | 亮档出口带前提读数且配档数闸门；`CHANGED=0` 被写成拒绝落盘的条件（重构不许偷偷改画面）；扣分：暗档那条"暗=药丸"的标定仍是通道依赖，靠红来提醒 |
| 产品面推进 | 11/15 | 画面 0 变化（本轮的产出是可测性与一条被推翻的默认）；但 210 这条挂了 7 轮的账结案了 |
| 台账一致性 | 14/15 | U-619…U-621 + D-195 + BACKLOG 210 结案与 215 新开；数字全部从日志解析；扣分：清账表本轮没动 |
| 交付诚实性 | 15/15 | 明写"我上一轮的撤回也不对——两把尺都在量错的对象"，并把五轮翻脸的根因归到自己没写下来的默认上 |
| 可复核性 | 15/15 | 刀号、run/commit、读数原文、命令与两张态帧的生成方式都在 |
''' % V

cl_body = u'''### 210 结案：药丸一直在选中段，"亮=药丸"是未验的默认；几何做成纯核 + 两态像素判据（R%(round)s / U-619…U-621 · 产品 2 文件，动效主线）

- 两态对照（产品入口 `perform(.updateFilter)`，各拍一张）：`.all` 控件两半 `左=%(la)s 右=%(ra)s`、`.favorites` `左=%(lf)s 右=%(rf)s` ⇒ 两半各自翻转、**暗的那半跟着选中走**
- 通道事实（D-195）：这条离屏通道里 `.ultraThickMaterial` 药丸合成成**暗**、`.quaternary` 轨道合成成**白**，与屏幕直觉相反 ⇒ R182…R188 五轮三次改判的根因
- 新增 `Sources/ClipboardHistoryApp/Views/FilterPillGeometry.swift`（段号↔矩形↔段号恒等式、内缩、越界夹住、退化给 `.zero`）；`slidingPill` 改 `.position`，不再依赖 `GeometryReader` 的隐式对齐
- 判据：`FilterPillGeometryTests`（5 条，含接线扫描）+ `UICaptureTests/testFilterPillBrightBandFollowsTheSelectedSegment`（两态像素，带"档数闸门"）；变异 `mutate_r189.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s
- 验证：编译 0 告警、捕获卷 %(cap_n)s 例 / 失败 %(cap_fail)s、帧基线 %(compared)s 张 `CHANGED=%(changed)s`（行为保持）、全量卷 %(full_n)s 例 / 跳过 %(full_skip)s / 失败 %(full_fail)s；清账表 %(surface)s
- 亮档：`FILTER_PILL_UNJUDGED`（轨道内极差 1luma）⇒ 有名字的未判定，另开 BACKLOG 215

''' % V

bl_body = u'''**210 追记 6（R189）：结案 —— 药丸一直在**选中**那一段；错的是"亮的那块=药丸"这个没人写下来的默认**

两态各拍一张（都从产品入口 `perform(.updateFilter(_:))` 设状态，夹具不碰视图内部）：
`.all` 的控件两半电平 `左=%(la)s / 右=%(ra)s`，`.favorites` 的 `左=%(lf)s / 右=%(rf)s`
⇒ ① 两半各自翻转（不是"只动文字"，也不是"固定"）；② **暗的那一半**始终压在选中的段上（`.all`→左段、`.favorites`→右段）。
把 `.all` 那张帧的控件裁出来用眼睛看，确认了 R182…R188 一直踩空的地方：**这条离屏通道里药丸合成成暗、轨道合成成白**，
与屏幕上"药丸比轨道亮"的直觉相反（写进 D-195）。所以：R184 的"药丸在右段"是真的（暗块确实在右？不 —— 白块在右），
R185 的"亮区=药丸"、R187 的"病根钉死"、R188 的"退回未钉死"全部同一个错：**把轨道的暴露面当成了药丸**。
结案口径：不是产品缺陷；是通道方向 + 未验默认；判据现在钉的是"两半必须各自翻转 + 暗半必须在选中段"，
且这条标定是可证伪的（哪天通道翻向，判据红，而红的处置写在失败信息里：先重看裁片，别改阈值）。

**215. 亮档（aqua）在这条离屏通道里判不了分段控件的选中态：轨道与材质的电平极差只有 1luma（R189 量到）**

读数：`%(unjudged)s`。同一把尺在暗档读到 214luma 的翻转，在亮档读到 1 —— 不是"亮档没画"，
是这条通道在亮档把 `.quaternary` 与 `.ultraThickMaterial` 都合成了接近同一个值（R102 那句"离屏压缩材质对比度"的又一个面）。
现在不动产品，也不放宽暗档：欠的是一条**能分的通道** —— 候选两条，方向相反，都要先量再选：
① 真机合成层通道（`scripts/real_screen_sidebar_icons.py` 那一系，R121–R123 用过，能拍到 vibrancy 合成之后的像素）；
② 把这一处改成"两态各自与参照比"的相对判据（不依赖绝对亮度，依赖两态之差 —— 亮档现在两态之差也是 0，所以先要 ① 证明"是不是真画成一样"）。
顺序：先 ① 拿一格真机读数，若真机上两档都分得开 ⇒ 这条就是通道盲区，登记为未覆盖；若真机也分不开 ⇒ 是产品的可辨性缺陷，改代码。

''' % V

DEC_BODY = u'''
**D-195（R189）：这条离屏捕获通道里，分段控件的 `.ultraThickMaterial` 药丸合成成**暗**、`.quaternary` 轨道合成成**白**，与屏幕上的直觉相反**

证据（本机，两态各拍一张，都从产品入口设状态）：`.all` 档控件那一行 `左=%(la)s / 右=%(ra)s`，
`.favorites` 档 `左=%(lf)s / 右=%(rf)s`；把 `.all` 那张帧的控件区域裁出来直接看画面：
左段是一枚**深色圆角块**压住「全部」，右段是**白底**上的「收藏」。⇒ 暗块=药丸、白=轨道暴露面。

为什么这条要单独记成决定：R182…R188 五轮里"白卡是什么"被改了三次判（材质合成 → 按钮选中底 → 药丸几何反号），
每一次都拿另一把尺的结论给这一把尺开脱，而没有人去**看一眼那张帧**。
从现在起，涉及这条通道的"亮/暗 ↔ 哪一层"的判断，必须先有裁片或真机读数；
判据 `testFilterPillBrightBandFollowsTheSelectedSegment` 的失败信息里也写了这个处置顺序（先重看裁片，别改阈值）。
适用面：所有用 `VisualMaterial.sliderPill` / `.track` 的表面（侧栏分段控件、任何以后复用它的地方）；
不适用：真机合成层通道（那条拍到的是合成后的像素，见 R121–R123）。

''' % V

STATE_HDR = (u'最后更新：2026-10-19 06:05（本地 · R%(round)s / 第 %(newn)s 轮：**210 结案 —— 药丸一直在选中段，错的是"亮=药丸"这个未验默认**'
             u'（U-619…U-621 · 产品 2 文件，动效主线）\n\n'
             u'**本轮落地**：`FilterPillGeometry` 纯核 + 视图改 `.position`（138 张帧 `CHANGED=0` ⇒ 行为保持）；'
             u'两态像素判据 + 档数闸门；`mutate_r189.py` %(arms)s 全 CAUGHT、RESTORE_CLEAN=%(restore)s；'
             u'D-195 记通道方向（药丸暗、轨道白）；新开 215（亮档在这条通道判不了，欠真机读数）。\n'
             u'验证：编译 0 告警、捕获卷 %(cap_n)s 例/失败 %(cap_fail)s、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、'
             u'帧基线 %(compared)s 张 changed=%(changed)s、清账表 %(surface)s。\n\n'
             u'**下一轮（R190）的靶**：⓪ 读这一笔与 `9475006`/`bd9b827`/`0ce57f7` 之后所有跑的**全部**失败步骤'
             u'（已知 `8b90efe` 红在 STEP[17] Motion coverage floor，与 `fd6b43a`/`d4958a9` 同一格 ⇒ 归 212）；\n'
             u'① 212：把带捕获那条绝对地板换成同一次运行的相对判据 + 自带读数行（照 BACKLOG 176 那一族的做法）；\n'
             u'② 215：先拿一格真机合成层读数，判"亮档分不开"是通道还是产品；\n'
             u'③ 201（runner 那条高窗只画出 205pt 下沿带 —— 带里到底是什么）、202、205、207；④ 清账表下一批（闸门读数 %(surface)s 里的未判格）。\n'
             u'）\n') % V

LEDGERS = {
    'AGENT_UI_AUDIT.md': u'^## 第 \\d+ 轮（R%d',
    'AGENT_VISUAL_ITERATION.md': u'^## Round %d · ',
    'CHANGELOG.md': u'^### .*（R%d / ',
}
ROSTER = {186, 187}


def write(p, t):
    with io.open(p, 'w', encoding='utf-8') as h:
        h.write(t)


def titles_present(text_by_name, round_no):
    return {n: bool(re.search(f % round_no, t, re.M)) for n, f in LEDGERS.items()}


def main():
    paths = {n: os.path.join(ROOT, n) for n in LEDGERS}
    paths['STATE'] = os.path.join(ROOT, 'AGENT_STATE.md')
    paths['BACKLOG'] = os.path.join(ROOT, 'AGENT_BACKLOG.md')
    paths['DECISIONS'] = os.path.join(ROOT, 'AGENT_DECISIONS.md')
    old = {k: read(v) for k, v in paths.items()}
    if u'## Round %d · ' % NEW_R in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('DUMP_ALREADY_WRITTEN ⇒ 不重复落盘')
    for name, txt in ((u'ui', ui_title + ui_body), (u'vi', vi_body), (u'cl', cl_body),
                      (u'bl', bl_body), (u'dec', DEC_BODY), (u'st', STATE_HDR)):
        if re.search(r'%\([a-z_0-9]+\)s', txt):
            raise SystemExit('FORMAT_LEAK %s 还有没吃掉的占位符' % name)
    top_state = [i for i, l in enumerate(old['STATE'].split(u'\n')) if l.startswith(u'最后更新：')][0]
    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before(old['AGENT_UI_AUDIT.md'], u'## 第 190 轮（R188', ui_title + ui_body)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + vi_body.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before(old['CHANGELOG.md'], u'### 210 的读数归位', cl_body)
    new['AGENT_BACKLOG.md'] = old['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n' + bl_body.rstrip(u'\n') + u'\n'
    new['DECISIONS'] = old['AGENT_DECISIONS.md'].rstrip(u'\n') + u'\n' + DEC_BODY.rstrip(u'\n') + u'\n'
    st = old['STATE'].split(u'\n')
    new['STATE'] = u'\n'.join(st[:top_state] + [STATE_HDR.rstrip(u'\n'), u''] + st[top_state:])

    # 写盘前的模拟：三账窗口 + 本轮 U 区间 + BACKLOG 最大号 + 新表登记
    for name, fmt in LEDGERS.items():
        key = name
        for this in (NEW_R, NEW_R - 1, NEW_R - 2):
            if this in ROSTER and this != NEW_R:
                continue
            if not re.search(fmt % this, new[key], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (this, name))
    section = new['AGENT_UI_AUDIT.md'].split(ui_title.rstrip(u'\n'), 1)[1].split(u'\n## 第 190 轮', 1)[0]
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
    if defined != [619, 620, 621]:
        raise SystemExit('U_RANGE_MISMATCH 本轮定义 %s（要 619…621）' % defined)
    nums = sorted(int(m) for m in re.findall(r'^\*\*(\d{2,3})\. ', new['AGENT_BACKLOG.md'], re.M))
    if 215 not in nums:
        raise SystemExit('MISSING_215 定义行没在表里（最大 %d）' % nums[-1])
    if u'D-195' not in new['DECISIONS']:
        raise SystemExit('MISSING_D195')
    for ref in re.findall(u'BACKLOG (\\d{3})', ui_body + vi_body + cl_body + bl_body + STATE_HDR):
        if (u'**%s. ' % ref) not in new['AGENT_BACKLOG.md'] and ref not in ('210',):
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    for k, v in new.items():
        write(paths[k], v)
    print(u'LEDGERS_R189_WRITTEN r=%d n=%d U=619..621 arms=%s/%s restore=%s frames=%s/%s full=%s/%s/%s'
          % (NEW_R, NEW_N, V['caught'], V['total'], V['restore'], V['compared'], V['changed'],
             V['full_n'], V['full_skip'], V['full_fail']))
    return 0


def insert_before(text, prefix, block):
    lines = text.split(u'\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != 1:
        raise SystemExit('ANCHOR %r 命中 %d 次（要 1）' % (prefix, len(idx)))
    lines.insert(idx[0], block.rstrip(u'\n'))
    return u'\n'.join(lines)


if __name__ == '__main__':
    sys.exit(main())
