import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json, os, random, math, re, time
from math import sqrt
from datetime import datetime

# ================================================================
# 0. 页面配置与全局状态
# ================================================================
st.set_page_config(
    page_title="味觉虫洞 Flavor Lab",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化状态
if "language" not in st.session_state:
    st.session_state.language = "zh"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_context_key" not in st.session_state:
    st.session_state.chat_context_key = ""
if "last_api_error" not in st.session_state:
    st.session_state.last_api_error = None
if "selected_cats" not in st.session_state:
    st.session_state.selected_cats = set()

def t(text_en, text_zh=None):
    if st.session_state.language == "zh":
        return text_zh if text_zh else text_en
    return text_en

# ================================================================
# 1. API 配置管理
# ================================================================
def get_api_config():
    """API 优先级：环境变量 > Streamlit Secrets > config.py"""
    DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # ── 1. 环境变量（本地 ~/.zshrc 已配置时自动生效）──
    ds_env = os.getenv("DASHSCOPE_API_KEY", "")
    if ds_env:
        return {"provider": "dashscope", "api_key": ds_env,
                "model": os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
                "base_url": DASHSCOPE_BASE}

    # ── 2. Streamlit Cloud Secrets ──
    try:
        secrets = st.secrets
        if "DASHSCOPE_API_KEY" in secrets and secrets["DASHSCOPE_API_KEY"]:
            return {"provider": "dashscope",
                    "api_key": secrets["DASHSCOPE_API_KEY"],
                    "model": secrets.get("DASHSCOPE_MODEL", "qwen-plus"),
                    "base_url": DASHSCOPE_BASE}
        if "GEMINI_API_KEY" in secrets and secrets["GEMINI_API_KEY"]:
            return {"provider": "gemini", "api_key": secrets["GEMINI_API_KEY"],
                    "model": secrets.get("GEMINI_MODEL", "gemini-2.0-flash")}
        if "OPENAI_API_KEY" in secrets and secrets["OPENAI_API_KEY"]:
            return {"provider": "openai", "api_key": secrets["OPENAI_API_KEY"],
                    "model": secrets.get("OPENAI_MODEL", "gpt-4o-mini"),
                    "base_url": secrets.get("OPENAI_BASE_URL", "https://api.openai.com/v1")}
    except Exception:
        pass

    # ── 3. config.py 本地文件 ──
    try:
        import config as _cfg
        if getattr(_cfg, "DASHSCOPE_API_KEY", ""):
            return {"provider": "dashscope", "api_key": _cfg.DASHSCOPE_API_KEY,
                    "model": getattr(_cfg, "DASHSCOPE_MODEL", "qwen-plus"),
                    "base_url": DASHSCOPE_BASE}
        if getattr(_cfg, "GEMINI_API_KEY", ""):
            return {"provider": "gemini", "api_key": _cfg.GEMINI_API_KEY,
                    "model": getattr(_cfg, "GEMINI_MODEL", "gemini-2.0-flash")}
    except Exception:
        pass
    return None

def check_api_status():
    config = get_api_config()
    if not config:
        return False, None
    key = config.get("api_key", "")
    if len(key) < 20:
        return False, config
    return True, config

# ================================================================
# 2. AI 调用引擎
# ================================================================
def call_ai_api(messages, context, max_retries=2):
    config = get_api_config()
    if not config:
        return False, "❌ API 未配置。请在 Streamlit Cloud Secrets 中设置 API Key。", False
    
    provider = config.get("provider", "gemini")
    
    system_prompt = (
        "你是一位顶级的「风味设计专家」与「分子美食科学家」。"
        "你运营着一个名为《味觉虫洞》的实验室，打破常规烹饪逻辑，"
        "利用食材的分子结构、味觉互补和嗅觉穿透力，为设计师和厨师提供极具创意的风味组合方案。\n\n"
        "【核心逻辑框架】\n"
        "- 锚点法则（Anchoring）：以用户食材为核心，寻找「虫洞连接」的配对\n"
        "- 分子共鸣（Molecular Profiling）：寻找共享香气分子，如遇黑胡椒关联木质调\n"
        "- 维度补偿（Balance）：酸、甜、苦、咸、鲜、辛、麻、涩的动态平衡\n"
        "- 极光效应（Aurora Effect）：关注能提升香气频率、产生鼻腔冲击力的组合\n\n"
        "【当前实验数据】\n" + context + "\n\n"
        "【回复必须包含的模块】\n"
        "🛰️ 虫洞坐标：食材的味觉坐标（如：[高频挥发辛凉] vs [低频坚果油脂]）\n"
        "🌀 关联逻辑：搭配原理（分子共鸣/味觉补偿/嗅觉电梯效应）\n"
        "🧪 实验报告：入口→中段→尾韵的感官演变曲线\n"
        "👨\u200d🍳 厨师应用：2-3个具体烹饪/研发场景（前菜/主菜/甜点/饮品）\n"
        "📊 风味星图参数：建议配比或关键技术处理\n\n"
        "【语气与风格】\n"
        "专业前卫、充满探索感。使用「频率/维度/碰撞/坍缩/共振」等词汇。"
        "对中国本土食材（黄茶/陈皮/益智仁/花椒）有深厚理解。"
        "每次回答结尾提出一个前沿延伸问题。"
    )
    
    # DashScope 使用 OpenAI 兼容模式（完全一致）
    if provider in ("dashscope", "openai"):
        return _call_openai(config, messages, system_prompt, max_retries)
    elif provider == "gemini":
        return _call_gemini(config, messages, system_prompt, max_retries)
    elif provider == "claude":
        return _call_claude(config, messages, system_prompt, max_retries)
    else:
        return _call_openai(config, messages, system_prompt, max_retries)

def _call_gemini(config, messages, system_prompt, max_retries):
    try:
        import google.generativeai as genai
        genai.configure(api_key=config["api_key"])
        model = genai.GenerativeModel(config.get("model", "gemini-2.0-flash"))
        
        for attempt in range(max_retries):
            try:
                chat = model.start_chat(history=[])
                chat.send_message(system_prompt)
                for msg in messages:
                    if msg["role"] == "user":
                        response = chat.send_message(msg["content"])
                return True, response.text, False
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "Resource has been exhausted" in err_str:
                    if attempt < max_retries - 1:
                        time.sleep((attempt + 1) * 2)
                        continue
                    return False, "⚠️ **Gemini 请求频率超限（429）**\n\n免费版每分钟限制 1-2 次调用。请等待 30-60 秒后重试，或考虑升级到 Gemini Pro", True
                elif "API_KEY_INVALID" in err_str:
                    return False, "❌ **Gemini API Key 无效**。请检查 Key 是否正确。", False
                else:
                    return False, f"⚠️ Gemini 调用出错: {err_str[:150]}", False
    except ImportError:
        return False, "❌ 未安装 google-generativeai 包", False

def _call_openai(config, messages, system_prompt, max_retries):
    try:
        import openai
        client = openai.OpenAI(api_key=config["api_key"], base_url=config.get("base_url", "https://api.openai.com/v1"))
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=config.get("model", "gpt-4o-mini"),
                    messages=api_messages,
                    temperature=0.7,
                    max_tokens=1500
                )
                return True, response.choices[0].message.content, False
            except Exception as e:
                err_str = str(e)
                if "rate limit" in err_str.lower() or "429" in err_str:
                    if attempt < max_retries - 1:
                        time.sleep((attempt + 1) * 2)
                        continue
                    return False, "⚠️ **OpenAI 请求频率超限**。请稍后重试。", True
                elif "invalid api key" in err_str.lower():
                    return False, "❌ **OpenAI API Key 无效**。请检查配置。", False
                else:
                    return False, f"⚠️ OpenAI 调用出错: {err_str[:150]}", False
    except ImportError:
        return False, "❌ 未安装 openai 包", False

def _call_claude(config, messages, system_prompt, max_retries):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config["api_key"])
        api_messages = []
        for msg in messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        
        for attempt in range(max_retries):
            try:
                response = client.messages.create(
                    model=config.get("model", "claude-3-haiku-20240307"),
                    max_tokens=1500,
                    system=system_prompt,
                    messages=api_messages
                )
                return True, response.content[0].text, False
            except Exception as e:
                err_str = str(e)
                if "rate_limit" in err_str.lower():
                    if attempt < max_retries - 1:
                        time.sleep((attempt + 1) * 2)
                        continue
                    return False, "⚠️ **Claude 请求频率超限**。请稍后重试。", True
                else:
                    return False, f"⚠️ Claude 调用出错: {err_str[:150]}", False
    except ImportError:
        return False, "❌ 未安装 anthropic 包", False

# ================================================================
# 3. 全局样式
# ================================================================
st.markdown("""
<style>
:root {
  --bg-main: #F4F6FA; --bg-sidebar: #FAFBFC; --bg-card: #FFFFFF;
  --border-color: #E8EAED; --text-primary: #111827; --text-second: #374151;
  --text-muted: #6B7280; --text-faint: #9CA3AF; --shadow: 0 2px 12px rgba(0,0,0,0.07);
  --accent-blue: #00D2FF; --accent-purple: #7B2FF7; --accent-pink: #FF6B6B;
  --accent-green: #22C55E; --accent-orange: #F97316;
}
.stApp { background: var(--bg-main) !important; }
[data-testid="stSidebar"] { background: var(--bg-sidebar) !important; border-right: 1px solid var(--border-color) !important; }
.hero-header {
  background: linear-gradient(135deg,#0A0A1A 0%,#1A1A3E 50%,#0D2137 100%);
  padding: 24px 32px; border-radius: 18px; margin-bottom: 20px;
  display: flex; align-items: center; gap: 14px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.hero-title {
  font-size: 1.85rem; font-weight: 800;
  background: linear-gradient(90deg,#00D2FF,#7B2FF7,#FF6B6B);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin: 0; line-height: 1.2;
}
.hero-sub { font-size: .75rem; color: rgba(255,255,255,.42) !important; margin: 0; letter-spacing: .08em; text-transform: uppercase; }
.card { background: var(--bg-card); padding: 20px; border-radius: 16px; box-shadow: var(--shadow); margin-bottom: 16px; border: 1px solid var(--border-color); }
.card h4, .card b, .card strong { color: var(--text-primary) !important; }
.card-title { margin: 0 0 14px 0 !important; font-size: 1rem !important; font-weight: 700 !important; color: var(--text-primary) !important; display: flex; align-items: center; gap: 6px; }
.card p, .card span, .card div { color: var(--text-second) !important; }
.card-dark { background: linear-gradient(135deg,#0A0A1A,#1A1A3E); padding: 22px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,.3); margin-bottom: 16px; border: 1px solid rgba(255,255,255,.08); text-align: center; }
.card-dark, .card-dark * { color: #FFFFFF !important; }
.tag { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: .76rem; font-weight: 600; margin: 2px; }
.tag-blue { background:#EEF6FF; color:#1D6FDB !important; border:1px solid #BDD7F5; }
.tag-green { background:#F0FDF4; color:#16A34A !important; border:1px solid #BBF7D0; }
.tag-orange { background:#FFF7ED; color:#C2410C !important; border:1px solid #FECBA1; }
.tag-purple { background:#F5F3FF; color:#7C3AED !important; border:1px solid #DDD6FE; }
.tag-pink { background:#FDF2F8; color:#BE185D !important; border:1px solid #FBCFE8; }
.tag-shared { background:linear-gradient(90deg,#E0F7FA,#EDE7F6); color:#5B21B6 !important; border:1px solid #C4B5FD; font-weight:700; }
.tag-contrast { background:#FEE2E2; color:#991B1B !important; border:1px solid #FECACA; }
.badge { display:inline-block; padding:4px 14px; border-radius:20px; font-size:.82rem; font-weight:700; }
.badge-resonance { background:#D1FAE5; color:#065F46 !important; }
.badge-contrast { background:#FEE2E2; color:#991B1B !important; }
.badge-neutral { background:var(--bg-card-hover); color:var(--text-second) !important; border:1px solid var(--border-color); }
.diag { border-radius:12px; padding:14px 16px; margin:8px 0; border-left:4px solid; }
.diag-res { background:#F0FDF4; border-color:#22C55E; }
.diag-ctr { background:#FFF7ED; border-color:#F97316; }
.diag-info { background:#EEF6FF; border-color:#3B82F6; }
.diag-warn { background:#FEF3C7; border-color:#F59E0B; }
.technique-wrap { position: relative; display: inline-block; cursor: help; }
.technique-term { color: #7B2FF7 !important; font-weight: 700; border-bottom: 2px dotted #7B2FF7; }
.technique-tooltip {
  visibility: hidden; opacity: 0; background: #1A1A3E; color: #F0F2F8 !important;
  text-align: left; border-radius: 10px; padding: 12px 14px; position: absolute;
  z-index: 9999; bottom: 130%; left: 50%; transform: translateX(-50%);
  width: 280px; font-size: .8rem; line-height: 1.5;
  box-shadow: 0 8px 24px rgba(0,0,0,.35); border: 1px solid rgba(255,255,255,.12);
  transition: opacity .2s, visibility .2s; pointer-events: none;
}
.technique-tooltip::after { content: ""; position: absolute; top: 100%; left: 50%; transform: translateX(-50%); border: 6px solid transparent; border-top-color: #1A1A3E; }
.technique-wrap:hover .technique-tooltip { visibility: visible; opacity: 1; }
.pbar-bg { background:var(--border-color); border-radius:6px; height:7px; overflow:hidden; margin:3px 0; }
.pbar-fill { height:100%; border-radius:6px; }
.ing-row { background: var(--bg-card-hover); border: 1px solid var(--border-color); border-radius: 10px; padding: 10px 14px; margin: 5px 0; }
.ing-row .muted { color: var(--text-muted) !important; }
.api-status { display: flex; align-items: center; gap: 8px; padding: 10px 14px; border-radius: 10px; font-size: 0.85rem; margin-bottom: 12px; }
.api-status.ready { background: #D1FAE5; color: #065F46; }
.api-status.error { background: #FEE2E2; color: #991B1B; }
.api-status.warning { background: #FEF3C7; color: #92400E; }
.chat-bubble-user { background: linear-gradient(135deg,#7B2FF7,#00D2FF); color: #fff !important; padding: 12px 18px; border-radius: 18px 18px 4px 18px; margin: 8px 0; display: inline-block; max-width: 80%; float: right; clear: both; font-size: 0.95rem; line-height: 1.5; box-shadow: 0 2px 8px rgba(123,47,247,0.25); }
.chat-bubble-ai { background: var(--bg-card); color: var(--text-primary) !important; border: 1px solid var(--border-color); padding: 12px 18px; border-radius: 18px 18px 18px 4px; margin: 8px 0; display: inline-block; max-width: 80%; float: left; clear: both; font-size: 0.95rem; line-height: 1.6; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.chat-bubble-ai.chat-error { background: #FEF2F2 !important; border: 1px solid #FECACA !important; color: #DC2626 !important; }
.chat-clearfix { clear:both; height: 8px; }
.chat-wrap { max-height: 500px; overflow-y: auto; padding: 12px; background: var(--bg-main); border-radius: 12px; }
.chat-time { font-size: 0.7rem; color: var(--text-faint); margin-top: 4px; text-align: right; }
.sec-label { font-size: .72rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--text-faint) !important; margin: 14px 0 6px; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.2rem !important; }
</style>
""", unsafe_allow_html=True)

# ================================================================
# 4. 本地化引擎
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
# 5. 数据加载
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
    df["mol_set"] = df.apply(lambda r: _parse_fp(r["flavor_profiles"]) | _parse_fl(r.get("flavors", "")), axis=1)
    df["mol_count"] = df["mol_set"].apply(len)
    return df[df["mol_count"] > 0].copy()

# ================================================================
# 6. 算法引擎
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
    lipo = sum(1 for m in mol_set if POLARITY.get(m) == "L")
    hydro = sum(1 for m in mol_set if POLARITY.get(m) == "H")
    total = lipo + hydro
    if total == 0: return {"type": "balanced", "lipo": 0, "hydro": 0, "total": 0}
    t = "lipophilic" if lipo > hydro else ("hydrophilic" if hydro > lipo else "balanced")
    return {"type": t, "lipo": lipo, "hydro": hydro, "total": total}

def find_bridges(df, set_a, set_b, selected, top_n=4):
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
    if not top: return []
    max_score = top[0][1]
    return [(name, score/max_score, sa, sb) for name, score, sa, sb in top]

def find_contrasts(df, set_a, set_b, selected, top_n=4):
    results = []
    for _, row in df.iterrows():
        if row["name"] in selected: continue
        s = row["mol_set"]
        diff_a = len(s - set_a) / max(len(s), 1)
        diff_b = len(s - set_b) / max(len(s), 1)
        contrast_score = (diff_a + diff_b) / 2
        if contrast_score > 0.3:
            results.append((row["name"], contrast_score, diff_a, diff_b))
    results.sort(key=lambda x: -x[1])
    top = results[:top_n]
    if not top: return []
    max_score = top[0][1]
    return [(name, score/max_score, diff_a, diff_b) for name, score, diff_a, diff_b in top]

RADAR_DIMS = {
    "甜味": ["sweet","caramel","honey","vanilla","sugar","butterscotch","candy","cotton candy"],
    "烘焙": ["roasted","baked","toasted","caramel","coffee","cocoa","bread","malt","popcorn"],
    "果香": ["fruity","berry","apple","pear","peach","citrus","tropical","grape","banana","strawberry"],
    "草本": ["herbaceous","herbal","green","mint","thyme","rosemary","basil","dill","leafy"],
    "木质烟熏": ["woody","wood","smoky","smoke","cedar","oak","leather","tobacco","resin"],
    "辛辣": ["spicy","pepper","cinnamon","ginger","clove","mustard","pungent","horseradish"],
    "花香": ["floral","rose","jasmine","lavender","violet","lily","blossom","jasmin"],
    "脂奶": ["fatty","creamy","buttery","butter","cream","dairy","milky","nutty"],
}

def radar_vals(mol_set):
    result = {}
    for dim, kws in RADAR_DIMS.items():
        hit = sum(1 for k in kws if k in mol_set)
        result[dim] = min(10, hit * 2.0 + (0.8 if hit > 0 else 0))
    return result

# ================================================================
# 7. 工艺术语 Tooltip
# ================================================================
TECHNIQUES = {
    "低温慢煮": {"en": "Sous Vide", "desc": "将食材密封后放入恒温水浴（通常 55-85°C）长时间烹饪。精确控温，最大程度锁住水分和芳香分子，避免高温氧化破坏挥发性香气。"},
    "乳化": {"en": "Emulsification", "desc": "将两种不相溶的液体（如油和水）通过乳化剂稳定结合。可同时呈现脂溶性和水溶性风味分子，是酱汁的核心技术。"},
    "真空萃取": {"en": "Vacuum Extraction", "desc": "利用负压降低液体沸点，在低温下完成萃取。保留热敏感香气，萃取效率比常压高 3-5 倍。"},
    "发酵": {"en": "Fermentation", "desc": "微生物分解糖类产生醇类、酸类和酯类，创造全新的复合风味。最古老也最复杂的风味转化手段之一。"},
    "烟熏": {"en": "Smoking", "desc": "木材不完全燃烧产生的烟雾渗入食材表面，形成独特的焦木香气，同时具有防腐作用。"},
    "冷冻干燥": {"en": "Freeze Drying", "desc": "在超低温下将水分直接升华，保留 95% 以上的芳香分子，是最温和的干燥方式。"},
    "浓缩收汁": {"en": "Reduction", "desc": "通过持续加热蒸发水分，将液体浓缩，使风味分子浓度大幅提升，可将基础风味放大 3-10 倍。"},
    "凝胶化": {"en": "Gelification", "desc": "使用明胶、琼脂等将液体凝固成半固态，使风味在口腔中缓慢释放，延长味觉持续时间。"},
    "Espuma": {"en": "Espuma / 泡沫技术", "desc": "使用奶油枪将液体充入氮气形成轻盈泡沫，将复杂风味以轻盈质地呈现，增强嗅觉感知。"},
    "Confit": {"en": "Confit / 油封", "desc": "将食材浸没在油脂中以低温长时间加热，脂溶性芳香分子充分融入油脂，使食材极度嫩滑。"},
    "Consommé": {"en": "Consommé / 澄清汤", "desc": "使用蛋白质澄清技术去除杂质，得到透明清澈的浓缩高汤，只保留水溶性风味分子。"},
    "乳化酱汁": {"en": "Emulsion Sauce", "desc": "通过乳化作用将油脂分散在水相中，同时呈现脂溶和水溶风味的双重层次。"},
    "甘纳许": {"en": "Ganache", "desc": "巧克力与奶油的乳化物，通过乳化使脂溶性可可芳香与水溶性奶香完美融合。"},
    "油封": {"en": "Confit", "desc": "将食材浸没在油脂中以低温长时间加热，脂溶性芳香分子充分融入油脂，使食材极度嫩滑。"},
    "澄清汤": {"en": "Consommé", "desc": "使用蛋白质澄清技术去除杂质，得到透明清澈的浓缩高汤，只保留水溶性风味分子。"},
    "泡沫": {"en": "Espuma", "desc": "使用奶油枪将液体充入氮气形成轻盈泡沫，将复杂风味以轻盈质地呈现，增强嗅觉感知。"},
}

def tech_tip(term):
    info = TECHNIQUES.get(term)
    if not info:
        return f"<b>{term}</b>"
    return f'<span class="technique-wrap"><span class="technique-term">{term}</span><span class="technique-tooltip"><b style="color:#00D2FF">{term} · {info["en"]}</b><br><br>{info["desc"]}</span></span>'

# ================================================================
# 8. HTML 辅助
# ================================================================
TAG_CLASSES = ["tag-blue","tag-green","tag-orange","tag-purple","tag-pink"]

def score_color(s):
    return "#22C55E" if s >= 80 else ("#3B82F6" if s >= 65 else ("#F97316" if s >= 50 else "#EF4444"))

def tags_html(notes, cls="tag-blue", max_n=8):
    return " ".join(f'<span class="tag {cls}">{n}</span>' for n in notes[:max_n])

def shared_tags_html(notes, max_n=10):
    return " ".join(f'<span class="tag tag-shared">⚡ {t_note(n)}</span>' for n in notes[:max_n])

def md_to_html(text):
    import re
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" style="color:#7B2FF7">\1</a>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?m)^[\-·]\s+(.+)$', r'<div style="padding:2px 0 2px 12px">• \1</div>', text)
    text = text.replace("\n", "<br>")
    return text

# ================================================================
# 9. AI 对话区
# ================================================================
def render_chat_section(api_config, cn1, cn2, selected, ratios, sim):
    st.markdown("---")
    st.markdown(f'<div class="card"><h4 class="card-title">🤖 风味虫洞顾问 <span style="font-size:.75rem;color:var(--text-muted);font-weight:400">· 基于 {cn1} × {cn2}</span></h4>', unsafe_allow_html=True)
    
    if not api_config:
        st.markdown("""
        <div class="diag diag-info">
          <b>🔑 AI 顾问未激活</b><br><br>
          <span>请在 Streamlit Cloud Secrets 中配置 API Key：</span><br><br>
          <b>方案一（推荐）：OpenAI</b><br>
          <code>OPENAI_API_KEY = "sk-..."</code><br><br>
          <b>方案二：Gemini</b><br>
          <code>GEMINI_API_KEY = "AIza..."</code><br><br>
          <span><a href="https://platform.openai.com/api-keys" target="_blank" style="color:#7B2FF7">→ 获取 OpenAI Key</a></span><br>
          <span><a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#7B2FF7">→ 获取 Gemini Key</a></span>
        </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    provider = api_config.get("provider", "unknown")
    provider_names = {"openai": "OpenAI", "gemini": "Gemini", "claude": "Claude", "dashscope": "通义千问 ✨"}
    provider_name = provider_names.get(provider, provider.upper())
    
    st.markdown(f'<div class="api-status ready"><span>✅</span><span>AI 顾问已连接 · {provider_name}</span></div>', unsafe_allow_html=True)
    
    # 构建上下文
    def build_context():
        lines = [f"正在分析食材搭配：{' + '.join(t_ingredient(n) for n in selected)}"]
        lines.append(f"分子共鸣指数：{sim['score']}%（类型：{'同源共振' if sim['type']=='resonance' else '对比碰撞' if sim['type']=='contrast' else '平衡搭档'}）")
        lines.append(f"共享风味分子数：{len(sim['shared'])} 个（Jaccard相似度 {int(sim['jaccard']*100)}%）")
        for n in selected:
            pct = int(ratios.get(n, 1/len(selected))*100)
            top5 = t_notes_list(mol_sets[n], 5)
            lines.append(f"• {t_ingredient(n)}（{pct}%）：主要风味 - {', '.join(top5)}")
        if sim["shared"]:
            shared_cn = [t_note(x) for x in sim["shared"][:8]]
            lines.append(f"共享节点：{', '.join(shared_cn)}")
        return "\n".join(lines)
    
    context_str = build_context()
    
    # 检测食材变化，重置对话
    current_key = "+".join(sorted(selected))
    if st.session_state.chat_context_key != current_key:
        st.session_state.chat_history = []
        st.session_state.chat_context_key = current_key
        st.session_state.last_api_error = None
    
    # 渲染历史消息
    if st.session_state.chat_history:
        chat_html = '<div class="chat-wrap">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f'<div class="chat-bubble-user">{msg["content"]}</div>'
                chat_html += f'<div class="chat-time">{msg.get("time", "")}</div>'
                chat_html += '<div class="chat-clearfix"></div>'
            else:
                is_error = msg.get("is_error", False)
                bubble_class = "chat-bubble-ai chat-error" if is_error else "chat-bubble-ai"
                content = md_to_html(msg["content"])
                chat_html += f'<div class="{bubble_class}">{content}</div>'
                chat_html += '<div class="chat-clearfix"></div>'
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        type_hints = {
            "resonance": f"它们共享大量相同的芳香分子，属于「**同源共振**」型搭配，适合用叠加增强来放大共鸣。",
            "contrast": f"它们风味差异显著，属于「**对比碰撞**」型搭配，高明的厨师会用这种张力创造层次感。",
            "neutral": f"它们适度交叠互补，属于「**平衡搭档**」型搭配，比例调整是提升这个组合的关键。",
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
            · 请帮我设计一道突出这个搭配的完整菜谱
          </span>
        </div>""", unsafe_allow_html=True)
    
    if st.session_state.last_api_error:
        st.markdown(f'<div class="diag diag-warn" style="margin: 12px 0;"><b>⚠️ 上次请求遇到问题</b><br><span>{st.session_state.last_api_error}</span></div>', unsafe_allow_html=True)
    
    # 快捷问题按钮
    st.markdown("<div style='margin: 16px 0 12px;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.85rem; color: var(--text-muted); margin-bottom: 8px;'>💡 快捷问题：</div>", unsafe_allow_html=True)
    
    n1, n2 = selected[0], selected[1]
    quick_qs = [
        f"为什么 {cn1} 要作为主食材？换成其他食材会怎样？",
        f"用 {cn1} + {cn2} 设计一道完整菜谱",
        f"当前 {int(ratios.get(n1,0.5)*100)}% vs {int(ratios.get(n2,0.5)*100)}% 的比例是最优的吗？",
    ]
    
    qcols = st.columns(3)
    for qi, q in enumerate(quick_qs):
        if qcols[qi].button(q, key=f"qbtn_{qi}", use_container_width=True):
            current_time = datetime.now().strftime("%H:%M")
            st.session_state.chat_history.append({"role": "user", "content": q, "time": current_time})
            st.session_state.last_api_error = None
            
            with st.spinner("🤖 AI 思考中..."):
                success, result, is_rate_limit = call_ai_api([{"role": "user", "content": q}], context_str)
            
            st.session_state.chat_history.append({"role": "assistant", "content": result, "is_error": not success})
            
            if not success:
                st.session_state.last_api_error = "API 调用失败" if not is_rate_limit else "频率限制，请稍后重试"
            
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 输入框
    st.markdown("<div style='margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-color);'>", unsafe_allow_html=True)
    
    user_input = st.text_input("向风味顾问提问...", placeholder=f"例如：我想了解 {cn1} 和 {cn2} 的最佳烹饪方式...", key="gemini_input", label_visibility="collapsed")
    
    col_send, col_clear = st.columns([4, 1])
    
    with col_send:
        if st.button("发送给风味顾问 ➤", key="send_btn", use_container_width=True, type="primary"):
            if user_input.strip():
                msg_history = []
                for msg in st.session_state.chat_history:
                    if msg["role"] in ["user", "assistant"] and not msg.get("is_error", False):
                        msg_history.append({"role": msg["role"], "content": msg["content"]})
                msg_history.append({"role": "user", "content": user_input.strip()})
                
                current_time = datetime.now().strftime("%H:%M")
                st.session_state.chat_history.append({"role": "user", "content": user_input.strip(), "time": current_time})
                st.session_state.last_api_error = None
                
                with st.spinner("🤖 AI 思考中..."):
                    success, result, is_rate_limit = call_ai_api(msg_history, context_str)
                
                st.session_state.chat_history.append({"role": "assistant", "content": result, "is_error": not success})
                
                if not success:
                    st.session_state.last_api_error = "API 调用失败" if not is_rate_limit else "频率限制，请稍后重试"
                
                st.rerun()
    
    with col_clear:
        if st.button("🗑️ 清空对话", key="clear_btn", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.last_api_error = None
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ================================================================
# 10. 主界面
# ================================================================
def main():
    global mol_sets
    df = load_data()
    if df is None:
        st.error("❌ 找不到 flavordb_data.csv")
        st.stop()

    # Hero + 语言切换
    col_hero, col_lang = st.columns([6, 1])
    with col_hero:
        st.markdown("""
        <div class="hero-header">
          <span style="font-size:2.2rem">🧬</span>
          <div>
            <p class="hero-title">味觉虫洞 · Flavor Lab</p>
            <p class="hero-sub">Professional Flavor Pairing Engine · V2.0</p>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with col_lang:
        if st.button("🌐 EN/中", key="lang_toggle"):
            st.session_state.language = "en" if st.session_state.language == "zh" else "zh"
            st.rerun()

    # 侧边栏
    with st.sidebar:
        st.markdown("### 🔬 实验参数")

        all_cats = sorted(df["category"].unique().tolist())
        st.markdown('<div class="sec-label">🗂 按分类筛选</div>', unsafe_allow_html=True)
        
        cat_cols = st.columns(3)
        for i, cat in enumerate(all_cats[:12]):
            cat_zh = t_category(cat)
            is_active = cat in st.session_state.selected_cats
            btn_style = "primary" if is_active else "secondary"
            if cat_cols[i % 3].button(cat_zh, key=f"cat_{cat}", use_container_width=True, type=btn_style):
                if is_active:
                    st.session_state.selected_cats.discard(cat)
                else:
                    st.session_state.selected_cats.add(cat)
                st.rerun()
        
        if st.session_state.selected_cats:
            df_show = df[df["category"].isin(st.session_state.selected_cats)]
        else:
            df_show = df

        is_vegan = st.toggle("🍃 仅植物基 Vegan", value=False)
        if is_vegan:
            excl = ["meat","dairy","fish","seafood","pork","beef","chicken","egg"]
            df_show = df_show[~df_show["category"].str.lower().apply(lambda c: any(kw in c for kw in excl))]

        st.markdown('<div class="sec-label">🔍 搜索食材</div>', unsafe_allow_html=True)
        search_query = st.text_input("输入名称搜索...", key="search_box", label_visibility="collapsed")
        
        if search_query.strip():
            query = search_query.lower()
            mask = df_show["name"].str.lower().str.contains(query, na=False) | df_show["category"].str.lower().str.contains(query, na=False)
            for idx, row in df_show.iterrows():
                if query in t_ingredient(row["name"]).lower():
                    mask.loc[idx] = True
            df_show = df_show[mask]

        total_n = len(df_show)
        st.markdown(f'<div class="sec-label">已解锁 {total_n} 种食材</div>', unsafe_allow_html=True)
        options = sorted(df_show["name"].unique().tolist())
        defaults = [n for n in ["Coffee","Strawberry"] if n in options] or options[:2]

        selected = st.multiselect("选择食材（2-4种）", options=options, default=defaults, format_func=display_name, help="最多支持4种食材同时分析", key="ing_select")

        ratios = {}
        if len(selected) >= 2:
            st.markdown('<div class="sec-label">⚖️ 配方比例</div>', unsafe_allow_html=True)
            st.markdown("""
            <div style="background:#F0F4FF;border-radius:10px;padding:10px 12px;margin-bottom:10px;font-size:.78rem;line-height:1.65;color:#374151;border-left:3px solid #7B2FF7">
            <b style="color:#7B2FF7">💡 比例设计思路</b><br>
            · <b>主风味（≥50%）</b>：设定菜式的记忆点与核心香气基调<br>
            · <b>副风味（25-40%）</b>：丰富层次，与主风味形成对话<br>
            · <b>提味（≤15%）</b>：点睛之笔，提升整体香气频率<br>
            拖动滑块后，右侧雷达图将<b>实时反映</b>各食材权重变化
            </div>""", unsafe_allow_html=True)
            raw_total = 0
            for name in selected:
                pct_now = int(100//len(selected))
                ratios[name] = st.slider(t_ingredient(name), 0, 100, pct_now, 5, key=f"r_{name}")
                raw_total += ratios[name]
            if raw_total > 0:
                ratios = {k: v/raw_total for k, v in ratios.items()}

        st.divider()
        
        api_ok, api_config = check_api_status()
        st.markdown("### 🤖 AI 风味顾问")
        
        if api_ok:
            provider = api_config.get("provider", "unknown")
            provider_names = {"openai": "OpenAI", "gemini": "Gemini", "claude": "Claude", "dashscope": "通义千问 ✨"}
            st.markdown(f'<div class="api-status ready"><span>✅</span><span>已连接 · {provider_names.get(provider, provider.upper())}</span></div>', unsafe_allow_html=True)
        elif api_config:
            st.markdown('<div class="api-status warning"><span>⚠️</span><span>配置异常，请检查 Key</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="api-status error"><span>❌</span><span>未配置 API Key</span></div>', unsafe_allow_html=True)
            with st.expander("如何配置？"):
                st.markdown("""
                **方案一（推荐）：OpenAI**
                ```
                OPENAI_API_KEY = "sk-..."
                ```
                
                **方案二：Gemini**
                ```
                GEMINI_API_KEY = "AIza..."
                ```
                
                [获取 OpenAI Key](https://platform.openai.com/api-keys)  
                [获取 Gemini Key](https://aistudio.google.com/app/apikey)
                """)
        
        st.divider()
        st.caption("数据来源：FlavorDB · 分子风味科学")

    # 未选择足够食材
    if len(selected) < 2:
        st.markdown("""
        <div class="card" style="text-align:center;padding:60px 40px">
          <div style="font-size:4rem;margin-bottom:20px">🧬</div>
          <h2 style="margin-bottom:16px">味觉虫洞 · Flavor Lab</h2>
          <p style="color:var(--text-muted);font-size:1.1rem;line-height:1.8;max-width:600px;margin:0 auto">
            基于 FlavorDB 分子数据库的专业食材搭配引擎<br>
            请在左侧选择 <b>2-4 种食材</b> 开始分析
          </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # 数据分析
    rows = {n: df[df["name"] == n].iloc[0] for n in selected}
    mol_sets = {n: rows[n]["mol_set"] for n in selected}
    n1, n2 = selected[0], selected[1]
    sim = calc_sim(mol_sets[n1], mol_sets[n2])
    cn1, cn2 = t_ingredient(n1), t_ingredient(n2)

    # 主内容区
    col_left, col_right = st.columns([1.35, 1], gap="large")

    with col_left:
        st.markdown('<div class="card"><h4 class="card-title">🔭 风味维度雷达图</h4>', unsafe_allow_html=True)
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
                r=vals_s, theta=dims+[dims[0]], fill="toself", fillcolor=fc,
                line=dict(color=lc, width=2.5), name=f"{t_ingredient(name)} ({pct}%)"))
        fig_radar.update_layout(
            polar=dict(bgcolor="rgba(248,249,255,0.4)", radialaxis=dict(visible=True,range=[0,10],tickfont=dict(size=9,color="#9CA3AF")), angularaxis=dict(tickfont=dict(size=12,color="#888888"))),
            showlegend=True, legend=dict(orientation="h",y=-0.15,font=dict(size=11,color="#888888")),
            height=420, margin=dict(t=20,b=70,l=40,r=40), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_radar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if sim["shared"]:
            st.markdown('<div class="card"><h4 class="card-title">🕸 分子连线网络图</h4>', unsafe_allow_html=True)
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
            fig_net.add_trace(go.Scatter(x=ex,y=ey,mode="lines", line=dict(color="rgba(150,150,200,0.22)",width=1.2),hoverinfo="none",showlegend=False))
            fig_net.add_trace(go.Scatter(x=nx_l,y=ny_l,mode="markers+text", text=ntxt,textposition="top center",textfont=dict(size=10,color="#888888"),
                marker=dict(color=nclr,size=nsz,line=dict(width=2,color="white"),opacity=0.92), hoverinfo="text",showlegend=False))
            fig_net.update_layout(height=300,margin=dict(t=10,b=10,l=10,r=10), xaxis=dict(visible=False),yaxis=dict(visible=False),
                paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(248,249,255,0.3)")
            st.plotly_chart(fig_net, use_container_width=True)
            st.caption(f"🔵 {cn1}  🟣 {cn2}  🟠 共享节点（共 {len(sim['shared'])} 个）")
            st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        sc = sim["score"]
        sc_c = score_color(sc)
        type_info = {
            "resonance": ("同源共振","badge-resonance","共享大量芳香分子，协同延长风味余韵"),
            "contrast": ("对比碰撞","badge-contrast","差异显著，形成张力对比切割"),
            "neutral": ("平衡搭档","badge-neutral","适度交叠，互补平衡"),
        }
        tlabel,tbadge,tdesc = type_info[sim["type"]]
        r1 = int(ratios.get(n1,0.5)*100); r2 = int(ratios.get(n2,0.5)*100)
        jpct = int(sim["jaccard"]*100)
        # 进度条颜色：红→橙→绿 渐变
        bar_color = "#22C55E" if sc >= 70 else ("#F97316" if sc >= 45 else "#EF4444")
        st.markdown(f"""
        <div class="card-dark" style="text-align:left;padding:24px 28px">
          <!-- 标签行 -->
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
            <div style="color:rgba(255,255,255,.5);font-size:.7rem;letter-spacing:.12em;text-transform:uppercase">
              🔬 分子共鸣指数
            </div>
            <span class="badge {tbadge}" style="font-size:.75rem">{tlabel}</span>
          </div>
          <!-- 核心数字 -->
          <div style="display:flex;align-items:baseline;gap:4px;margin-bottom:12px">
            <span style="font-size:4.5rem;font-weight:900;line-height:1;color:{sc_c};font-variant-numeric:tabular-nums">{sc}</span>
            <span style="font-size:1.6rem;font-weight:400;color:rgba(255,255,255,.5)">%</span>
          </div>
          <!-- 进度条 -->
          <div style="background:rgba(255,255,255,.12);border-radius:6px;height:6px;margin-bottom:16px;overflow:hidden">
            <div style="width:{sc}%;height:100%;background:linear-gradient(90deg,{bar_color},{sc_c});border-radius:6px;transition:width .6s ease"></div>
          </div>
          <!-- 描述 -->
          <div style="color:rgba(255,255,255,.75);font-size:.85rem;line-height:1.6;margin-bottom:14px">{tdesc}</div>
          <!-- 比例行 -->
          <div style="color:rgba(255,255,255,.4);font-size:.75rem;border-top:1px solid rgba(255,255,255,.1);padding-top:10px">
            {cn1} <b style="color:rgba(255,255,255,.7)">{r1}%</b> &nbsp;·&nbsp; {cn2} <b style="color:rgba(255,255,255,.7)">{r2}%</b>
          </div>
          <!-- 科普说明 -->
          <div style="margin-top:14px;background:rgba(255,255,255,.06);border-radius:10px;padding:12px 14px;font-size:.76rem;line-height:1.7;color:rgba(255,255,255,.5)">
            <b style="color:rgba(255,255,255,.7)">📐 计算原理</b><br>
            基于 <b style="color:rgba(255,255,255,.65)">Jaccard 相似系数</b>：两种食材共享芳香分子数 ÷ 两者分子总量。
            共享分子 <b style="color:{sc_c}">{len(sim["shared"])} 种</b>，原始 Jaccard {jpct}%，
            经感知权重校正后得出综合共鸣指数。
            <br><span style="color:rgba(255,255,255,.35)">
            &gt; 70% 同源共振 · 45-70% 平衡搭档 · &lt; 45% 对比碰撞</span>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="card"><h4 class="card-title">🧪 风味指纹</h4>', unsafe_allow_html=True)
        for i, name in enumerate(selected):
            cn = t_ingredient(name)
            notes_cn = t_notes_list(rows[name]["mol_set"], top_n=10)
            pct = int(ratios.get(name, 1/len(selected))*100)
            cls = TAG_CLASSES[i % len(TAG_CLASSES)]
            dom = ""
            if pct >= 40: dom = '<span style="background:#FEF3C7;color:#92400E;font-size:.69rem;padding:1px 7px;border-radius:8px;margin-left:6px;font-weight:700">主导</span>'
            elif pct <= 15: dom = '<span style="background:#E0F2FE;color:#0369A1;font-size:.69rem;padding:1px 7px;border-radius:8px;margin-left:6px;font-weight:700">提味</span>'
            st.markdown(f"""
            <div style="margin-bottom:12px">
              <div style="font-weight:700;color:var(--text-primary);margin-bottom:3px">{cn} <span style="color:var(--text-faint);font-weight:400;font-size:.78rem">{pct}%</span>{dom}</div>
              <div class="pbar-bg"><div class="pbar-fill" style="width:{pct}%;background:linear-gradient(90deg,#00D2FF,#7B2FF7)"></div></div>
              <div style="margin-top:5px">{tags_html(notes_cn, cls, 8)}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card"><h4 class="card-title">🔬 深度诊断</h4>', unsafe_allow_html=True)
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
              <span>经典「切割平衡」结构。<b>{cn1}</b> 以 <b>{a3}</b> 主导，<b>{cn2}</b> 以 <b>{b3}</b> 抗衡，差异创造层次感。</span>
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

        pol = polarity_analysis(mol_sets[n1] | mol_sets[n2])
        if pol["total"] > 0:
            st.markdown('<div class="card"><h4 class="card-title">💧 介质推演</h4>', unsafe_allow_html=True)
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

        st.markdown('<div class="card"><h4 class="card-title">👨‍🍳 主厨工艺建议</h4>', unsafe_allow_html=True)
        tips_pool = {
            "resonance": [
                ("🔥 叠加放大", f"以 <b>{cn1}</b> 为基底，将 <b>{cn2}</b> {tech_tip('浓缩收汁')}后叠加，在同一芳香维度形成「风味放大」效果。"),
                ("🌡️ 低温保留", f"共享分子建议通过 {tech_tip('低温慢煮')} 保留，避免高温氧化破坏共鸣节点。"),
                ("🍮 质地穿插", f"将 <b>{cn2}</b> 制成 {tech_tip('凝胶化')}，穿插在 <b>{cn1}</b> 的质地层间，延长风味余韵。"),
            ],
            "contrast": [
                ("✂️ 切割平衡", f"利用 <b>{cn2}</b> 的对比维度「切割」{cn1} 的厚重感，以提味剂形式在收尾阶段引入。"),
                ("📈 分阶引入", f"先以 <b>{cn1}</b> 建立底味，后期通过 {tech_tip('低温慢煮')} 的 <b>{cn2}</b> 制造味觉转折。"),
                ("☁️ 泡沫覆盖", f"将 <b>{cn2}</b> 做成 {tech_tip('Espuma')}，轻盈覆盖 <b>{cn1}</b> 的厚重质地，创造对比张力。"),
            ],
            "neutral": [
                ("📊 比例递进", f"从 <b>{cn1}</b> 的纯净基调出发，逐步引入 <b>{cn2}</b> 的差异维度，通过 {tech_tip('乳化')} 融合。"),
                ("🔬 分子融合", f"{tech_tip('真空萃取')} 让两者在分子层面充分融合，实现比例可控的风味协同。"),
                ("❄️ 粉末跳跃", f"以 <b>{cn1}</b> 为主味质地，<b>{cn2}</b> 通过 {tech_tip('冷冻干燥')} 制成粉末，提供风味跳跃感。"),
            ],
        }
        all_tips = tips_pool[sim["type"]]
        type_guide = {
            "resonance": "同源共振型 · 核心策略：叠加放大——强化共同分子，深化香气维度",
            "contrast":  "对比碰撞型 · 核心策略：分阶切割——利用差异制造味觉节奏与层次感",
            "neutral":   "平衡搭档型 · 核心策略：比例调控——通过权重微调寻找最佳共鸣平衡点",
        }
        tip_colors   = ["#EEF6FF", "#F0FDF4", "#FFF7ED"]
        tip_borders  = ["#3B82F6", "#22C55E", "#F97316"]
        st.markdown(f"""<div style="background:linear-gradient(135deg,#F0F4FF,#F5F0FF);border-radius:10px;
        padding:12px 16px;margin-bottom:14px;border-left:4px solid #7B2FF7;font-size:.82rem;line-height:1.6">
        <b style="color:#7B2FF7">🧭 策略方向</b>&emsp;{type_guide[sim["type"]]}</div>""", unsafe_allow_html=True)
        tip_cols = st.columns(3)
        for i, (label, tip_text) in enumerate(all_tips):
            with tip_cols[i]:
                st.markdown(f"""<div style="background:{tip_colors[i]};border:1px solid {tip_borders[i]}44;
                border-top:3px solid {tip_borders[i]};border-radius:10px;padding:14px;min-height:140px">
                <div style="font-size:.78rem;font-weight:700;color:{tip_borders[i]};margin-bottom:8px">{label}</div>
                <div style="font-size:.79rem;color:#374151;line-height:1.65">{tip_text}</div>
                </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    cb, cc = st.columns([1,1], gap="large")

    with cb:
        st.markdown(f'<div class="card"><h4 class="card-title">🌉 风味桥接推荐</h4>', unsafe_allow_html=True)
        st.markdown(f"<p style='color:var(--text-muted);font-size:.82rem'>寻找能串联 <b>{cn1}</b> 与 <b>{cn2}</b> 的「第三食材」</p>", unsafe_allow_html=True)
        bridges = find_bridges(df, mol_sets[n1], mol_sets[n2], selected)
        if bridges:
            for bname, bsc, sa, sb in bridges:
                bcn = t_ingredient(bname)
                bcat_en = df[df["name"]==bname].iloc[0]["category"] if len(df[df["name"]==bname])>0 else ""
                bcat_zh = t_category(bcat_en)
                ps = min(100, int(bsc*100)); pa = min(100, int(sa*100)); pb = min(100, int(sb*100))
                st.markdown(f"""
                <div class="ing-row">
                  <div style="font-weight:700;color:var(--text-primary)">{bcn}<span class="muted" style="font-size:.75rem;font-weight:400"> {bname}</span></div>
                  <div class="muted" style="font-size:.74rem">{bcat_zh} · 连接力 {ps}%</div>
                  <div class="muted" style="font-size:.74rem">与{cn1} {pa}% | 与{cn2} {pb}%</div>
                  <div class="pbar-bg" style="margin-top:5px"><div class="pbar-fill" style="width:{ps}%;background:linear-gradient(90deg,#F97316,#FBBF24)"></div></div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("未找到合适的桥接食材")
        st.markdown("</div>", unsafe_allow_html=True)

    with cc:
        st.markdown(f'<div class="card"><h4 class="card-title">⚡ 对比风味推荐</h4>', unsafe_allow_html=True)
        st.markdown(f"<p style='color:var(--text-muted);font-size:.82rem'>与 <b>{cn1}</b> × <b>{cn2}</b> 形成张力对比的食材</p>", unsafe_allow_html=True)
        contrasts = find_contrasts(df, mol_sets[n1], mol_sets[n2], selected)
        if contrasts:
            for cname, csc, da, db in contrasts:
                ccn = t_ingredient(cname)
                ccat_en = df[df["name"]==cname].iloc[0]["category"] if len(df[df["name"]==cname])>0 else ""
                ccat_zh = t_category(ccat_en)
                ps = min(100, int(csc*100))
                st.markdown(f"""
                <div class="ing-row">
                  <div style="font-weight:700;color:var(--text-primary)">{ccn}<span class="muted" style="font-size:.75rem;font-weight:400"> {cname}</span></div>
                  <div class="muted" style="font-size:.74rem">{ccat_zh} · 对比度 {ps}%</div>
                  <div class="muted" style="font-size:.74rem">差异风味 · 创造层次感</div>
                  <div class="pbar-bg" style="margin-top:5px"><div class="pbar-fill" style="width:{ps}%;background:linear-gradient(90deg,#EF4444,#F97316)"></div></div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("未找到合适的对比食材")
        st.markdown("</div>", unsafe_allow_html=True)

    # AI 对话区
    api_ok, api_config = check_api_status()
    render_chat_section(api_config if api_ok else None, cn1, cn2, selected, ratios, sim)

    st.markdown(f"""
    <div style="text-align:center;padding:14px;color:var(--text-faint);font-size:.76rem">
      🧬 FlavorDB · {len(df)} 种食材 · 共享分子 {len(sim['shared'])} 个 · Jaccard {int(sim['jaccard']*100)}%
    </div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
