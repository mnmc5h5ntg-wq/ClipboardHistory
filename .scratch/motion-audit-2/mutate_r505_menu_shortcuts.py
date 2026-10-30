#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R505 变异表：状态菜单标准快捷键的可见性（M1354–M1356）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
UTIL="Sources/ClipboardHistoryApp/Utilities/MenuCommandShortcutPresentation.swift"
APP="Sources/ClipboardHistoryApp/App.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
TEST="MenuShortcutPresentationTests/testStandardShortcutsAreVisibleInTheSwiftUIMenu"
ARMS=[
  ("M1354","设置的标准快捷键不再映射（菜单右列消失）", UTIL,
   '''            return ","''',
   '''            return nil'''),
  ("M1355","退出的标准快捷键映射成错键", UTIL,
   '''            return "q"''',
   '''            return "w"'''),
  ("M1356","退出项不再挂快捷键修饰器（显示与触发都丢）", APP,
   '''                .modifier(MenuCommandShortcutModifier(command: .quit))''',
   '''                // M1356：这里被删掉'''),
]
def run():
    p=subprocess.run(["swift","test","--filter",TEST],cwd=ROOT,capture_output=True,text=True,env=ENV,timeout=2400)
    out=p.stdout+p.stderr
    if "Test Case" not in out: return "DID-NOT-RUN",out
    return ("CAUGHT" if " failed" in out else "PASSED"),out
def main():
    paths=sorted({os.path.join(ROOT,a[2]) for a in ARMS})
    orig={p:open(p,encoding="utf-8").read() for p in paths}
    code,out=run(); print("预检:",code)
    if code!="PASSED": print(out[-500:]); return 2
    ok=True
    for mid,desc,rel,old,new in ARMS:
        path=os.path.join(ROOT,rel); cur=orig[path]
        n=cur.count(old)
        if n!=1: print(mid,"needle",n); ok=False; continue
        open(path,"w",encoding="utf-8").write(cur.replace(old,new))
        try: code,out=run()
        finally: open(path,"w",encoding="utf-8").write(orig[path])
        print("%s: %s"%(mid,code)); ok=ok and code=="CAUGHT"
    clean=all(open(p,"rb").read()==orig[p].encode("utf-8") for p in paths)
    print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if ok and clean else 1
if __name__=="__main__": sys.exit(main())
