#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K2.json(直播源文本) -> K2.m3u(M3U, 注入 logo + 分组)

K2.json 格式（直播源通用文本格式）：
  - 分组头:  <组名>,#genre#           例:  🌺江苏移动All,#genre#
  - 频道行:  <频道名>,<URL>           例:  CCTV1,http://xxx/index.m3u8

转换规则（与 add_logo.py 一致，复用其 logo 匹配/4K 逻辑）：
  1) logo 双源并集：sample1 优先，sample2 补充；仅当目标 logo 确实存在于样本时才切换（防死链）。
     - 4K 规则：频道名不含 4K -> logo 文件名也去 4K；频道名含 4K -> 保留/优先 4K 版。
  2) 分组头改写为纯注释风格：  <组名>,#genre#  ->  #====== 组名======  （匹配 sample1 风格）
  3) 每条频道注入 group-title="<组名>"（TVBox 分组归属）。
  4) 文件头注入 EPG：  #EXTM3U x-tvg-url="..."  （已有则保留）。

输出新文件 K2.m3u（不覆盖任何源文件）。
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
import add_logo as A  # 复用 logo 映射/匹配/4K 逻辑

SAMPLE1 = os.path.join(BASE, "sample1.m3u")
SAMPLE2 = os.path.join(BASE, "sample2.m3u")
SRC = os.path.join(BASE, "K2.json")
OUT = os.path.join(BASE, "K2.m3u")
EPG_URL = A.EPG_URL

# 频道行里“名字”与“URL”的分隔符：正常是逗号；少数电影条目用了 $ 或 .
# （如 `袭击2(HD中字$https://...` 或 `摆渡人2007(HD中字).https://...`）。
# 用正则定位首个 URL，其左侧结尾的分隔符（,/$/.等）用于切分名字与 URL。
_URL_RE = re.compile(r"(?i)(?:https?://|rtmp://|rtsp://|p3p://|p2p://|mitv://)")


def split_channel(line):
    """把一条频道文本切成 (名字, URL)。
    源里分隔符混乱，需兼容多种情况：
      - 正常 `名字,URL`：最后一个逗号切。
      - `名字,名字$URL` / `名字,URL`（名字里夹带）等：先按最后逗号切，
        若切出的“URL”里仍含真实 URL 协议，则再在协议处切一次（去除名字重复/脏前缀）。
      - `名字$URL` / `名字.URL`：无逗号，定位首个 URL，左侧结尾分隔符剥离后作名字。
      - 仅 URL（无名字）：名字用 URL 兜底，避免丢条目。
      - 既无逗号也无 URL：返回 (None, None) 视为其它行。
    """
    if "," in line:
        name, _, url = line.rpartition(",")
        name = name.strip()
        url = url.strip()
        # 切出的“URL”若仍含真实协议（如 `HD国语$https://...`、`$https://...`、
        # `P2p://...`），说明逗号后面夹带了名字/脏字符，按协议再切一次
        m2 = _URL_RE.search(url)
        if m2:
            url = url[m2.start():].strip()
            bad = name  # 逗号前的名字（可能是真实名字，后面夹带的需丢弃）
            # 真实名字 = 逗号前整体里、不含协议的那段（这里 bad 已是逗号前部分）
            return bad, url
        return name, url
    m = _URL_RE.search(line)
    if m:
        url = line[m.start():].strip()
        name = line[:m.start()].strip().rstrip("$., \t")
        if not name:
            name = url  # URL 兜底为名字，避免空名丢条目
        return name, url
    return None, None


def main():
    bt1, bd1, kn1 = A.build_logo_maps(SAMPLE1)
    bt2, bd2, kn2 = A.build_logo_maps(SAMPLE2)
    known = kn1 | kn2  # 并集：4K 升降级判断用，避免死链
    m1 = (bt1, bd1)
    m2 = (bt2, bd2)

    total = 0
    matched = 0
    matched1 = 0   # 来自 sample1
    matched2 = 0   # 来自 sample2（补充）
    drop4k = 0
    add4k = 0
    groups = 0
    others = 0
    unmatched = []
    current_group = None

    out = ['#EXTM3U x-tvg-url="%s"' % EPG_URL]

    with open(SRC, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip("\r").strip()
            if not line:
                continue
            # 分组头：<组名>,#genre#
            if line.endswith(",#genre#"):
                g = line[: -len(",#genre#")].strip()
                current_group = g
                groups += 1
                out.append("#====== %s======" % g)
                continue
            # 频道行：名字 + URL（正常逗号分隔；少数电影条目用 $ / . 或直接相连）
            name, url = split_channel(line)
            if name is None and url is None:
                # 既不是频道也不是分组头：原样保留，便于排查
                others += 1
                out.append(line)
                continue
            if not url:
                # 名字存在但 URL 为空（如 `少年包青天,`）—— 无效条目，跳过不输出
                others += 1
                continue
            total += 1
            logo, src, method = A.find_logo_dual(name, m1, m2) if name else (None, 0, "")
            if logo:
                matched += 1
                if src == 1:
                    matched1 += 1
                else:
                    matched2 += 1
                logo, act = A.adjust_logo(logo, name, known)
                if act == "drop4k":
                    drop4k += 1
                elif act == "add4k":
                    add4k += 1
                logo_attr = ' tvg-logo="%s"' % logo
            else:
                if name and len(unmatched) < 60:
                    unmatched.append(name)
                logo_attr = ""
            gt = ' group-title="%s"' % current_group if current_group else ""
            out.append('#EXTINF:-1%s%s,%s' % (logo_attr, gt, name))
            if url:
                out.append(url)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")

    print("=== K2.json -> K2.m3u（sample1 优先 + sample2 补充，双源并集）===")
    print("分组数            :", groups)
    print("频道数            :", total)
    print("成功填 logo 数    :", matched)
    print("  - 来自 sample1  :", matched1)
    print("  - 来自 sample2  :", matched2)
    print("  - logo 去4K(名无4K):", drop4k)
    print("  - logo 加4K(名有4K):", add4k)
    print("未匹配(保持无logo):", total - matched)
    print("其它行(原样保留)  :", others)
    print("输出文件          :", OUT)
    print()
    print("--- 未匹配示例(前60) ---")
    for x in unmatched:
        print("   ", x)


if __name__ == "__main__":
    main()
