#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时探针：拉取 DodgeZhang/tvbox 的 tree 与关键 JSON，仅供分析合并规则。"""
import json, ssl, urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get(url, binary=False, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "okhttp/4.10.0",
                                               "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")

REPO = "DodgeZhang/tvbox"
BRANCH = "main"

# 1) tree
tree_url = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
try:
    data = json.loads(get(tree_url))
    tree = data.get("tree", [])
    print(f"[tree] truncated={data.get('truncated')} total={len(tree)}")
    for sub in ("pangmao", "moyu"):
        items = [(t["path"], t.get("size", 0)) for t in tree
                 if t.get("type") == "blob" and t["path"].startswith(sub + "/")]
        total = sum(s for _, s in items)
        print(f"\n== {sub}: {len(items)} 个文件, {total/1048576:.2f} MB ==")
        for p, s in sorted(items, key=lambda x: -x[1])[:15]:
            print(f"   {s:>10}  {p}")
except Exception as e:
    print("[tree] ERROR", type(e).__name__, e)

# 2) 关键 JSON 内容
for path in ("pangmao/pm.json", "moyu/my.json", "moyu/config.json", "pangmao/fm.json"):
    url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}"
    try:
        txt = get(url)
        print(f"\n===== {path} ({len(txt)} bytes) =====")
        # 只打印前 2500 字符，重点看结构
        print(txt[:2500])
    except Exception as e:
        print(f"\n===== {path} ERROR: {type(e).__name__} {e}")
