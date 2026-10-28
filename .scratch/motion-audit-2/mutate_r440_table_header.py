#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R440 变异对照：表格表头字重（去掉表头字体 / 整块都加粗，两把刀同一文件）。"""
import os, shutil, subprocess, sys, tempfile, time
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE=os.path.join(ROOT,"Sources/ClipboardHistoryApp/Utilities/MarkdownPresentation.swift")
BASE_ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
FILTER="UICaptureTests/testTableHeadersAreSemibold"
DRAW_NEEDLE='''                if let header = TableHeaderPresentation.headerRange(in: content) {
                    result.addAttribute(.font, value: TableHeaderPresentation.headerFont,
                                        range: NSRange(location: start, length: header.length))
                }'''
RANGE_NEEDLE='                    result.addAttribute(.font, value: TableHeaderPresentation.headerFont,\n                                        range: NSRange(location: start, length: header.length))'
MUTATIONS=[
 ("M1206","表头字体整块不写（两行回到 regular）",FILE,DRAW_NEEDLE,
  '''                _ = content''',["TABLE_HEADER","表头没有比表体重"]),
 ("M1207","表头字体打到整块（两行都 semibold）",FILE,RANGE_NEEDLE,
  '''                    result.addAttribute(.font, value: TableHeaderPresentation.headerFont,
                                        range: NSRange(location: start, length: blockContentLength))''',
  ["TABLE_HEADER","表头没有比表体重"]),
]
def read(p):
    with open(p,encoding="utf-8") as h: return h.read()
def run(f):
    shots=tempfile.mkdtemp(prefix="r440-mut-shots-"); env=dict(BASE_ENV); env["CLIPBOARD_HISTORY_UI_SHOTS"]=shots
    try:
        p=subprocess.run(["swift","test","--filter",f],cwd=ROOT,capture_output=True,text=True,env=env,timeout=1800)
        out=p.stdout+p.stderr; rc=p.returncode
    except subprocess.TimeoutExpired as e:
        raw=e.stdout or b""; out=raw.decode("utf-8","replace") if isinstance(raw,bytes) else (raw or ""); rc=-1
    finally: shutil.rmtree(shots,ignore_errors=True)
    verdicts=[l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts: return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"),out,[]
    if "error:" in out and not any(" failed" in l for l in verdicts): return "BROKEN-MUTATION",out,[]
    failed=[l.split("]")[0].replace("Test Case '-[","") for l in verdicts if " failed" in l]
    return ("CAUGHT" if rc!=0 else "ESCAPED"),out,failed
def main():
    original=read(FILE)
    for mid,_d,_p,old,_n,_x in MUTATIONS:
        c=read(FILE).count(old)
        if c!=1: raise SystemExit("预检中止：%s 针命中 %d 次"%(mid,c))
    code,out,_=run(FILTER)
    if code!="ESCAPED": raise SystemExit("预检失败 %s %s\n%s"%(FILTER,code,out[-1500:]))
    print("预检 OK "+FILTER)
    caught=wrong=0
    for mid,desc,path,old,new,needles in MUTATIONS:
        stamp=time.time()+2
        open(path,"w",encoding="utf-8").write(original.replace(old,new,1)); os.utime(path,(stamp,stamp))
        landed=old not in read(path) and new in read(path)
        try: code,out,failed=run(FILTER)
        finally:
            open(path,"w",encoding="utf-8").write(original); os.utime(path,(stamp+1,stamp+1))
        hit=all(any(n in l for l in failed) or n in out for n in needles)
        right=code=="CAUGHT" and hit and landed
        caught+=1 if code=="CAUGHT" else 0; wrong+=0 if right else 1
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"%(mid,desc,code,right,hit,failed,read(path)==original))
    clean=read(FILE)==original
    code,_,_=run(FILTER)
    print("还原后复跑：%s=%s"%(FILTER,code))
    print("R440_TABLE_HEADER_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"%(len(MUTATIONS),caught,wrong,"yes" if clean else "NO"))
    return 0 if (caught==len(MUTATIONS) and wrong==0 and clean and code=="ESCAPED") else 1
if __name__=="__main__": sys.exit(main())
