#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_all.py — 合并多源 TVBox 线路配置，产出 All.json
====================================================

功能：
  - 以 tools/Line.json 为基底（等同旧 dianshi.json 的角色）
  - 并入 DodgeZhang/tvbox 仓的 moyu/config.json、moyu/my.json、
    pangmao/fm.json、pangmao/pm.json（pm.json 优先级最高）
  - 同 key 站点后者覆盖前者（pm 最高）；lives/parses 按 name 去重追加
  - 顶层 spider 取优先级最高的源（即 pm.json 的 spider.jar）
  - 扫描所有本地依赖(./jar ./ext ./py ./js)，生成"待搬运文件清单.json"
  - 产出仓库根的 All.json（与 G.json 同目录，每日更新）

特性：
  - 零依赖（仅标准库 urllib/ssl/json/re/os/sys/time）
  - 容错解析：兼容 // 注释行与尾逗号（TVBox 配置常见非标准写法）
  - 单源拉取失败不致命（跳过并记录告警），不会让整个流水线崩
  - 支持 --self-test 用内置样例验证合并逻辑（无需联网）

用法：
  python merge_all.py            # 联网拉取并合并，写出 All.json
  python merge_all.py --self-test # 用内置样例验证（不联网、不写仓库 All.json）
"""

import os
import re
import sys
import json
import time
import ssl
import urllib.request

# ---- 路径基准：tools/merge_all.py -> 父目录即仓库根 ----
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = HERE

# ---- 合并源（按覆盖优先级从低到高，pm.json 最高）----
# priority 越大越晚合并（覆盖前者）。
SOURCES = [
    {"name": "Line.json (本地基底)", "priority": 1,
     "local": os.path.join(TOOLS, "Line.json")},
    {"name": "DodgeZhang/moyu/config.json", "priority": 2,
     "url": "https://raw.githubusercontent.com/DodgeZhang/tvbox/main/moyu/config.json"},
    {"name": "DodgeZhang/moyu/my.json", "priority": 3,
     "url": "https://raw.githubusercontent.com/DodgeZhang/tvbox/main/moyu/my.json"},
    {"name": "DodgeZhang/pangmao/fm.json", "priority": 4,
     "url": "https://raw.githubusercontent.com/DodgeZhang/tvbox/main/pangmao/fm.json"},
    {"name": "DodgeZhang/pangmao/pm.json", "priority": 5,
     "url": "https://raw.githubusercontent.com/DodgeZhang/tvbox/main/pangmao/pm.json"},
]

ALL_JSON = os.path.join(ROOT, "All.json")
MOVE_LIST = os.path.join(ROOT, "待搬运文件清单.json")

LIST_KEYS = ("sites", "lives", "parses")  # 这几个做"合并"而非"覆盖"


# ----------------------------------------------------------------------
# 容错解析 / 拉取
# ----------------------------------------------------------------------
def parse_jsonc(txt):
    """去掉 // 注释行与尾逗号，再 json.loads（兼容 TVBox 非标准配置）。"""
    txt = re.sub(r'^\s*//.*$', '', txt, flags=re.M)
    txt = re.sub(r',(\s*[}\]])', r'\1', txt)
    return json.loads(txt)


def fetch(url, timeout=30, retries=3):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "okhttp/4.10.0"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def load_sources():
    """加载所有源，返回 [(name, priority, data_or_None, error)]。"""
    out = []
    for src in SOURCES:
        name = src["name"]
        pri = src["priority"]
        try:
            if "local" in src:
                txt = open(src["local"], encoding="utf-8").read()
            else:
                txt = fetch(src["url"])
            data = parse_jsonc(txt)
            out.append((name, pri, data, None))
            print(f"  [OK] {name} 站点={len(data.get('sites', []))} "
                  f"lives={len(data.get('lives', []))} parses={len(data.get('parses', []))}")
        except Exception as e:  # noqa: BLE001
            out.append((name, pri, None, str(e)))
            print(f"  [失败] {name}: {type(e).__name__} {e}")
    return out


# ----------------------------------------------------------------------
# 合并
# ----------------------------------------------------------------------
def name_of(item):
    """取 lives/parses 元素的去重键。"""
    if isinstance(item, dict):
        return item.get("name") or item.get("url")
    if isinstance(item, list) and item:
        return item[0]
    return None


def choose_spider(spider_sources):
    """spider 取优先级最高的源（即 pm.json 的 spider.jar，覆盖层级最高）。
    返回 (spider_val, 说明)。"""
    if not spider_sources:
        return "", "未设置 spider"
    p, n, v = max(spider_sources, key=lambda x: x[0])
    return v, f"采用 {n} 的 spider（优先级最高）"


def merge_sources(loaded):
    """loaded: [(name, priority, data, error)] -> (final_dict, stats)。"""
    ok = [(n, p, d) for (n, p, d, e) in loaded if d is not None]
    failed = [(n, e) for (n, p, d, e) in loaded if d is None]

    # 单值字段：后者覆盖前者（按优先级升序）；spider 单独选择
    single_order = []
    single = {}
    spider_sources = []  # (priority, name, spider_val)
    for name, _pri, data in sorted(ok, key=lambda x: x[1]):
        for k, v in data.items():
            if k in LIST_KEYS:
                continue
            if k == "spider":
                if v:
                    spider_sources.append((_pri, name, v))
                continue
            if k not in single:
                single_order.append(k)
            single[k] = v

    # sites：按 key 合并，记录来源；后者覆盖前者
    sites_map = {}          # key -> (site, src_name)
    src_counts = {}         # src_name -> 贡献站点数
    for name, _pri, data in sorted(ok, key=lambda x: x[1]):
        for s in data.get("sites", []) or []:
            k = s.get("key")
            if not k:
                continue
            sites_map[k] = (s, name)
        src_counts[name] = src_counts.get(name, 0) + len(
            [s for s in (data.get("sites", []) or []) if s.get("key")])

    # lives / parses：按 name 去重，后者覆盖前者
    lives_map, parses_map = {}, {}
    for _name, _pri, data in sorted(ok, key=lambda x: x[1]):
        for it in data.get("lives", []) or []:
            kk = name_of(it)
            lives_map[kk if kk is not None else f"_live_{id(it)}"] = it
        for it in data.get("parses", []) or []:
            kk = name_of(it)
            parses_map[kk if kk is not None else f"_parse_{id(it)}"] = it

    # 组装 final（spider 安全选择后置顶）
    spider_val, spider_note = choose_spider(spider_sources)
    final = {}
    if spider_val:
        final["spider"] = spider_val  # spider 置顶
    for k in single_order:
        if k in single and k != "spider":
            final[k] = single[k]
    final["sites"] = [v[0] for k, v in sorted(sites_map.items())]
    final["lives"] = list(lives_map.values())
    final["parses"] = list(parses_map.values())

    stats = {
        "成功源数": len(ok),
        "失败源数": len(failed),
        "失败源": [n for n, _ in failed],
        "spider说明": spider_note,
        "各源贡献站点数": src_counts,
        "合并后站点总数": len(final["sites"]),
        "合并后直播数": len(final["lives"]),
        "合并后解析数": len(final["parses"]),
    }
    return final, stats, sites_map


# ----------------------------------------------------------------------
# 待搬运清单
# ----------------------------------------------------------------------
def scan_deps(final, sites_map):
    """扫描所有本地依赖(./ 开头)，标注仓库是否存在。"""
    deps = {}  # rel_path -> {count, srcs:set, exists}

    def add(path, src):
        if not isinstance(path, str):
            return
        if not path or not path.startswith("./"):
            return
        rel = path[2:]
        if not rel:
            return
        abs_p = os.path.join(ROOT, rel)
        e = os.path.exists(abs_p)
        d = deps.setdefault(rel, {"count": 0, "srcs": set(), "exists": e})
        d["count"] += 1
        d["srcs"].add(src)

    # spider 字段（形如 ./jar/spider.jar;md5;xxx）
    sp = final.get("spider", "") or ""
    if ";" in sp:
        add(sp.split(";")[0], "spider字段")
    elif sp.startswith("./"):
        add(sp, "spider字段")

    for k, (site, src) in sites_map.items():
        # jar 可能含 ;md5;xxx
        jar = (site.get("jar") or "")
        if ";" in jar:
            jar = jar.split(";")[0]
        add(jar, src)
        add(site.get("ext") or "", src)
        add(site.get("api") or "", src)

    for it in final.get("lives", []) + final.get("parses", []):
        if isinstance(it, dict) and isinstance(it.get("ext"), str):
            add(it["ext"], "lives/parses")

    missing, present = [], []
    for rel, info in sorted(deps.items()):
        entry = {"path": "./" + rel, "引用次数": info["count"],
                 "来自源": sorted(info["srcs"]), "仓库中存在": info["exists"]}
        (missing if not info["exists"] else present).append(entry)
    return missing, present


# ----------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------
def run(loaded):
    final, stats, sites_map = merge_sources(loaded)

    # 写出 All.json（格式化、中文不转义，便于人读与 diff）
    with open(ALL_JSON, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
        f.write("\n")

    missing, present = scan_deps(final, sites_map)
    move = {
        "生成时间": time.strftime("%Y-%m-%d %H:%M:%S"),
        "仓库根": ROOT,
        "spider说明": stats.get("spider说明"),
        "说明": "以下为 All.json 中引用但仓库根不存在的本地文件，需从对应源仓(DodgeZhang/tvbox)手动搬运；"
                "已存在项仅供参考，确认无同名冲突即可。本脚本绝不自动覆盖现有文件。",
        "缺失依赖(需搬运)": missing,
        "已存在依赖(核对用)": present,
    }
    with open(MOVE_LIST, "w", encoding="utf-8") as f:
        json.dump(move, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("\n=== 合并统计 ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"  缺失依赖数: {len(missing)}  已存在依赖数: {len(present)}")
    print(f"  已写出: {ALL_JSON}")
    print(f"  已写出: {MOVE_LIST}")
    return final, stats, missing


def main():
    if "--self-test" in sys.argv:
        run_self_test()
        return
    print("开始合并多源 TVBox 线路 -> All.json")
    loaded = load_sources()
    if not any(d is not None for _, _, d, _ in loaded):
        print("错误：所有源都加载失败，无法合并。")
        sys.exit(1)
    run(loaded)


# ----------------------------------------------------------------------
# 自测（内置样例，不联网、不写仓库 All.json）
# ----------------------------------------------------------------------
MOCK = {
    "Line.json (本地基底)": {
        "priority": 1,
        "data": {
            "spider": "./jar/aidaox.jar",  # 基底自带 spider（仅作基线）
            "wallpaper": "wp", "logo": "lg",
            "sites": [
                {"key": "home", "name": "导航", "type": 3, "api": "csp_Douban"},
                {"key": "s1", "name": "源1", "type": 1, "api": "http://a.com/api",
                 "ext": "./ext/douban.json"},
            ],
            "lives": [{"name": "liveA", "type": 0, "url": "proxy://x"}],
            "parses": [{"name": "p1", "type": 0, "url": "http://jx1"}],
        },
    },
    "DodgeZhang/moyu/config.json": {
        "priority": 2,
        "data": {
            "sites": [{"key": "s2", "name": "源2", "type": 1, "api": "http://b.com"}],
            "lives": [{"name": "liveB", "type": 0, "url": "http://liveb"}],
        },
    },
    "DodgeZhang/moyu/my.json": {
        "priority": 3,
        "data": {
            "spider": "./jar/moyu_spider.jar;md5;mmm",  # 中优先级源
            "sites": [{"key": "s3", "name": "源3", "type": 3, "api": "csp_X",
                       "jar": "./jar/my.jar;md5;m1"}],
        },
    },
    "DodgeZhang/pangmao/fm.json": {
        "priority": 4,
        "data": {
            "sites": [{"key": "home", "name": "导航FM覆盖", "type": 3, "api": "csp_Fm"}],
        },
    },
    "DodgeZhang/pangmao/pm.json": {
        "priority": 5,
        "data": {
            "spider": "./jar/spider.jar;md5;bbb",  # 最高优先级源（pm），应被采用
            "sites": [{"key": "s4", "name": "源4", "type": 3, "api": "csp_Pm",
                       "jar": "./jar/pm.jar;md5;p1"}],
        },
    },
}


def run_self_test():
    print("=== SELF TEST ===")
    loaded = [(n, v["priority"], v["data"], None) for n, v in MOCK.items()]
    final, stats, sites_map = merge_sources(loaded)
    missing, present = scan_deps(final, sites_map)

    tmp = os.path.join(TOOLS, "_selftest_All.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    # ---- 断言 ----
    assert len(final["sites"]) == 5, f"站点数应为5，实际{len(final['sites'])}"
    assert final["spider"] == "./jar/spider.jar;md5;bbb", \
        f"spider应取最高优先级(pm)的，实际{final['spider']}"
    home = [s for s in final["sites"] if s["key"] == "home"][0]
    assert home["name"] == "导航FM覆盖", f"home应被fm覆盖，实际{home['name']}"
    all_paths = {m["path"] for m in missing} | {p["path"] for p in present}
    for expect in ["./ext/douban.json", "./jar/my.jar", "./jar/pm.jar", "./jar/spider.jar"]:
        assert expect in all_paths, f"依赖清单应含 {expect}"
    # 校验可重新解析
    reloaded = parse_jsonc(open(tmp, encoding="utf-8").read())
    assert len(reloaded["sites"]) == 5

    os.remove(tmp)
    print("  站点数:", len(final["sites"]), "(期望5)")
    print("  spider:", final["spider"], "(期望 ./jar/spider.jar;md5;bbb)")
    print("  home 站点名:", home["name"], "(期望 导航FM覆盖)")
    print("  依赖路径(缺失+已存在):", sorted(all_paths))
    print("  统计:", stats["各源贡献站点数"])
    print("=== SELF TEST PASSED ===")


if __name__ == "__main__":
    main()
