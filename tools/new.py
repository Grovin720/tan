# -*- coding: utf-8 -*-
"""
new.py —— 基于 xiao.py 的合并脚本（专用于 G.json 链路）

与 xiao.py 的区别：
1. 只给"远程(api.json)线路"的 name 加分类表情前缀，并把分隔符统一成 ┃（去除前后空格）
2. 模板(dianshi.json)站点的 name 原样保留，不做任何重命名（用户已在模板里手动加好表情）
3. 合并按 key 配对：远程同 key 覆盖模板（保留模板 name）；远程独有 key 按 name 开头表情归类，插到模板里同类第一个站前面
4. 铁律：绝不修改 key（重命名只动远程站点的 name）

用法：python new.py <本地api.json路径> <本地dianshi.json路径>
示例：python new.py ./output/api.json dianshi.json
"""
import json
import sys
import re
import os
import hashlib
from datetime import datetime, timezone, timedelta

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


def _strip_json_comments(text):
    """剥离 JSON 里的 // 行注释与 /* */ 块注释（不破坏字符串内的 //）。"""
    out = []
    i, n = 0, len(text)
    in_str = False
    esc = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == '/' and i + 1 < n and text[i + 1] == '/':
            while i < n and text[i] != '\n':
                i += 1
            continue
        if c == '/' and i + 1 < n and text[i + 1] == '*':
            i += 2
            while i < n and not (text[i] == '*' and i + 1 < n and text[i + 1] == '/'):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def load_json_file(path):
    """读取本地 JSON，容忍 // 与 /* */ 注释。"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return json.loads(_strip_json_comments(text))


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


def _is_emoji_char(ch):
    cp = ord(ch)
    if 0x1F000 <= cp <= 0x1FAFF:
        return True
    if 0x2600 <= cp <= 0x27BF:
        return True
    if 0x2B00 <= cp <= 0x2BFF:
        return True
    if 0xFE00 <= cp <= 0xFE0F:   # 变体选择符
        return True
    if cp == 0x20E3:              # 组合键帽
        return True
    return False


def emoji_prefix(name):
    """提取 name 开头连续的 emoji 作为分类标记（如 ✡️ / 🚀 / 🥦 / 🍄 / 🔥）。
    无 emoji 开头则返回 None。重复表情以第一个为准。"""
    if not isinstance(name, str) or not name:
        return None
    prefix = ""
    for ch in name:
        if _is_emoji_char(ch):
            prefix += ch
        else:
            break
    return prefix or None


def merge_by_key(template_sites, remote_sites):
    """按 key 配对合并，并按分类表情就近归类。
    - 远程同 key 覆盖模板（保留模板 name，key 不变）
    - 远程独有 key：按 name 开头的表情前缀归类，插到模板里同类“第一个站”前面
    - 模板独有 key 原样保留
    - 远程同 key 重复：取第一个
    - 模板里没有对应表情类的远程站：追加到末尾
    铁律：绝不修改 key；模板站 name 原样保留（用户已在模板里手动加好表情）。
    """
    template_by_key = {}
    for s in template_sites:
        if isinstance(s, dict) and "key" in s:
            template_by_key[s["key"]] = s

    remote_by_key = {}
    for s in remote_sites:
        if isinstance(s, dict) and "key" in s:
            remote_by_key.setdefault(s["key"], s)

    # 1) 合并模板（远程同 key 覆盖 live 数据，保留模板 name）
    merged = []
    for t in template_sites:
        k = t.get("key") if isinstance(t, dict) else None
        if k in remote_by_key:
            r = dict(remote_by_key[k])      # 取远程 live 数据
            r["name"] = t.get("name")         # name 用模板的（key 不动）
            merged.append(r)
        else:
            merged.append(t)

    # 2) 远程独有站，按表情前缀分组
    unique_remote = [r for r in remote_sites
                     if isinstance(r, dict) and r.get("key") not in template_by_key]
    remote_by_cat = {}   # emoji_prefix -> [sites]
    ungrouped = []
    for r in unique_remote:
        em = emoji_prefix(r.get("name", ""))
        if em:
            remote_by_cat.setdefault(em, []).append(r)
        else:
            ungrouped.append(r)

    # 3) 模板里各表情类首次出现的位置（决定插入点）
    first_pos = {}
    for i, s in enumerate(merged):
        if not isinstance(s, dict):
            continue
        em = emoji_prefix(s.get("name", ""))
        if em and em not in first_pos:
            first_pos[em] = i

    # 4) 插入：遇到模板里某类的第一个站时，先插入该类远程站（插到它前面）
    result = []
    inserted = set()
    for s in merged:
        em = emoji_prefix(s.get("name", "")) if isinstance(s, dict) else None
        if em and em in remote_by_cat and em not in inserted:
            result.extend(remote_by_cat[em])
            inserted.add(em)
        result.append(s)

    # 5) 未被归类的远程站（模板里没有对应表情类）追加末尾
    result.extend(ungrouped)
    return result


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

    # 3. 读本地模板（容忍 // 与 /* */ 注释）
    dianshi = load_json_file(local_file)
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

    # 6.5 第一个站点（zy_金鹰资源）加盖更新日期 —— 用户要求的特例，覆盖"模板 name 不动"规则
    STAMP_KEY = "zy_金鹰资源"
    stamp_date = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%m.%d")
    for s in dianshi.get("sites", []):
        if isinstance(s, dict) and s.get("key") == STAMP_KEY:
            base = s.get("name", "")
            prefix = (base.split("┃", 1)[0] + "┃") if "┃" in base else base
            s["name"] = f"{prefix}<{stamp_date}更新>"
            print(f"📅 已给首站盖章: {s.get('name')}")
            break

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
