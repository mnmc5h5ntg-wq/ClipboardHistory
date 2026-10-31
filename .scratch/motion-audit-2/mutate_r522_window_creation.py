#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R522 变异表：无窗口时创建唯一主窗口（M1393–M1394）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW="Sources/ClipboardHistoryApp/Managers/WindowManager.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
ARMS=[
  ("M1393","无窗口时不创建（旧行为）", VIEW,
   '''        if creatingIfNeeded, let created = createMainWindow() {
            present(created)
            LifecycleDebugLogger.logAppState("after showMainWindow created main window", menuBarController: menuBarController)
            return
        }''',
   '''        // M1393：无窗口时不创建（旧行为）'''),
  ("M1394","已有窗口也照样再建一个", VIEW,
   '''        // 优先使用直接引用。弱引用还活着不等于窗口还能用：被 AppKit 关掉的窗口会离开
        // `NSApp.windows`，但别处的强引用可能让它继续存活（测试里销毁窗口时就是这个形状）。
        // 只认"仍在 AppKit 窗口表里"的那一份 —— 用户的关窗走 delegate（orderOut，仍在表里），
        // 所以这条检查不会把"隐藏"误判成"没有"。
        if let window = _mainWindow, isAttachedToApplication(window) {
            LifecycleDebugLogger.log("[SHOW-WIN] found via weak ref. isMiniaturized=\\(window.isMiniaturized) isVisible=\\(window.isVisible)")
            if window.isMiniaturized {
                window.deminiaturize(nil)
            }
            present(window)
            LifecycleDebugLogger.logAppState("after showMainWindow via weak ref", menuBarController: menuBarController)
            return
        }

        // 回退：在窗口列表中搜索
        if let window = mainWindow {
            LifecycleDebugLogger.log("[SHOW-WIN] found via identifier search. isMiniaturized=\\(window.isMiniaturized) isVisible=\\(window.isVisible)")
            if window.isMiniaturized {
                window.deminiaturize(nil)
            }
            present(window)
            LifecycleDebugLogger.logAppState("after showMainWindow via identifier search", menuBarController: menuBarController)
            return
        }''',
   '''        // M1394：不查已有窗口，直接创建'''),
]
TESTS={
  "M1393": "MainWindowCreationTests/testReopenCreatesExactlyOneVisibleMainWindowWhenNoneExists",
  "M1394": "MainWindowCreationTests/testReopenCreatesExactlyOneVisibleMainWindowWhenNoneExists",
}
def run(test):
    p=subprocess.run(["swift","test","--filter",test],cwd=ROOT,capture_output=True,text=True,env=ENV,timeout=2400)
    out=p.stdout+p.stderr
    if "Test Case" not in out: return "DID-NOT-RUN",out
    return ("CAUGHT" if " failed" in out else "PASSED"),out
def main():
    paths=sorted({os.path.join(ROOT,a[2]) for a in ARMS})
    orig={p:open(p,encoding="utf-8").read() for p in paths}
    for mid,desc,rel,old,new in ARMS:
        code,out=run(TESTS[mid]); print("预检 %s: %s"%(mid,code))
        if code!="PASSED": print(out[-500:]); return 2
    ok=True
    for mid,desc,rel,old,new in ARMS:
        path=os.path.join(ROOT,rel); cur=orig[path]
        n=cur.count(old)
        if n!=1: print(mid,"needle",n); ok=False; continue
        open(path,"w",encoding="utf-8").write(cur.replace(old,new))
        try: code,out=run(TESTS[mid])
        finally: open(path,"w",encoding="utf-8").write(orig[path])
        print("%s: %s"%(mid,code)); ok=ok and code=="CAUGHT"
    clean=all(open(p,"rb").read()==orig[p].encode("utf-8") for p in paths)
    print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if ok and clean else 1
if __name__=="__main__": sys.exit(main())
