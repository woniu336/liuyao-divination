---
name: liuyao-divination
description: >-
  Use this skill whenever the user asks for Liuyao (六爻) hexagram divination or interpretation,
  or provides a hexagram setup (本卦, optional 变卦/静卦, 公历时间, 所问何事, 性别).
  It runs deterministic calendar/Najia/moving-line/Hu-Ti calculations, retrieves categorized
  techniques from the local 7-book classical & modern corpus in references/, and synthesizes
  Jia Bingran's "Dual-Element" (二元兼象定论) rules with Shang Binghe's "Bagua & Hu-Ti Imagery"
  (八卦互体正象取象法) into a rigorous, multi-question divination analysis.
---

# Liuyao & Classical Xiangshu Divination Skill (皇极二元 × 尚氏象数解卦技能)

This skill provides a complete, deterministic workflow for Liuyao divination backed by seven curated Chinese divination texts stored in `./references/`.

## Input Requirements

Check the user's request for the following 5 inputs:
1. **本卦** *(Required)*: e.g., `天地否` or `否` (64 hexagram full or short name).
2. **变卦** *(Optional)*: e.g., `天山遁` or `遁`. If omitted, `"无"`, `"静卦"`, or identical to 本卦, treat the cast as a **静卦** (static hexagram). *Do not require the user to specify 动爻 — `paipan.py` computes moving lines automatically.*
3. **公历时间** *(Required)*: e.g., `2026-11-26 14:35` or `2026-11-26`. Used to calculate exact Solar-Term Month Branch (`月建`), Day Stem-Branch (`日辰`), `旬空`, `月破`, and `六神`.
4. **所问何事** *(Required)*: One core question or multiple questions.
5. **性别** *(Required)*: `男` or `女` (critical for marriage, relationship, fertility, and role mapping).

*If any of the 4 required fields (`本卦`, `公历时间`, `所问何事`, `性别`) is missing, politely ask the user to supply it before running the calculation.*

---

## Execution Workflow (5 Mandatory Steps)

### Step 1: Deterministic Hexagram & Moving-Line Calculation
NEVER compute Gregorian-to-GanZhi, 旬空, 伏神, 卦身, 世身, 互体, or 动爻 mentally. Always run [paipan.py](./scripts/paipan.py):

```bash
# Run from the skill directory (liuyao-divination/)
python ./scripts/paipan.py \
  --ben "<本卦>" \
  --bian "<变卦或空>" \
  --time "<公历时间>" \
  --gender "<男/女>" \
  --question "<所问何事>"
```

Verify from the output:
- Exact 四直 (`年/月建/日辰/时辰`), `旬空`, `月破`
- Auto-calculated 动爻 (`○` 阳动变阴 / `×` 阴动变阳) or 静卦
- `世爻`, `应爻`, `卦身` (if not on board, fall back to `世身`), `子孙胎爻`
- `伏神` and飞伏 relation (`出暴/伤身/泄气/得助/比和`)
- Shang Binghe `内互(2-4爻)` / `外互(3-5爻)` hexagram (`互体卦`) and `反对倒体`

### Step 2: Question Decomposition & Implicit Hazard Scan
1. Break `所问何事` into **【核心问题 Q1】** and any **【附属问题 Q2, Q3...】**.
2. Scan the board for **【隐性预警 Q-Alert】** ("占此应彼"): If `世爻` and `兼象爻` (`卦身`/`世身` for self; `应爻` for proxy) are both severely clashing/harmed, trigger `《六爻病灾秘法》第1章第4节` hazard warning even when the user asked about wealth or marriage.

### Step 3: Chapter-Indexed Corpus Retrieval (按问查章)
Query the relevant categorized rules from `./references/` using [query_corpus.py](./scripts/query_corpus.py) before drafting interpretations:

```bash
# Run from the skill directory (liuyao-divination/)
python ./scripts/query_corpus.py \
  --category "<门类关键词>" \
  --max-chars 1400
```
Or inspect specific books/chapters with `--book` and `--query`:
- Books: `点窍` (`六爻秘法点窍.md`), `病灾` (`六爻病灾秘法.md`), `婚孕` (`六爻婚孕秘法（简体版）.md`), `古筮` (`周易古筮考通解.md`), `天机` (`《断易天机》分类占断技法与白话精粹.md`), `尚占` (`《周易尚占》分类占断技法与白话精粹.md`), `易林` (`《易林补遗》分类占断技法与白话精粹.md`).

**Category Routing Map**:
| Question Category | 《六爻秘法点窍》 | 《六爻病灾秘法》 | 《六爻婚孕秘法》 | 《周易古筮考通解》 / 明清三经 |
|---|---|---|---|---|
| **取象 / 万物类象** | 第1章（第1-13节） | 第1章第1、3节 | 自序 | 卷一、卷八、卷九、附录《左传国语易象释》 |
| **财运 / 投资 / 开店 / 借贷 / 合同** | 第2章（第1-11节） | 第1章第4节、第2章第4节 | — | 上下正象+互体辨行业与隐情；《天机》第19-20章 |
| **官运 / 升迁 / 求职** | 第3章（第1-5节） | 第1章第6节 | — | 乾震离巽升迁象；《天机》第11章 |
| **考试 / 考学 / 考证** | 第4章（第1-3节） | — | — | 离坎父母文印互象；《天机》第10章 |
| **婚恋 / 相亲 / 外遇 / 离婚** | 第5章（第1-2节） | 第1章第4节（防病灾） | 第1章（第1-10节）、第2章（第1-6节） | 少女/长男等正互象；《天机》第8章 |
| **孕产 / 子嗣 / 剖腹产 / 男女** | 第6章（第1-2节） | — | 第3章（第1-8节）、第4章（第1-7节） | 坤腹坎血胎水；《天机》第9章 |
| **出行 / 行人 / 出走 / 失踪** | 第7章（第1-5节） | 第1章第4、5、7节 | — | 震足巽风坎险艮止；《天机》第21-23、30章 |
| **遗失 / 被盗 / 捕盗** | 第8章（第1-4节） | 第2章第4节 | — | **卷十管辂郭璞射覆法**（正互描绘物象）；《天机》第16-17章 |
| **疾病 / 症候 / 医药 / 灾祸** | 第9章（第1-4节） | 第1-5章全篇 | — | 八卦脏腑部位+互体病灶转化；《天机》第24、35章 |
| **民事 / 刑事诉讼 / 官司** | 第10章（第1-2节） | 第6章（民事）、第7章（刑事） | — | 讼/噬嗑/坎险/艮止互象；《天机》第15章 |

### Step 4: Dual-Engine Synthesis (皇极二元 + 尚氏互体正象)
For **each** user question, apply the retrieved rules directly to the calculated board:
1. **测事成败 vs 测人吉凶**：
   - 成败类（求财、投资、工作、考试、买卖）→ 主用神为主纲，第二元为辅助；投资必查“财有无去处”（兄鬼动否）。
   - 吉凶生死类（意外、病体、孕产安危、刑事诉讼）→ 必须严格用**皇极二元定位（主用神 + 兼象爻）**，双元同伤方断实质灾祸。
   - **特殊铁律**：用神克世若真破（月破+化回头克无生）反主毫无厌恶分手之心而应查对方病灾；孕产须“子孙 + 胎爻”双备，有子无胎为抱养；出走失踪反喜用神休囚受克；被盗以“兄为贼、官为官方、子孙为公安”。
2. **尚秉和正象互体取象**：
   - 结合**本卦上下体 + 内互(2-4爻) + 外互(3-5爻) + 变卦 + 倒体**的八卦物象，将生克结论还原为具体的画面、物品细节、隐情与事情演变过程。
3. **古法补充（不抢主纲）**：参酌《断易天机》天玄赋六纲（无鬼无气、绝处逢生、合处逢冲、随官入墓、逢冲暗动、助鬼伤身）与《期日章》应期定则。

### Step 5: Compose Structured, Board-Grounded Output
Present the final analysis strictly in the structured Markdown format below, weaving the rules seamlessly into the specific hexagram board and answering **every** question cleanly:

1. **一、卦盘全息建构与象数立极**：列明四直干支、旬空月破、本卦/变卦及自动算出的**动爻**（或静卦）、全盘纳甲伏神表、卦身/世身/胎爻、尚氏互体卦与倒体卦。
2. **二、分类查章立极与逐问深度精断**：
   - 按 `问题一`、`问题二`……逐节独立展开，严禁混为一谈。每问包含：
     - **典籍章节依据**：真实引述查到的章节名（如《点窍》第X章第Y节，书无专条则直说“未设专条，依通则断”，严禁杜撰）。
     - **皇极二元推演**：用神与兼象的旺衰动变逻辑。
     - **尚氏正象互体透视**：本/互/变卦象还原真实隐情、人物心思、行业/病灶/物品细节。
     - **结论与应期**：斩钉截铁的断语及干支应期。
   - 若触发“占此应彼”隐患，单列 **【附】隐性灾祸预警**。
3. **三、综合研判与趋吉避凶策应指南**：串联多问在盘面上的共同根源，并给出可落地的风控与趋避行动建议。

---

## Corpus References
All full-text and essence references reside in `./references/`:
- [六爻秘法点窍.md](./references/六爻秘法点窍.md)
- [六爻病灾秘法.md](./references/六爻病灾秘法.md)
- [六爻婚孕秘法（简体版）.md](./references/六爻婚孕秘法（简体版）.md)
- [周易古筮考通解.md](./references/周易古筮考通解.md)
- [《断易天机》分类占断技法与白话精粹.md](./references/《断易天机》分类占断技法与白话精粹.md)
- [《周易尚占》分类占断技法与白话精粹.md](./references/《周易尚占》分类占断技法与白话精粹.md)
- [《易林补遗》分类占断技法与白话精粹.md](./references/《易林补遗》分类占断技法与白话精粹.md)
