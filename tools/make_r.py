#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把明文 G.json 加密成 TVBox「格式2」配置: AES-128-CBC, key/iv 内嵌, 以 2423 前缀开头。
输出 R.json 到仓库根目录。

为什么这么做:
- Gitee 等平台对明文配置做"违规"关键词扫描, 密文不含任何可读 URL/中文, 可过审。
- TVBox / 影视仓 客户端加载 R.json 时用内置 AES.CBC() 自动解密, 用户无需任何操作。
- G.json 保持明文不变 (GitHub raw 仍可直接用); R.json 仅作为 Gitee 侧的配置地址。

格式 (与社区 ken6565/hipy-drpy2 实现一致, 客户端可识别):
  密文 hex = hex("$#" + KEY + "#$") + ciphertext_hex + hex(IV)
  - 开头 hex("$#") == "2423", 客户端据此判定为格式2。
  - KEY / IV 内嵌于密文, 客户端自取, 故此处 key/iv 非保密用途。
"""
import sys
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# 默认 13 位, 右补 0 到 16 字节。沿用社区常用值, 便于排查; 也可自行修改。
KEY = "1234567890123"
IV = "1234567890123"


def encrypt_text(text: str) -> str:
    key_b = KEY.ljust(16, "0").encode("utf-8")
    iv_b = IV.ljust(16, "0").encode("utf-8")
    cipher = AES.new(key_b, AES.MODE_CBC, iv_b)
    ct = cipher.encrypt(pad(text.encode("utf-8"), AES.block_size))
    header_hex = f"$#{KEY}#$".encode("utf-8").hex()  # 以 "2423" 开头
    iv_hex = IV.encode("utf-8").hex()
    return header_hex + ct.hex() + iv_hex


def decrypt_text(hexstr: str) -> str:
    marker = "#$".encode("utf-8").hex()  # "2324"
    header_end = hexstr.find(marker) + len(marker)
    header_hex = hexstr[:header_end]
    iv_hex = hexstr[-26:]  # hex(13 位 IV) == 26 字符
    cipher_hex = hexstr[header_end:-26]
    real_key = bytes.fromhex(header_hex).decode()[2:-2]  # 去掉 $# 与 #$
    real_iv = bytes.fromhex(iv_hex).decode()
    key_b = real_key.ljust(16, "0").encode("utf-8")
    iv_b = real_iv.ljust(16, "0").encode("utf-8")
    cipher = AES.new(key_b, AES.MODE_CBC, iv_b)
    pt = unpad(cipher.decrypt(bytes.fromhex(cipher_hex)), AES.block_size)
    return pt.decode("utf-8")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    # 默认: 在 tools/ 下运行 -> 读 ../G.json, 写 ../R.json; 允许 argv 覆盖路径。
    in_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "G.json")
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "R.json")
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

    # 自校验: 解密回来应与原文逐字节一致
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
    print("完成。请把 R.json 的 raw 地址配置到影视仓 (Gitee 侧)。")


if __name__ == "__main__":
    main()
