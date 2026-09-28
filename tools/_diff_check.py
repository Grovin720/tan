# -*- coding: utf-8 -*-
"""核对本地 tools/Line.json、tools/merge_all.py、run.yml 与 GitHub 最新版差异。"""
import io, os, ssl, urllib.request, hashlib
from urllib.parse import quote

OWNER, REPO, BR = "Grovin720", "tan", "main"
ROOT = r"D:\BuddySpace\tvbox\tvbox-master"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE


def remote(path):
    url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BR}/{quote(path)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
        return r.read()


FILES = [".github/workflows/run.yml", "tools/Line.json", "tools/merge_all.py",
         "tools/sync_ds.py", "All.json"]

for f in FILES:
    lp = os.path.join(ROOT, f.replace("/", os.sep))
    print("=" * 68)
    print(f)
    print("=" * 68)
    lb = io.open(lp, "rb").read() if os.path.exists(lp) else None
    try:
        rb = remote(f)
    except Exception as e:
        print("  远程读取失败:", type(e).__name__, e)
        continue
    lh = hashlib.sha1(lb).hexdigest()[:10] if lb is not None else "(本地无)"
    rh = hashlib.sha1(rb).hexdigest()[:10]
    print(f"  本地 {len(lb) if lb else 0:>7} B  sha1:{lh}")
    print(f"  远程 {len(rb):>7} B  sha1:{rh}")
    print("  => " + ("一致 ✅" if lb == rb else "有差异 ⚠️"))
    if f == "tools/Line.json":
        for tag, b in (("本地", lb), ("远程", rb)):
            if not b:
                continue
            import json
            try:
                j = json.loads(b.decode("utf-8", "replace"))
                print(f"    {tag} spider = {j.get('spider')!r}  sites={len(j.get('sites', []))}")
            except Exception as e:
                print(f"    {tag} 解析失败 {e}")
    if f == ".github/workflows/run.yml":
        for tag, b in (("本地", lb), ("远程", rb)):
            if not b:
                continue
            txt = b.decode("utf-8", "replace")
            print(f"    {tag}: 含 merge_all = {'merge_all.py' in txt}, 含 sync_ds = {'sync_ds.py' in txt}, "
                  f"行数 = {len(txt.splitlines())}")
    if f == "tools/merge_all.py":
        for tag, b in (("本地", lb), ("远程", rb)):
            if not b:
                continue
            txt = b.decode("utf-8", "replace")
            print(f"    {tag}: 含 md5 剥离 = {'split(\";md5;\")' in txt}, spider 告警 = {'顶层 spider 指向的文件在仓库里不存在' in txt}")
    if f == "All.json":
        import json
        for tag, b in (("本地", lb), ("远程", rb)):
            if not b:
                continue
            try:
                j = json.loads(b.decode("utf-8", "replace"))
                print(f"    {tag} spider = {j.get('spider')!r}  sites={len(j.get('sites', []))}")
            except Exception as e:
                print(f"    {tag} 解析失败 {e}")
