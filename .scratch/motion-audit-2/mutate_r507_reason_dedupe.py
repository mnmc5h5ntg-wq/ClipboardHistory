#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R507 变异表：推荐理由类型词去重（M1360–M1361）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE="Sources/ClipboardHistoryApp/Intelligence/RecommendationPresenter.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
TEST="RecommendationPresenterTests/testContentTypeWordAppearsOnlyOnce"
ARMS=[
  ("M1360","类型词去重失效（裸类型 + 常用类型并存）",
   '''        let showKind = !(contentTypeTagText?.contains(kind) ?? false)''',
   '''        let showKind = true'''),
  ("M1361","把内容类型标签整个丢掉（重复没了但「常用」信息也没了）",
   '''        if let contentTypeTagText {
            tags.append(contentTypeTagText)
        }''',
   '''        if let contentTypeTagText {
            _ = contentTypeTagText
        }'''),
]
def run():
    p=subprocess.run(["swift","test","--filter",TEST],cwd=ROOT,capture_output=True,text=True,env=ENV,timeout=2400)
    out=p.stdout+p.stderr
    if "Test Case" not in out: return "DID-NOT-RUN",out
    return ("CAUGHT" if " failed" in out else "PASSED"),out
def main():
    path=os.path.join(ROOT,FILE); orig=open(path,encoding="utf-8").read(); code,out=run(); print("预检:",code)
    if code!="PASSED": print(out[-500:]); return 2
    ok=True
    for mid,desc,old,new in ARMS:
        n=orig.count(old)
        if n!=1: print(mid,"needle",n); ok=False; continue
        open(path,"w",encoding="utf-8").write(orig.replace(old,new))
        try: code,out=run()
        finally: open(path,"w",encoding="utf-8").write(orig)
        print("%s: %s"%(mid,code)); ok=ok and code=="CAUGHT"
    clean=open(path,"rb").read()==orig.encode("utf-8"); print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if ok and clean else 1
if __name__=="__main__": sys.exit(main())
