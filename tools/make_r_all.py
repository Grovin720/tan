#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_r_all.py — 把明文 All.json 加密成 TVBox「格式2」配置（与 R.json 同算法），输出 AllR.json
====================================================================================

为什么：
  - Gitee 等平台对明文配置做违规关键词扫描，All.json 含大量可读 URL/中文会被拦截/打不开；
    密文不含任何可读明文，可过审。
  - 算法完全复用 tools/make_r.py 的 encrypt_text（AES-128-CBC, key/iv 内嵌, 以 2423 前缀开头），
    影视仓/ TVBox 客户端加载 AllR.json 时用内置 AES.CBC() 自动解密，用户无需任何操作。
  - All.json 保持明文不变（GitHub raw 仍可直接订阅）；AllR.json 仅作为 Gitee 侧订阅地址。

用法：
  python make_r_all.py              # 读 ../All.json, 写 ../AllR.json
  python make_r_all.py <in> <out>   # 自定义输入输出路径
"""

import os
import sys

# 复用 make_r.py 的加密实现（保证与 R.json 同算法/同密钥）
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from make_r import encrypt_text, decrypt_text  # noqa: E402

ROOT = os.path.dirname(HERE)
ALL_JSON = os.path.join(ROOT, "All.json")
ALLR_JSON = os.path.join(ROOT, "AllR.json")


def main():
    in_path = sys.argv[1] if len(sys.argv) > 1 else ALL_JSON
    out_path = sys.argv[2] if len(sys.argv) > 2 else ALLR_JSON
    in_path = os.path.abspath(in_path)
    out_path = os.path.abspath(out_path)

    if not os.path.isfile(in_path):
        print(f"✗ 找不到输入文件: {in_path}")
        sys.exit(1)

    with open(in_path, "r", encoding="utf-8") as f:
        raw = f.read()

    enc = encrypt_text(raw)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(enc)

    # 自校验：解密回来应与原文逐字节一致
    dec = decrypt_text(enc)
    ok = dec == raw
    print(f"加密: {in_path}")
    print(f"  -> 输出: {out_path}")
    print(f"  密文长度: {len(enc)} 字符 (hex), 前缀: {enc[:4]}")
    print(f"  往返校验: {'PASS ✓' if ok else 'FAIL ✗ (解密与原文不一致!)'}")
    if not ok:
        for i, (a, b) in enumerate(zip(raw, dec)):
            if a != b:
                print(f"  首个差异 @ {i}: 原文={a!r} 解密={b!r}")
                break
        sys.exit(1)
    print("完成。请把 AllR.json 的 raw 地址配置到影视仓（Gitee 侧）。")


if __name__ == "__main__":
    main()
