#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R511 变异表：最窄详情 meta 按优先级省字符数（M1370–M1372）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
TYPO="Sources/ClipboardHistoryApp/Utilities/DetailTypography.swift"
VIEW="Sources/ClipboardHistoryApp/Views/DetailView.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
TEST="Round3DetailTypographyTests"
ARMS=[
  ("M1370","includeSize 失效（最窄版仍带字符数）", TYPO,
   '''        if includeSize { pieces.append(size) }''',
   '''        pieces.append(size)'''),
  ("M1371","最窄版仍带「复制」", TYPO,
   '''        var pieces = [includeCopyVerb ? "\\(copiedAt) 复制" : copiedAt]''',
   '''        var pieces = ["\\(copiedAt) 复制"]'''),
  ("M1372","详情头部没有最窄一档（只剩 middle 截断）", VIEW,
   '''                            headerMeta(entry, includeIcon: false, includeCopyVerb: false, includeSize: false)''',
   '''                            // M1372：这里被删掉'''),
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
