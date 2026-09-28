#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_ds.py — 同步 DodgeZhang/tvbox 仓库的 pangmao/ 和 moyu/ 文件夹到本地
=========================================================================
用途：在仓库根目录（与 xiaosa/ 同级）生成 pangmao/ 和 moyu/ 两个文件夹，
      内容与 GitHub 上 DodgeZhang/tvbox 的对应目录保持一致（含 json/jar/ext/img）。
      这样 merge_all.py 就能用本地文件合并，且依赖文件（jar/ext）由同步文件夹提供。

机制：
  - 调用 GitHub tree API 列出整个仓库文件树，过滤出 pangmao/ 或 moyu/ 下的 blob
  - 逐个用 raw.githubusercontent.com 下载，按原目录结构落盘到仓库根
  - 若本地已存在且字节数与 tree 中记录一致则跳过（增量同步，省流量）
  - 覆盖式同步（每次取远程最新），符合"每日自动更新"语义

零依赖：仅用标准库（urllib/ssl/json/os/sys/time）

用法：
  python sync_ds.py                 # 同步 pangmao/ 和 moyu/
  python sync_ds.py pangmao        # 只同步 pangmao/
  python sync_ds.py moyu            # 只同步 moyu/
  python sync_ds.py --list          # 只列出将下载的文件与总体积，不落盘
"""

import os
import sys
import json
import time
import ssl
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)               # 仓库根（xiaosa/ 同级）
REPO = "DodgeZhang/tvbox"
BRANCH = "main"
SUBFOLDERS = ["pangmao", "moyu"]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def api_get(url, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "okhttp/4.10.0",
                              "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def raw_get_bytes(url, retries=3, timeout=120):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "okhttp/4.10.0"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def list_folder(subfolder):
    """返回 [(path, size), ...] 仅该子文件夹下的 blob。"""
    tree_url = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
    data = api_get(tree_url)
    if data.get("truncated"):
        print(f"  ⚠️ tree 被截断（>100k 文件），请改用其他方式")
    tree = data.get("tree", [])
    out = []
    for t in tree:
        p = t["path"]
        if t.get("type") != "blob":
            continue
        if not p.startswith(subfolder + "/"):
            continue
        if ".bak" in p:          # 跳过 aidaox 的 .bak_* 备份 jar（垃圾）
            continue
        out.append((p, t.get("size", 0)))
    return out


def sync_folder(subfolder, dry_run=False):
    files = list_folder(subfolder)
    total = sum(s for _, s in files)
    print(f"== {subfolder}: 远程 {len(files)} 个文件, 总体积 {total/1048576:.1f} MB ==")
    if dry_run:
        for p, s in files[:20]:
            print(f"   {s:>9}  {p}")
        if len(files) > 20:
            print(f"   ... 其余 {len(files)-20} 个")
        return 0

    count = skip = fail = 0
    for path, size in files:
        dest = os.path.join(ROOT, path)
        # 增量：本地已存在且同体积则跳过
        if os.path.exists(dest) and os.path.getsize(dest) == size:
            skip += 1
            continue
        raw_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}"
        try:
            blob = raw_get_bytes(raw_url, timeout=max(60, min(300, int(size/1024)+30)))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(blob)
            count += 1
        except Exception as e:  # noqa: BLE001
            print(f"   ❌ 下载失败 {path}: {e}")
            fail += 1
    print(f"   已下载 {count} 个, 跳过 {skip} 个(已同), 失败 {fail} 个 -> {os.path.join(ROOT, subfolder)}")
    return count


def main():
    args = sys.argv[1:]
    dry = "--list" in args
    folders = [a for a in args if a in SUBFOLDERS] or SUBFOLDERS
    if dry:
        print("（--list 仅列出，不下载）")
    for f in folders:
        sync_folder(f, dry_run=dry)
    print("同步完成。" if not dry else "列出完成。")


if __name__ == "__main__":
    main()
