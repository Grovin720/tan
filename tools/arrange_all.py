#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arrange_all.py — 对生成的 All.json 做「4K 线路归位」后处理
====================================================================================

规则（用户要求）：
  - 找出所有 name 含 "4K"（大小写不敏感）的站点；
  - 将它们从原位置抽离，作为【连续一块】插入到 key=="wpys"
    （name=="--- 网盘影视需登录---"）标记【之后】；
  - 其余站点保持原有相对顺序不变；
  - 原地写回 All.json。

本脚本在 merge_all.py 生成 All.json 之后调用（每日更新 / run.yml 中衔接），
也可单独对已成型的 All.json 反复执行（幂等：多次执行结果一致）。

用法：
  python arrange_all.py             # 处理仓库根 All.json（原地写回）
  python arrange_all.py --self-test # 用内置样例验证归位逻辑（不写仓库文件）
"""

import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ALL_JSON = os.path.join(ROOT, "All.json")
MARKER_KEY = "wpys"          # 网盘影视需登录 标记
MARKER_NAME_HINT = "网盘影视"


def is_4k(site):
    """name 是否含 '4K'（大小写不敏感）。"""
    name = site.get("name") or ""
    return "4k" in name.lower()


def arrange(sites):
    """把 4K 站点抽出来，插到 wpys 标记之后；返回 (新列表, 移动条数)。"""
    fourk = [s for s in sites if is_4k(s)]
    rest = [s for s in sites if not is_4k(s)]

    # 在「非4K」列表中定位 wpys 标记
    rest_marker_idx = next(
        (i for i, s in enumerate(rest) if s.get("key") == MARKER_KEY), None
    )
    if rest_marker_idx is None:
        # 兜底：若连 wpys 标记都找不到，则放到末尾
        print(f"  [警告] 未找到 key=='{MARKER_KEY}' 的标记站点，4K 站点将追加到末尾")
        rest_marker_idx = len(rest) - 1

    new_sites = rest[: rest_marker_idx + 1] + fourk + rest[rest_marker_idx + 1:]
    return new_sites, len(fourk)


def dump_tvbox_json(data):
    """仿 G.json 风格序列化（仍是标准合法 JSON，影视仓/TVBox 用 JSON 解析器读取，空白不影响，绝不失效）。
      - 顶层 2 空格缩进；
      - sites / lives 等【数组】内每个对象压成【单独一行】(compact，嵌套对象内联不换行)，
        与 G.json「一个线路一行」完全一致；
      - 顶层标量/对象按 2 空格缩进。
    这样既能让 git diff / 人工查看清爽（一条线路一行），又完全兼容客户端解析。
    """
    out = ["{"]
    items = list(data.items())
    n = len(items)
    for i, (k, v) in enumerate(items):
        comma = "," if i < n - 1 else ""
        kk = json.dumps(k, ensure_ascii=False)
        if isinstance(v, list):
            out.append(f"  {kk}: [")
            for j, elem in enumerate(v):
                ec = "," if j < len(v) - 1 else ""
                out.append("    " + json.dumps(elem, ensure_ascii=False) + ec)
            out.append("  ]" + comma)
        else:
            s = json.dumps(v, ensure_ascii=False, indent=2)
            if "\n" in s:
                s = s.replace("\n", "\n  ")
                out.append(f"  {kk}: {s}{comma}")
            else:
                out.append(f"  {kk}: {s}{comma}")
    out.append("}")
    return "\n".join(out) + "\n"


def run():
    print(f"开始归位 4K 线路 -> {ALL_JSON}")
    if not os.path.isfile(ALL_JSON):
        print(f"  [错误] 找不到 {ALL_JSON}，请先运行 merge_all.py 生成")
        sys.exit(1)

    with open(ALL_JSON, encoding="utf-8") as f:
        data = json.load(f)

    sites = data.get("sites", []) or []
    before = len(sites)
    new_sites, moved = arrange(sites)
    data["sites"] = new_sites

    with open(ALL_JSON, "w", encoding="utf-8") as f:
        f.write(dump_tvbox_json(data))

    # 验证：标记之后紧跟的若干条应全是 4K
    keys = [s.get("key") for s in new_sites]
    mi = keys.index(MARKER_KEY)
    after = keys[mi + 1: mi + 1 + moved] if moved else []
    all_after_are_4k = all(is_4k(new_sites[mi + 1 + i]) for i in range(moved)) if moved else True

    print(f"  站点总数: {before} -> {len(new_sites)}（不变）")
    print(f"  移动到 wpys 之后的 4K 站点: {moved} 条")
    print(f"  wpys 之后前 {min(moved, 6)} 个 key: {after[:6]}")
    print(f"  归位校验: {'PASS ✓' if (moved == 0 or all_after_are_4k) else 'FAIL ✗'}")
    if moved and not all_after_are_4k:
        sys.exit(1)
    print(f"  已写回: {ALL_JSON}")


def run_self_test():
    print("=== SELF TEST ===")
    sites = [
        {"key": "A", "name": "普通线路A"},
        {"key": "wpys", "name": "--- 网盘影视需登录---"},
        {"key": "B", "name": "普通线路B"},
        {"key": "C", "name": "4K超清"},
        {"key": "D", "name": "普通线路D"},
        {"key": "E", "name": "蓝光4k专区"},
        {"key": "F", "name": "普通线路F"},
    ]
    new, moved = arrange(sites)
    keys = [s["key"] for s in new]
    print("  新顺序:", keys)
    assert moved == 2, f"应移动 2 条 4K, 实际 {moved}"
    # C(4K) 与 E(4K) 应紧跟 wpys
    mi = keys.index("wpys")
    assert keys[mi + 1] == "C" and keys[mi + 2] == "E", f"4K 未紧跟 wpys: {keys}"
    # 其余相对顺序保持: A, wpys, (C,E), B, D, F
    assert keys == ["A", "wpys", "C", "E", "B", "D", "F"], f"顺序错误: {keys}"
    # 幂等：再跑一次，输出列表应完全一致（moved 计数仍会等于 4K 条数，但列表不变）
    new2, moved2 = arrange(new)
    assert [s["key"] for s in new2] == keys, "二次归位应幂等（列表不变）"
    print(f"  二次归位后顺序: {[s['key'] for s in new2]}（移动计数={moved2}，但列表不变，符合幂等）")

    # 格式校验：dump_tvbox_json 输出必须是合法 JSON 且 sites 数组内每个对象单独一行
    text = dump_tvbox_json({"spider": "./jar/x.jar", "sites": new,
                            "lives": [{"name": "TV", "url": "http://a"}]})
    parsed = json.loads(text)  # 能解析即合法 JSON（TVBox 不会失效）
    assert parsed["sites"] == new, "dump 后 sites 内容应与原列表一致"
    # 只统计 sites 数组体内部的行（避免把顶层 { 或 lives 元素误算）
    in_sites = False
    site_lines = []
    for ln in text.splitlines():
        st = ln.strip()
        if st.startswith('"sites": ['):
            in_sites = True
            continue
        if in_sites:
            if st.startswith("]"):
                break
            site_lines.append(ln)
    assert len(site_lines) == len(new), f"每个站点应单独成行, 实际 {len(site_lines)}/{len(new)}"
    assert all(ln.strip().startswith("{") for ln in site_lines), "sites 内每行应是独立对象"
    assert text.startswith("{\n  \"spider\"") and '"sites": [' in text, "顶层应为 2 空格缩进"
    print(f"  格式校验: 合法JSON ✓  站点单独成行 ✓（{len(new)} 站）")
    print("=== SELF TEST PASSED ===")


def main():
    if "--self-test" in sys.argv:
        run_self_test()
        return
    run()


if __name__ == "__main__":
    main()
