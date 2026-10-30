#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R508 变异表：两处搜索入口共用占位文案（M1362–M1363）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
MAIN="Sources/ClipboardHistoryApp/Views/SearchField.swift"
QUICK="Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
TEST="SearchPlaceholderTests"
ARMS=[
  ("M1362","共享常量改回长文案（两处一起漂）", MAIN,
   '''    static let text = "搜索历史…"''',
   '''    static let text = "搜索历史记录…"'''),
  ("M1363","浮层绕开共享常量、自己写一句", QUICK,
   '''        field.placeholderString = SearchPlaceholder.text''',
   '''        field.placeholderString = "搜索历史记录…"'''),
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
