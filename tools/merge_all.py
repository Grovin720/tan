#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_all.py — 以 Line.json 为基底，合并 pangmao/pm.json 与 moyu/my.json，产出 All.json
====================================================================================

合并规则（用户最终确认版）：
  1. 基底 = tools/Line.json（其顶层字段 spider/logo/wallpaper 及 sites 作为基线，原样保留）
  2. pangmao/pm.json 的 sites 并入：按 key 合并，同 key 后者（pm）覆盖前者（Line 同名导航站）
  3. moyu/my.json 的 sites 插入到 Line.json 中 key=="my" 的标记站点【之后】；
     且 my.json 的每条 site 都补上 jar 字段（= moyu 的 spider jar，路径改写为 ./moyu/jar/...）
  4. 依赖路径“源感知”改写（只改相对路径 ./ 开头，http/proxy/csp_ 不动）：
       - 来自 pm.json 的 ./ext/.. ./jar/.. ./img/..  ->  ./pangmao/ext/.. 等
       - 来自 my.json 的 ./ext/.. ./jar/.. ./img/..  ->  ./moyu/ext/.. 等
       - Line.json 自带的 ./ 路径保持不动（仓库根已存在对应文件）
  5. 顶层 spider/logo 等保留 Line.json 的（基底）；pm/my 仅贡献 sites，不覆盖顶层。

依赖：仅标准库（urllib/ssl/json/re/os/sys/time）。
本地文件优先；本地缺失时回退 GitHub raw（便于首次运行 / --self-test / CI 兜底）。

用法：
  python merge_all.py            # 读本地(回退远程)并合并，写出 All.json + 待搬运文件清单.json
  python merge_all.py --self-test # 用内置样例验证合并逻辑（不联网、不写仓库 All.json）
"""

import os
import re
import sys
import json
import time
import ssl
import urllib.request

# 复用 arrange_all 的「一个站点一行」序列化（仿 G.json 风格，仍是合法 JSON，TVBox 兼容）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arrange_all import dump_tvbox_json  # noqa: E402

# ---- 路径基准：tools/merge_all.py -> 父目录即仓库根 ----
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = HERE

LINE_LOCAL = os.path.join(TOOLS, "Line.json")
PM_LOCAL = os.path.join(ROOT, "pangmao", "pm.json")
MY_LOCAL = os.path.join(ROOT, "moyu", "my.json")

REPO = "DodgeZhang/tvbox"
BRANCH = "main"
PM_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/pangmao/pm.json"
MY_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/moyu/my.json"

PANGMAO_PREFIX = "./pangmao/"
MOYU_PREFIX = "./moyu/"

ALL_JSON = os.path.join(ROOT, "All.json")
MOVE_LIST = os.path.join(ROOT, "待搬运文件清单.json")

# 需要被路径重写的字段（顶层与站点级），ext 可能是对象/字符串，需递归
REWRITE_FIELDS = ("spider", "logo", "wallpaper", "ext", "jar", "api", "py", "js")


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


def load_local_or_remote(local_path, url, label):
    """优先读本地文件；本地不存在则回退 GitHub raw。返回 (data, source)。"""
    if os.path.exists(local_path):
        try:
            txt = open(local_path, encoding="utf-8").read()
            data = parse_jsonc(txt)
            print(f"  [本地] {label} <- {local_path}  站点={len(data.get('sites', []) or [])}")
            return data, "local"
        except Exception as e:  # noqa: BLE001
            print(f"  [警告] 本地 {label} 解析失败({e})，尝试远程")
    try:
        txt = fetch(url)
        data = parse_jsonc(txt)
        print(f"  [远程] {label} <- {url}  站点={len(data.get('sites', []) or [])}")
        return data, "remote"
    except Exception as e:  # noqa: BLE001
        print(f"  [失败] {label}: {type(e).__name__} {e}")
        return None, "none"


# ----------------------------------------------------------------------
# 路径重写（源感知）
# ----------------------------------------------------------------------
# 只改写这几种本地相对目录引用；http/proxy/csp_ 不会以 "./" 开头，天然跳过。
_LOCAL_REF = re.compile(r'\./(ext|jar|img|py|js)/')


def rewrite_paths(value, prefix):
    """递归地把所有本地相对路径改写为 prefix + 原相对路径。
    prefix 形如 "./pangmao/"；以下三种情形都覆盖：
      1) 整串就是相对路径："./ext/x.json"        -> "./pangmao/ext/x.json"
      2) 字典/列表内嵌：{"home":{"douban":"./ext/x.json"}} -> 同样改写
      3) JSON 字符串内嵌：'{"filters":"./ext/x.json"}'       -> 提取其中 ./ext/.. 改写
    已带前缀(./pangmao/ ./moyu/)的不会二次匹配（./pangmao/ext 不含 "./ext/" 子串）。"""
    if isinstance(value, str):
        if value.startswith("./"):
            return prefix + value[2:]
        # 处理 JSON 字符串或普通字符串中内嵌的本地引用（如 {"filters":"./ext/x.json"}）
        return _LOCAL_REF.sub(lambda m: prefix + m.group(1) + "/", value)
    if isinstance(value, dict):
        return {k: rewrite_paths(v, prefix) for k, v in value.items()}
    if isinstance(value, list):
        return [rewrite_paths(v, prefix) for v in value]
    return value


def rewrite_site(site, prefix):
    out = dict(site)
    for f in REWRITE_FIELDS:
        if f in out and out[f] not in (None, ""):
            out[f] = rewrite_paths(out[f], prefix)
    return out


# ----------------------------------------------------------------------
# 合并
# ----------------------------------------------------------------------
def merge(base, pm, my):
    """base=Line.json, pm=pangmao/pm.json(可None), my=moyu/my.json(可None)
    返回 (final_dict, stats)。"""
    stats = {"基底站点": len(base.get("sites", []) or []),
             "pm参与": pm is not None, "my参与": my is not None}

    # ---- 顶层：以 base(Line) 为基准，原样保留 ----
    final = {}
    for k, v in base.items():
        final[k] = v  # 包含 spider/logo/wallpaper/sites 等

    # 用有序列表 + key->index 做按 key 合并与去重
    sites = list(final.get("sites", []) or [])
    seen = {s.get("key"): i for i, s in enumerate(sites) if s.get("key")}

    # ---- 2) pm.json sites 并入（按 key，后者覆盖）----
    pm_added = pm_replaced = 0
    if pm:
        for s in (pm.get("sites", []) or []):
            k = s.get("key")
            if not k:
                continue
            rs = rewrite_site(s, PANGMAO_PREFIX)
            if k in seen:
                sites[seen[k]] = rs
                pm_replaced += 1
            else:
                sites.append(rs)
                seen[k] = len(sites) - 1
                pm_added += 1
    stats["pm新增"] = pm_added
    stats["pm覆盖"] = pm_replaced

    # ---- 3) my.json sites 插入到 "my" 标记之后，且每条补 jar ----
    my_inserted = my_skipped = 0
    moyu_jar = None
    if my:
        # moyu 的 spider jar（改写路径）作为每条 site 的 jar
        sp = my.get("spider", "") or ""
        if sp.startswith("./"):
            moyu_jar = rewrite_paths(sp, MOYU_PREFIX)  # ./jar/x.jar;md5;.. -> ./moyu/jar/x.jar;md5;..

        # 先找 "my" 标记位置（在 Line+pm 合并后的列表里）
        marker_idx = next((i for i, s in enumerate(sites) if s.get("key") == "my"), None)
        if marker_idx is None:
            print("  [警告] 未在基底找到 key=='my' 的标记站点，my.json 的 sites 将追加到末尾")
            marker_idx = len(sites) - 1

        # 准备 my sites（改写路径 + 补 jar）
        my_ready = []
        for s in (my.get("sites", []) or []):
            k = s.get("key")
            if not k:
                continue
            rs = rewrite_site(s, MOYU_PREFIX)
            if moyu_jar:
                rs["jar"] = moyu_jar  # 每条补 jar（覆盖/新增）
            # 去重：若前面已存在同 key（如 Line 的 Douban），则移除旧条目，避免 TVBox 重复 key
            if k in seen and seen[k] != marker_idx:
                old = seen[k]
                sites[old] = None  # 标记待删
            my_ready.append(rs)
            my_inserted += 1

        # 插入到标记之后
        insert_at = marker_idx + 1
        sites[insert_at:insert_at] = my_ready
        # 清理被替换成 None 的旧条目
        sites = [s for s in sites if s is not None]
        # 重建 seen（插入/删除后索引变了）
        seen = {s.get("key"): i for i, s in enumerate(sites) if s.get("key")}
    stats["my插入"] = my_inserted

    final["sites"] = sites
    stats["合并后站点总数"] = len(sites)
    return final, stats


# ----------------------------------------------------------------------
# 待搬运清单（核对依赖是否都已同步到本地）
# ----------------------------------------------------------------------
def scan_deps(final):
    deps = {}

    def add(path):
        if not isinstance(path, str):
            return
        # TVBox 的 jar/spider 常写成 "./jar/x.jar;md5;<hash>"，校验后缀不能算进路径
        clean = path.split(";md5;")[0]
        if not clean.startswith("./"):
            return
        rel = clean[2:]
        abs_p = os.path.join(ROOT, rel)
        e = os.path.exists(abs_p)
        d = deps.setdefault(rel, {"count": 0, "exists": e})
        d["count"] += 1

    sp = final.get("spider", "") or ""
    add(sp)  # add() 内部会剥掉 ";md5;<hash>" 校验后缀
    for s in final.get("sites", []):
        for f in ("jar", "ext", "api", "py", "js"):
            v = s.get(f)
            if isinstance(v, str):
                add(v)
            elif isinstance(v, dict):  # ext 可能是对象，递归找字符串
                for val in _walk_str(v):
                    add(val)

    missing, present = [], []
    for rel, info in sorted(deps.items()):
        entry = {"path": "./" + rel, "引用次数": info["count"], "仓库中存在": info["exists"]}
        (missing if not info["exists"] else present).append(entry)
    return missing, present


def _walk_str(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_str(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_str(v)


# ----------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------
def run():
    print("开始合并 -> All.json")
    base = parse_jsonc(open(LINE_LOCAL, encoding="utf-8").read())
    pm, _ = load_local_or_remote(PM_LOCAL, PM_URL, "pangmao/pm.json")
    my, _ = load_local_or_remote(MY_LOCAL, MY_URL, "moyu/my.json")

    if pm is None and my is None:
        print("错误：pm 与 my 均加载失败，无法合并（基底 Line.json 仍会原样写出）。")
    final, stats = merge(base, pm, my)

    with open(ALL_JSON, "w", encoding="utf-8") as f:
        f.write(dump_tvbox_json(final))

    missing, present = scan_deps(final)

    # 顶层 spider 是最致命的依赖：它加载不到，所有 jar 源全废。单独醒目告警。
    sp_clean = (final.get("spider", "") or "").split(";md5;")[0]
    if sp_clean.startswith("./") and not os.path.exists(os.path.join(ROOT, sp_clean[2:])):
        print(f"\n  ⚠️ 警告：顶层 spider 指向的文件在仓库里不存在 -> {sp_clean}")
        print("     Line.json 的 spider 必须指向仓库中真实存在的 jar，否则影视仓加载不到 spider，所有 jar 源失效。")
        print("     请修正 tools/Line.json 的顶层 spider，或先把该 jar 同步进仓库。")

    move = {
        "生成时间": time.strftime("%Y-%m-%d %H:%M:%S"),
        "仓库根": ROOT,
        "说明": "以下为 All.json 中引用但仓库根【不存在】的本地文件，需先运行 sync_ds.py 同步；"
                "已存在项仅供参考。All.json 依赖 ./pangmao/ 与 ./moyu/ 同步文件夹。",
        "缺失依赖(需先 sync_ds.py)": missing,
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


def main():
    if "--self-test" in sys.argv:
        run_self_test()
        return
    run()


# ----------------------------------------------------------------------
# 自测（内置样例，不联网、不写仓库 All.json）
# ----------------------------------------------------------------------
def run_self_test():
    print("=== SELF TEST ===")
    # 基底：含 key=="my" 标记 + 一个将被 pm 覆盖的 Douban
    base = {
        "spider": "./jar/aidaox.jar",
        "sites": [
            {"key": "Douban", "name": "豆瓣导航", "type": 3, "api": "csp_Douban",
             "ext": "./ext/douban.json"},
            {"key": "my", "name": "--- my---"},
            {"key": "Market", "name": "商店", "type": 3, "api": "csp_Market"},
        ],
    }
    pm = {
        "spider": "./jar/aidaox-20260911.jar;md5;abc",
        "sites": [
            {"key": "Douban", "name": "豆瓣导航(pm覆盖)", "type": 3, "api": "csp_Douban",
             "ext": "./ext/douban.json"},
            {"key": "pmExtra", "name": "PM新增", "type": 3, "api": "csp_X",
             "ext": "./ext/pm.json"},
            {"key": "pmStr", "name": "PM内嵌串", "type": 3, "api": "csp_Y",
             "ext": '{"filters":"./ext/douban.json","api":"https://x.com"}'},
        ],
    }
    my = {
        "spider": "./jar/moyu.jar;md5;def",
        "sites": [
            {"key": "M1", "name": "摸鱼1", "type": 3, "api": "csp_PianDan",
             "ext": {"home": {"douban": "./ext/douban.json", "tmdb": "./ext/tmdb.json"}}},
            {"key": "Douban", "name": "片单(my覆盖)", "type": 3, "api": "csp_PianDan"},
        ],
    }

    final, stats = merge(base, pm, my)

    keys = [s["key"] for s in final["sites"]]
    # 1) my 标记位置 + my sites 紧随其后
    mi = keys.index("my")
    assert keys[mi + 1] == "M1", f"M1 应紧跟 my 标记, 实际 {keys}"
    assert "pmExtra" in keys, "pmExtra 应被并入"
    # 2) pm 覆盖 Douban（在 my 之前的那条）—— Line 的 Douban 应被 pm 覆盖，
    #    而 my 的 Douban 插入在 my 之后；因此列表中有两条 Douban 吗？不应有。
    #    按规则：Line 的 Douban 被 pm 覆盖 -> 仍为 Line 位置；my 的 Douban 插入到 my 之后并移除前面同名 -> 最终仅 1 条 Douban(my)
    douban = [s for s in final["sites"] if s["key"] == "Douban"]
    assert len(douban) == 1, f"Douban 应只剩 1 条(my覆盖), 实际 {len(douban)}"
    assert douban[0]["name"] == "片单(my覆盖)", f"Douban 应为 my 版, 实际 {douban[0]['name']}"
    # 3) my 每条补 jar = ./moyu/jar/moyu.jar;md5;def
    m1 = [s for s in final["sites"] if s["key"] == "M1"][0]
    assert m1["jar"] == "./moyu/jar/moyu.jar;md5;def", f"M1 jar 错误: {m1.get('jar')}"
    # 4) 路径改写：pm 的 ext -> ./pangmao/ext/pm.json
    pme = [s for s in final["sites"] if s["key"] == "pmExtra"][0]
    assert pme["ext"] == "./pangmao/ext/pm.json", f"pm ext 改写错误: {pme['ext']}"
    # 5) my 的嵌套 ext 改写 -> ./moyu/ext/...
    assert m1["ext"]["home"]["douban"] == "./moyu/ext/douban.json", f"my 嵌套 ext 改写错误: {m1['ext']}"
    # 5b) pm 的 JSON 字符串内嵌 ./ext/ 也需改写（回归）
    pmstr = [s for s in final["sites"] if s["key"] == "pmStr"][0]
    assert pmstr["ext"] == '{"filters":"./pangmao/ext/douban.json","api":"https://x.com"}', \
        f"pm 内嵌串 ext 改写错误: {pmstr['ext']}"
    # 6) Line 自带 ./ 不动
    assert final["spider"] == "./jar/aidaox.jar", f"顶层 spider 应保留 Line: {final['spider']}"
    # 7) 可重新解析
    tmp = os.path.join(TOOLS, "_selftest_All.json")
    json.dump(final, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    parse_jsonc(open(tmp, encoding="utf-8").read())
    os.remove(tmp)

    print("  站点顺序:", keys)
    print("  统计:", stats)
    print("  M1 jar:", m1["jar"])
    print("  pmExtra ext:", pme["ext"])
    print("  my 嵌套 ext:", m1["ext"]["home"])
    print("=== SELF TEST PASSED ===")


if __name__ == "__main__":
    main()
