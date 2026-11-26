# -*- coding: utf-8 -*-
"""
皇极六爻 × 尚氏象数 全自动排盘与动爻计算器 (paipan.py)
输入：本卦名、变卦名(可选，留空/无/同本卦即为静卦)、公历时间、所问何事、性别
自动计算：
  1. 公历 → 节气月建、日辰、时辰干支、旬空、月破（基于 lunar_python）
  2. 对比本卦与变卦阴阳爻位 → 自动计算动爻位置（○/×）或静卦标识
  3. 京房八宫、世应、六冲/六合/游魂/归魂、本宫纯卦伏神（含飞伏生克关系）
  4. 纳甲干支五行六亲（变卦依本卦宫配六亲）、六神
  5. 皇极兼象关键参数：卦身、世身、子孙胎爻
  6. 尚秉和象数：内互卦（二三四爻）、外互卦（三四五爻）、反对倒体卦
  7. 动爻化出：回头生/克、化进/退神、化墓/绝、化空/月破、伏吟/反吟
"""
import argparse
import re
import sys
from datetime import datetime
from lunar_python import Solar

TRIGRAM_BITS = {
    "乾": (1, 1, 1), "兑": (1, 1, 0), "离": (1, 0, 1), "震": (1, 0, 0),
    "巽": (0, 1, 1), "坎": (0, 1, 0), "艮": (0, 0, 1), "坤": (0, 0, 0),
}
BITS_TRIGRAM = {v: k for k, v in TRIGRAM_BITS.items()}
TRIGRAM_NATURE = {
    "乾": "天/健/首/君/金", "兑": "泽/悦/口/毁折/少女",
    "离": "火/明/目/文书/戈甲", "震": "雷/动/足/长男",
    "巽": "风/入/股/木绳/长女", "坎": "水/险/耳/血/盗",
    "艮": "山/止/手背/门庭/少男", "坤": "地/顺/腹/众/母",
}

HEX = [
    (1, "乾为天", "乾", "乾"), (2, "坤为地", "坤", "坤"), (3, "水雷屯", "坎", "震"),
    (4, "山水蒙", "艮", "坎"), (5, "水天需", "坎", "乾"), (6, "天水讼", "乾", "坎"),
    (7, "地水师", "坤", "坎"), (8, "水地比", "坎", "坤"), (9, "风天小畜", "巽", "乾"),
    (10, "天泽履", "乾", "兑"), (11, "地天泰", "坤", "乾"), (12, "天地否", "乾", "坤"),
    (13, "天火同人", "乾", "离"), (14, "火天大有", "离", "乾"), (15, "地山谦", "坤", "艮"),
    (16, "雷地豫", "震", "坤"), (17, "泽雷随", "兑", "震"), (18, "山风蛊", "艮", "巽"),
    (19, "地泽临", "坤", "兑"), (20, "风地观", "巽", "坤"), (21, "火雷噬嗑", "离", "震"),
    (22, "山火贲", "艮", "离"), (23, "山地剥", "艮", "坤"), (24, "地雷复", "坤", "震"),
    (25, "天雷无妄", "乾", "震"), (26, "山天大畜", "艮", "乾"), (27, "山雷颐", "艮", "震"),
    (28, "泽风大过", "兑", "巽"), (29, "坎为水", "坎", "坎"), (30, "离为火", "离", "离"),
    (31, "泽山咸", "兑", "艮"), (32, "雷风恒", "震", "巽"), (33, "天山遁", "乾", "艮"),
    (34, "雷天大壮", "震", "乾"), (35, "火地晋", "离", "坤"), (36, "地火明夷", "坤", "离"),
    (37, "风火家人", "巽", "离"), (38, "火泽睽", "离", "兑"), (39, "水山蹇", "坎", "艮"),
    (40, "雷水解", "震", "坎"), (41, "山泽损", "艮", "兑"), (42, "风雷益", "巽", "震"),
    (43, "泽天夬", "兑", "乾"), (44, "天风姤", "乾", "巽"), (45, "泽地萃", "兑", "坤"),
    (46, "地风升", "坤", "巽"), (47, "泽水困", "兑", "坎"), (48, "水风井", "坎", "巽"),
    (49, "泽火革", "兑", "离"), (50, "火风鼎", "离", "巽"), (51, "震为雷", "震", "震"),
    (52, "艮为山", "艮", "艮"), (53, "风山渐", "巽", "艮"), (54, "雷泽归妹", "震", "兑"),
    (55, "雷火丰", "震", "离"), (56, "火山旅", "离", "艮"), (57, "巽为风", "巽", "巽"),
    (58, "兑为泽", "兑", "兑"), (59, "风水涣", "巽", "坎"), (60, "水泽节", "坎", "兑"),
    (61, "风泽中孚", "巽", "兑"), (62, "雷山小过", "震", "艮"), (63, "水火既济", "坎", "离"),
    (64, "火水未济", "离", "坎"),
]

HEX_BY_NAME = {}
HEX_BY_BITS = {}
SHORT_MAP = {}
for kw, name, up, low in HEX:
    bits = TRIGRAM_BITS[low] + TRIGRAM_BITS[up]
    HEX_BY_NAME[name] = (kw, name, up, low, bits)
    HEX_BY_BITS[bits] = (kw, name, up, low)
    SHORT_MAP[name] = name
    if len(name) == 3 and name[1] == "为":
        SHORT_MAP[name[0]] = name
        SHORT_MAP[name[0] + "卦"] = name
    elif len(name) >= 3:
        SHORT_MAP[name[2:]] = name
        SHORT_MAP[name[2:] + "卦"] = name
SHORT_MAP.update({"天风娠": "天风姤", "天风垢": "天风姤", "泽天央": "泽天夬", "山水濛": "山水蒙"})

PALACE_WX = {"乾": "金", "兑": "金", "离": "火", "震": "木", "巽": "木", "坎": "水", "艮": "土", "坤": "土"}

# 京房八宫世序与卦名归属（由各纯卦按八宫规则推演）
def build_palace_table():
    res = {}
    for p in ["乾", "坎", "艮", "震", "巽", "离", "坤", "兑"]:
        base = list(TRIGRAM_BITS[p] + TRIGRAM_BITS[p])
        # gen: (name_tag, flip_indices, shi_1based, ying_1based)
        gens = [
            ("本宫", [], 6, 3),
            ("一世", [0], 1, 4),
            ("二世", [0, 1], 2, 5),
            ("三世", [0, 1, 2], 3, 6),
            ("四世", [0, 1, 2, 3], 4, 1),
            ("五世", [0, 1, 2, 3, 4], 5, 2),
            ("游魂", [0, 1, 2, 4], 4, 1),
            ("归魂", [4], 3, 6),  # Wait: check 坤->比(4? No! Upper trigram flips back to 0,1? Wait let's check!)
        ]
        #Wait: Let's construct generation by generation cumulatively like Jing Fang!
        # g0: base
        # g1: flip 0
        # g2: flip 1
        # g3: flip 2
        # g4: flip 3
        # g5: flip 4
        # g6 (游魂): flip 3 (4th yao back!)
        # g7 (归魂): flip 0,1,2 (lower trigram back to base!)
        b = base[:]
        seq = [("本宫", b[:], 6, 3)]
        for idx_g, (lbl, flip_idx, sh, yn) in enumerate([
            ("一世", [0], 1, 4), ("二世", [1], 2, 5), ("三世", [2], 3, 6),
            ("四世", [3], 4, 1), ("五世", [4], 5, 2), ("游魂", [3], 4, 1), ("归魂", [0, 1, 2], 3, 6),
        ]):
            for fi in flip_idx:
                b[fi] ^= 1
            seq.append((lbl, b[:], sh, yn))
        for lbl, bits_list, sh, yn in seq:
            _, gname, _, _ = HEX_BY_BITS[tuple(bits_list)]
            res[gname] = (p, lbl, sh, yn)
    return res

PALACE_INFO = build_palace_table()

NAJIA_LOWER = {
    "乾": [("甲", "子"), ("甲", "寅"), ("甲", "辰")],
    "坤": [("乙", "未"), ("乙", "巳"), ("乙", "卯")],
    "震": [("庚", "子"), ("庚", "寅"), ("庚", "辰")],
    "巽": [("辛", "丑"), ("辛", "亥"), ("辛", "酉")],
    "坎": [("戊", "寅"), ("戊", "辰"), ("戊", "午")],
    "离": [("己", "卯"), ("己", "丑"), ("己", "亥")],
    "艮": [("丙", "辰"), ("丙", "午"), ("丙", "申")],
    "兑": [("丁", "巳"), ("丁", "卯"), ("丁", "丑")],
}
NAJIA_UPPER = {
    "乾": [("壬", "午"), ("壬", "申"), ("壬", "戌")],
    "坤": [("癸", "丑"), ("癸", "亥"), ("癸", "酉")],
    "震": [("庚", "午"), ("庚", "申"), ("庚", "戌")],
    "巽": [("辛", "未"), ("辛", "巳"), ("辛", "卯")],
    "坎": [("戊", "申"), ("戊", "戌"), ("戊", "子")],
    "离": [("己", "酉"), ("己", "未"), ("己", "巳")],
    "艮": [("丙", "戌"), ("丙", "子"), ("丙", "寅")],
    "兑": [("丁", "亥"), ("丁", "酉"), ("丁", "未")],
}

ZHI = "子丑寅卯辰巳午未申酉戌亥"
ZHI_WX = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
SHENG = {"木":"火", "火":"土", "土":"金", "金":"水", "水":"木"}
KE = {"木":"土", "土":"水", "水":"火", "火":"金", "金":"木"}
CHONG = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅","卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}
HE6 = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯","辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}
JIN_SHEN = {("亥","子"),("寅","卯"),("巳","午"),("申","酉"),("丑","辰"),("辰","未"),("未","戌"),("戌","丑")}
TUI_SHEN = {(b, a) for a, b in JIN_SHEN}
TOMB = {"木":"未", "火":"戌", "金":"丑", "水":"辰", "土":"辰"}
EXTINCT = {"木":"申", "火":"亥", "金":"寅", "水":"巳", "土":"巳"}
TAI_MAP = {"水":"午", "土":"午", "木":"酉", "火":"子", "金":"卯"}
SHISHEN_LINE = {"子":1,"午":1,"丑":2,"未":2,"寅":3,"申":3,"卯":4,"酉":4,"辰":5,"戌":5,"巳":6,"亥":6}

GODS = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
GOD_START = {"甲":0,"乙":0,"丙":1,"丁":1,"戊":2,"己":3,"庚":4,"辛":4,"壬":5,"癸":5}

LIU_CHONG_GUAS = {"乾为天","坤为地","坎为水","离为火","震为雷","巽为风","艮为山","兑为泽","天雷无妄","雷天大壮"}
LIU_HE_GUAS = {"天地否","地天泰","火山旅","山火贲","水泽节","泽水困","雷地豫","地雷复"}

def get_liuqin(palace_wx, yao_wx):
    if yao_wx == palace_wx: return "兄弟"
    if SHENG[palace_wx] == yao_wx: return "子孙"
    if SHENG[yao_wx] == palace_wx: return "父母"
    if KE[palace_wx] == yao_wx: return "妻财"
    return "官鬼"

def resolve_hex(name):
    if not name: return None
    s = name.strip().replace("卦", "")
    if s in HEX_BY_NAME: return HEX_BY_NAME[s]
    if s in SHORT_MAP: return HEX_BY_NAME[SHORT_MAP[s]]
    if s + "卦" in SHORT_MAP: return HEX_BY_NAME[SHORT_MAP[s + "卦"]]
    raise ValueError(f"无法识别卦名: '{name}'，请提供如 '天地否' 或 '否'。")

def parse_time(t_str):
    t_str = t_str.strip()
    m = re.match(r'^(\d{4})[-/.年](\d{1,2})[-/.月](\d{1,2})(?:[日\sT]+(\d{1,2})(?:[:：点时](\d{1,2}))?)?', t_str)
    if not m:
        raise ValueError(f"无法解析公历时间: '{t_str}'，请使用 YYYY-MM-DD HH:MM 格式。")
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    hh = int(m.group(4)) if m.group(4) is not None else 12
    mm = int(m.group(5)) if m.group(5) is not None else 0
    has_hour = m.group(4) is not None
    solar = Solar.fromYmdHms(y, mo, d, hh, mm, 0)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()
    return {
        "input": f"{y:04d}-{mo:02d}-{d:02d}" + (f" {hh:02d}:{mm:02d}" if has_hour else ""),
        "year": ec.getYear(),
        "month": ec.getMonth(),
        "day": ec.getDay(),
        "hour": ec.getTime() + "时" if has_hour else "（未提供时刻）",
        "xunkong": ec.getDayXunKong(),
        "yuepo": CHONG[ec.getMonth()[1]],
        "solar_term": f"{lunar.getPrevJieQi(True).getName()}后" if lunar.getPrevJieQi(True) else "",
    }

def build_yaos(up, low, palace_wx):
    njs = NAJIA_LOWER[low] + NAJIA_UPPER[up]
    out = []
    for gan, zhi in njs:
        wx = ZHI_WX[zhi]
        lq = get_liuqin(palace_wx, wx)
        out.append({"gan": gan, "zhi": zhi, "wx": wx, "lq": lq, "label": f"{lq}{gan}{zhi}{wx}"})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ben", required=True, help="本卦名称，如 天地否 / 否")
    ap.add_argument("--bian", default="", help="变卦名称（静卦可留空或填 无）")
    ap.add_argument("--time", required=True, help="公历时间，如 2026-11-26 14:35")
    ap.add_argument("--gender", default="未说明", help="性别：男 / 女")
    ap.add_argument("--question", default="", help="所问何事")
    args = ap.parse_args()

    ben_kw, ben_name, ben_up, ben_low, ben_bits = resolve_hex(args.ben)
    bian_clean = args.bian.strip()
    is_static = (not bian_clean) or bian_clean in ("无", "静", "静卦", "无变卦")
    if not is_static:
        bian_kw, bian_name, bian_up, bian_low, bian_bits = resolve_hex(bian_clean)
        if bian_bits == ben_bits:
            is_static = True
    else:
        bian_kw, bian_name, bian_up, bian_low, bian_bits = ben_kw, ben_name, ben_up, ben_low, ben_bits

    dt = parse_time(args.time)
    palace, gen_lbl, shi_pos, ying_pos = PALACE_INFO[ben_name]
    palace_wx = PALACE_WX[palace]

    ben_yaos = build_yaos(ben_up, ben_low, palace_wx)
    # 变卦六亲一律按【本卦所属卦宫】五行配
    bian_yaos = build_yaos(bian_up, bian_low, palace_wx)

    # 伏神（本宫纯卦六爻）
    pure_yaos = build_yaos(palace, palace, palace_wx)
    present_lqs = {y["lq"] for y in ben_yaos}
    missing_lqs = set(["父母", "兄弟", "子孙", "妻财", "官鬼"]) - present_lqs

    # 六神
    g_start = GOD_START[dt["day"][0]]
    gods = [GODS[(g_start + i) % 6] for i in range(6)]

    # 动爻自动计算（自初爻 index 0 至 上爻 index 5）
    moving = []
    for i in range(6):
        if ben_bits[i] != bian_bits[i]:
            moving.append(i + 1)

    # 卦身、世身、子孙胎爻
    shi_idx = shi_pos - 1
    shi_bit = ben_bits[shi_idx]
    gua_shen_zhi = ZHI[shi_idx % 12] if shi_bit == 1 else ZHI[(6 + shi_idx) % 12]
    gua_shen_wx = ZHI_WX[gua_shen_zhi]
    shi_zhi = ben_yaos[shi_idx]["zhi"]
    shi_shen_pos = SHISHEN_LINE[shi_zhi]
    shi_shen_yao = ben_yaos[shi_shen_pos - 1]

    # 找子孙爻五行 -> 胎爻（优先本卦出现，否则找伏神）
    zs_yaos = [y for y in ben_yaos if y["lq"] == "子孙"]
    if not zs_yaos:
        zs_yaos = [y for y in pure_yaos if y["lq"] == "子孙"]
    tai_zhs = sorted(set(TAI_MAP[y["wx"]] for y in zs_yaos))

    # 尚秉和互体与反对倒体
    hu_low = BITS_TRIGRAM[ben_bits[1:4]]
    hu_up = BITS_TRIGRAM[ben_bits[2:5]]
    hu_kw, hu_name, _, _ = HEX_BY_BITS[ben_bits[1:4] + ben_bits[2:5]]
    dao_bits = tuple(reversed(ben_bits))
    dao_kw, dao_name, dao_up, dao_low = HEX_BY_BITS[dao_bits]

    # 本卦特殊属性
    tags = [f"{palace}宫·{gen_lbl}"]
    if ben_name in LIU_CHONG_GUAS: tags.append("六冲卦")
    if ben_name in LIU_HE_GUAS: tags.append("六合卦")
    if is_static: tags.append("静卦")
    if not is_static and ben_up == bian_up and ben_low == bian_low: pass
    # 反吟 / 伏吟判定
    fy_tag = ""
    if not is_static:
        if all(CHONG[ben_yaos[i]["zhi"]] == bian_yaos[i]["zhi"] for i in range(6)):
            fy_tag = "卦变反吟"
        elif all(ben_yaos[i]["zhi"] == bian_yaos[i]["zhi"] for i in range(6)):
            fy_tag = "卦变伏吟"
    if fy_tag: tags.append(fy_tag)

    print(f"# 皇极六爻 × 尚氏象数 自动排盘结果\n")
    print(f"- **所问何事**：{args.question or '（未填）'}")
    print(f"- **求测性别**：{args.gender}")
    print(f"- **公历时间**：{dt['input']}（{dt['solar_term']}）")
    print(f"- **四直干支**：`{dt['year']}年` `{dt['month']}月(建)` `{dt['day']}日` `{dt['hour']}`")
    print(f"- **旬空 / 月破**：旬空 `{dt['xunkong']}` ｜ 月破 `{dt['yuepo']}`")
    print(f"- **本卦变卦**：**{ben_name}** `{chr(0x4DC0 + ben_kw - 1)}`（{' / '.join(tags)}）" +
          ("（静卦无变）" if is_static else f" → **{bian_name}** `{chr(0x4DC0 + bian_kw - 1)}`"))
    print(f"- **自动计算动爻**：" + ("无动爻（六爻安静）" if not moving else "、".join(f"第{m}爻（{'阳动○' if ben_bits[m-1]==1 else '阴动×'}）" for m in moving)))
    print(f"- **皇极二元兼象核心坐标**：")
    print(f"  - 世爻：`{shi_pos}爻 {ben_yaos[shi_idx]['label']}` ｜ 应爻：`{ying_pos}爻 {ben_yaos[ying_pos-1]['label']}`")
    on_board_gs = [i+1 for i, y in enumerate(ben_yaos) if y["zhi"] == gua_shen_zhi]
    print(f"  - **卦身**：`{gua_shen_zhi}{gua_shen_wx}`（" + (f"上卦在{'、'.join(str(x) for x in on_board_gs)}爻" if on_board_gs else "卦身不上卦，改取世身") + "）")
    print(f"  - **世身**：`{shi_shen_pos}爻 {shi_shen_yao['label']}`")
    print(f"  - **子孙胎爻**：`{' / '.join(t + ZHI_WX[t] for t in tai_zhs)}`（孕产占二元必参）")
    print(f"- **尚秉和象数全构（正象 / 互体 / 倒体）**：")
    print(f"  - **本卦上下体**：上卦`{ben_up}`（{TRIGRAM_NATURE[ben_up]}） ／ 下卦`{ben_low}`（{TRIGRAM_NATURE[ben_low]}）")
    print(f"  - **互体卦**：**{hu_name}** `{chr(0x4DC0 + hu_kw - 1)}`（外互3-5爻 `{hu_up}` ／ 内互2-4爻 `{hu_low}`）")
    print(f"  - **反对倒体**：**{dao_name}** `{chr(0x4DC0 + dao_kw - 1)}`（上`{dao_up}` 下`{dao_low}`）")
    print("\n## 六爻纳甲全盘（自上爻至初爻）\n")

    if is_static:
        print("| 爻位 | 伏神(飞伏) | 六神 | 本卦纳甲 | 爻画 | 世应 | 状态标注(空/破/身) |")
        print("|---|---|---|---|---|---|---|")
    else:
        print("| 爻位 | 伏神(飞伏) | 六神 | 本卦纳甲 | 动变 | 世应 | 变卦纳甲 | 动化生克/状态 |")
        print("|---|---|---|---|---|---|---|---|")

    yao_names = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]
    m_branch = dt["month"][1]
    d_branch = dt["day"][1]

    for i in range(5, -1, -1):
        y = ben_yaos[i]
        py = pure_yaos[i]
        fu_str = ""
        if py["lq"] in missing_lqs:
            # 飞伏关系
            fwx, pwx = y["wx"], py["wx"]
            if pwx == fwx: rel = "比和"
            elif SHENG[fwx] == pwx: rel = "飞生伏(得助)"
            elif SHENG[pwx] == fwx: rel = "伏生飞(泄气)"
            elif KE[pwx] == fwx: rel = "伏克飞(出暴)"
            else: rel = "飞克伏(伤身)"
            fu_str = f"{py['label']} [{rel}]"

        bar_str = "▅▅▅▅▅" if ben_bits[i] == 1 else "▅▅　▅▅"
        sy = "世" if (i + 1) == shi_pos else ("应" if (i + 1) == ying_pos else "")

        tags_line = []
        if y["zhi"] in dt["xunkong"]: tags_line.append("旬空")
        if y["zhi"] == dt["yuepo"]: tags_line.append("月破")
        if CHONG[y["zhi"]] == d_branch: tags_line.append("日冲")
        if HE6[y["zhi"]] == d_branch: tags_line.append("日合")
        if HE6[y["zhi"]] == m_branch: tags_line.append("月合")
        if y["zhi"] == gua_shen_zhi: tags_line.append("卦身")
        if (i + 1) == shi_shen_pos: tags_line.append("世身")
        if y["zhi"] in tai_zhs: tags_line.append("胎爻")

        if is_static:
            print(f"| {yao_names[i]} | {fu_str} | {gods[i]} | {y['label']} | {bar_str} | {sy} | {'、'.join(tags_line)} |")
        else:
            by = bian_yaos[i]
            is_mv = (i + 1) in moving
            mv_sym = f"{bar_str} ○→" if (is_mv and ben_bits[i] == 1) else (f"{bar_str} ×→" if is_mv else bar_str)
            bian_bar = "▅▅▅▅▅" if bian_bits[i] == 1 else "▅▅　▅▅"
            bian_str = f"{by['label']} {bian_bar}"

            if is_mv:
                if by["wx"] == y["wx"]:
                    if (y["zhi"], by["zhi"]) in JIN_SHEN: tags_line.append("化进神")
                    elif (y["zhi"], by["zhi"]) in TUI_SHEN: tags_line.append("化退神")
                    else: tags_line.append("化比和")
                elif SHENG[by["wx"]] == y["wx"]: tags_line.append("化回头生")
                elif KE[by["wx"]] == y["wx"]: tags_line.append("化回头克")
                elif SHENG[y["wx"]] == by["wx"]: tags_line.append("化泄气")
                elif KE[y["wx"]] == by["wx"]: tags_line.append("化克出")
                if by["zhi"] == TOMB[y["wx"]]: tags_line.append("化墓")
                if by["zhi"] == EXTINCT[y["wx"]]: tags_line.append("化绝")
                if by["zhi"] in dt["xunkong"]: tags_line.append("化空")
                if by["zhi"] == dt["yuepo"]: tags_line.append("化破")
            print(f"| {yao_names[i]} | {fu_str} | {gods[i]} | {y['label']} | {mv_sym} | {sy} | {bian_str} | {'、'.join(tags_line)} |")


if __name__ == "__main__":
    main()
