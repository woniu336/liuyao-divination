# -*- coding: utf-8 -*-
"""
本地六爻典籍章节与关键词检索器 (query_corpus.py)
用于在解卦前按门类、章节或关键词快速调阅 skills/liuyao-divination/references/ 下的七部核心典籍。
"""
import os
import re
import argparse

REF_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references"))

BOOKS = {
    "点窍": "六爻秘法点窍.md",
    "病灾": "六爻病灾秘法.md",
    "婚孕": "六爻婚孕秘法（简体版）.md",
    "古筮": "周易古筮考通解.md",
    "天机": "《断易天机》分类占断技法与白话精粹.md",
    "尚占": "《周易尚占》分类占断技法与白话精粹.md",
    "易林": "《易林补遗》分类占断技法与白话精粹.md",
}

CATEGORY_ROUTES = {
    "取象": [("点窍", "第一章六爻取万物类象"), ("点窍", "八卦万物类象"), ("点窍", "卦宫、内外卦取象"), ("点窍", "爻位取象"), ("古筮", "左传")],
    "财运": [("点窍", "第二章财运预测"), ("点窍", "皇极六爻投资求财"), ("点窍", "经营求财"), ("点窍", "合作求财"), ("天机", "占求财第十九"), ("天机", "占买卖第二十")],
    "投资": [("点窍", "皇极六爻投资求财"), ("点窍", "合作求财预测立极"), ("点窍", "合同求财"), ("病灾", "在一切卦中都可以预判灾祸")],
    "官运": [("点窍", "第三章 官运工作预测"), ("点窍", "官职升迁预测"), ("点窍", "找工作，谋职位"), ("病灾", "官灾的预判秘法"), ("天机", "占仕宦第十一")],
    "考试": [("点窍", "第四章 考试预测"), ("点窍", "考学预测立极"), ("天机", "选举占第十")],
    "婚姻": [("婚孕", "第三节 婚姻预测点窍"), ("婚孕", "世应确定彼此的关系"), ("婚孕", "婚姻成败看用神"), ("婚孕", "用神克世爻"), ("婚孕", "双官两夫"), ("婚孕", "财伏官下"), ("天机", "占婚姻第八")],
    "孕产": [("婚孕", "第三章 孕产预测点窍"), ("婚孕", "如何断命中无子"), ("婚孕", "是否难产的判断"), ("婚孕", "生男生女的断法"), ("天机", "占分娩第九")],
    "出行": [("点窍", "第七章 出行行人预测"), ("点窍", "出走、失踪预测立极"), ("病灾", "车祸的预判秘法"), ("天机", "占出行第二十一"), ("天机", "占行人第二十二")],
    "失物": [("点窍", "第八章失物捕盗预测"), ("点窍", "遗失预测立极"), ("点窍", "皇极六爻捕盗预测立极"), ("古筮", "射包烟卷锡纸球"), ("天机", "占盗贼第十六"), ("天机", "占遗失第十七")],
    "疾病": [("病灾", "第三章病体吉凶秘法"), ("病灾", "病体吉凶预测一言点窍"), ("病灾", "六冲近病即愈"), ("病灾", "用神之病处"), ("病灾", "医药判断一言点窍"), ("点窍", "第九章 皇极六爻疾病预测"), ("天机", "占疾病第二十四")],
    "灾祸": [("病灾", "事分成败得失"), ("病灾", "在一切卦中都可以预判灾祸"), ("病灾", "防骗预测一言点窍"), ("病灾", "人为之祸的预判秘法")],
    "诉讼": [("点窍", "第十章 官司刑狱预测"), ("病灾", "第六章民事诉讼秘法"), ("病灾", "第七章刑事诉讼秘法"), ("天机", "占词讼第十五")],
    "古筮": [("古筮", "原序"), ("古筮", "用九用六解"), ("古筮", "魏管辂为刘邠射覆"), ("古筮", "纳甲考"), ("古筮", "尚秉和与《周易古筮考》")],
}

def extract_section(filepath, heading_query, max_chars=1800):
    text = open(filepath, encoding="utf-8").read()
    # Find markdown heading containing heading_query
    pat = re.compile(rf'^(#{{1,4}}\s+[^\n]*{re.escape(heading_query)}[^\n]*)$', re.M)
    m = pat.search(text)
    if not m:
        idx = text.find(heading_query)
        if idx == -1:
            return None
        start = max(0, idx - 80)
        return text[start:start + max_chars]
    start = m.start()
    # Read until next ## heading or max_chars (skip ### inside if looking at ##, unless too long)
    nxt = re.search(r'\n##\s+', text[start + 10:])
    end = start + 10 + nxt.start() if nxt else len(text)
    snippet = text[start:min(end, start + max_chars)]
    return snippet

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="", help=f"按门类批量检索: {', '.join(CATEGORY_ROUTES.keys())}")
    ap.add_argument("--book", default="", choices=[""] + list(BOOKS.keys()), help="指定书简称")
    ap.add_argument("--query", default="", help="章节名或关键词")
    ap.add_argument("--max-chars", type=int, default=1400, help="每条最大返回字符数")
    args = ap.parse_args()

    if args.category:
        # Fuzzy match category
        cat = args.category.strip()
        matched_keys = [k for k in CATEGORY_ROUTES if k in cat or cat in k]
        if not matched_keys:
            print(f"[提示] 未匹配到预设门类 '{cat}'，可用门类：{', '.join(CATEGORY_ROUTES.keys())}")
            return
        for ck in matched_keys:
            print(f"================ 门类检索：{ck} ================")
            for bkey, hq in CATEGORY_ROUTES[ck]:
                fp = os.path.join(REF_DIR, BOOKS[bkey])
                snip = extract_section(fp, hq, max_chars=args.max_chars)
                if snip:
                    print(f"\n--- [{BOOKS[bkey]} :: {hq}] ---")
                    print(snip.strip())
                    print()
        return

    targets = [BOOKS[args.book]] if args.book else list(BOOKS.values())
    if not args.query:
        for fn in targets:
            fp = os.path.join(REF_DIR, fn)
            t = open(fp, encoding="utf-8").read()
            heads = re.findall(r'^##\s+.+$', t, re.M)
            print(f"=== {fn} (## headings: {len(heads)}) ===")
            for h in heads[:30]:
                print(" ", h)
        return

    for fn in targets:
        fp = os.path.join(REF_DIR, fn)
        snip = extract_section(fp, args.query, max_chars=args.max_chars)
        if snip:
            print(f"\n=== [{fn}] 匹配 '{args.query}' ===")
            print(snip.strip())

if __name__ == "__main__":
    main()
