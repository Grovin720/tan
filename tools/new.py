# -*- coding: utf-8 -*-
"""
new.py —— 基于 xiao.py 的合并脚本（专用于 G.json 链路）

与 xiao.py 的区别：
1. 只给"远程(api.json)线路"的 name 加分类表情前缀，并把分隔符统一成 ┃（去除前后空格）
2. 模板(dianshi.json)站点的 name 原样保留，不做任何重命名（用户已在模板里手动加好表情）
3. 合并按 key 配对：远程同 key 覆盖模板（保留模板 name），远程独有 key 插到 阿里云盘 之后
4. 铁律：绝不修改 key（重命名只动远程站点的 name）

用法：python new.py <本地api.json路径> <本地dianshi.json路径>
示例：python new.py ./output/api.json dianshi.json
"""
import json
import sys
import re
import os
import hashlib

# jar 路径（用于计算 md5）
primary_jar_path = "jar/spider.jar"
fallback_jar_path = "../xiaosa/spider.jar"

# 需要删除的站点 key（保留这层保护，与 xiao.py 一致）
remove_keys = {"版本信息", "腾讯视频", "优酷视频", "芒果视频", "爱奇艺", "三六零", "豆瓣",
               "push_agent", "配置中心", "本地", "预告"}

# ===== 分类表情映射（优先级从上到下取首个命中）=====
CATEGORY_EMOJI = [
    ("APP", "✡️┃"),
    ("短剧", "🚀┃"),
    ("影视", "🥦┃"),
    ("动漫", "🍄┃"),
]
DEFAULT_EMOJI = "🔥┃"
# 预留候选表情（待分配关键词）：⚡ 💋 ⚽ 🧼 💎
PREFIXES = [emo for _, emo in CATEGORY_EMOJI] + [DEFAULT_EMOJI]

# 常见分隔符（统一转 ┃）
SEPARATORS = ["•", "·", "|", "—", "–", "‐", "‑"]


# ===== 保存 JSON（折叠字典数组为单行，空数组和基础数组一行）=====
class CompactJSONEncoder(json.JSONEncoder):
    def iterencode(self, o, _one_shot=False):
        def _compact_list(lst, indent_level):
            pad = '  ' * indent_level
            if not lst or all(isinstance(i, (str, int, float, bool, type(None))) for i in lst):
                return json.dumps(lst, ensure_ascii=False)
            if all(isinstance(i, dict) for i in lst):
                return '[\n' + ',\n'.join([pad + '  ' + json.dumps(i, ensure_ascii=False, separators=(',', ': ')) for i in lst]) + '\n' + pad + ']'
            return json.dumps(lst, ensure_ascii=False, indent=2)

        def _encode(obj, indent_level=0):
            pad = '  ' * indent_level
            if isinstance(obj, dict):
                lines = [f'"{k}": {_encode(v, indent_level+1)}' for k, v in obj.items()]
                return '{\n' + pad + '  ' + (',\n' + pad + '  ').join(lines) + '\n' + pad + '}'
            elif isinstance(obj, list):
                return _compact_list(obj, indent_level)
            return json.dumps(obj, ensure_ascii=False)

        return iter([_encode(o)])


def fetch_json(path_or_url):
    if os.path.exists(path_or_url):
        with open(path_or_url, "r", encoding="utf-8") as f:
            return json.load(f)
    raise ValueError(f"无效路径或 URL：{path_or_url}")


def get_md5(filepath):
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            md5.update(chunk)
    return md5.hexdigest()


def replace_drpy_path(site):
    """将 ./js/drpy2.min.js 替换为 ./lib/drpy2.min.js"""
    if not isinstance(site, dict):
        return
    for field in ("api", "ext"):
        val = site.get(field)
        if isinstance(val, str) and val == "./js/drpy2.min.js":
            site[field] = "./lib/drpy2.min.js"


def normalize_separators(name):
    """常见分隔符统一转 ┃，并去除 ┃ 前后空格；裸连字符(如 CCTV-1)不碰。"""
    s = name
    for sep in SEPARATORS:
        s = s.replace(sep, "┃")
    # 仅替换"带空格包围"的连字符，避免破坏 CCTV-1 之类
    s = re.sub(r'\s+[-\u2010\u2011\u2013]\s+', "┃", s)
    # 去除 ┃ 前后的空格
    s = re.sub(r'\s*┃\s*', "┃", s)
    return s


def rename_name(name):
    """给 name 加分类表情前缀；已带前缀则幂等跳过。只动 name，绝不改 key。"""
    if not isinstance(name, str) or not name:
        return name
    if any(name.startswith(p) for p in PREFIXES):
        return name
    new = normalize_separators(name)
    prefix = DEFAULT_EMOJI
    for kw, emo in CATEGORY_EMOJI:
        if kw in new:
            prefix = emo
            break
    return prefix + new


def merge_by_key(template_sites, remote_sites):
    """按 key 配对合并。
    - 远程同 key 覆盖模板（保留模板 name，key 不变）
    - 远程独有 key 插到 '阿里云盘' 之后
    - 模板独有 key 原样保留
    - 远程同 key 重复：取第一个
    """
    template_by_key = {}
    for s in template_sites:
        if isinstance(s, dict) and "key" in s:
            template_by_key[s["key"]] = s

    remote_by_key = {}
    for s in remote_sites:
        if isinstance(s, dict) and "key" in s:
            remote_by_key.setdefault(s["key"], s)

    merged = []
    for t in template_sites:
        k = t.get("key") if isinstance(t, dict) else None
        if k in remote_by_key:
            r = dict(remote_by_key[k])      # 取远程 live 数据
            r["name"] = t.get("name")         # name 用模板的（key 不动）
            merged.append(r)
        else:
            merged.append(t)

    unique_remote = [r for r in remote_sites if r.get("key") not in template_by_key]

    idx = None
    for i, s in enumerate(merged):
        if isinstance(s, dict) and s.get("key") == "阿里云盘":
            idx = i
            break
    if idx is not None:
        merged[idx + 1:idx + 1] = unique_remote
    else:
        merged.extend(unique_remote)
    return merged


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python new.py <本地api.json路径> <本地dianshi.json路径>")
        print("示例: python new.py ../xiaosa/api.json dianshi.json")
        sys.exit(1)

    remote_url = sys.argv[1]
    local_file = sys.argv[2]

    # 1. 读远程 JSON
    data = fetch_json(remote_url)
    sites = data.get("sites", [])
    filtered_sites = [s for s in sites if isinstance(s, dict)]

    # 2. 远程站预处理：drpy 路径修正、删 jar、重命名 name
    for site in filtered_sites:
        replace_drpy_path(site)
        if isinstance(site, dict) and "jar" in site:
            site.pop("jar", None)
        if isinstance(site, dict) and "name" in site:
            site["name"] = rename_name(site.get("name"))

    # 3. 读本地模板
    with open(local_file, "r", encoding="utf-8") as f:
        dianshi = json.load(f)
    dianshi_sites = dianshi.get("sites", [])

    # 4. remove_keys 过滤（保留保护）
    if remove_keys:
        before = len(filtered_sites)
        filtered_sites = [s for s in filtered_sites if s.get("key") not in remove_keys]
        print(f"✅ 已按 remove_keys 剔除 {before - len(filtered_sites)} 个远程站点")

    # 5. 模板站 name 原样保留，不做任何重命名（用户已在模板里手动加好表情）
    #    注意：下面合并时仍以模板站为准，远程同 key 覆盖也只替换 live 数据、不动 name

    # 6. 合并（按 key）
    dianshi["sites"] = merge_by_key(dianshi_sites, filtered_sites)
    print(f"✅ 合并后站点数: {len(dianshi['sites'])}")

    # 7. 设置 spider 为 jar+md5
    jar_path = primary_jar_path if os.path.exists(primary_jar_path) else fallback_jar_path
    if os.path.exists(jar_path):
        md5_val = get_md5(jar_path)
        dianshi["spider"] = f"./jar/spider.jar;md5;{md5_val}"
        print(f"🔄 spider 已更新为: {dianshi['spider']}")
    else:
        print(f"⚠️ 找不到 jar 文件，未更新 spider：{primary_jar_path} / {fallback_jar_path}")

    # 8. 保存合并结果（新文件）
    output_file = f"{local_file.rsplit('.', 1)[0]}_with_app_sites.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dianshi, f, ensure_ascii=False, indent=2, cls=CompactJSONEncoder)

    print(f"✅ 合并完成，已保存为 {output_file}")
