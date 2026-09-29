#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双源并集注入 logo（以 sample1 为准）：
  - sample1.m3u 优先（用户第一次提供的源，覆盖更全，作为基准）
  - sample2.m3u 补充（用户第二次提供的源）
  匹配规则：先拿 K2 频道名去 sample1 找 logo，找不到再去 sample2 找；
            并集，但 sample1 优先（同名频道用 sample1 的台标）。

频道名匹配规则（优先级从高到低）：
  1) K2 显示名 与 sample 的 tvg-name / 显示名 精确匹配(大小写不敏感)
  2) 横杠归一化: sample 用 "CCTV-1" 而 K2 用 "CCTV1" 时对齐 (例: CCTV-1 -> CCTV1, CCTV-5+ -> CCTV5+)
  3) 去掉 K2 名前导的 CCTV / CETV 再匹配  (例: CCTV央视台球 -> 央视台球)
  4) 去掉 K2 名尾部 4K / HD 再匹配          (例: 北京卫视4K -> 北京卫视)

logo 4K 规则（用户要求）：
  - 频道名不含 4K -> logo 文件名也去掉 4K (例: 江苏卫视4K.png -> 江苏卫视.png)
  - 频道名含 4K   -> 优先用 4K 版 logo
  - 仅当目标 logo 确实存在于任一 sample 中时才切换，避免产生死链。

输出新文件 K2_logo.m3u（不覆盖原 K2.m3u）。
"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE1 = os.path.join(BASE, "sample1.m3u")
SAMPLE2 = os.path.join(BASE, "sample2.m3u")
K2 = os.path.join(BASE, "K2.m3u")
OUT = os.path.join(BASE, "K2_logo.m3u")

# EPG(电子节目单)地址，写入 #EXTM3U 头部 x-tvg-url 属性，TVBox 自动加载台标与节目预告
EPG_URL = "http://epg.51zmt.top:8000/e.xml"


def norm_key(s):
    """归一化频道名用于匹配：CCTV-1 -> cctv1, CCTV-5+ -> cctv5+ (去掉前缀后的横杠/空格/·)。
    仅作用于 CCTV/CETV 前缀后的分隔符，不影响其它名称。"""
    s = s.lower().strip()
    s = re.sub(r"^(cctv|cetv)[\-·\s]+", r"\1", s)
    return s


def build_logo_maps(path):
    by_tvg = {}   # tvg-name(小写) -> logo
    by_disp = {}  # 显示名(小写) -> logo
    known = set()  # sample 中出现过的所有 logo url
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s.startswith("#EXTINF"):
                continue
            lg = re.search(r'tvg-logo="([^"]*)"', s)
            if not lg:
                continue
            logo = lg.group(1)
            known.add(logo)
            tm = re.search(r'tvg-name="([^"]*)"', s)
            if tm:
                by_tvg.setdefault(tm.group(1).lower(), logo)
                by_tvg.setdefault(norm_key(tm.group(1)), logo)
            comma = s.rfind(",")
            dn = s[comma + 1:].strip() if comma >= 0 else ""
            if dn:
                by_disp.setdefault(dn.lower(), logo)
                by_disp.setdefault(norm_key(dn), logo)
    return by_tvg, by_disp, known


def find_logo_dual(title, m1, m2):
    """先在 m1(sample1) 匹配，匹配不到再在 m2(sample2) 匹配。
    返回 (logo, src, method)：
      src   = 1 来自 sample1 / 2 来自 sample2
      method = 'exact' | 'norm' | 'pre' | 'suf'
    """
    t = title.strip()
    if not t:
        return None, 0, ""
    key = t.lower()
    pairs = (m1, m2)
    # 1) 精确匹配
    for idx, (bt, bd) in enumerate(pairs, start=1):
        if key in bt:
            return bt[key], idx, "exact"
        if key in bd:
            return bd[key], idx, "exact"
    # 2) 横杠归一化: CCTV-1 -> cctv1
    nk = norm_key(t)
    if nk != key:
        for idx, (bt, bd) in enumerate(pairs, start=1):
            if nk in bt:
                return bt[nk], idx, "norm"
            if nk in bd:
                return bd[nk], idx, "norm"
    # 3) 去掉前导 CCTV / CETV
    for pre in ("cctv", "cetv"):
        if t.lower().startswith(pre) and len(t) > len(pre):
            rem = t[len(pre):].strip().lower()
            for idx, (bt, bd) in enumerate(pairs, start=1):
                if rem in bt:
                    return bt[rem], idx, "pre"
                if rem in bd:
                    return bd[rem], idx, "pre"
    # 4) 去掉尾部 4K / HD
    for suf in ("4k", "hd"):
        if t.lower().endswith(suf) and len(t) > len(suf):
            rem = t[: -len(suf)].strip().lower()
            for idx, (bt, bd) in enumerate(pairs, start=1):
                if rem in bt:
                    return bt[rem], idx, "suf"
                if rem in bd:
                    return bd[rem], idx, "suf"
    return None, 0, ""


def adjust_logo(logo, title, known):
    """按「名字是否含 4K」调整 logo 文件名里的 4K；仅当目标存在时才切换。
    返回 (logo, action)  action ∈ {'', 'drop4k', 'add4k'}"""
    d, _, f = logo.rpartition("/")
    name_has_4k = "4k" in title.lower()
    file_has_4k = "4k" in f.lower()
    if not name_has_4k and file_has_4k:
        # 去掉文件名里的 4K（4K/4k）
        nf = re.sub(r"4k", "", f, flags=re.IGNORECASE)
        cand = d + "/" + nf
        if cand in known and cand != logo:
            return cand, "drop4k"
    elif name_has_4k and not file_has_4k:
        # 名字含 4K 但 logo 不含 -> 若存在 4K 版则升级
        stem, dot, ext = f.rpartition(".")
        cand = d + "/" + stem + "4K" + (dot + ext if dot else "")
        if cand in known:
            return cand, "add4k"
    return logo, ""


def extract_group(title):
    """从分组行标题里取出组名。
    分组行标题形如:  '====== 🌺江苏移动All,#genre# ======'
    取出其中 🌺江苏移动All（位于 '====== ' 与 ',#genre#' 之间）。"""
    m = re.match(r"^=+\s*(.+?)\s*,#genre#", title)
    if m:
        return m.group(1).strip()
    return None


def add_group_title(line, group):
    """给一条 EXTINF 频道行注入/替换 group-title="<group>"（插在末尾标题逗号之前）。
    若行内已存在 group-title= 则替换为当前组，保证幂等。"""
    s = line.strip()
    comma = s.rfind(",")
    if comma < 0:
        return line
    head = s[:comma].rstrip()      # 属性部分（含 tvg-logo 等）
    title = s[comma + 1:].strip()  # 末尾显示名
    if "group-title=" in head:
        head = re.sub(r'group-title="[^"]*"', 'group-title="%s"' % group, head)
    else:
        head = head + ' group-title="%s"' % group
    return "%s,%s" % (head, title)


def process(m1, m2, known):
    total = 0
    matched = 0
    matched1 = 0   # 来自 sample1
    matched2 = 0   # 来自 sample2（补充）
    genre_skip = 0
    already = 0
    gt_added = 0   # 注入 group-title 的频道数
    exact = 0
    norm = 0
    strip_pre = 0
    strip_suf = 0
    drop4k = 0
    add4k = 0
    unmatched_samples = []

    current_group = None  # 当前分组（最近一次分组行的组名）
    skip_next = False     # 丢弃分组行后紧跟的伪频道 URL（如 http://0/0.m3u8）
    out_lines = []
    with open(K2, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip("\r")
            # 丢弃紧跟在分组注释之后的伪频道 URL（如 http://0/0.m3u8 / http://1/1.m3u8）
            if skip_next:
                skip_next = False
                s0 = line.strip()
                if s0.startswith("http://") or s0.startswith("https://"):
                    continue
            if line.strip().startswith("#EXTINF"):
                total += 1
                s = line.strip()
                # 标题分隔逗号 = EXTINF 时长字段('EXTINF:')之后的【第一个】逗号
                # （属性与显示名之间）。分组行的显示名内含一个逗号('...X,#genre#'），
                # 必须用第一个逗号，否则会把 '#genre#' 当成显示名、且取不到组名。
                ci = s.find(":")
                title_comma = s.find(",", ci) if ci >= 0 else -1
                if title_comma < 0:
                    title_comma = s.rfind(",")
                comma = title_comma
                title = s[comma + 1:].strip() if comma >= 0 else ""
                # 分组行（#genre#）：改写为纯注释分组头（匹配 sample1 风格 `#====== 组名======`），
                # 不再保留原 #EXTINF 伪频道行；其后的伪频道 URL 在下一轮被丢弃。
                if "#genre#" in title:
                    genre_skip += 1
                    g = extract_group(title)
                    if g:
                        current_group = g
                    out_lines.append("#====== %s======" % g if g else "#====== ======")
                    skip_next = True
                    continue
                # 真实频道行：先确定内容（已有 logo / 匹配到 logo / 无 logo）
                if 'tvg-logo=' in s:
                    already += 1
                    content = line
                else:
                    logo, src, method = find_logo_dual(title, m1, m2)
                    if logo:
                        matched += 1
                        if src == 1:
                            matched1 += 1
                        else:
                            matched2 += 1
                        if method == "exact":
                            exact += 1
                        elif method == "norm":
                            norm += 1
                        elif method == "pre":
                            strip_pre += 1
                        elif method == "suf":
                            strip_suf += 1
                        # 4K 规则
                        logo, act = adjust_logo(logo, title, known)
                        if act == "drop4k":
                            drop4k += 1
                        elif act == "add4k":
                            add4k += 1
                        content = '%s tvg-logo="%s"%s' % (
                            s[:comma].rstrip(), logo, s[comma:])
                    else:
                        if len(unmatched_samples) < 60:
                            unmatched_samples.append(title)
                        content = line
                # 注入 group-title（仅在已知当前分组时）
                if current_group is not None:
                    content = add_group_title(content, current_group)
                    gt_added += 1
                out_lines.append(content)
            else:
                # 头部行 #EXTM3U：注入/保留 x-tvg-url（EPG）
                s = line.strip()
                if s.startswith("#EXTM3U"):
                    if "x-tvg-url=" in s:
                        out_lines.append(line)  # 已有 EPG 则保留
                    else:
                        out_lines.append('#EXTM3U x-tvg-url="%s"' % EPG_URL)
                else:
                    out_lines.append(line)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")

    print("=== 处理统计（sample1 优先 + sample2 补充，双源并集）===")
    print("K2 EXTINF 总数      :", total)
    print("已含 logo(跳过)     :", already)
    print("分组行(跳过)        :", genre_skip)
    print("注入 group-title 数 :", gt_added)
    print("成功填 logo 数      :", matched)
    print("  - 来自 sample1    :", matched1)
    print("  - 来自 sample2补充:", matched2)
    print("  - 精确匹配        :", exact)
    print("  - 横杠归一化       :", norm)
    print("  - 去前导CCTV/CETV  :", strip_pre)
    print("  - 去尾部4K/HD      :", strip_suf)
    print("  - logo 去4K(名无4K):", drop4k)
    print("  - logo 加4K(名有4K):", add4k)
    print("未匹配(保持无logo)  :", total - already - genre_skip - matched)
    print("输出文件            :", OUT)
    print()
    print("--- 未匹配示例(前60) ---")
    for x in unmatched_samples:
        print("   ", x)


if __name__ == "__main__":
    bt1, bd1, kn1 = build_logo_maps(SAMPLE1)
    bt2, bd2, kn2 = build_logo_maps(SAMPLE2)
    known = kn1 | kn2  # 并集：4K 升降级判断用，避免死链
    m1 = (bt1, bd1)
    m2 = (bt2, bd2)
    print("sample1 logo 键: by_tvg=%d by_disp=%d 已知logo=%d" % (len(bt1), len(bd1), len(kn1)))
    print("sample2 logo 键: by_tvg=%d by_disp=%d 已知logo=%d" % (len(bt2), len(bd2), len(kn2)))
    print("并集 已知logo    :", len(known))
    print()
    process(m1, m2, known)
