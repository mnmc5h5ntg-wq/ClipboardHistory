#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R506 变异表：状态菜单推荐理由并入同一个 Text（M1357–M1359）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
UTIL="Sources/ClipboardHistoryApp/Utilities/MenuRecommendationPresentation.swift"
VIEW="Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
TEST="MenuRecommendationPresentationTests"
ARMS=[
  ("M1357","推荐理由后缀永远为空（理由再次消失）", UTIL,
   '''        return trimmed.isEmpty ? "" : "  " + trimmed''',
   '''        return ""'''),
  ("M1358","理由与标题之间只剩一个空格（列间距被吃掉）", UTIL,
   '''        return trimmed.isEmpty ? "" : "  " + trimmed''',
   '''        return trimmed.isEmpty ? "" : " " + trimmed'''),
  ("M1359","推荐行不再走理由后缀（退回裸理由）", VIEW,
   '''Text(MenuRecommendationPresentation.reasonSuffix(reasonText))''',
   '''Text(reasonText)'''),
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
