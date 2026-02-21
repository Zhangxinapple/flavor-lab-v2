import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
import json, os, random, math, re, time
from datetime import datetime

# ================================================================
# 0. API Key 配置 - 仅通过 Streamlit Secrets
# ================================================================
_GEMINI_MODEL = "gemini-2.0-flash"

def get_api_key():
    """从 Streamlit Secrets 获取 Gemini API Key"""
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key and "AIza" in key:
            return key
    except:
        pass
    return ""

# ================================================================
# 1. 页面配置
# ================================================================
st.set_page_config(
    page_title="味觉虫洞 Flavor Lab",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================================================
# 2. 全局样式 - 升级版
# ================================================================
st.markdown("""
<style>
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
  --accent-blue:   #00D2FF;
  --accent-purple: #7B2FF7;
  --accent-pink:   #FF6B6B;
}
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
.stApp { background: var(--bg-main) !important; }
[data-testid="stSidebar"] {
  background: var(--bg-sidebar) !important;
  border-right: 1px solid var(--border-color) !important;
}
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
.welcome-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 40px 48px;
  margin-bottom: 20px;
  box-shadow: var(--shadow);
}
.step-card {
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px 20px;
  flex: 1;
  min-width: 200px;
}
.score-big { font-size: 4.5rem; font-weight: 900; line-height: 1; display: block; }
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
.badge { display:inline-block; padding:4px 14px; border-radius:20px; font-size:.82rem; font-weight:700; }
.badge-resonance { background:#D1FAE5; color:#065F46 !important; }
.badge-contrast  { background:#FEE2E2; color:#991B1B !important; }
.badge-neutral   { background:var(--bg-card-hover); color:var(--text-second) !important; border:1px solid var(--border-color); }
.diag { border-radius:12px; padding:14px 16px; margin:8px 0; border-left:4px solid; }
.diag-res  { background:#F0FDF4; border-color:#22C55E; }
.diag-ctr  { background:#FFF7ED; border-color:#F97316; }
.diag-info { background:#EEF6FF; border-color:#3B82F6; }
.diag-warn { background:#FEF3C7; border-color:#F59E0B; }
.pbar-bg   { background:var(--border-color); border-radius:6px; height:7px; overflow:hidden; margin:3px 0; }
.pbar-fill { height:100%; border-radius:6px; }
.ing-row {
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 10px 14px;
  margin: 5px 0;
}
/* 升级版聊天气泡 */
.chat-bubble-user {
  background: linear-gradient(135deg,#7B2FF7,#00D2FF);
  color: #fff !important;
  padding: 12px 18px;
  border-radius: 18px 18px 4px 18px;
  margin: 8px 0;
  display: inline-block;
  max-width: 80%;
  float: right;
  clear: both;
  font-size: 0.95rem;
  line-height: 1.5;
  box-shadow: 0 2px 8px rgba(123,47,247,0.25);
}
.chat-bubble-ai {
  background: var(--bg-card);
  color: var(--text-primary) !important;
  border: 1px solid var(--border-color);
  padding: 12px 18px;
  border-radius: 18px 18px 18px 4px;
  margin: 8px 0;
  display: inline-block;
  max-width: 80%;
  float: left;
  clear: both;
  font-size: 0.95rem;
  line-height: 1.6;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.chat-bubble-ai b { color: var(--accent-purple) !important; }
.chat-clearfix { clear:both; height: 8px; }
.chat-wrap { max-height: 500px; overflow-y: auto; padding: 12px; background: var(--bg-main); border-radius: 12px; }
/* 时间戳样式 */
.chat-time {
  font-size: 0.7rem;
  color: var(--text-faint);
  margin-top: 4px;
  text-align: right;
}
/* 错误提示样式 */
.chat-error {
  background: #FEF2F2 !important;
  border: 1px solid #FECACA !important;
  color: #DC2626 !important;
}
/* 加载动画 */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.loading-dot {
  animation: pulse 1.5s infinite;
  display: inline-block;
}
.sec-label {
  font-size: .72rem;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--text-faint) !important;
  margin: 14px 0 6px;
}
/* API 状态指示器 */
.api-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 0.85rem;
  margin-bottom: 12px;
}
.api-status.ready {
  background: #D1FAE5;
  color: #065F46;
}
.api-status.error {
  background: #FEE2E2;
  color: #991B1B;
}
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.2rem !important; }
/* 快捷按钮样式优化 */
.quick-btn {
  font-size: 0.85rem !important;
  white-space: normal !important;
  height: auto !important;
  padding: 10px 12px !important;
  line-height: 1.4 !important;
}
</style>
""", unsafe_allow_html=True)


# ================================================================
# 3. 本地化引擎
# ================================================================
@st.cache_resource
def load_localization():
    if os.path.exists("localization_zh.json"):
        with open("localization_zh.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {"ingredients": {}, "flavor_notes": {}, "categories": {}}

LOC = load_localization()

def t_ingredient(name):
    return LOC.get("ingredients", {}).get(name, name)

def t_category(cat):
    return LOC.get("categories", {}).get(cat, cat)

def t_note(note):
    return LOC.get("flavor_notes", {}).get(note.strip().lower(), note.strip())

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
# 4. 数据加载
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
# 5. 算法引擎
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
        raw_score = math.sqrt(sa * sb) * (1 + min(sa, sb))
        if raw_score > 0.04:
            results.append((row["name"], raw_score, sa, sb))
    results.sort(key=lambda x: -x[1])
    top = results[:top_n]
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
# 6. Gemini API 调用 - 升级版（带重试机制和缓存）
# ================================================================
@st.cache_resource
def get_gemini_model():
    """缓存 Gemini 模型实例，避免重复初始化"""
    api_key = get_api_key()
    if not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(_GEMINI_MODEL)
    except:
        return None

def call_gemini_with_retry(messages: list, context: str, max_retries=3) -> tuple:
    """调用 Gemini API，带智能重试机制
    
    Returns:
        (success: bool, result: str, is_rate_limit: bool)
    """
    api_key = get_api_key()
    if not api_key or "AIza" not in api_key:
        return False, "❌ API Key 未配置。请在 Streamlit Cloud Secrets 中设置 GEMINI_API_KEY。", False
    
    model = get_gemini_model()
    if not model:
        return False, "❌ 无法初始化 Gemini 模型，请检查 API Key。", False
    
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
    
    for attempt in range(max_retries):
        try:
            # 构建对话历史
            chat = model.start_chat(history=[])
            
            # 发送系统提示
            chat.send_message(system_prompt)
            
            # 发送用户消息历史
            for msg in messages:
                if msg["role"] == "user":
                    response = chat.send_message(msg["content"])
            
            return True, response.text, False
            
        except Exception as e:
            err_str = str(e)
            
            # 429 频率限制 - 需要等待后重试
            if "429" in err_str or "Resource has been exhausted" in err_str:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3  # 递增等待时间
                    time.sleep(wait_time)
                    continue
                else:
                    return False, "⚠️ **请求频率超限（429）**\n\nGemini 免费版 API 有每分钟调用限制。请等待 30-60 秒后重试，或考虑升级到付费版。", True
            
            # API Key 无效
            elif "API_KEY_INVALID" in err_str or "401" in err_str:
                return False, "❌ **API Key 无效**\n\n请确认 Key 正确且 Gemini API 已在 Google AI Studio 中启用。", False
            
            # 权限不足
            elif "403" in err_str:
                return False, "❌ **API Key 无权限**\n\n请确认已在 Google AI Studio 中启用 Gemini API。", False
            
            # 服务不可用
            elif "500" in err_str or "503" in err_str:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return False, "⚠️ **Gemini 服务暂时不可用**\n\n请稍后重试。", False
            
            # 其他错误
            else:
                return False, f"⚠️ **调用出错**: {err_str[:200]}", False
    
    return False, "⚠️ 多次尝试后仍无法连接，请稍后重试。", False


# ================================================================
# 7. HTML 辅助函数
# ================================================================
TAG_CLASSES = ["tag-blue","tag-green","tag-orange","tag-purple","tag-pink"]

def score_color(s):
    return "#22C55E" if s >= 80 else ("#3B82F6" if s >= 65 else ("#F97316" if s >= 50 else "#EF4444"))

def tags_html(notes, cls="tag-blue", max_n=8):
    return " ".join(f'<span class="tag {cls}">{n}</span>' for n in notes[:max_n])

def shared_tags_html(notes, max_n=10):
    return " ".join(f'<span class="tag tag-shared">⚡ {t_note(n)}</span>' for n in notes[:max_n])

def md_to_html(text: str) -> str:
    """把 AI 回复的 Markdown 转成 HTML"""
    import re as _re
    text = _re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" style="color:#7B2FF7">\1</a>', text)
    text = _re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = _re.sub(r'(?m)^[\-·]\s+(.+)$', r'<div style="padding:2px 0 2px 12px">• \1</div>', text)
    text = text.replace("\n", "<br>")
    return text


# ================================================================
# 8. 欢迎页
# ================================================================
def render_welcome():
    st.markdown("""
    <div class="welcome-card">
      <div style="text-align:center;margin-bottom:28px">
        <div style="font-size:3.5rem;margin-bottom:8px">🧬</div>
        <h2 style="margin:0;font-size:1.7rem;color:var(--text-primary)">味觉虫洞 · Flavor Lab</h2>
        <p style="margin:8px 0 0;font-size:1rem;color:var(--text-muted)">
          基于 FlavorDB 分子数据库的专业食材搭配引擎
        </p>
      </div>
      <p style="font-size:.95rem;line-height:1.8;margin-bottom:24px;color:var(--text-second)">
        <b>味觉虫洞</b>通过分析食材中的挥发性芳香分子，科学揭示哪些食材在分子层面"天生一对"，
        帮助厨师、食品研发者和美食爱好者发现意想不到的绝妙搭配。
      </p>
      <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:28px">
        <div class="step-card">
          <div style="font-size:1.6rem">①</div>
          <h4 style="color:var(--text-primary)">选择食材</h4>
          <p style="color:var(--text-muted);font-size:.85rem">在左侧栏选择 2-4 种想要研究的食材</p>
        </div>
        <div class="step-card">
          <div style="font-size:1.6rem">②</div>
          <h4 style="color:var(--text-primary)">调整比例</h4>
          <p style="color:var(--text-muted);font-size:.85rem">通过滑块设定各食材在配方中的比例</p>
        </div>
        <div class="step-card">
          <div style="font-size:1.6rem">③</div>
          <h4 style="color:var(--text-primary)">查看分析</h4>
          <p style="color:var(--text-muted);font-size:.85rem">获得分子共鸣指数、风味指纹、工艺建议</p>
        </div>
        <div class="step-card">
          <div style="font-size:1.6rem">④</div>
          <h4 style="color:var(--text-primary)">AI 深度对话</h4>
          <p style="color:var(--text-muted);font-size:.85rem">与 AI 顾问就当前搭配进行专业探讨</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ================================================================
# 9. 侧边栏 - 升级版（根据 API 状态显示不同内容）
# ================================================================
def render_sidebar_api_status():
    """渲染 API 状态区域"""
    st.markdown("### 🤖 AI 风味顾问")
    
    api_key = get_api_key()
    
    if api_key:
        # API 已配置 - 显示简洁状态
        st.markdown("""
        <div class="api-status ready">
          <span>✅</span>
          <span>AI 顾问已就绪</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 显示使用提示
        with st.expander("ℹ️ 使用提示", expanded=False):
            st.markdown("""
            **关于 API 调用限制：**
            - Gemini 免费版有每分钟调用次数限制
            - 如遇 429 错误，请等待 30-60 秒后重试
            - 连续对话会消耗更多配额
            
            **优化建议：**
            - 使用快捷问题按钮更高效
            - 一次提问尽量详细
            """)
    else:
        # API 未配置 - 显示配置指引
        st.markdown("""
        <div class="api-status error">
          <span>⚠️</span>
          <span>API Key 未配置</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("""
        **配置方法：**
        
        1. 访问 [Google AI Studio](https://aistudio.google.com/app/apikey)
        2. 创建 API Key
        3. 在 Streamlit Cloud 中：
           - 点击 **⋮** → **Settings**
           - 选择 **Secrets**
           - 添加：`GEMINI_API_KEY = "你的Key"`
        4. 重启应用
        """)
    
    st.divider()


# ================================================================
# 10. AI 对话区 - 升级版（修复循环问题）
# ================================================================
def render_chat_section(api_key, cn1, cn2, selected, ratios, build_context):
    """渲染 AI 对话区"""
    st.markdown("---")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<h4>🤖 风味虫洞顾问 <span style="font-size:.75rem;color:var(--text-muted);font-weight:400">· 基于 {cn1} × {cn2} 的分子分析数据</span></h4>', unsafe_allow_html=True)
    
    if not api_key:
        st.markdown("""
        <div class="diag diag-info">
          <b>🔑 AI 顾问未激活</b><br><br>
          <span>请在 Streamlit Cloud Secrets 中配置 GEMINI_API_KEY 以启用 AI 对话功能。</span><br><br>
          <span><a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#7B2FF7">
          → 免费获取 Gemini Key</a></span>
        </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # 初始化 session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_context_key" not in st.session_state:
        st.session_state.chat_context_key = ""
    if "last_api_error" not in st.session_state:
        st.session_state.last_api_error = None
    
    # 检测食材变化，重置对话
    current_key = "+".join(sorted(selected))
    if st.session_state.chat_context_key != current_key:
        st.session_state.chat_history = []
        st.session_state.chat_context_key = current_key
        st.session_state.last_api_error = None
    
    context_str = build_context()
    
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
        # 显示引导信息
        type_hints = {
            "resonance": f"它们共享大量相同的芳香分子，属于「**同源共振**」型搭配，适合用叠加增强来放大共鸣。",
            "contrast":  f"它们风味差异显著，属于「**对比碰撞**」型搭配，高明的厨师会用这种张力创造层次感。",
            "neutral":   f"它们适度交叠互补，属于「**平衡搭档**」型搭配，比例调整是提升这个组合的关键。",
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
    
    # 显示之前的错误（如果有）
    if st.session_state.last_api_error:
        st.markdown(f"""
        <div class="diag diag-warn" style="margin: 12px 0;">
          <b>⚠️ 上次请求遇到问题</b><br>
          <span>{st.session_state.last_api_error}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # 快捷问题按钮
    st.markdown("<div style='margin: 16px 0 12px;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.85rem; color: var(--text-muted); margin-bottom: 8px;'>💡 快捷问题：</div>", unsafe_allow_html=True)
    
    n1, n2 = selected[0], selected[1]
    quick_qs = [
        f"为什么 {cn1} 要作为主食材？换成其他食材会怎样？",
        f"用 {cn1} + {cn2} 设计一道完整菜谱，含烹饪步骤",
        f"当前 {int(ratios.get(n1,0.5)*100)}% vs {int(ratios.get(n2,0.5)*100)}% 的比例是最优的吗？",
    ]
    
    qcols = st.columns(3)
    for qi, q in enumerate(quick_qs):
        if qcols[qi].button(q, key=f"qbtn_{qi}", use_container_width=True):
            # 添加用户消息
            current_time = datetime.now().strftime("%H:%M")
            st.session_state.chat_history.append({
                "role": "user", 
                "content": q,
                "time": current_time
            })
            st.session_state.last_api_error = None
            
            # 调用 API
            with st.spinner("🤖 AI 思考中..."):
                success, result, is_rate_limit = call_gemini_with_retry(
                    [{"role": "user", "content": q}], 
                    context_str
                )
            
            # 添加 AI 回复
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result,
                "is_error": not success
            })
            
            if not success:
                st.session_state.last_api_error = "API 调用失败，请查看消息详情"
            
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 输入框区域
    st.markdown("<div style='margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-color);'>", unsafe_allow_html=True)
    
    user_input = st.text_input(
        "向风味顾问提问...",
        placeholder=f"例如：我想了解 {cn1} 和 {cn2} 的最佳烹饪方式...",
        key="gemini_input", 
        label_visibility="collapsed")
    
    col_send, col_clear = st.columns([4, 1])
    
    with col_send:
        if st.button("发送给风味顾问 ➤", key="send_btn", use_container_width=True, type="primary"):
            if user_input.strip():
                # 构建完整消息历史
                msg_history = []
                for msg in st.session_state.chat_history:
                    if msg["role"] in ["user", "assistant"] and not msg.get("is_error", False):
                        msg_history.append({"role": msg["role"], "content": msg["content"]})
                msg_history.append({"role": "user", "content": user_input.strip()})
                
                # 添加用户消息到显示
                current_time = datetime.now().strftime("%H:%M")
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_input.strip(),
                    "time": current_time
                })
                st.session_state.last_api_error = None
                
                # 调用 API
                with st.spinner("🤖 AI 思考中..."):
                    success, result, is_rate_limit = call_gemini_with_retry(msg_history, context_str)
                
                # 添加 AI 回复
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": result,
                    "is_error": not success
                })
                
                if not success:
                    st.session_state.last_api_error = "API 调用失败，请查看消息详情"
                
                st.rerun()
    
    with col_clear:
        if st.button("🗑️ 清空对话", key="clear_btn", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.last_api_error = None
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ================================================================
# 11. 主界面
# ================================================================
def main():
    df = load_data()
    if df is None:
        st.error("❌ 找不到 flavordb_data.csv，请放到与 app.py 相同目录。")
        st.stop()

    # Hero 顶栏
    st.markdown("""
    <div class="hero-header">
      <span style="font-size:2.2rem">🧬</span>
      <div>
        <p class="hero-title">味觉虫洞 · Flavor Lab</p>
        <p class="hero-sub">Professional Flavor Pairing Engine · V2.0</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ========== 侧边栏 ==========
    with st.sidebar:
        st.markdown("### 🔬 实验参数")

        # 分类筛选
        all_cats = sorted(df["category"].unique().tolist())
        cat_display = {f"{t_category(c)}（{c}）": c for c in all_cats}
        st.markdown('<div class="sec-label">🗂 按分类筛选</div>', unsafe_allow_html=True)
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
        
        # 渲染 API 状态区域
        render_sidebar_api_status()
        
        st.caption("数据来源：FlavorDB · 分子风味科学")

    # ========== 未选择足够食材：显示欢迎页 ==========
    if len(selected) < 2:
        render_welcome()
        return

    # ========== 数据分析 ==========
    rows = {n: df[df["name"] == n].iloc[0] for n in selected}
    mol_sets = {n: rows[n]["mol_set"] for n in selected}
    n1, n2 = selected[0], selected[1]
    sim = calc_sim(mol_sets[n1], mol_sets[n2])
    cn1, cn2 = t_ingredient(n1), t_ingredient(n2)

    # 构建 Gemini 上下文
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

    # ========== 主内容区 ==========
    col_left, col_right = st.columns([1.35, 1], gap="large")

    # ===== 左栏 =====
    with col_left:
        # 雷达图
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h4>🔭 风味维度雷达图</h4>", unsafe_allow_html=True)
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
                  <span>推荐：油封(Confit)、甘纳许、慕斯基底、乳化酱汁</span>
                </div>""", unsafe_allow_html=True)
            elif pol["type"] == "hydrophilic":
                st.markdown(f"""<div class="diag diag-info">
                  <b>🫗 水溶性主导</b> <span style="color:var(--text-muted)">（水溶 {hp}% / 脂溶 {lp}%）</span><br>
                  <span>推荐：澄清汤(Consommé)、澄清冻、冰沙、真空萃取</span>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="diag diag-res">
                  <b>⚖️ 双亲性平衡</b> <span style="color:var(--text-muted)">（脂溶 {lp}% / 水溶 {hp}%）</span><br>
                  <span>推荐：乳化酱汁、泡沫(Espuma)、真空萃取</span>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ========== 第二行 ==========
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
                ps = min(100, int(bsc*100)); pa = min(100, int(sa*100)); pb = min(100, int(sb*100))
                st.markdown(f"""
                <div class="ing-row">
                  <div style="font-weight:700;color:var(--text-primary)">{bcn}
                    <span style="color:var(--text-muted);font-size:.75rem;font-weight:400"> {bname}</span>
                  </div>
                  <div style="color:var(--text-muted);font-size:.74rem">{bcat_zh} · 连接力 {ps}%</div>
                  <div style="color:var(--text-muted);font-size:.74rem">与{cn1} {pa}% | 与{cn2} {pb}%</div>
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
                  <div style="font-weight:700;font-size:.95rem;color:var(--text-primary)">{cn}</div>
                  <div style="color:var(--text-muted);font-size:.76rem;margin:2px 0">{t_category(row['category'])} · {row['mol_count']} 个风味分子</div>
                  <div style="margin-top:5px">{tags_html(n5, cls)}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ========== AI 对话区 ==========
    api_key = get_api_key()
    render_chat_section(api_key, cn1, cn2, selected, ratios, build_context)

    # 底部统计
    st.markdown(f"""
    <div style="text-align:center;padding:14px;color:var(--text-faint);font-size:.76rem">
      🧬 FlavorDB · {len(df)} 种食材 · 共享分子 {len(sim['shared'])} 个 · Jaccard {int(sim['jaccard']*100)}%
    </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
