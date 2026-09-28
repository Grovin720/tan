#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核验生成的 All.json 是否符合合并规则（仅检查，不修改）。"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALL = os.path.join(ROOT, "All.json")
data = json.load(open(ALL, encoding="utf-8"))
sites = data.get("sites", [])
keys = [s.get("key") for s in sites]

def find(key):
    return [s for s in sites if s.get("key") == key]

print("总站点:", len(sites))
print("顶层 spider:", data.get("spider"))
print("顶层 logo:", data.get("logo"))

# 1) my 标记存在 + my 站点紧跟其后
assert "my" in keys, "缺少 my 标记"
mi = keys.index("my")
after = keys[mi+1:mi+6]
print("\nmy 标记后前5个 key:", after)

# 统计：插入的 my 站点（来自 moyu）应都带 jar 且 jar 指向 ./moyu/
moyu_jar_ok = 0
moyu_jar_bad = 0
for s in sites:
    j = s.get("jar", "")
    if j.startswith("./moyu/"):
        moyu_jar_ok += 1
    elif j.startswith("./jar/") or j.startswith("./pangmao/"):
        pass
print("\njar 以 ./moyu/ 开头的站点数:", moyu_jar_ok)

# 2) 抽几个真实 my 站点检查 ext 改写 + jar
print("\n--- 抽查 my 站点(应带 ./moyu/ jar 与 ./moyu/ext) ---")
shown = 0
for s in sites:
    if s.get("key") == "my":
        continue
    j = s.get("jar", "")
    if j.startswith("./moyu/") and shown < 4:
        ext = s.get("ext")
        print(f"  key={s.get('key')!r} name={s.get('name')!r}")
        print(f"    jar={j}")
        print(f"    ext={ext if not isinstance(ext, dict) else {k: (v if not isinstance(v, dict) else '...') for k, v in ext.items()}}")
        shown += 1

# 3) pm 站点 ext 应改写为 ./pangmao/ext
print("\n--- 抽查 pm 覆盖的导航站 ext 改写 ---")
for k in ("Douban", "DoubanPan", "BinMarket"):
    s = find(k)
    if s:
        s = s[0]
        print(f"  key={k} name={s.get('name')!r} ext={s.get('ext')}")

# 4) Line 自带 ./ 不应被改写
print("\n--- 检查 Line 顶层 spider 未动 ---")
assert data.get("spider") == "./jar/aidaox.jar", f"spider 被改: {data.get('spider')}"
print("  OK: spider 仍为", data.get("spider"))

# 5) 是否存在任何 my/pm 站点仍残留 ./ext/ 或 ./jar/ 未改写（不含 ./pangmao/ ./moyu/）
bad = []
for s in sites:
    for f in ("ext", "jar", "api"):
        v = s.get(f)
        if isinstance(v, str) and re.match(r"^\./(ext|jar|img|py|js)/", v) and not v.startswith(("./pangmao/", "./moyu/")):
            bad.append((s.get("key"), f, v))
print("\n残留未改写相对路径(应为空):", bad[:10], "总数", len(bad))

print("\n=== 核验完成 ===")
