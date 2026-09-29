#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用版：直播源文本(json/txt 等) -> 同名 .m3u，注入 logo + 分组。

与 json_to_m3u.py 的区别：
  - 输入 json 文件可自由选择（不再写死 K2.json）
  - logo 源可传入【任意多个】（不再只限 sample1/sample2），
    按传入顺序作为优先级（越靠前越优先，后面的做补充并集）
  - 输出文件名与输入 json 同名（K2.json -> K2.m3u），默认放在输入文件同目录

用法:
  # 第一个位置参数是输入 json；其后的位置参数都是 logo 源（可多个，可省略）
  python json2m3u.py INPUT.json [LOGO1.m3u LOGO2.m3u ...]

  # 也可用 --logo 显式指定 logo 源列表（与位置参数二选一/可混用）
  python json2m3u.py --json INPUT.json --logo LOGO1.m3u LOGO2.m3u

  # 可选：--out 指定输出路径（默认 <输入去扩展名>.m3u）；--epg 覆盖 EPG 地址
  python json2m3u.py INPUT.json LOGO1.m3u --out OUT.m3u --epg "http://..."

说明:
  - 不传任何 logo 源时，只做“文本 -> m3u 转换 + 分组注释头 + group-title”，不注入 logo。
  - 复用 add_logo.py 的 build_logo_maps / adjust_logo / norm_key / EPG_URL。

直播源文本格式（通用）：
  - 分组头:  <组名>,#genre#           例:  🌺江苏移动All,#genre#
  - 频道行:  <频道名>,<URL>           例:  CCTV1,http://xxx/index.m3u8
            （也兼容少数电影条目用 $ / . / 直接相连 的脏分隔符）
"""
import os
import re
import sys
import argparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
import add_logo as A  # 复用 logo 映射/匹配/4K 逻辑

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


def find_logo_multi(title, maps):
    """多源并集匹配：按 maps 顺序（优先级递减）查找 logo。
    maps: list of (bt, bd)。返回 (logo, src_idx(1-based), method)。
    匹配优先级（每个源内）：
      1) 精确匹配  2) 横杠归一化(CCTV-1->cctv1)  3) 去前导 CCTV/CETV
      4) 去尾部 4K/HD
    """
    t = title.strip()
    if not t:
        return None, 0, ""
    key = t.lower()
    # 1) 精确匹配
    for idx, (bt, bd) in enumerate(maps, start=1):
        if key in bt:
            return bt[key], idx, "exact"
        if key in bd:
            return bd[key], idx, "exact"
    # 2) 横杠归一化: CCTV-1 -> cctv1
    nk = A.norm_key(t)
    if nk != key:
        for idx, (bt, bd) in enumerate(maps, start=1):
            if nk in bt:
                return bt[nk], idx, "norm"
            if nk in bd:
                return bd[nk], idx, "norm"
    # 3) 去掉前导 CCTV / CETV
    for pre in ("cctv", "cetv"):
        if t.lower().startswith(pre) and len(t) > len(pre):
            rem = t[len(pre):].strip().lower()
            for idx, (bt, bd) in enumerate(maps, start=1):
                if rem in bt:
                    return bt[rem], idx, "pre"
                if rem in bd:
                    return bd[rem], idx, "pre"
    # 4) 去掉尾部 4K / HD
    for suf in ("4k", "hd"):
        if t.lower().endswith(suf) and len(t) > len(suf):
            rem = t[: -len(suf)].strip().lower()
            for idx, (bt, bd) in enumerate(maps, start=1):
                if rem in bt:
                    return bt[rem], idx, "suf"
                if rem in bd:
                    return bd[rem], idx, "suf"
    return None, 0, ""


def main():
    ap = argparse.ArgumentParser(
        description="直播源文本(json/txt) -> 同名 .m3u，注入 logo + 分组")
    ap.add_argument("json", help="输入直播源文本文件（如 K2.json）")
    ap.add_argument("logos", nargs="*",
                    help="logo 源 m3u 列表（可多个，越靠前越优先；可省略）")
    ap.add_argument("--logo", nargs="*", default=[],
                    help="与位置参数等效的 logo 源列表（可混用）")
    ap.add_argument("--out", default=None,
                    help="输出 m3u 路径（默认 <输入去扩展名>.m3u）")
    ap.add_argument("--epg", default=A.EPG_URL,
                    help="写入 #EXTM3U 头的 x-tvg-url（默认内置 EPG）")
    args = ap.parse_args()

    src = args.json
    if not os.path.isfile(src):
        print("错误：输入文件不存在:", src)
        sys.exit(1)

    # 合并位置参数与 --logo 的 logo 源，去重保序
    seen = set()
    logo_sources = []
    for lp in list(args.logos) + list(args.logo):
        ap2 = os.path.abspath(lp)
        if ap2 in seen:
            continue
        seen.add(ap2)
        if not os.path.isfile(lp):
            print("警告：logo 源不存在，跳过:", lp)
            continue
        logo_sources.append(lp)

    # 为每个 logo 源构建映射，并收集并集 known（4K 升降级防死链用）
    maps = []
    knowns = set()
    for lp in logo_sources:
        bt, bd, kn = A.build_logo_maps(lp)
        maps.append((bt, bd))
        knowns |= kn

    out = args.out or (os.path.splitext(src)[0] + ".m3u")

    # 统计
    total = 0
    matched = 0
    matched_by_src = [0] * len(maps)      # 各 logo 源贡献的匹配数
    method = {"exact": 0, "norm": 0, "pre": 0, "suf": 0}
    drop4k = 0
    add4k = 0
    groups = 0
    others = 0
    unmatched = []
    current_group = None

    out_lines = ['#EXTM3U x-tvg-url="%s"' % args.epg]

    with open(src, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip("\r").strip()
            if not line:
                continue
            # 分组头：<组名>,#genre#
            if line.endswith(",#genre#"):
                g = line[: -len(",#genre#")].strip()
                current_group = g
                groups += 1
                out_lines.append("#====== %s======" % g)
                continue
            # 频道行：名字 + URL（正常逗号分隔；少数电影条目用 $ / . 或直接相连）
            name, url = split_channel(line)
            if name is None and url is None:
                # 既不是频道也不是分组头：原样保留，便于排查
                others += 1
                out_lines.append(line)
                continue
            if not url:
                # 名字存在但 URL 为空（如 `少年包青天,`）—— 无效条目，跳过不输出
                others += 1
                continue
            total += 1
            logo, src_idx, mth = find_logo_multi(name, maps) if name else (None, 0, "")
            if logo:
                matched += 1
                if 1 <= src_idx <= len(matched_by_src):
                    matched_by_src[src_idx - 1] += 1
                if mth in method:
                    method[mth] += 1
                logo, act = A.adjust_logo(logo, name, knowns)
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
            out_lines.append('#EXTINF:-1%s%s,%s' % (logo_attr, gt, name))
            if url:
                out_lines.append(url)

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")

    print("=== %s -> %s ===" % (os.path.basename(src), os.path.basename(out)))
    print("logo 源数         :", len(maps))
    for i, lp in enumerate(logo_sources, start=1):
        print("  - 源%d 匹配数   : %d  (%s)" % (i, matched_by_src[i - 1], os.path.basename(lp)))
    print("分组数            :", groups)
    print("频道数            :", total)
    print("成功填 logo 数    :", matched)
    print("  - 精确匹配      :", method["exact"])
    print("  - 横杠归一化     :", method["norm"])
    print("  - 去前导CCTV/CETV:", method["pre"])
    print("  - 去尾部4K/HD    :", method["suf"])
    print("  - logo 去4K(名无4K):", drop4k)
    print("  - logo 加4K(名有4K):", add4k)
    print("未匹配(保持无logo):", total - matched)
    print("其它行(原样保留)  :", others)
    print("输出文件          :", out)
    print()
    print("--- 未匹配示例(前60) ---")
    for x in unmatched:
        print("   ", x)


if __name__ == "__main__":
    main()
