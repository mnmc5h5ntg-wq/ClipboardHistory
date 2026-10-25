#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R341：真机尺两处修补（一次落盘）。

① **对象门**（`capture_identity` / `activate_and_wait`）：屏幕解锁后同一条调用链拍到的可能是
   别人的窗口（R341 撞到 Numbers 的保存对话框），而 `frame_ready` 只问「画完没有」⇒ 放行，
   旧尺接着报 `no_band` —— 一个关于产品的假结论。门问的是**对象**。
② **第二形状**（`pair_split` / `prefer_shape`）：R339 把选中那颗抬到轨道**之上**之后，
   真机上控件是 `左(选中)=107 / 右(未选)=80 / 页底=43`，而旧模型把「胶囊」定义成
   「容器里与页底同档的那一段」⇒ 修好之后那一段不存在 ⇒ 真机上永远判不出「好了没有」。
   第二形状只说产品本来的样子：一个控件、两段，选中段在**左**（产品打开时选中「全部」，这是输入）。
   两种形状都在时**先用旧的**（`prefer_shape`），同一台机器前后的读数才还是同一个量。
"""
import ast
import io

P = u"/Users/wangziyi/Codex_Project0/scripts/real_screen_filter_pill.py"
s = io.open(P, encoding=u"utf-8").read()

# ---------- ① 对象门 ----------
A_CONST = u'DELTA = 8.0                 # 与胶片那把尺同一个 delta（分箱/分离都按它算）'
CONST_NEW = A_CONST + u'''
APP_PROCESS = u"ClipboardHistoryApp"    # System Events 的**进程名**（= 可执行名，不是显示名「时间剪史」）


def capture_identity(frontmost, target=APP_PROCESS):
    u"""这一帧要拍的**对象**是不是它 —— 前台进程必须是目标进程。

    R341 当场撞的：`frame_ready` 只问「这帧画完了没有」（≥3 档电平各占 ≥2%），它答不了「这帧是谁」。
    屏幕解锁后同一条调用链拍到的是 Numbers 的保存对话框（用户的表格），背景中位 247、电平 26 档 ⇒
    放行，接着尺报 `no_band`（侧栏没有控件）—— 一个关于**产品**的假结论，而产品窗口根本不在前台。
    这是「尺读的不是它声称的对象」那一族第四次（D-090 / 176 / 372 之后）：闸门要问对象，不是像素多不多。

    三态，`ok` 之外都自带名字：
      `ok`                      前台就是目标进程 ⇒ 这一帧可以是它的
      `occluded_not_frontmost`  前台是别人 ⇒ 拍到的像素属于别人，这一格没跑
      `frontmost_unknown`       System Events 答不出前台 ⇒ 连对象都问不到，这一格没跑
    """
    if not frontmost:
        return u"frontmost_unknown"
    if frontmost == target:
        return u"ok"
    return u"occluded_not_frontmost"


def frontmost_name():
    rc, out = osascript(u'tell application "System Events" to get name of first application process '
                        u'whose frontmost is true')
    return out if rc == 0 and out else None


def activate_and_wait(pid, timeout=6.0):
    u"""把目标进程推到前台并**等它真的变成前台**；返回最后一次读到的前台名。

    `open -a` 起得来的进程不一定被激活，而 `screencapture -R` 拍的是**屏幕**、不是窗口 ——
    不在前台就拍到别人的窗口。所以这里不是「叫一声就完」，而是「叫到读数为准」。
    """
    deadline = time.time() + timeout
    name = frontmost_name()
    while time.time() < deadline and name != APP_PROCESS:
        osascript(u'tell application "System Events" to set frontmost of '
                  u'(first process whose unix id is %d) to true' % pid)
        time.sleep(0.4)
        name = frontmost_name()
    return name'''
assert s.count(A_CONST) == 1
s = s.replace(A_CONST, CONST_NEW, 1)

A_CALL = u"""        print("WINDOW x=%d y=%d w=%d h=%d" % bounds)
        ok, tries = wait_for_rendered_frame(bounds, png, max(6.0, args.timeout * 0.6))"""
CALL_NEW = u"""        print("WINDOW x=%d y=%d w=%d h=%d" % bounds)
        who = activate_and_wait(pid, max(4.0, args.timeout * 0.3))
        gate = capture_identity(who)
        print("CAPTURE_IDENTITY 前台=%s 目标=%s 判=%s" % (who, APP_PROCESS, gate))
        if gate != u"ok":
            print("REALSCREEN_NOT_RUN %s（前台是 %r，不是目标窗口 ⇒ 拍到的像素属于别人；"
                  "尺子不猜像素属于谁 —— 这一格是没跑，不是「侧栏没有控件」）" % (gate, who))
            return 1
        ok, tries = wait_for_rendered_frame(bounds, png, max(6.0, args.timeout * 0.6))"""
assert s.count(A_CALL) == 1
s = s.replace(A_CALL, CALL_NEW, 1)

A_AFTER = u"""        if not ok:
            print("REALSCREEN_NOT_RUN frame_not_rendered（截到的是未绘制的表面，不是「侧栏没有控件」）")
            return 1
        found, meta = scan(png, bounds[2])"""
AFTER_NEW = u"""        if not ok:
            print("REALSCREEN_NOT_RUN frame_not_rendered（截到的是未绘制的表面，不是「侧栏没有控件」）")
            return 1
        who2 = frontmost_name()
        gate2 = capture_identity(who2)
        print("CAPTURE_IDENTITY_AFTER 前台=%s 判=%s" % (who2, gate2))
        if gate2 != u"ok":
            print("REALSCREEN_NOT_RUN %s（拍照这一段时间里前台换成了 %r ⇒ 这一帧作废）" % (gate2, who2))
            return 1
        found, meta = scan(png, bounds[2])"""
assert s.count(A_AFTER) == 1
s = s.replace(A_AFTER, AFTER_NEW, 1)

# ---------- ② 第二形状 ----------
A_FN = u"def track_solidity(px, y_center_pt, x0_pt, x1_pt, track, scale, delta, height_pt=12):"
PAIR_FN = u'''def pair_split(profile, page, stride_px, scale, delta, gap=2):
    u"""两段式控件的第二形状：一个控件、左右两半，选中段在**左**。

    为什么要有它（R341 真机现读）：R339 把选中那颗抬到轨道**之上**以后，屏幕上是
    `左=107 / 右=80 / 页底=43`；而 `measure_row` 把「胶囊」定义成「容器里与页底同档的那一段」，
    修好之后那一段根本不存在 ⇒ 尺报 `no_band`（侧栏没有控件）。**修好了的产品被判成没有控件**，
    比不量更坏：它把人引回去改产品。

    形状只说产品本来的样子：侧栏那行是**一个控件、两段**；选中段是左边那一段
    （产品打开时选中「全部」—— 这是输入，不是从像素里猜的；换选另一段时本形状不适用）。
    两半按控件宽度中点切开，切口左右各让 `gap` 个采样点，免得把接缝读进任何一半。
    返回 None 的每种条件都写成可数的：不够宽 / 切不开 / 两半差不到一档。

    为了不出现两套下游口径，这里把「选中段」直接写成 `pill`、把「未选段」写成 `track`，
    `report()` 那一段一字不动 —— 换形状不换量纲。
    """
    if not profile or page is None:
        return None
    differs = [abs(v - page) >= delta for _x, v in profile]
    if not any(differs):
        return None
    first = differs.index(True)
    last = len(differs) - 1 - differs[::-1].index(True)
    extent = profile[first:last + 1]
    width_pt = (last - first + 1) * stride_px / scale
    if width_pt < MIN_CONTAINER_PT:
        return None
    mid = len(extent) // 2
    if mid - gap <= 0 or mid + gap >= len(extent):
        return None
    left = sorted(v for _x, v in extent[:mid - gap])
    right = sorted(v for _x, v in extent[mid + gap:])
    lvl_l, lvl_r = left[len(left) // 2], right[len(right) // 2]
    if abs(lvl_l - lvl_r) < delta:
        return None
    return {
        "pair": True,
        "page": page,
        "page_mode_in_row": mode_level(profile, delta),
        "pill": lvl_l,
        "track": lvl_r,
        "left_x0": first * stride_px / scale,
        "left_x1": (first + mid - gap) * stride_px / scale,
        "extent_pt": width_pt,
        "extent_x0": first * stride_px / scale,
        "hole_pt": (mid - gap) * stride_px / scale,
        "hole_x0": first * stride_px / scale,
        "hole_x1": (first + mid - gap) * stride_px / scale,
        "hole_share": (mid - gap) / float(len(extent)),
    }


def prefer_shape(rows):
    u"""两种形状都在时选哪一种：**有胶囊形状就先用它**，只有一行都读不出胶囊时才退到两段形状。

    顺序是承重的：胶囊形状是 377 结案的原始台阶；两种都能读时不许换尺，
    否则同一台机器上前后的读数就不再是同一个量。返回 `(kind, best)` 或 `(None, None)`。
    """
    pills = [g for g in rows if not g.get(u"pair")]
    pairs = [g for g in rows if g.get(u"pair")]
    if pills:
        return u"pill", max(pills, key=lambda g: (g["extent_pt"], g["hole_pt"]))
    if pairs:
        return u"pair", max(pairs, key=lambda g: (g["extent_pt"], g["solidity"]))
    return None, None


'''
assert s.count(A_FN) == 1
s = s.replace(A_FN, PAIR_FN + A_FN, 1)

A_SCAN = u"""        got = measure_row(profile, page, stride, scale, DELTA)
        if not got:
            continue
        got["ref_stable"] = ref_stable
        got["solidity"] = track_solidity(px, y_pt + band_pt / 2.0, 0.0,
                                         min(SIDEBAR_W_PT, width_pt), got["track"], scale, DELTA)
        if got["solidity"] >= MIN_SOLIDITY:
            got["y"] = y_pt
            found.append(got)"""
SCAN_NEW = u"""        got = measure_row(profile, page, stride, scale, DELTA)
        if not got:
            got = pair_split(profile, page, stride, scale, DELTA)
        if not got:
            continue
        got["ref_stable"] = ref_stable
        if got.get(u"pair"):
            got["solidity"] = track_solidity(px, y_pt + band_pt / 2.0, got["left_x0"],
                                             got["left_x1"], got["pill"], scale, DELTA)
        else:
            got["solidity"] = track_solidity(px, y_pt + band_pt / 2.0, 0.0,
                                             min(SIDEBAR_W_PT, width_pt), got["track"], scale, DELTA)
        if got["solidity"] >= MIN_SOLIDITY:
            got["y"] = y_pt
            found.append(got)"""
assert s.count(A_SCAN) == 1
s = s.replace(A_SCAN, SCAN_NEW, 1)

# provisional 那一趟也要认得第二形状，否则 pair 行在第一次筛里就被丢了
A_PROV = u"""    provisional = []
    for y_pt, profile in rows:
        got = measure_row(profile, mode_level(profile, DELTA), stride, scale, DELTA)
        if got:
            provisional.append(y_pt)"""
PROV_NEW = u"""    provisional = []
    for y_pt, profile in rows:
        row_page = mode_level(profile, DELTA)
        got = measure_row(profile, row_page, stride, scale, DELTA) \\
            or pair_split(profile, row_page, stride, scale, DELTA)
        if got:
            provisional.append(y_pt)"""
assert s.count(A_PROV) == 1
s = s.replace(A_PROV, PROV_NEW, 1)

A_BEST = u"""    best = max(stable, key=lambda g: (g["extent_pt"], g["hole_pt"]))
    for g in sorted(stable, key=lambda g: g["y"])[:6]:"""
BEST_NEW = u"""    kind, best = prefer_shape(stable)
    if best is None:
        print(u"REALSCREEN_VERDICT=no_band 有 %d 行过了参照门，但两种形状都读不出来" % len(stable))
        return 1
    print(u"PILL_SHAPE=%s（pill=容器里与页底同档的那一段；pair=一个控件两段、选中段在左）" % kind)
    for g in sorted(stable, key=lambda g: g["y"])[:6]:"""
assert s.count(A_BEST) == 1
s = s.replace(A_BEST, BEST_NEW, 1)

ast.parse(s)
io.open(P, u"w", encoding=u"utf-8").write(s)
print(u"R341_RULER_PATCH_OK")
