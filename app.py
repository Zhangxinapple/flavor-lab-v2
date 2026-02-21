import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json, os, random, math, re
from math import sqrt

# ── 后台配置（API Key 存于 config.py，不出现在前端）──
try:
    import config as _cfg
    _BACKEND_KEY   = _cfg.GEMINI_API_KEY
    _GEMINI_MODEL  = _cfg.GEMINI_MODEL
except Exception:
    _BACKEND_KEY  = ""
    _GEMINI_MODEL = "gemini-2.0-flash"

# ================================================================
# 0. 页面配置
# ================================================================
st.set_page_config(
    page_title="味觉虫洞 Flavor Lab",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================================================
# 1. 全局样式 — 深色/浅色双主题自适应
#    使用 CSS 变量 + prefers-color-scheme，彻底解决夜间模式字体消失
# ================================================================
st.markdown("""
<style>
/* ── CSS 变量：浅色主题默认值 ── */
:root {
  --bg-main:       #F4F6FA;
  --bg-sidebar:    #FAFBFC;
  --bg-card:       #FFFFFF;
  --bg-card-hover: #F8F9FB;
  --border-color:  #E8EAED;
  --text-primary:  #111827;
  --text-second:   #374151;
  --text-muted:    #6B7280;
  --text-faint:    #9CA3AF;
  --shadow:        0 2px 12px rgba(0,0,0,0.07);
}

/* ── 深色主题覆盖 ── */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-main:       #0F1117;
    --bg-sidebar:    #1A1D27;
    --bg-card:       #1E2130;
    --bg-card-hover: #252840;
    --border-color:  #2D3148;
    --text-primary:  #F0F2F8;
    --text-second:   #C5CBD8;
    --text-muted:    #8B93A8;
    --text-faint:    #5A6178;
    --shadow:        0 2px 12px rgba(0,0,0,0.3);
  }
}

/* Streamlit 深色模式也触发 */
[data-theme="dark"] {
  --bg-main:       #0F1117;
  --bg-sidebar:    #1A1D27;
  --bg-card:       #1E2130;
  --bg-card-hover: #252840;
  --border-color:  #2D3148;
  --text-primary:  #F0F2F8;
  --text-second:   #C5CBD8;
  --text-muted:    #8B93A8;
  --text-faint:    #5A6178;
  --shadow:        0 2px 12px rgba(0,0,0,0.3);
}

/* ── 基础布局 ── */
.stApp { background: var(--bg-main) !important; }
[data-testid="stSidebar"] {
  background: var(--bg-sidebar) !important;
  border-right: 1px solid var(--border-color) !important;
}

/* ── Hero 顶栏（固定深色渐变，无论主题） ── */
.hero-header {
  background: linear-gradient(135deg,#0A0A1A 0%,#1A1A3E 50%,#0D2137 100%);
  padding: 24px 32px;
  border-radius: 18px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.hero-title {
  font-size: 1.85rem;
  font-weight: 800;
  background: linear-gradient(90deg,#00D2FF,#7B2FF7,#FF6B6B);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0; line-height: 1.2;
}
.hero-sub {
  font-size: .75rem;
  color: rgba(255,255,255,.42) !important;
  margin: 0;
  letter-spacing: .08em;
  text-transform: uppercase;
}

/* ── 白色卡片（主题自适应） ── */
.card {
  background: var(--bg-card);
  padding: 20px;
  border-radius: 16px;
  box-shadow: var(--shadow);
  margin-bottom: 16px;
  border: 1px solid var(--border-color);
}
.card h4, .card b, .card strong { color: var(--text-primary) !important; }
.card p, .card span, .card div  { color: var(--text-second)  !important; }

/* ── 深色评分卡（固定深色） ── */
.card-dark {
  background: linear-gradient(135deg,#0A0A1A,#1A1A3E);
  padding: 22px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,.3);
  margin-bottom: 16px;
  border: 1px solid rgba(255,255,255,.08);
  text-align: center;
}
.card-dark, .card-dark * { color: #FFFFFF !important; }

/* ── 欢迎卡片 ── */
.welcome-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 40px 48px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
}
.welcome-card h2 { color: var(--text-primary) !important; }
.welcome-card p, .welcome-card li { color: var(--text-second) !important; }
.step-card {
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px 20px;
  flex: 1;
  min-width: 200px;
}
.step-card h4 { color: var(--text-primary) !important; margin:6px 0 4px; }
.step-card p  { color: var(--text-muted)   !important; font-size:.85rem; margin:0; }

/* ── 评分数字 ── */
.score-big {
  font-size: 4.5rem;
  font-weight: 900;
  line-height: 1;
  display: block;
}

/* ── 风味标签 ── */
.tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: .76rem;
  font-weight: 600;
  margin: 2px 2px;
}
.tag-blue   { background:#EEF6FF; color:#1D6FDB !important; border:1px solid #BDD7F5; }
.tag-green  { background:#F0FDF4; color:#16A34A !important; border:1px solid #BBF7D0; }
.tag-orange { background:#FFF7ED; color:#C2410C !important; border:1px solid #FECBA1; }
.tag-purple { background:#F5F3FF; color:#7C3AED !important; border:1px solid #DDD6FE; }
.tag-pink   { background:#FDF2F8; color:#BE185D !important; border:1px solid #FBCFE8; }
.tag-shared { background:linear-gradient(90deg,#E0F7FA,#EDE7F6); color:#5B21B6 !important; border:1px solid #C4B5FD; font-weight:700; }

/* ── 徽章 ── */
.badge { display:inline-block; padding:4px 14px; border-radius:20px; font-size:.82rem; font-weight:700; }
.badge-resonance { background:#D1FAE5; color:#065F46 !important; }
.badge-contrast  { background:#FEE2E2; color:#991B1B !important; }
.badge-neutral   { background:var(--bg-card-hover); color:var(--text-second) !important; border:1px solid var(--border-color); }

/* ── 诊断区块 ── */
.diag { border-radius:12px; padding:14px 16px; margin:8px 0; border-left:4px solid; }
.diag-res  { background:#F0FDF4; border-color:#22C55E; }
.diag-ctr  { background:#FFF7ED; border-color:#F97316; }
.diag-info { background:#EEF6FF; border-color:#3B82F6; }
.diag b, .diag strong { color:var(--text-primary) !important; }
.diag span { color:var(--text-second) !important; }

/* ── Tooltip（工艺术语悬停说明） ── */
.technique-wrap {
  position: relative;
  display: inline-block;
  cursor: help;
}
.technique-term {
  color: #7B2FF7 !important;
  font-weight: 700;
  border-bottom: 2px dotted #7B2FF7;
  text-decoration: none;
}
.technique-tooltip {
  visibility: hidden;
  opacity: 0;
  background: #1A1A3E;
  color: #F0F2F8 !important;
  text-align: left;
  border-radius: 10px;
  padding: 12px 14px;
  position: absolute;
  z-index: 9999;
  bottom: 130%;
  left: 50%;
  transform: translateX(-50%);
  width: 260px;
  font-size: .8rem;
  line-height: 1.5;
  box-shadow: 0 8px 24px rgba(0,0,0,.35);
  border: 1px solid rgba(255,255,255,.12);
  transition: opacity .2s, visibility .2s;
  pointer-events: none;
}
.technique-tooltip::after {
  content: "";
  position: absolute;
  top: 100%; left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: #1A1A3E;
}
.technique-wrap:hover .technique-tooltip {
  visibility: visible;
  opacity: 1;
}

/* ── 进度条 ── */
.pbar-bg   { background:var(--border-color); border-radius:6px; height:7px; overflow:hidden; margin:3px 0; }
.pbar-fill { height:100%; border-radius:6px; }

/* ── 食材行 ── */
.ing-row {
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 10px 14px;
  margin: 5px 0;
}
.ing-row * { color: var(--text-primary) !important; }
.ing-row .muted { color: var(--text-muted) !important; }

/* ── Gemini 对话区 ── */
.chat-bubble-user {
  background: linear-gradient(135deg,#7B2FF7,#00D2FF);
  color: #fff !important;
  padding: 10px 16px;
  border-radius: 16px 16px 4px 16px;
  margin: 6px 0;
  display: inline-block;
  max-width: 85%;
  float: right;
  clear: both;
}
.chat-bubble-ai {
  background: var(--bg-card-hover);
  color: var(--text-primary) !important;
  border: 1px solid var(--border-color);
  padding: 10px 16px;
  border-radius: 16px 16px 16px 4px;
  margin: 6px 0;
  display: inline-block;
  max-width: 85%;
  float: left;
  clear: both;
}
.chat-clearfix { clear:both; }
.chat-wrap { max-height:420px; overflow-y:auto; padding:8px 0; }


/* ── 诊断区块深色模式覆盖 ── */
@media (prefers-color-scheme: dark) {
  .diag-res  { background:#0D2818; border-color:#22C55E; }
  .diag-ctr  { background:#2D1800; border-color:#F97316; }
  .diag-info { background:#0D1D3A; border-color:#3B82F6; }
  .welcome-card { background:var(--bg-card) !important; }
  .step-card { background:var(--bg-card-hover) !important; }
}
[data-theme="dark"] .diag-res  { background:#0D2818; border-color:#22C55E; }
[data-theme="dark"] .diag-ctr  { background:#2D1800; border-color:#F97316; }
[data-theme="dark"] .diag-info { background:#0D1D3A; border-color:#3B82F6; }
[data-theme="dark"] .welcome-card { background:var(--bg-card) !important; }

/* ── section 标题 ── */
.sec-label {
  font-size: .72rem;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--text-faint) !important;
  margin: 14px 0 6px;
}

/* ── 隐藏 streamlit 默认元素 ── */
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.2rem !important; }
</style>
""", unsafe_allow_html=True)


# ================================================================
# 2. 本地化引擎
# ================================================================
@st.cache_resource
def load_localization():
    if os.path.exists("localization_zh.json"):
        with open("localization_zh.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {"ingredients": {}, "flavor_notes": {}, "categories": {}}

LOC = load_localization()

def t_ingredient(name):
    m = LOC.get("ingredients", {})
    return m.get(name) or m.get(name.strip()) or name

def t_category(cat):
    return LOC.get("categories", {}).get(cat, cat)

def t_note(note):
    m = LOC.get("flavor_notes", {})
    n = note.strip().lower()
    return m.get(n) or m.get(note.strip()) or note.strip()

def t_notes_list(mol_input, top_n=999):
    if isinstance(mol_input, set):
        raw = sorted(mol_input)
    else:
        raw = [n.strip().lower() for n in re.split(r"[@,]+", str(mol_input)) if n.strip()]
    seen, result = set(), []
    for item in (t_note(n) for n in raw):
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result[:top_n]

def display_name(name):
    cn = t_ingredient(name)
    return f"{cn}（{name}）" if cn != name else cn


# ================================================================
# 3. 数据加载（同时解析 flavor_profiles 和 flavors 两列）
# ================================================================
def _parse_fp(s):
    if not s or str(s).strip() in ("", "nan"): return set()
    return set(t.strip().lower() for t in str(s).split(",") if t.strip())

def _parse_fl(s):
    if not s or str(s).strip() in ("", "nan"): return set()
    return set(t.strip().lower() for t in re.split(r"[@,]+", str(s)) if t.strip())

@st.cache_data
def load_data():
    path = "flavordb_data.csv"
    if not os.path.exists(path): return None
    df = pd.read_csv(path)
    df["flavor_profiles"] = df["flavor_profiles"].fillna("")
    df["mol_set"] = df.apply(
        lambda r: _parse_fp(r["flavor_profiles"]) | _parse_fl(r.get("flavors", "")), axis=1)
    df["mol_count"] = df["mol_set"].apply(len)
    return df[df["mol_count"] > 0].copy()


# ================================================================
# 4. 算法引擎
# ================================================================
POLARITY = {
    "fat":"L","fatty":"L","oil":"L","oily":"L","waxy":"L","buttery":"L",
    "butter":"L","cream":"L","creamy":"L","lard":"L","tallow":"L",
    "resin":"L","woody":"L","leather":"L","smoky":"L","smoke":"L",
    "sweet":"H","sour":"H","acid":"H","citrus":"H","fruity":"H",
    "floral":"H","honey":"H","alcoholic":"H","wine":"H","vinegar":"H",
    "fresh":"H","green":"H","sugar":"H",
}

def calc_sim(a, b):
    inter = a & b
    union = a | b
    j = len(inter) / len(union) if union else 0
    w = min(1.0, (len(inter) / max(len(a), len(b), 1)) * 1.5)
    score = int(min(97, max(50, j * 250 + w * 120)))
    typ = "resonance" if j >= 0.35 else ("contrast" if j < 0.12 else "neutral")
    return {"score": score, "jaccard": j, "shared": sorted(inter),
            "only_a": sorted(a - b), "only_b": sorted(b - a), "type": typ}

def polarity_analysis(mol_set):
    lipo  = sum(1 for m in mol_set if POLARITY.get(m) == "L")
    hydro = sum(1 for m in mol_set if POLARITY.get(m) == "H")
    total = lipo + hydro
    if total == 0: return {"type": "balanced", "lipo": 0, "hydro": 0, "total": 0}
    t = "lipophilic" if lipo > hydro else ("hydrophilic" if hydro > lipo else "balanced")
    return {"type": t, "lipo": lipo, "hydro": hydro, "total": total}

def find_bridges(df, set_a, set_b, selected, top_n=4):
    """计算桥接分，归一化到 0-100 范围内"""
    results = []
    for _, row in df.iterrows():
        if row["name"] in selected: continue
        s = row["mol_set"]
        sa = len(s & set_a) / max(len(set_a), 1)
        sb = len(s & set_b) / max(len(set_b), 1)
        raw_score = sqrt(sa * sb) * (1 + min(sa, sb))
        if raw_score > 0.04:
            results.append((row["name"], raw_score, sa, sb))
    results.sort(key=lambda x: -x[1])
    top = results[:top_n]
    # 归一化：最高分映射为 100，其他按比例
    if not top: return []
    max_score = top[0][1]
    return [(name, score/max_score, sa, sb) for name, score, sa, sb in top]

RADAR_DIMS = {
    "甜味":    ["sweet","caramel","honey","vanilla","sugar","butterscotch","candy","cotton candy"],
    "烘焙":    ["roasted","baked","toasted","caramel","coffee","cocoa","bread","malt","popcorn"],
    "果香":    ["fruity","berry","apple","pear","peach","citrus","tropical","grape","banana","strawberry"],
    "草本":    ["herbaceous","herbal","green","mint","thyme","rosemary","basil","dill","leafy"],
    "木质烟熏":["woody","wood","smoky","smoke","cedar","oak","leather","tobacco","resin"],
    "辛辣":    ["spicy","pepper","cinnamon","ginger","clove","mustard","pungent","horseradish"],
    "花香":    ["floral","rose","jasmine","lavender","violet","lily","blossom","jasmin"],
    "脂奶":    ["fatty","creamy","buttery","butter","cream","dairy","milky","nutty"],
}

def radar_vals(mol_set):
    result = {}
    for dim, kws in RADAR_DIMS.items():
        hit = sum(1 for k in kws if k in mol_set)
        result[dim] = min(10, hit * 2.0 + (0.8 if hit > 0 else 0))
    return result


# ================================================================
# 5. 工艺术语 Tooltip 数据库
# ================================================================
TECHNIQUES = {
    "低温慢煮": {
        "en": "Sous Vide",
        "desc": "将食材密封后放入恒温水浴（通常 55-85°C）长时间烹饪。优点：精确控温，最大程度锁住水分和芳香分子，避免高温氧化破坏挥发性香气。",
    },
    "乳化": {
        "en": "Emulsification",
        "desc": "将两种不相溶的液体（如油和水）通过乳化剂（蛋黄、芥末等）稳定结合。可将脂溶性和水溶性风味分子同时呈现，是酱汁的核心技术。",
    },
    "真空萃取": {
        "en": "Vacuum Extraction",
        "desc": "利用负压降低液体沸点，在低温下完成萃取。保留热敏感香气，萃取效率比常压高 3-5 倍，常用于高端风味提取。",
    },
    "发酵": {
        "en": "Fermentation",
        "desc": "微生物（酵母、细菌）分解糖类产生醇类、酸类和酯类，创造全新的复合风味。发酵是最古老也最复杂的风味转化手段之一。",
    },
    "烟熏": {
        "en": "Smoking",
        "desc": "木材不完全燃烧产生的烟雾（含酚类、木质素降解物）渗入食材表面，形成独特的焦木香气，同时具有防腐作用。",
    },
    "冷冻干燥": {
        "en": "Freeze Drying / Lyophilization",
        "desc": "在超低温（-40°C以下）下将水分直接从固态升华为气态，无需经过液态。能保留 95% 以上的芳香分子和营养成分，是最温和的干燥方式。",
    },
    "Reduction": {
        "en": "Reduction / 浓缩收汁",
        "desc": "通过持续加热蒸发水分，将液体浓缩，使风味分子浓度大幅提升。常用于酱汁和高汤，可将基础风味放大 3-10 倍。",
    },
    "Gel": {
        "en": "Gelification / 凝胶化",
        "desc": "使用明胶、琼脂或结冷胶等将液体凝固成半固态，使风味在口腔中缓慢释放，延长味觉持续时间，也用于创造质地对比。",
    },
    "Espuma": {
        "en": "Espuma / 泡沫技术",
        "desc": "西班牙分子料理技术，使用奶油枪将液体充入氮气形成轻盈泡沫。泡沫能将复杂风味以轻盈的质地呈现，增强嗅觉感知。",
    },
    "Confit": {
        "en": "Confit / 油封",
        "desc": "将食材浸没在油脂中以低温（70-90°C）长时间加热。脂溶性芳香分子充分融入油脂，使食材极度嫩滑且风味浓郁，是法式经典技术。",
    },
    "Consommé": {
        "en": "Consommé / 澄清汤",
        "desc": "使用蛋白质澄清技术去除肉汤中的杂质，得到透明清澈的浓缩高汤。只保留水溶性风味分子，代表风味的极致纯粹。",
    },
    "乳化酱汁": {
        "en": "Emulsion Sauce",
        "desc": "通过乳化作用将油脂分散在水相中（如蛋黄酱）或水分散在油相中（如黄油酱汁 Beurre Blanc）。同时呈现脂溶和水溶风味的双重层次。",
    },
    "甘纳许": {
        "en": "Ganache",
        "desc": "巧克力与奶油的乳化物，比例通常为 2:1 到 1:1。通过乳化使脂溶性可可芳香与水溶性奶香完美融合，是巧克力工艺的核心配方。",
    },
}

def make_tooltip(term: str) -> str:
    """生成带 tooltip 的术语 HTML"""
    info = TECHNIQUES.get(term)
    if not info:
        return f"<b>{term}</b>"
    en = info["en"]
    desc = info["desc"]
    return f"""<span class="technique-wrap">
      <span class="technique-term">{term}</span>
      <span class="technique-tooltip">
        <b style="color:#00D2FF">{term} · {en}</b><br><br>{desc}
      </span>
    </span>"""


# ================================================================
# 6. HTML 辅助
# ================================================================
TAG_CLASSES = ["tag-blue","tag-green","tag-orange","tag-purple","tag-pink"]

def score_color(s):
    return "#22C55E" if s >= 80 else ("#3B82F6" if s >= 65 else ("#F97316" if s >= 50 else "#EF4444"))

def tags_html(notes, cls="tag-blue", max_n=8):
    return " ".join(f'<span class="tag {cls}">{n}</span>' for n in notes[:max_n])

def shared_tags_html(notes, max_n=10):
    return " ".join(f'<span class="tag tag-shared">⚡ {t_note(n)}</span>' for n in notes[:max_n])

def tech_tip(term):
    """便捷函数：返回带 tooltip 的术语"""
    return make_tooltip(term)


# ================================================================
# 7. Gemini API 对话
# ================================================================
def call_gemini(api_key: str, messages: list, context: str) -> str:
    """调用 Gemini API，直接接收 api_key 参数，避免 session_state 时序问题"""
    import urllib.request, urllib.error
    if not api_key or not api_key.strip():
        return "❌ <b>未配置 API Key</b>，请在左侧栏输入 Gemini API Key。"
    key = api_key.strip()
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           + _GEMINI_MODEL + ":generateContent?key=" + key)

    system_prompt = (
        "你是「风味虫洞」的专属 AI 风味顾问，拥有分子烹饪、风味化学和米其林餐厅经验。\n\n"
        "【当前搭配数据】\n" + context + "\n\n"
        "【你的任务】\n"
        "1. 基于上方分子数据帮助用户深入理解食材搭配的科学原理\n"
        "2. 当用户描述数据库里没有的食材时，用知识库估计其风味分子特征来作答\n"
        "3. 主动引导用户思考：主食材选择理由、比例调整效果、实际烹饪落地方案\n"
        "4. 可引用具体风味分子名（如：己醛、芳樟醇）、化学原理或经典菜式案例\n"
        "5. 遇到数据库没有的食材，明确告知并基于知识库分析\n\n"
        "【回答风格】\n"
        "- 专业但亲切的中文，像有深度的厨师朋友在交流\n"
        "- 多用比喻和具体例子\n"
        "- 每次回答结尾提出一个延伸问题引导用户继续探索"
    )

    contents = [
        {"role": "user",  "parts": [{"text": system_prompt + "\n\n请确认你已了解搭配数据，用一句话介绍核心特点，然后提出2个最值得探索的问题。"}]},
        {"role": "model", "parts": [{"text": "已了解！我是你的风味虫洞顾问，随时准备深度探讨。"}]}
    ]
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    body_dict = {
        "contents": contents,
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 1024}
    }
    payload = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = ""
        if e.code == 429:
            return "⚠️ <b>请求频率超限（429）</b><br>稍等 30 秒后再试，或检查 API 配额是否耗尽。"
        elif e.code == 400:
            return "❌ <b>请求格式错误（400）</b><br>详情：" + err_body[:300]
        elif e.code in (401, 403):
            return "❌ <b>API Key 无效或无权限（" + str(e.code) + "）</b><br>请确认 Key 正确且 Gemini API 已启用。"
        elif e.code in (500, 503):
            return "⚠️ <b>Gemini 服务暂时不可用</b>，请稍后重试。"
        else:
            return "⚠️ HTTP 错误 " + str(e.code) + "：" + err_body[:300]
    except Exception as ex:
        err_msg = str(ex)
        if "timed out" in err_msg.lower() or "timeout" in err_msg.lower():
            return "⚠️ <b>请求超时</b>，请稍后重试。"
        return "⚠️ 网络异常：" + err_msg


# 8. 欢迎页
# ================================================================
def render_welcome():
    st.markdown("""
    <div class="welcome-card">
      <div style="text-align:center;margin-bottom:28px">
        <div style="font-size:3.5rem;margin-bottom:8px">🧬</div>
        <h2 style="margin:0;font-size:1.7rem">味觉虫洞 · Flavor Lab</h2>
        <p style="margin:8px 0 0;font-size:1rem;color:var(--text-muted)">
          基于 FlavorDB 分子数据库的专业食材搭配引擎
        </p>
      </div>

      <p style="font-size:.95rem;line-height:1.8;margin-bottom:24px">
        <b>味觉虫洞</b>通过分析食材中的挥发性芳香分子，科学揭示哪些食材在分子层面"天生一对"，
        帮助厨师、食品研发者和美食爱好者发现意想不到的绝妙搭配。
        数据库涵盖 <b>551 种食材</b>、<b>464 个风味维度</b>。
      </p>

      <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:28px">
        <div class="step-card">
          <div style="font-size:1.6rem">①</div>
          <h4>选择食材</h4>
          <p>在左侧栏选择 2-4 种想要研究的食材，可按分类筛选或直接搜索</p>
        </div>
        <div class="step-card">
          <div style="font-size:1.6rem">②</div>
          <h4>调整比例</h4>
          <p>通过滑块设定各食材在配方中的比例，雷达图实时反映比例变化</p>
        </div>
        <div class="step-card">
          <div style="font-size:1.6rem">③</div>
          <h4>查看分析</h4>
          <p>获得分子共鸣指数、风味指纹、介质推演和主厨工艺建议</p>
        </div>
        <div class="step-card">
          <div style="font-size:1.6rem">④</div>
          <h4>AI 深度对话</h4>
          <p>输入 Gemini API Key，与 AI 顾问就当前搭配进行专业深度探讨</p>
        </div>
      </div>

      <div style="background:var(--bg-card-hover);border-radius:12px;padding:16px 20px;border:1px solid var(--border-color)">
        <b style="color:#7B2FF7">💡 使用提示</b>
        <ul style="margin:8px 0 0;padding-left:20px;font-size:.88rem;line-height:1.9">
          <li>工艺术语（如<b>低温慢煮</b>）上方悬停鼠标可查看详细解说</li>
          <li>风味桥接推荐：系统自动寻找能串联两种食材的"第三食材"</li>
          <li>分子连线网络图直观展示食材通过哪些香气节点相连</li>
          <li>分类筛选支持多选，Vegan 模式自动过滤动物性食材</li>
        </ul>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ================================================================
# 9. 主界面
# ================================================================
def main():
    df = load_data()
    if df is None:
        st.error("❌ 找不到 flavordb_data.csv，请放到与 app.py 相同目录。")
        st.stop()

    # ── Hero ──
    st.markdown("""
    <div class="hero-header">
      <span style="font-size:2.2rem">🧬</span>
      <div>
        <p class="hero-title">味觉虫洞 · Flavor Lab</p>
        <p class="hero-sub">Professional Flavor Pairing Engine &nbsp;·&nbsp; V2.0</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 侧边栏 ──
    with st.sidebar:
        st.markdown("### 🔬 实验参数")

        # 分类筛选
        all_cats = sorted(df["category"].unique().tolist())
        cat_display = {f"{t_category(c)}（{c}）": c for c in all_cats}
        st.markdown('<div class="sec-label">🗂 按分类筛选（不选 = 全部）</div>', unsafe_allow_html=True)
        selected_cat_labels = st.multiselect(
            label="分类", options=list(cat_display.keys()),
            default=[], label_visibility="collapsed", key="cat_filter")
        if selected_cat_labels:
            df_show = df[df["category"].isin([cat_display[l] for l in selected_cat_labels])]
        else:
            df_show = df

        is_vegan = st.toggle("🍃 仅植物基 Vegan", value=False)
        if is_vegan:
            excl = ["meat","dairy","fish","seafood","pork","beef","chicken","egg"]
            df_show = df_show[~df_show["category"].str.lower().apply(
                lambda c: any(kw in c for kw in excl))]

        total_n = len(df_show)
        st.markdown(f'<div class="sec-label">已解锁 {total_n} 种食材</div>', unsafe_allow_html=True)
        options = sorted(df_show["name"].unique().tolist())
        defaults = [n for n in ["Coffee","Strawberry"] if n in options] or options[:2]

        selected = st.multiselect(
            label="选择食材（2-4种）", options=options,
            default=defaults, format_func=display_name,
            help="最多支持4种食材同时分析", key="ing_select")

        # 比例滑块
        ratios = {}
        if len(selected) >= 2:
            st.markdown('<div class="sec-label">⚖️ 配方比例</div>', unsafe_allow_html=True)
            raw_total = 0
            for name in selected:
                ratios[name] = st.slider(t_ingredient(name), 0, 100,
                                          100//len(selected), 5, key=f"r_{name}")
                raw_total += ratios[name]
            if raw_total > 0:
                ratios = {k: v/raw_total for k, v in ratios.items()}

        st.divider()

        # ── AI 顾问：config.py 后台 Key + 侧边栏可覆盖 ──
        st.markdown("### 🤖 AI 风味顾问")
        manual_key = st.text_input(
            "Gemini API Key", type="password",
            placeholder="留空则使用后台内置 Key",
            help="粘贴新 Key 可立即覆盖内置配置",
            key="manual_gemini_key")
        # 优先用手动输入，否则用后台配置
        active_key = manual_key.strip() if manual_key.strip() else _BACKEND_KEY
        if active_key:
            label = "（自定义）" if manual_key.strip() else "（内置）"
            st.success(f"✅ AI 顾问就绪 {label}", icon="🔑")
        else:
            st.warning("⚠️ 未配置 API Key")
            st.caption("[获取免费 Gemini Key →](https://aistudio.google.com/app/apikey)")

        st.divider()
        st.caption("数据来源：FlavorDB · 551 种食材 · 464 个风味维度")

    # ── 未选择食材：显示欢迎页 ──
    if len(selected) < 2:
        render_welcome()
        return

    rows = {n: df[df["name"] == n].iloc[0] for n in selected}
    mol_sets = {n: rows[n]["mol_set"] for n in selected}
    n1, n2 = selected[0], selected[1]
    sim = calc_sim(mol_sets[n1], mol_sets[n2])
    cn1, cn2 = t_ingredient(n1), t_ingredient(n2)

    # 为 Gemini 构建上下文
    def build_context():
        lines = [f"正在分析食材搭配：{' + '.join(t_ingredient(n) for n in selected)}"]
        lines.append(f"分子共鸣指数：{sim['score']}%（类型：{'同源共振' if sim['type']=='resonance' else '对比碰撞' if sim['type']=='contrast' else '平衡搭档'}）")
        lines.append(f"共享风味分子数：{len(sim['shared'])} 个（Jaccard相似度 {int(sim['jaccard']*100)}%）")
        for n in selected:
            pct = int(ratios.get(n, 1/len(selected))*100)
            top5 = t_notes_list(rows[n]["mol_set"], 5)
            lines.append(f"• {t_ingredient(n)}（{pct}%）：主要风味 - {', '.join(top5)}")
        if sim["shared"]:
            shared_cn = [t_note(x) for x in sim["shared"][:8]]
            lines.append(f"共享节点：{', '.join(shared_cn)}")
        return "\n".join(lines)

    col_left, col_right = st.columns([1.35, 1], gap="large")

    # ===== 左栏 =====
    with col_left:
        # 雷达图
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"<h4>🔭 风味维度雷达图</h4>", unsafe_allow_html=True)
        palette = [("#00D2FF","rgba(0,210,255,0.15)"),("#7B2FF7","rgba(123,47,247,0.15)"),
                   ("#FF6B6B","rgba(255,107,107,0.15)"),("#00E676","rgba(0,230,118,0.15)")]
        fig_radar = go.Figure()
        dims = list(RADAR_DIMS.keys())
        for i, name in enumerate(selected[:4]):
            rv = radar_vals(mol_sets[name])
            vals = [rv[d] for d in dims]
            scale = 0.5 + ratios.get(name, 1/len(selected)) * 0.5 * len(selected)
            vals_s = [min(10, v*scale) for v in vals] + [min(10, vals[0]*scale)]
            lc, fc = palette[i]
            pct = int(ratios.get(name, 1/len(selected))*100)
            fig_radar.add_trace(go.Scatterpolar(
                r=vals_s, theta=dims+[dims[0]],
                fill="toself", fillcolor=fc,
                line=dict(color=lc, width=2.5),
                name=f"{t_ingredient(name)} ({pct}%)"))
        fig_radar.update_layout(
            polar=dict(bgcolor="rgba(248,249,255,0.4)",
                radialaxis=dict(visible=True,range=[0,10],tickfont=dict(size=9,color="#9CA3AF")),
                angularaxis=dict(tickfont=dict(size=12,color="#888888"))),
            showlegend=True,
            legend=dict(orientation="h",y=-0.15,font=dict(size=11,color="#888888")),
            height=420, margin=dict(t=20,b=70,l=40,r=40),
            paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_radar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 分子网络图
        if sim["shared"]:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h4>🕸 分子连线网络图</h4>", unsafe_allow_html=True)
            shared_top = sim["shared"][:14]
            nx_l,ny_l,ntxt,nclr,nsz,ex,ey = [],[],[],[],[],[],[]
            nx_l+= [-1.6,1.6]; ny_l+=[0,0]
            ntxt+=[cn1,cn2]; nclr+=["#00D2FF","#7B2FF7"]; nsz+=[30,30]
            for idx, note in enumerate(shared_top):
                angle = math.pi/2 + idx*2*math.pi/len(shared_top)
                px,py = 1.15*math.cos(angle), 1.15*math.sin(angle)
                nx_l.append(px); ny_l.append(py)
                ntxt.append(t_note(note)); nclr.append("#F97316"); nsz.append(13)
                for sx,sy in [(-1.6,0),(1.6,0)]:
                    ex+=[sx,px,None]; ey+=[sy,py,None]
            fig_net = go.Figure()
            fig_net.add_trace(go.Scatter(x=ex,y=ey,mode="lines",
                line=dict(color="rgba(150,150,200,0.22)",width=1.2),hoverinfo="none",showlegend=False))
            fig_net.add_trace(go.Scatter(x=nx_l,y=ny_l,mode="markers+text",
                text=ntxt,textposition="top center",textfont=dict(size=10,color="#888888"),
                marker=dict(color=nclr,size=nsz,line=dict(width=2,color="white"),opacity=0.92),
                hoverinfo="text",showlegend=False))
            fig_net.update_layout(height=300,margin=dict(t=10,b=10,l=10,r=10),
                xaxis=dict(visible=False),yaxis=dict(visible=False),
                paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(248,249,255,0.3)")
            st.plotly_chart(fig_net, use_container_width=True)
            st.caption(f"🔵 {cn1}  🟣 {cn2}  🟠 共享节点（共 {len(sim['shared'])} 个）")
            st.markdown("</div>", unsafe_allow_html=True)

    # ===== 右栏 =====
    with col_right:
        # 评分卡
        sc = sim["score"]
        sc_c = score_color(sc)
        type_info = {
            "resonance": ("同源共振","badge-resonance","共享大量芳香分子，协同延长风味余韵"),
            "contrast":  ("对比碰撞","badge-contrast",  "差异显著，形成张力对比切割"),
            "neutral":   ("平衡搭档","badge-neutral",   "适度交叠，互补平衡"),
        }
        tlabel,tbadge,tdesc = type_info[sim["type"]]
        r1 = int(ratios.get(n1,0.5)*100); r2 = int(ratios.get(n2,0.5)*100)
        st.markdown(f"""
        <div class="card-dark">
          <div style="color:rgba(255,255,255,.5);font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px">分子共鸣指数</div>
          <span class="score-big" style="color:{sc_c}">{sc}<span style="font-size:2rem;font-weight:400">%</span></span>
          <div style="margin:12px 0"><span class="badge {tbadge}">{tlabel}</span></div>
          <div style="color:rgba(255,255,255,.65);font-size:.82rem">{tdesc}</div>
          <div style="margin-top:12px;color:rgba(255,255,255,.4);font-size:.78rem">
            {cn1} {r1}% &nbsp;·&nbsp; {cn2} {r2}%
          </div>
        </div>""", unsafe_allow_html=True)

        # 风味指纹
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h4>🧪 风味指纹</h4>", unsafe_allow_html=True)
        for i, name in enumerate(selected):
            cn = t_ingredient(name)
            notes_cn = t_notes_list(rows[name]["mol_set"], top_n=10)
            pct = int(ratios.get(name, 1/len(selected))*100)
            cls = TAG_CLASSES[i % len(TAG_CLASSES)]
            dom = ""
            if pct >= 40:   dom = '<span style="background:#FEF3C7;color:#92400E;font-size:.69rem;padding:1px 7px;border-radius:8px;margin-left:6px;font-weight:700">主导</span>'
            elif pct <= 15: dom = '<span style="background:#E0F2FE;color:#0369A1;font-size:.69rem;padding:1px 7px;border-radius:8px;margin-left:6px;font-weight:700">提味</span>'
            st.markdown(f"""
            <div style="margin-bottom:12px">
              <div style="font-weight:700;color:var(--text-primary);margin-bottom:3px">
                {cn} <span style="color:var(--text-faint);font-weight:400;font-size:.78rem">{pct}%</span>{dom}
              </div>
              <div class="pbar-bg">
                <div class="pbar-fill" style="width:{pct}%;background:linear-gradient(90deg,#00D2FF,#7B2FF7)"></div>
              </div>
              <div style="margin-top:5px">{tags_html(notes_cn, cls, 8)}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 深度诊断
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h4>🔬 深度诊断</h4>", unsafe_allow_html=True)
        jpct = int(sim["jaccard"]*100)
        if sim["type"] == "resonance":
            st.markdown(f"""
            <div class="diag diag-res">
              <b>✅ 高度共振</b> — 共享风味分子比例 {jpct}%<br>
              <span>两者拥有大量相同的芳香分子，结合后将显著延长风味余韵，主副调高度协同。</span><br><br>
              <b>共享节点：</b><br>{shared_tags_html(sim['shared'][:10])}
            </div>""", unsafe_allow_html=True)
        elif sim["type"] == "contrast":
            a3 = " / ".join(t_notes_list(rows[n1]["mol_set"], 3))
            b3 = " / ".join(t_notes_list(rows[n2]["mol_set"], 3))
            st.markdown(f"""
            <div class="diag diag-ctr">
              <b>⚡ 对比碰撞</b> — 共享分子比例 {jpct}%<br>
              <span>经典「切割平衡」结构。{cn1} 以 <b>{a3}</b> 主导，{cn2} 以 <b>{b3}</b> 抗衡，差异创造层次感。</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="diag diag-info">
              <b>🔵 平衡搭档</b> — 共享分子比例 {jpct}%<br>
              <span>风味有交叠也有差异，形成良好互补，适合底味与提味组合。</span><br><br>
              <b>共享节点：</b><br>{shared_tags_html(sim['shared'][:8])}
            </div>""", unsafe_allow_html=True)

        oa = sim["only_a"][:6]; ob = sim["only_b"][:6]
        if oa or ob:
            ca2, cb2 = st.columns(2)
            with ca2:
                st.markdown(f"<div style='font-size:.82rem;font-weight:700;margin-bottom:4px;color:var(--text-primary)'>{cn1} 独有</div>", unsafe_allow_html=True)
                st.markdown(tags_html([t_note(n) for n in oa],"tag-blue"), unsafe_allow_html=True)
            with cb2:
                st.markdown(f"<div style='font-size:.82rem;font-weight:700;margin-bottom:4px;color:var(--text-primary)'>{cn2} 独有</div>", unsafe_allow_html=True)
                st.markdown(tags_html([t_note(n) for n in ob],"tag-purple"), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 介质推演
        pol = polarity_analysis(mol_sets[n1] | mol_sets[n2])
        if pol["total"] > 0:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h4>💧 介质推演</h4>", unsafe_allow_html=True)
            lp = int(pol["lipo"]/pol["total"]*100); hp = 100-lp
            if pol["type"] == "lipophilic":
                st.markdown(f"""<div class="diag diag-ctr">
                  <b>🫙 脂溶性主导</b> <span style="color:var(--text-muted)">（脂溶 {lp}% / 水溶 {hp}%）</span><br>
                  <span>推荐：{tech_tip('Confit')}、{tech_tip('甘纳许')}、慕斯基底、{tech_tip('乳化')}酱汁</span>
                </div>""", unsafe_allow_html=True)
            elif pol["type"] == "hydrophilic":
                st.markdown(f"""<div class="diag diag-info">
                  <b>🫗 水溶性主导</b> <span style="color:var(--text-muted)">（水溶 {hp}% / 脂溶 {lp}%）</span><br>
                  <span>推荐：{tech_tip('Consommé')}、澄清冻、冰沙、{tech_tip('真空萃取')}</span>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="diag diag-res">
                  <b>⚖️ 双亲性平衡</b> <span style="color:var(--text-muted)">（脂溶 {lp}% / 水溶 {hp}%）</span><br>
                  <span>推荐：{tech_tip('乳化酱汁')}、{tech_tip('Espuma')}、{tech_tip('真空萃取')}</span>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 主厨建议（含 tooltip）
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h4>👨‍🍳 主厨工艺建议</h4>", unsafe_allow_html=True)
        tips_pool = {
            "resonance": [
                f"以 <b>{cn1}</b> 为基底，将 <b>{cn2}</b> 浓缩（{tech_tip('Reduction')}）后叠加，在同一芳香维度形成「风味放大」效果。",
                f"两者共享的芳香分子建议通过 {tech_tip('低温慢煮')} 保留，避免高温氧化破坏共鸣节点。",
                f"考虑将 <b>{cn2}</b> 制成 {tech_tip('Gel')}，穿插在 <b>{cn1}</b> 的质地层间，延长风味余韵。",
            ],
            "contrast": [
                f"利用 <b>{cn2}</b> 的对比维度「切割」{cn1} 的厚重感，建议以提味剂形式在收尾阶段引入，而非作为前调。",
                f"对比型搭配分阶段引入：先以 <b>{cn1}</b> 建立底味，后期通过 {tech_tip('低温慢煮')} 的 <b>{cn2}</b> 制造味觉转折。",
                f"将 <b>{cn2}</b> 做成 {tech_tip('Espuma')}，轻盈地覆盖 <b>{cn1}</b> 的厚重质地，创造对比张力。",
            ],
            "neutral": [
                f"比例递进策略：从 <b>{cn1}</b> 的纯净基调出发，逐步引入 <b>{cn2}</b> 的差异维度，通过 {tech_tip('乳化')} 融合。",
                f"{tech_tip('真空萃取')} 让两者在分子层面充分融合，实现比例可控的风味协同。",
                f"将 <b>{cn1}</b> 作为主味质地，<b>{cn2}</b> 通过 {tech_tip('冷冻干燥')} 制成粉末，提供风味跳跃感。",
            ],
        }
        tip = random.choice(tips_pool[sim["type"]])
        procs = ["低温慢煮（Sous Vide）","乳化（Emulsification）","真空萃取","发酵","烟熏","冷冻干燥"]
        proc_key = random.choice(list(TECHNIQUES.keys()))
        proc_html = tech_tip(proc_key)

        st.markdown(f"""
        <div class="diag diag-info" style="margin-bottom:10px">
          💡 {tip}
        </div>
        <p style="color:var(--text-second)">🔧 <b>推荐工艺：</b>{proc_html}</p>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 第二行 ──
    st.markdown("---")
    cb, cc = st.columns([1,1], gap="large")

    with cb:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"<h4>🌉 风味桥接推荐</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:var(--text-muted);font-size:.82rem'>寻找能串联 <b>{cn1}</b> 与 <b>{cn2}</b> 的「第三食材」</p>", unsafe_allow_html=True)
        bridges = find_bridges(df, mol_sets[n1], mol_sets[n2], selected)
        if bridges:
            for bname, bsc, sa, sb in bridges:
                bcn = t_ingredient(bname)
                bcat_en = df[df["name"]==bname].iloc[0]["category"] if len(df[df["name"]==bname])>0 else ""
                bcat_zh = t_category(bcat_en)
                # bsc 已归一化到 0-1，×100 得到 0-100 的连接力
                ps = min(100, int(bsc*100)); pa = min(100, int(sa*100)); pb = min(100, int(sb*100))
                st.markdown(f"""
                <div class="ing-row">
                  <div style="font-weight:700;color:var(--text-primary)">{bcn}
                    <span class="muted" style="font-size:.75rem;font-weight:400"> {bname}</span>
                  </div>
                  <div class="muted" style="font-size:.74rem">{bcat_zh} · 连接力 {ps}%</div>
                  <div class="muted" style="font-size:.74rem">与{cn1} {pa}% | 与{cn2} {pb}%</div>
                  <div class="pbar-bg" style="margin-top:5px">
                    <div class="pbar-fill" style="width:{ps}%;background:linear-gradient(90deg,#F97316,#FBBF24)"></div>
                  </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("未找到合适的桥接食材")
        st.markdown("</div>", unsafe_allow_html=True)

    with cc:
        if len(selected) > 2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h4>📊 多食材相似度矩阵</h4>", unsafe_allow_html=True)
            names = selected[:4]
            mat = [[calc_sim(mol_sets[na],mol_sets[nb])["score"] if na!=nb else 100 for nb in names] for na in names]
            cn_names = [t_ingredient(n) for n in names]
            hm = go.Figure(go.Heatmap(
                z=mat, x=cn_names, y=cn_names,
                colorscale=[[0,"#FEE2E2"],[0.5,"#DBEAFE"],[1,"#D1FAE5"]],
                text=[[f"{v}%" for v in r] for r in mat],
                texttemplate="%{text}", showscale=False,
                hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>%{z}%<extra></extra>"))
            hm.update_layout(height=270,margin=dict(t=10,b=30,l=10,r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickfont=dict(size=11,color="#888888")),
                yaxis=dict(tickfont=dict(size=11,color="#888888")))
            st.plotly_chart(hm, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h4>📋 食材档案</h4>", unsafe_allow_html=True)
            for i, name in enumerate(selected[:2]):
                cn = t_ingredient(name)
                row = rows[name]
                n5 = t_notes_list(row["mol_set"], 5)
                cls = TAG_CLASSES[i % len(TAG_CLASSES)]
                st.markdown(f"""
                <div class="ing-row" style="margin-bottom:10px">
                  <div style="font-weight:700;font-size:.95rem">{cn}</div>
                  <div class="muted" style="font-size:.76rem;margin:2px 0">{t_category(row['category'])} · {row['mol_count']} 个风味分子</div>
                  <div style="margin-top:5px">{tags_html(n5, cls)}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ── Gemini 对话区 ──
    st.markdown("---")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<h4>🧬 风味虫洞顾问 <span style="font-size:.75rem;color:var(--text-muted);font-weight:400">· 基于 {cn1} × {cn2} 的分子分析数据</span></h4>', unsafe_allow_html=True)

    # 对话区：active_key 从侧边栏 widget 实时读取
    active_key = st.session_state.get("manual_gemini_key", "").strip() or _BACKEND_KEY
    if not active_key:
        st.markdown("""
        <div class="diag diag-info">
          <b>🔑 请在左侧栏输入 Gemini API Key</b><br>
          <span><a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#7B2FF7">
          → 免费获取（Google AI Studio）</a></span>
        </div>""", unsafe_allow_html=True)
    else:
        # 初始化对话历史
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "chat_context_key" not in st.session_state:
            st.session_state.chat_context_key = ""

        # 如果切换了食材，重置对话
        current_key = "+".join(sorted(selected))
        if st.session_state.chat_context_key != current_key:
            st.session_state.chat_history = []
            st.session_state.chat_context_key = current_key

        context_str = build_context()

        def md_to_html(text: str) -> str:
            """把 AI 回复的 Markdown 转成 HTML，支持加粗/链接/换行/有序无序列表"""
            import re as _re
            # 链接 [text](url)
            text = _re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                           r'<a href="\2" target="_blank" style="color:#7B2FF7">\1</a>', text)
            # 加粗 **text**
            text = _re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            # 无序列表行 "- item" 或 "· item"
            text = _re.sub(r'(?m)^[\-·]\s+(.+)$', r'<div style="padding:2px 0 2px 12px">• \1</div>', text)
            # 有序列表行 "1. item"
            text = _re.sub(r'(?m)^\d+\.\s+(.+)$', r'<div style="padding:2px 0 2px 12px">\1</div>', text)
            # 换行
            text = text.replace("\n", "<br>")
            return text

        # 渲染历史消息
        if st.session_state.chat_history:
            chat_html = '<div class="chat-wrap">'
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    chat_html += f'<div class="chat-bubble-user">{msg["content"]}</div><div class="chat-clearfix"></div>'
                else:
                    content = md_to_html(msg["content"])
                    chat_html += f'<div class="chat-bubble-ai">{content}</div><div class="chat-clearfix"></div>'
            chat_html += "</div>"
            st.markdown(chat_html, unsafe_allow_html=True)
        else:
            # 动态生成引导卡，基于当前搭配类型给出针对性引导
            type_hints = {
                "resonance": f"它们共享大量相同的芳香分子，属于「同源共振」型搭配，适合用叠加增强来放大共鸣。",
                "contrast":  f"它们风味差异显著，属于「对比碰撞」型搭配，高明的厨师会用这种张力创造层次感。",
                "neutral":   f"它们适度交叠互补，属于「平衡搭档」型搭配，比例调整是提升这个组合的关键。",
            }
            hint_text = type_hints.get(sim["type"], "")
            st.markdown(f"""
            <div class="diag diag-res" style="margin-bottom:12px">
              <b style="font-size:1rem">🧬 关于 {cn1} × {cn2} 这个搭配</b><br><br>
              <span>{hint_text}</span><br><br>
              <span style="color:var(--text-muted);font-size:.85rem">
                💬 <b>你可以问我：</b><br>
                · 为什么选 {cn1} 作为主食材，而不是其他？<br>
                · 如果我手边没有 {cn2}，有什么替代方案？<br>
                · 这两种食材在数据库里没有收录的搭配方式是什么？<br>
                · 请帮我设计一道突出这个搭配的完整菜谱
              </span>
            </div>""", unsafe_allow_html=True)

        # 快捷问题按钮
        st.markdown("<div style='margin-bottom:8px'>", unsafe_allow_html=True)
        quick_qs = [
            f"为什么 {cn1} 要作为主食材？换成其他食材会怎样？",
            f"用 {cn1} + {cn2} 设计一道完整菜谱，含烹饪步骤",
            f"如果数据库里没有我想要的食材，我该怎么描述给你？",
            f"当前 {int(ratios.get(n1,0.5)*100)}% vs {int(ratios.get(n2,0.5)*100)}% 的比例是最优的吗？",
        ]
        qcols = st.columns(2)
        for qi, q in enumerate(quick_qs):
            if qcols[qi%2].button(q, key=f"qbtn_{qi}", use_container_width=True):
                with st.spinner("AI 思考中..."):
                    resp = call_gemini(active_key, st.session_state.chat_history + [{"role":"user","content":q}], context_str)
                st.session_state.chat_history.append({"role":"user","content":q})
                st.session_state.chat_history.append({"role":"assistant","content":resp})
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 输入框
        user_input = st.text_input(
            "向风味顾问提问...",
            placeholder=f"例如：我想用榴莲+{cn2}，数据库没有榴莲但我知道它有硫化物气息，请帮我分析...",
            key="gemini_input", label_visibility="collapsed")
        col_send, col_clear = st.columns([4,1])
        with col_send:
            if st.button("发送给风味顾问 ➤", key="send_btn", use_container_width=True, type="primary"):
                if user_input.strip():
                    with st.spinner("AI 思考中..."):
                        resp = call_gemini(active_key, st.session_state.chat_history + [{"role":"user","content":user_input}], context_str)
                    st.session_state.chat_history.append({"role":"user","content":user_input})
                    st.session_state.chat_history.append({"role":"assistant","content":resp})
                    st.rerun()
        with col_clear:
            if st.button("清空", key="clear_btn", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # 底部统计
    st.markdown(f"""
    <div style="text-align:center;padding:14px;color:var(--text-faint);font-size:.76rem">
      🧬 FlavorDB · {len(df)} 种食材 · {len(LOC.get('ingredients',{}))} 个食材已汉化 ·
      共享分子 {len(sim['shared'])} 个 · Jaccard {int(sim['jaccard']*100)}%
    </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
