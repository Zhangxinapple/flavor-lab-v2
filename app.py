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

def _init_state(key, val):
    if key not in st.session_state:
        st.session_state[key] = val

_init_state("language", "zh")
_init_state("chat_history", [])
_init_state("chat_context_key", "")
_init_state("last_api_error", None)
_init_state("selected_cats", set())
_init_state("vegan_on", True)
_init_state("sidebar_tab", "实验台")
_init_state("show_debug", False)
_init_state("manual_api_key", "")
_init_state("selected_ingredients", [])  # 持久化已选食材，跨标签共享
# ⚠️  关键修复：用两个独立标志控制 AI 请求，避免 rerun 死循环
_init_state("pending_ai_message", None)   # {"content": str} 有消息待发送时非None
_init_state("is_ai_thinking", False)      # AI 正在思考中标志
_init_state("thinking_started_at", None)  # 开始时间戳，超过40秒自动重置
_init_state("selected_groups", set())     # 分类筛选的选中大组

def t(text_en, text_zh=None):
    if st.session_state.language == "zh":
        return text_zh if text_zh else text_en
    return text_en

# ================================================================
# 1. API 配置管理 —— 全面统一为阿里云千问(DashScope)
# ================================================================
DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL   = "qwen-turbo"   # turbo 响应速度比 plus 快 3-5 倍

def get_api_config():
    """
    优先级: 手动输入 > Streamlit Secrets > 环境变量
    统一返回 dashscope 配置，使用 OpenAI 兼容模式调用
    """
    # 1. 手动输入（最高优先级）
    manual = st.session_state.get("manual_api_key", "").strip()
    if manual and len(manual) > 20:
        manual_model = st.session_state.get("manual_model", DEFAULT_MODEL)
        return {"provider": "dashscope", "api_key": manual,
                "model": manual_model, "base_url": DASHSCOPE_BASE}

    # 2. Streamlit Secrets
    try:
        secrets = st.secrets
        key = (secrets.get("DASHSCOPE_API_KEY") or
               secrets.get("QWEN_API_KEY") or "")
        if key:
            return {"provider": "dashscope", "api_key": key,
                    "model": secrets.get("DASHSCOPE_MODEL", DEFAULT_MODEL),
                    "base_url": DASHSCOPE_BASE}
    except Exception:
        pass

    # 3. 环境变量
    key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY", "")
    if key:
        return {"provider": "dashscope", "api_key": key,
                "model": os.getenv("DASHSCOPE_MODEL", DEFAULT_MODEL),
                "base_url": DASHSCOPE_BASE}

    # 4. 本地 config.py
    try:
        import config as _cfg
        key = getattr(_cfg, "DASHSCOPE_API_KEY", "") or getattr(_cfg, "QWEN_API_KEY", "")
        if key:
            return {"provider": "dashscope", "api_key": key,
                    "model": getattr(_cfg, "DASHSCOPE_MODEL", DEFAULT_MODEL),
                    "base_url": DASHSCOPE_BASE}
    except Exception:
        pass

    return None

def check_api_status():
    config = get_api_config()
    if not config:
        return False, None
    if len(config.get("api_key", "")) < 20:
        return False, config
    return True, config

# ================================================================
# 2. AI 调用引擎 —— 统一 OpenAI 兼容接口调用千问
# ================================================================
FLAVOR_GEM_PROMPT = """你是「风味虫洞顾问」，分子美食科学家。基于食材分子结构、味觉互补提供创意风味方案。

【当前实验数据】
{context}

【回复结构（简洁有力，每项2-3句）】
🛰️ 虫洞坐标：两种食材的味觉维度定位
🌀 关联逻辑：分子共鸣或对比碰撞的核心原理
🧪 实验报告：入口→中段→尾韵三段感官曲线
👨‍🍳 厨师应用：2个具体烹饪场景
📊 风味星图：最优比例或关键处理技法

语气专业前卫。结尾提一个延伸探索问题。中文回答，控制在400字内。"""

def call_ai_api(messages, context, max_retries=2):
    """
    统一调用通义千问（DashScope OpenAI兼容模式）
    返回 (success: bool, result: str, is_rate_limit: bool)
    """
    config = get_api_config()
    if not config:
        return (False,
                "❌ **API 未配置**\n\n请在侧边栏「设置」标签中输入阿里云 DashScope API Key。\n\n"
                "[→ 获取免费 Key](https://dashscope.console.aliyun.com/)",
                False)

    try:
        import openai
        import httpx
    except ImportError:
        return False, "❌ 未安装依赖包，请检查 requirements.txt", False

    system_prompt = FLAVOR_GEM_PROMPT.format(context=context)
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    # ⚠️ 问题2修复：设置30秒超时，防止永久卡住
    client = openai.OpenAI(
        api_key=config["api_key"],
        base_url=config.get("base_url", DASHSCOPE_BASE),
        timeout=httpx.Timeout(30.0, connect=10.0)
    )

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=config.get("model", DEFAULT_MODEL),
                messages=api_messages,
                temperature=0.75,
                max_tokens=800   # 控制回复长度，turbo+800token约3-5秒响应
            )
            return True, response.choices[0].message.content, False
        except Exception as e:
            err = str(e)
            if "rate limit" in err.lower() or "429" in err:
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 3)
                    continue
                return False, "⚠️ **请求频率超限**，请等待 30 秒后重试。", True
            elif "overdue" in err.lower() or "good standing" in err.lower() or ("400" in err and "access denied" in err.lower()):
                msg = (
                    "💳 **账户欠费或未开通**\n\n"
                    "错误：Access denied — account not in good standing\n\n"
                    "**解决步骤：**\n"
                    "1. 登录阿里云控制台：https://dashscope.console.aliyun.com/\n"
                    "2. 检查账户余额，充值后服务通常1-2分钟内恢复\n"
                    "3. 确认「模型服务灵积 DashScope」已开通\n\n"
                    "qwen-turbo 约 0.004 元/千 Token，充值10元可用很久"
                )
                return False, msg, False
            elif "invalid api key" in err.lower() or "authentication" in err.lower() or "401" in err:
                return False, "❌ **API Key 无效**，请在设置中重新输入正确的 Key。", False
            elif "timeout" in err.lower() or "timed out" in err.lower():
                return False, "⏱️ **请求超时（30s）**，千问服务器响应慢，请稍后重试。", False
            elif "connection" in err.lower():
                return False, "❌ **网络连接失败**，请检查网络后重试。", False
            else:
                return False, f"⚠️ 调用出错（{err[:300]}）", False

    return False, "❌ 重试次数耗尽，请稍后再试。", False

# ================================================================
# 3. 全局样式
# ================================================================
st.markdown("""
<style>
/* === 浅色模式（默认）=== */
:root {
  --bg-main: #F4F6FA; --bg-sidebar: #FAFBFC; --bg-card: #FFFFFF;
  --border-color: #E8EAED; --text-primary: #111827; --text-second: #374151;
  --text-muted: #6B7280; --text-faint: #9CA3AF;
  --shadow-sm: 0 1px 8px rgba(0,0,0,0.06),0 4px 16px rgba(0,0,0,0.04);
  --diag-res-bg:#F0FDF4; --diag-res-text:#14532d;
  --diag-ctr-bg:#FFF7ED; --diag-ctr-text:#7c2d12;
  --diag-info-bg:#EEF6FF; --diag-info-text:#1e3a8a;
  --diag-warn-bg:#FEF3C7; --diag-warn-text:#78350f;
  --tag-blue-bg:#EEF6FF; --tag-blue-text:#1D6FDB; --tag-blue-border:#BDD7F5;
  --tag-green-bg:#F0FDF4; --tag-green-text:#16A34A; --tag-green-border:#BBF7D0;
  --tag-orange-bg:#FFF7ED; --tag-orange-text:#C2410C; --tag-orange-border:#FECBA1;
  --tag-purple-bg:#F5F3FF; --tag-purple-text:#7C3AED; --tag-purple-border:#DDD6FE;
  --tag-pink-bg:#FDF2F8; --tag-pink-text:#BE185D; --tag-pink-border:#FBCFE8;
  --ing-row-bg:#F9FAFB;
  --ratio-guide-bg:linear-gradient(135deg,#F0F4FF,#F8F0FF);
  --ratio-guide-text:#374151;
  --hot-card-bg:#FFFFFF; --hot-card-border:#E5E7EB;
  --pbar-bg:#E5E7EB;
  --badge-neutral-bg:#F3F4F6; --badge-neutral-text:#374151; --badge-neutral-border:#E5E7EB;
  --chat-error-bg:#FEF2F2; --chat-error-border:#FECACA;
  --onboarding-text:#374151;
}
/* === 深色模式（跟随系统）=== */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-main:#0F1117; --bg-sidebar:#161b22; --bg-card:#1c2128;
    --border-color:#30363d; --text-primary:#e6edf3; --text-second:#cdd9e5;
    --text-muted:#8b949e; --text-faint:#6e7681;
    --shadow-sm:0 1px 8px rgba(0,0,0,0.3),0 4px 16px rgba(0,0,0,0.2);
    --diag-res-bg:#0d2818; --diag-res-text:#4ade80;
    --diag-ctr-bg:#2d1b00; --diag-ctr-text:#fb923c;
    --diag-info-bg:#0d1f3c; --diag-info-text:#60a5fa;
    --diag-warn-bg:#2d2000; --diag-warn-text:#fbbf24;
    --tag-blue-bg:#0d2340; --tag-blue-text:#60a5fa; --tag-blue-border:#1d4ed8;
    --tag-green-bg:#0d2e1a; --tag-green-text:#4ade80; --tag-green-border:#166534;
    --tag-orange-bg:#2d1500; --tag-orange-text:#fb923c; --tag-orange-border:#9a3412;
    --tag-purple-bg:#1e0d40; --tag-purple-text:#a78bfa; --tag-purple-border:#6d28d9;
    --tag-pink-bg:#2d0d1e; --tag-pink-text:#f472b6; --tag-pink-border:#9d174d;
    --ing-row-bg:#22272e;
    --ratio-guide-bg:linear-gradient(135deg,#1a1f3c,#1e1a3c);
    --ratio-guide-text:#cdd9e5;
    --hot-card-bg:#1c2128; --hot-card-border:#30363d;
    --pbar-bg:#30363d;
    --badge-neutral-bg:#22272e; --badge-neutral-text:#cdd9e5; --badge-neutral-border:#30363d;
    --chat-error-bg:#2d0d0d; --chat-error-border:#7f1d1d;
    --onboarding-text:#cdd9e5;
  }
}
/* Streamlit 自身 dark class 兜底 */
[data-theme="dark"] {
  --bg-main:#0F1117!important; --bg-sidebar:#161b22!important; --bg-card:#1c2128!important;
  --border-color:#30363d!important; --text-primary:#e6edf3!important; --text-second:#cdd9e5!important;
  --text-muted:#8b949e!important; --text-faint:#6e7681!important;
  --diag-res-bg:#0d2818!important; --diag-res-text:#4ade80!important;
  --diag-ctr-bg:#2d1b00!important; --diag-ctr-text:#fb923c!important;
  --diag-info-bg:#0d1f3c!important; --diag-info-text:#60a5fa!important;
  --diag-warn-bg:#2d2000!important; --diag-warn-text:#fbbf24!important;
  --tag-blue-bg:#0d2340!important; --tag-blue-text:#60a5fa!important; --tag-blue-border:#1d4ed8!important;
  --tag-green-bg:#0d2e1a!important; --tag-green-text:#4ade80!important; --tag-green-border:#166534!important;
  --tag-orange-bg:#2d1500!important; --tag-orange-text:#fb923c!important; --tag-orange-border:#9a3412!important;
  --tag-purple-bg:#1e0d40!important; --tag-purple-text:#a78bfa!important; --tag-purple-border:#6d28d9!important;
  --tag-pink-bg:#2d0d1e!important; --tag-pink-text:#f472b6!important; --tag-pink-border:#9d174d!important;
  --ing-row-bg:#22272e!important;
  --hot-card-bg:#1c2128!important; --hot-card-border:#30363d!important;
  --pbar-bg:#30363d!important;
  --badge-neutral-bg:#22272e!important; --badge-neutral-text:#cdd9e5!important; --badge-neutral-border:#30363d!important;
  --chat-error-bg:#2d0d0d!important; --chat-error-border:#7f1d1d!important;
  --onboarding-text:#cdd9e5!important; --ratio-guide-text:#cdd9e5!important;
}

.stApp { background: var(--bg-main) !important; color: var(--text-primary) !important; }
[data-testid="stSidebar"] {
  background: var(--bg-sidebar) !important;
  border-right: 1px solid var(--border-color) !important;
}
/* 覆盖 Streamlit 原生文字 */
.stApp p, .stApp li, .stApp span:not([class*="badge"]):not([class*="tag"]) { color: var(--text-primary); }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: var(--text-second) !important; }

/* Hero */
.hero-header {
  background: linear-gradient(135deg,#0A0A1A 0%,#1A1A3E 55%,#0D2137 100%);
  padding: 20px 32px; border-radius: 16px;
  display: flex; align-items: center; justify-content: space-between; gap: 14px;
  box-shadow: 0 6px 28px rgba(0,0,0,0.28);
  border: 1px solid rgba(255,255,255,0.06); margin-bottom: 20px;
}
.hero-left { display: flex; align-items: center; gap: 16px; }
.hero-icon { font-size: 2rem; }
.hero-title {
  font-size: 1.7rem; font-weight: 900;
  background: linear-gradient(90deg,#00D2FF,#7B2FF7,#FF6B6B);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin: 0; line-height: 1.2;
}
.hero-sub { font-size: .68rem; color: rgba(255,255,255,.38) !important; margin: 2px 0 0; letter-spacing: .1em; text-transform: uppercase; }
.hero-badge { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.hero-badge-pill { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.12); border-radius: 20px; padding: 4px 12px; font-size: .68rem; color: rgba(255,255,255,.5) !important; }
.hero-badge-pill b { color: rgba(255,255,255,.8) !important; }

/* 卡片 */
.card {
  background: var(--bg-card); padding: 18px 20px; border-radius: 14px;
  box-shadow: var(--shadow-sm);
  margin-bottom: 14px; border: 1px solid var(--border-color);
}
.card-title { margin: 0 0 12px 0 !important; font-size: .95rem !important; font-weight: 700 !important; color: var(--text-primary) !important; display: flex; align-items: center; gap: 6px; }
.card-dark { background: linear-gradient(135deg,#0A0A1A,#1A1A3E); padding: 20px 24px; border-radius: 14px; box-shadow: 0 4px 20px rgba(0,0,0,.4); margin-bottom: 14px; border: 1px solid rgba(255,255,255,.08); }

/* 标签 */
.tag { display: inline-block; padding: 2px 9px; border-radius: 14px; font-size: .72rem; font-weight: 600; margin: 2px; }
.tag-blue   { background:var(--tag-blue-bg);   color:var(--tag-blue-text)   !important; border:1px solid var(--tag-blue-border); }
.tag-green  { background:var(--tag-green-bg);  color:var(--tag-green-text)  !important; border:1px solid var(--tag-green-border); }
.tag-orange { background:var(--tag-orange-bg); color:var(--tag-orange-text) !important; border:1px solid var(--tag-orange-border); }
.tag-purple { background:var(--tag-purple-bg); color:var(--tag-purple-text) !important; border:1px solid var(--tag-purple-border); }
.tag-pink   { background:var(--tag-pink-bg);   color:var(--tag-pink-text)   !important; border:1px solid var(--tag-pink-border); }
.tag-shared { background:linear-gradient(90deg,var(--tag-blue-bg),var(--tag-purple-bg)); color:var(--tag-purple-text) !important; border:1px solid var(--tag-purple-border); font-weight:700; }

/* 徽章 */
.badge { display:inline-block; padding:4px 14px; border-radius:20px; font-size:.82rem; font-weight:700; }
.badge-resonance { background:#D1FAE5; color:#065F46 !important; }
.badge-contrast  { background:#FEE2E2; color:#991B1B !important; }
.badge-neutral   { background:var(--badge-neutral-bg); color:var(--badge-neutral-text) !important; border:1px solid var(--badge-neutral-border); }

/* 诊断框 */
.diag { border-radius:10px; padding:12px 14px; margin:6px 0; border-left:3px solid; }
.diag-res  { background:var(--diag-res-bg);  border-color:#22C55E; color:var(--diag-res-text); }
.diag-ctr  { background:var(--diag-ctr-bg);  border-color:#F97316; color:var(--diag-ctr-text); }
.diag-info { background:var(--diag-info-bg); border-color:#3B82F6; color:var(--diag-info-text); }
.diag-warn { background:var(--diag-warn-bg); border-color:#F59E0B; color:var(--diag-warn-text); }
.diag b, .diag span { color:inherit !important; }

/* 进度条 */
.pbar-bg  { background:var(--pbar-bg); border-radius:4px; height:5px; overflow:hidden; margin:2px 0; }
.pbar-fill { height:100%; border-radius:4px; }

/* 食材行 */
.ing-row { background:var(--ing-row-bg); border:1px solid var(--border-color); border-radius:10px; padding:10px 14px; margin:5px 0; color:var(--text-primary); }
.ing-row div { color:var(--text-primary) !important; }

/* API 状态 */
.api-status { display: flex; align-items: center; gap: 8px; padding: 9px 13px; border-radius: 10px; font-size: .82rem; margin-bottom: 10px; font-weight: 600; }
.api-status.ready { background: linear-gradient(135deg,#D1FAE5,#ECFDF5); color: #065F46; border: 1px solid #A7F3D0; }
.api-status.error { background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }
.api-status.warning { background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }

/* 聊天气泡 */
.chat-bubble-user {
  background: linear-gradient(135deg,#7B2FF7,#00D2FF); color: #fff !important;
  padding: 10px 16px; border-radius: 18px 18px 4px 18px; margin: 6px 0;
  display: inline-block; max-width: 80%; float: right; clear: both;
  font-size: .9rem; line-height: 1.5;
}
.chat-bubble-ai {
  background: var(--bg-card); color: var(--text-primary) !important;
  border: 1px solid var(--border-color); padding: 10px 16px;
  border-radius: 18px 18px 18px 4px; margin: 6px 0;
  display: inline-block; max-width: 85%; float: left; clear: both;
  font-size: .9rem; line-height: 1.6;
}
.chat-bubble-ai * { color: var(--text-primary) !important; }
.chat-bubble-ai.chat-error { background: var(--chat-error-bg) !important; border-color: var(--chat-error-border) !important; }
.chat-clearfix { clear: both; height: 6px; }
.chat-wrap { max-height: 500px; overflow-y: auto; padding: 12px; background: var(--bg-main); border-radius: 12px; border: 1px solid var(--border-color); margin-bottom: 12px; }
.chat-time { font-size: .68rem; color: var(--text-faint); float: right; clear: both; margin-bottom: 4px; }

/* 工艺 Tooltip */
.technique-wrap { position: relative; display: inline-block; cursor: help; }
.technique-term { color: #a78bfa !important; font-weight: 700; border-bottom: 2px dotted #a78bfa; }
.technique-tooltip {
  visibility: hidden; opacity: 0; background: #1A1A3E; color: #F0F2F8 !important;
  text-align: left; border-radius: 10px; padding: 12px 14px; position: absolute;
  z-index: 9999; bottom: 130%; left: 50%; transform: translateX(-50%);
  width: 280px; font-size: .8rem; line-height: 1.5;
  box-shadow: 0 8px 24px rgba(0,0,0,.5); border: 1px solid rgba(255,255,255,.14);
  transition: opacity .2s, visibility .2s; pointer-events: none;
}
.technique-tooltip * { color: #F0F2F8 !important; }
.technique-tooltip::after { content: ""; position: absolute; top: 100%; left: 50%; transform: translateX(-50%); border: 6px solid transparent; border-top-color: #1A1A3E; }
.technique-wrap:hover .technique-tooltip { visibility: visible; opacity: 1; }

/* 比例引导 */
.ratio-guide { background: var(--ratio-guide-bg); border-radius: 10px; padding: 10px 12px; margin-bottom: 10px; font-size: .77rem; line-height: 1.7; color: var(--ratio-guide-text); border-left: 3px solid #7B2FF7; }
.ratio-guide b { color: #a78bfa !important; }

/* 空状态 */
.hot-experiment-card { background: var(--hot-card-bg); border: 1px solid var(--hot-card-border); border-radius: 12px; padding: 16px; transition: all 0.2s ease; }
.onboarding-step { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 16px; }
.onboarding-step .num {
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, #7B2FF7, #00D2FF);
  color: white; font-size: .75rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.onboarding-step .text { font-size: .85rem; color: var(--onboarding-text); line-height: 1.5; }

/* 移动端适配 */
@media (max-width: 768px) {
  .hero-header { flex-direction: column; padding: 16px 20px; text-align: center; }
  .hero-title { font-size: 1.3rem; }
  .chat-bubble-user, .chat-bubble-ai { max-width: 95% !important; }
  .card { padding: 14px 16px; }
}

#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: .8rem !important; }
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
    return set(x.strip().lower() for x in str(s).split(",") if x.strip())

def _parse_fl(s):
    if not s or str(s).strip() in ("", "nan"): return set()
    return set(x.strip().lower() for x in re.split(r"[@,]+", str(s)) if x.strip())

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
    "butter":"L","cream":"L","creamy":"L","resin":"L","woody":"L",
    "leather":"L","smoky":"L","smoke":"L",
    "sweet":"H","sour":"H","acid":"H","citrus":"H","fruity":"H",
    "floral":"H","honey":"H","alcoholic":"H","wine":"H","vinegar":"H",
    "fresh":"H","green":"H","sugar":"H",
}

def calc_sim(a, b):
    """
    分子共鸣指数 v3 —— 彻底修复虚高问题：
    核心公式：score = Jaccard^0.6 × BiCoverage^0.4 × 97
      - 纯比例运算，无绝对数量项，大集合不再自动加分
      - BiCoverage = min(cov_a, cov_b)，双向严格约束
      - 分数自然分布在 18-97，真实反映重叠程度
    典型值验证：
      Coffee × Cocoa   → Jaccard~0.45 → score~75  (共振)
      Coffee × Strawberry → Jaccard~0.25 → score~52 (平衡)
      Coffee × Grapefruit → Jaccard~0.08 → score~28 (对比)
    """
    if not a or not b:
        return {"score": 0, "jaccard": 0, "shared": [], "only_a": [], "only_b": [], "type": "contrast",
                "detail": {"shared_count": 0, "only_a_count": 0, "only_b_count": 0}}

    inter = a & b
    union = a | b
    only_a = a - b
    only_b = b - a

    j = len(inter) / len(union) if union else 0   # Jaccard 0~1

    # 双向覆盖率：共享分子分别覆盖 A 和 B 各自的比例，取最小值
    # 这是防止"大集合稀释"的关键——双方都必须高覆盖才能高分
    cov_a = len(inter) / max(len(a), 1)
    cov_b = len(inter) / max(len(b), 1)
    bi_cov = min(cov_a, cov_b)  # 严格双向

    # 核心得分：幂次加权组合（纯比例，无绝对数量项）
    # j^0.6 拉伸低段；bi_cov^0.4 对低覆盖惩罚
    raw = (j ** 0.6) * 0.65 + (bi_cov ** 0.4) * 0.35

    # 映射到 18-97 区间
    score = int(round(18 + raw * 79))
    score = max(18, min(97, score))

    # 类型判定（v4：收紧 neutral 区间，让真正的对比组显示红色）
    # 数据实测：典型对比组 Jaccard 在 0.05-0.15 之间
    # 旧阈值 j>=0.10 → neutral 导致大量对比组被误判为黄色
    if score >= 65:
        typ = "resonance"
    elif score >= 42:
        typ = "neutral"
    else:
        typ = "contrast"

    return {
        "score": score,
        "jaccard": j,
        "shared": sorted(inter),
        "only_a": sorted(only_a),
        "only_b": sorted(only_b),
        "type": typ,
        "detail": {
            "shared_count": len(inter),
            "only_a_count": len(only_a),
            "only_b_count": len(only_b),
            "coverage_a": round(cov_a * 100),
            "coverage_b": round(cov_b * 100),
        }
    }

def polarity_analysis(mol_set):
    lipo = sum(1 for m in mol_set if POLARITY.get(m) == "L")
    hydro = sum(1 for m in mol_set if POLARITY.get(m) == "H")
    total = lipo + hydro
    if total == 0: return {"type": "balanced", "lipo": 0, "hydro": 0, "total": 0}
    t2 = "lipophilic" if lipo > hydro else ("hydrophilic" if hydro > lipo else "balanced")
    return {"type": t2, "lipo": lipo, "hydro": hydro, "total": total}

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
        cs = (diff_a + diff_b) / 2
        if cs > 0.3:
            results.append((row["name"], cs, diff_a, diff_b))
    results.sort(key=lambda x: -x[1])
    top = results[:top_n]
    if not top: return []
    max_score = top[0][1]
    return [(name, score/max_score, da, db) for name, score, da, db in top]


# 全球经典风味配对数据库
CLASSIC_RESONANCE_PAIRS = [
    ("Coffee", "Cocoa",       "意式摩卡 — 咖啡与可可共享烘焙苦香，百年意式经典"),
    ("Strawberry","Raspberry","法式果酱 — 莓果家族共振，酯类分子高度重叠"),
    ("Garlic",  "Onion",      "地中海基础香 — 硫化物家族，是无数名菜的风味基石"),
    ("Butter",  "Cream",      "法式奶香 — 脂肪酸链同源，口感绵密如一"),
    ("Lemon",   "Orange",     "柑橘共鸣 — 萜烯类分子高度共享，酸甜叠加"),
    ("Vanilla", "Cinnamon",   "肉桂拿铁 — 醛类香气家族共振，温暖甜蜜"),
    ("Tomato",  "Basil",      "意式经典 — 番茄与罗勒，青草酯香完美共鸣"),
    ("Ginger",  "Cardamom",   "印度香料茶 — 姜科共振，辛香温热"),
]

CLASSIC_CONTRAST_PAIRS = [
    ("dark chocolate","Chili",       "Mole酱灵魂 — 苦甜与辛辣的墨西哥碰撞"),
    ("Strawberry",   "Black pepper", "草莓黑椒 — Heston Blumenthal 名菜，甜与辛的张力"),
    ("Coffee",       "Cardamom",     "中东咖啡 — 烘焙苦香遇上清凉辛香，文化碰撞"),
    ("Honey",        "Garlic",       "蜂蜜大蒜 — 甜腻与辛辣，韩式烧烤秘酱"),
    ("Lemon",        "Garlic",       "地中海鲜 — 酸亮与辛厚的完美对比"),
    ("Vanilla",      "Chili",        "甜辣悖论 — 墨西哥辣椒巧克力的灵感来源"),
    ("Coffee",       "Tomato",       "番茄浓缩咖啡 — 意大利 Espresso 配番茄的鲜苦碰撞"),
    ("Strawberry",   "Balsamic vinegar", "草莓香醋 — 意大利夏日经典，甜酸对比"),
]

# 雷达图维度：参照 SCA 咖啡风味轮 + Le Nez du Vin 葡萄酒香气轮盘
RADAR_DIMS = {
    "甜感": ["sweet","caramel","honey","vanilla","sugar","butterscotch","candy","molasses","toffee"],
    "烘烤": ["roasted","baked","toasted","caramel","coffee","cocoa","bread","malt","smoky","charred"],
    "果香": ["fruity","berry","apple","pear","peach","citrus","tropical","grape","banana","cherry","lemon"],
    "草木": ["herbaceous","herbal","green","mint","thyme","rosemary","basil","dill","leafy","fresh","grassy"],
    "木质": ["woody","wood","cedar","oak","resin","tobacco","leather","earthy","mushroom","pine"],
    "辛香": ["spicy","pepper","cinnamon","ginger","clove","mustard","pungent","horseradish","anise","nutmeg"],
    "花香": ["floral","rose","jasmine","lavender","violet","lily","blossom","jasmin","geranium","orange blossom"],
    "醇厚": ["fatty","creamy","buttery","butter","cream","dairy","milky","nutty","waxy","oily","rich"],
}

# 雷达图维度 tooltip 说明（鼠标悬停显示）
RADAR_TOOLTIPS = {
    "甜感": "SCA风味轮·甜香区 | 焦糖、蜂蜜、香草等甜蜜芳香；来自糖类美拉德反应，是愉悦感的核心维度",
    "烘烤": "SCA风味轮·烘烤区 | 咖啡、可可、面包、麦芽等火焰工艺香气；高温焦糖化与美拉德反应的产物",
    "果香": "SCA风味轮·果香区 | 浆果、苹果、柑橘、热带水果等天然酯类香气；乙酸乙酯家族的感官表达",
    "草木": "SCA风味轮·草本区 | 薄荷、罗勒、青草、新鲜蔬菜的清新气息；源自叶绿素与萜烯类物质",
    "木质": "SCA风味轮·木质区 | 橡木、雪松、泥土、蘑菇的沉稳深度；多酚类与腐殖质分子的表达",
    "辛香": "SCA风味轮·香料区 | 胡椒、肉桂、生姜等刺激性香料；萜烯醛与苯基丙烷类化合物",
    "花香": "SCA风味轮·花香区 | 玫瑰、茉莉、薰衣草的高雅芬芳；萜烯醇如芳樟醇、香叶醇的感官表达",
    "醇厚": "SCA风味轮·质地区 | 奶油、坚果、黄油的圆润质感；长链脂肪酸与内酯类物质形成的口腔质地",
}

def radar_vals(mol_set):
    """
    重构版雷达图算法：
    - 每个维度最多匹配关键词数量不同，需要归一化
    - 引入分级：1-2个关键词=基础(3-4分)，3-4个=中等(5-7分)，5+个=强烈(8-10分)
    - 避免只要有匹配就接近满分的问题
    """
    result = {}
    for dim, kws in RADAR_DIMS.items():
        hit = sum(1 for k in kws if k in mol_set)
        max_kws = len(kws)

        if hit == 0:
            val = 0.0
        elif hit == 1:
            # 仅1个关键词匹配：微弱存在感
            val = 2.5 + random.uniform(-0.3, 0.3)
        elif hit == 2:
            # 2个：有该维度特征
            val = 4.5 + random.uniform(-0.5, 0.5)
        elif hit <= 4:
            # 3-4个：明显特征
            val = 5.5 + (hit - 2) * 1.0 + random.uniform(-0.3, 0.3)
        else:
            # 5+个：强烈特征，但要根据该维度总词数归一化
            ratio = hit / max_kws
            val = 7.0 + ratio * 3.0

        result[dim] = round(min(10.0, max(0.0, val)), 1)
    return result

# ================================================================
# 7. 工艺术语 Tooltip
# ================================================================
TECHNIQUES = {
    "低温慢煮": {"en": "Sous Vide", "desc": "将食材密封后放入恒温水浴（55-85°C）长时间烹饪。精确控温，最大程度锁住水分和芳香分子。"},
    "乳化": {"en": "Emulsification", "desc": "将两种不相溶的液体（如油和水）通过乳化剂稳定结合，同时呈现脂溶性和水溶性风味分子。"},
    "真空萃取": {"en": "Vacuum Extraction", "desc": "利用负压降低液体沸点，在低温下完成萃取。保留热敏感香气，萃取效率比常压高 3-5 倍。"},
    "发酵": {"en": "Fermentation", "desc": "微生物分解糖类产生醇类、酸类和酯类，创造全新的复合风味。"},
    "烟熏": {"en": "Smoking", "desc": "木材不完全燃烧产生的烟雾渗入食材表面，形成独特的焦木香气。"},
    "冷冻干燥": {"en": "Freeze Drying", "desc": "在超低温下将水分直接升华，保留 95% 以上的芳香分子。"},
    "浓缩收汁": {"en": "Reduction", "desc": "通过持续加热蒸发水分，将液体浓缩，使风味分子浓度大幅提升。"},
    "凝胶化": {"en": "Gelification", "desc": "使用明胶、琼脂等将液体凝固成半固态，使风味在口腔中缓慢释放。"},
    "Espuma": {"en": "Espuma / 泡沫技术", "desc": "使用奶油枪将液体充入氮气形成轻盈泡沫，增强嗅觉感知。"},
    "Confit": {"en": "Confit / 油封", "desc": "将食材浸没在油脂中以低温长时间加热，脂溶性芳香分子充分融入油脂。"},
    "Consommé": {"en": "Consommé / 澄清汤", "desc": "使用蛋白质澄清技术去除杂质，得到透明清澈的浓缩高汤。"},
    "乳化酱汁": {"en": "Emulsion Sauce", "desc": "通过乳化作用将油脂分散在水相中，同时呈现脂溶和水溶风味的双重层次。"},
    "甘纳许": {"en": "Ganache", "desc": "巧克力与奶油的乳化物，使脂溶性可可芳香与水溶性奶香完美融合。"},
}

def tech_tip(term):
    info = TECHNIQUES.get(term)
    if not info:
        return f"<b>{term}</b>"
    return (f'<span class="technique-wrap"><span class="technique-term">{term}</span>'
            f'<span class="technique-tooltip"><b style="color:#00D2FF">{term} · {info["en"]}</b>'
            f'<br><br>{info["desc"]}</span></span>')

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
    highlight_terms = ["🛰️ 虫洞坐标", "🌀 关联逻辑", "🧪 实验报告", "👨‍🍳 厨师应用", "📊 风味星图"]
    for term in highlight_terms:
        text = text.replace(term,
            f'<span style="background: linear-gradient(90deg, #7B2FF7, #00D2FF); '
            f'-webkit-background-clip: text; -webkit-text-fill-color: transparent; '
            f'font-weight: 700;">{term}</span>')
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" style="color:#7B2FF7">\1</a>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?m)^[\-·]\s+(.+)$', r'<div style="padding:2px 0 2px 12px">• \1</div>', text)
    text = text.replace("\n", "<br>")
    return text


# ================================================================
# 9. AI 对话区 ——  关键重构：彻底解决"无限发送"问题
#
# 原因分析：
#   旧代码用 quick_question_clicked 标志 + st.rerun() 触发AI请求。
#   但 rerun 后 chat_section 再次渲染，发现标志非空，再次触发…死循环。
#
# 修复方案：
#   • pending_ai_message: 仅存储"待发送内容"，发送完立即置None
#   • is_ai_thinking: 标志AI正在处理，渲染时显示loading，不重复触发
#   • AI请求与消息记录在同一次执行中完成（非rerun），然后再rerun刷新UI
# ================================================================
def _do_ai_request(user_content, context_str):
    """执行实际 AI 请求，更新 chat_history，清理状态"""
    current_time = datetime.now().strftime("%H:%M")

    # 构建发送给 AI 的历史（只含正常消息，排除错误消息）
    msg_history = []
    for msg in st.session_state.chat_history:
        if msg["role"] in ["user", "assistant"] and not msg.get("is_error", False):
            msg_history.append({"role": msg["role"], "content": msg["content"]})
    msg_history.append({"role": "user", "content": user_content})

    # 记录用户消息
    st.session_state.chat_history.append({
        "role": "user", "content": user_content, "time": current_time
    })
    st.session_state.last_api_error = None

    # 调用 AI
    success, result, is_rate_limit = call_ai_api(msg_history, context_str)

    # 记录 AI 回复
    st.session_state.chat_history.append({
        "role": "assistant", "content": result, "is_error": not success
    })

    if not success:
        st.session_state.last_api_error = "频率限制，请稍后重试" if is_rate_limit else "API 调用失败"

    # 注意：is_ai_thinking / pending 由调用方（render_chat_section）统一管理，此处不重置


def render_chat_section(api_config, cn1, cn2, selected, ratios, sim, mol_sets, df):
    st.markdown("---")
    st.markdown(
        f'<div class="card"><h4 class="card-title">🤖 风味虫洞顾问 '
        f'<span style="font-size:.75rem;color:var(--text-muted);font-weight:400">· 基于 {cn1} × {cn2}</span></h4>',
        unsafe_allow_html=True
    )

    if not api_config:
        st.markdown("""
        <div class="diag diag-info">
          <b>🔑 AI 顾问未激活</b><br><br>
          请在侧边栏「设置」标签中配置阿里云 DashScope API Key：<br><br>
          <b>方法一：在设置中直接粘贴 Key</b>（最简单）<br><br>
          <b>方法二：Streamlit Cloud 部署</b><br>
          在 Secrets 中添加：<code>DASHSCOPE_API_KEY = "sk-..."</code><br><br>
          <a href="https://dashscope.console.aliyun.com/" target="_blank" style="color:#7B2FF7">
            → 免费获取千问 API Key（每月百万 Token 免费额度）
          </a>
        </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    model = api_config.get("model", DEFAULT_MODEL)
    st.markdown(
        f'<div class="api-status ready"><span>✅</span>'
        f'<span>通义千问已连接 · {model}</span></div>',
        unsafe_allow_html=True
    )

    # ── 构建上下文 ──
    def build_context():
        lines = [f"## 当前实验食材组合"]
        lines.append(f"选择食材：{' + '.join(t_ingredient(n) for n in selected)}")
        lines.append(f"\n## 分子共鸣分析")
        lines.append(f"共鸣指数：{sim['score']}%")
        lines.append(f"共鸣类型：{'同源共振' if sim['type']=='resonance' else '对比碰撞' if sim['type']=='contrast' else '平衡搭档'}")
        lines.append(f"共享分子数：{len(sim['shared'])} 个")
        lines.append(f"\n## 各食材详情")
        for n in selected:
            pct = int(ratios.get(n, 1/len(selected))*100)
            top5 = t_notes_list(mol_sets[n], 5)
            lines.append(f"- **{t_ingredient(n)}**（{pct}%）：{', '.join(top5)}")
        if sim["shared"]:
            lines.append(f"\n## 共享风味分子（前8）")
            lines.append(", ".join(t_note(x) for x in sim["shared"][:8]))
        return "\n".join(lines)

    context_str = build_context()

    # ── 食材变化时重置对话 ──
    current_key = "+".join(sorted(selected))
    if st.session_state.chat_context_key != current_key:
        st.session_state.chat_history = []
        st.session_state.chat_context_key = current_key
        st.session_state.last_api_error = None
        st.session_state.pending_ai_message = None
        st.session_state.is_ai_thinking = False

    # ── AI 请求状态机（唯一处理点，防止任何重复）──
    # 规则：pending非空 且 未在思考中 → 执行一次，执行完清除锁，rerun
    # 注意：绝对不能有任何其他地方修改 is_ai_thinking 或 pending_ai_message
    pending = st.session_state.get("pending_ai_message")
    thinking = st.session_state.get("is_ai_thinking", False)
    ts = st.session_state.get("thinking_started_at")

    # 检测僵死：有锁但超过60秒 → 强制解锁
    if thinking and ts and (time.time() - ts) > 60:
        st.session_state.is_ai_thinking = False
        st.session_state.thinking_started_at = None
        st.session_state.pending_ai_message = None
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "⏱️ **请求超时（60秒）** — 千问响应过慢。请重试，或在设置中确认使用 qwen-turbo。",
            "is_error": True
        })
        st.rerun()

    # 正常触发：有 pending 且无锁
    elif pending and not thinking:
        msg_content = pending["content"]
        st.session_state.pending_ai_message = None   # 先清 pending
        st.session_state.is_ai_thinking = True        # 再加锁
        st.session_state.thinking_started_at = time.time()
        with st.spinner("🧬 风味顾问思考中..."):
            _do_ai_request(msg_content, context_str)
        st.session_state.is_ai_thinking = False       # 解锁
        st.session_state.thinking_started_at = None
        st.rerun()

    # ── 渲染历史消息 ──
    if st.session_state.chat_history:
        chat_html = '<div class="chat-wrap">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f'<div class="chat-bubble-user">{msg["content"]}</div>'
                chat_html += f'<div class="chat-time">{msg.get("time", "")}</div>'
                chat_html += '<div class="chat-clearfix"></div>'
            else:
                is_error = msg.get("is_error", False)
                cls = "chat-bubble-ai chat-error" if is_error else "chat-bubble-ai"
                content = md_to_html(msg["content"])
                chat_html += f'<div class="{cls}">{content}</div>'
                chat_html += '<div class="chat-clearfix"></div>'
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        type_hints = {
            "resonance": f"它们共享大量芳香分子，属于「**同源共振**」型搭配，适合叠加增强。",
            "contrast": f"它们风味差异显著，属于「**对比碰撞**」型搭配，高明的厨师会用这种张力创造层次感。",
            "neutral": f"它们适度交叠互补，属于「**平衡搭档**」型搭配，比例调整是关键。",
        }
        hint_text = type_hints.get(sim["type"], "")
        st.markdown(f"""
        <div class="diag diag-res" style="margin-bottom:12px">
          <b style="font-size:1rem">🧬 关于 {cn1} × {cn2} 这个搭配</b><br><br>
          <span>{hint_text}</span><br><br>
          <span style="color:var(--text-muted);font-size:.85rem">
            💬 你可以问：<br>
            · 为什么 {cn1} 适合作为主食材？<br>
            · 用 {cn1} + {cn2} 设计一道完整菜谱<br>
            · 当前比例是最优的吗？
          </span>
        </div>""", unsafe_allow_html=True)

    # ── 上次错误提示 ──
    if st.session_state.last_api_error:
        st.markdown(
            f'<div class="diag diag-warn"><b>⚠️ 上次请求遇到问题</b><br>'
            f'<span>{st.session_state.last_api_error}</span></div>',
            unsafe_allow_html=True
        )
        if st.button("🔄 重试", key="retry_btn"):
            # 找最后一条用户消息重试
            for msg in reversed(st.session_state.chat_history):
                if msg["role"] == "user":
                    # 移除之前的错误回复
                    st.session_state.chat_history = [
                        m for m in st.session_state.chat_history
                        if not (m["role"] == "assistant" and m.get("is_error", False))
                    ]
                    # 移除最后一条用户消息（会在_do_ai_request中重新添加）
                    st.session_state.chat_history = st.session_state.chat_history[:-1]
                    st.session_state.last_api_error = None
                    st.session_state.pending_ai_message = {"content": msg["content"]}
                    st.rerun()
                    break

    # ── 快捷问题按钮（⚠️ 只设置 pending，不直接调用 AI）──
    st.markdown("<div style='margin: 16px 0 8px;font-size:.85rem;color:var(--text-muted);'>💡 快捷问题：</div>",
                unsafe_allow_html=True)
    n1, n2 = selected[0], selected[1]
    quick_qs = [
        f"为什么 {cn1} 适合作为主食材？换成其他食材会怎样？",
        f"用 {cn1} + {cn2} 设计一道完整菜谱",
        f"当前 {int(ratios.get(n1, 0.5)*100)}:{int(ratios.get(n2, 0.5)*100)} 的比例是最优的吗？",
    ]
    qcols = st.columns(3)
    for qi, q in enumerate(quick_qs):
        btn_key = f"qbtn_{qi}"
        # ⚠️ 防重复：如果已有 pending 或正在思考，完全禁用按钮
        already_pending = (
            st.session_state.is_ai_thinking or
            st.session_state.pending_ai_message is not None
        )
        if qcols[qi].button(q, key=btn_key, use_container_width=True, disabled=already_pending):
            # 二次检查：只有当前没有任何待处理消息才设置
            if not st.session_state.pending_ai_message and not st.session_state.is_ai_thinking:
                st.session_state.pending_ai_message = {"content": q}
                st.rerun()

    # ── 文本输入 + 发送 ──
    st.markdown("<div style='margin-top:16px;padding-top:16px;border-top:1px solid var(--border-color);'>",
                unsafe_allow_html=True)

    user_input = st.text_input(
        "向风味顾问提问...",
        placeholder=f"例如：我想了解 {cn1} 和 {cn2} 的最佳烹饪方式...",
        key="chat_input",
        label_visibility="collapsed",
        disabled=st.session_state.is_ai_thinking
    )

    col_send, col_clear = st.columns([4, 1])
    with col_send:
        send_clicked = st.button(
            "发送给风味顾问 ➤", key="send_btn",
            use_container_width=True, type="primary",
            disabled=st.session_state.is_ai_thinking
        )
        if send_clicked and user_input.strip():
            # 防重复：只有没有待处理消息时才设置
            if not st.session_state.pending_ai_message and not st.session_state.is_ai_thinking:
                st.session_state.pending_ai_message = {"content": user_input.strip()}
                st.rerun()

    with col_clear:
        if st.button("🗑️ 清空", key="clear_btn", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.last_api_error = None
            st.session_state.pending_ai_message = None
            st.session_state.is_ai_thinking = False
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ================================================================
# 10. 主界面
# ================================================================
def render_sidebar_tabs(df):
    tabs = ["实验台", "配方台", "设置"]
    selected_tab = st.radio(
        "标签",
        tabs,
        index=tabs.index(st.session_state.sidebar_tab),
        label_visibility="collapsed",
        key="sidebar_tab_radio",
        horizontal=True
    )
    if selected_tab != st.session_state.sidebar_tab:
        st.session_state.sidebar_tab = selected_tab
        st.rerun()

    # 问题4：标签使用引导
    tab_guides = {
        "实验台": "🧪 **实验台** — 选择 2-4 种食材，右侧实时呈现分子共鸣分析、雷达图和 AI 顾问",
        "配方台": "⚖️ **配方台** — 拖动滑块调整各食材比例，雷达图面积随比例实时变化",
        "设置":   "🔑 **设置** — 填入千问 API Key 以启用 AI 风味顾问对话功能",
    }
    st.caption(tab_guides[selected_tab])
    st.markdown("---")
    return selected_tab

def render_experiment_tab(df):
    ANIMAL_KW = ["meat","dairy","fish","seafood","pork","beef","chicken","egg","alcohol"]

    is_vegan = st.toggle("🌿 仅植物基 Vegan", value=st.session_state.vegan_on, key="vegan_toggle")
    st.session_state.vegan_on = is_vegan

    # ── Vegan 过滤（先过滤数据，再建分类列表）──
    # 扩展动物性关键词，修复"香肠出现在Vegan"的问题
    ANIMAL_CATS = {"meat","dairy","fish","seafood","pork","beef","chicken","egg",
                   "alcohol","poultry","shellfish","sausage","ham","bacon",
                   "lamb","veal","duck","turkey","anchovy","lard","gelatin"}
    if is_vegan:
        df_base = df[~df["category"].str.lower().apply(
            lambda c: any(kw in c.lower() for kw in ANIMAL_CATS))]
    else:
        df_base = df

    # ── 分类按钮组（替代 multiselect）──
    all_cats = sorted(df_base["category"].unique().tolist())
    # 对分类做大众友好的分组映射
    CAT_GROUP = {
        "🌾 谷物淀粉": ["cereal","grain","flour","starch","bread","rice","wheat","corn","oat"],
        "🫑 蔬菜": ["vegetable","veggie","root","tuber","onion","garlic","pepper","cabbage","bean","legume","pea"],
        "🍎 水果": ["fruit","berry","citrus","tropical","melon","stone fruit","apple","banana"],
        "🌿 香草香料": ["herb","spice","seed","bark","leaf","seasoning","flavoring"],
        "🍄 菌菇": ["mushroom","fungus","truffle","fungi"],
        "☕ 饮品原料": ["beverage","coffee","tea","cocoa","chocolate","cacao"],
        "🧈 油脂坚果": ["nut","oil","fat","seed oil","butter"],
        "🐟 海鲜水产": ["fish","seafood","shellfish","shrimp","crab","lobster","anchovy"],
        "🥩 肉类蛋奶": ["meat","poultry","dairy","egg","cheese","milk","beef","pork","chicken","lamb"],
        "🧪 发酵腌制": ["fermented","pickled","vinegar","wine","beer","miso","sauce"],
        "🍬 甜味调料": ["sugar","sweet","syrup","jam","candy","confectionery"],
        "🌊 其他": [],
    }

    def get_group(cat):
        cat_l = cat.lower()
        for group, kws in CAT_GROUP.items():
            if any(kw in cat_l for kw in kws):
                return group
        return "🌊 其他"

    # 按大组聚合分类
    cat_to_group = {c: get_group(c) for c in all_cats}
    groups_present = sorted(set(cat_to_group.values()))

    st.markdown('<div style="font-size:.82rem;color:var(--text-muted);margin-bottom:6px">🗂 按大类筛选（可多选）</div>', unsafe_allow_html=True)
    
    selected_groups = st.session_state.get("selected_groups", set())
    # 清除已不存在的分类
    selected_groups = selected_groups & set(groups_present)
    
    # 渲染分类按钮（用 checkbox 模拟按钮组）
    btn_cols = st.columns(3)
    new_groups = set()
    for gi, grp in enumerate(groups_present):
        checked = grp in selected_groups
        with btn_cols[gi % 3]:
            if st.checkbox(grp, value=checked, key=f"grp_{gi}"):
                new_groups.add(grp)
    
    if new_groups != selected_groups:
        st.session_state["selected_groups"] = new_groups
        st.rerun()

    # 根据选中的大组确定显示的食材
    if new_groups:
        selected_raw_cats = {c for c, g in cat_to_group.items() if g in new_groups}
        df_show = df_base[df_base["category"].isin(selected_raw_cats)]
    else:
        df_show = df_base

    search_query = st.text_input("🔍 搜索食材", key="search_box", placeholder="输入名称...")
    if search_query.strip():
        q = search_query.lower()
        mask = df_show["name"].str.lower().str.contains(q, na=False)
        for idx, row in df_show.iterrows():
            if q in t_ingredient(row["name"]).lower():
                mask.loc[idx] = True
        df_show = df_show[mask]

    col_count = st.columns([1])[0]
    with col_count:
        st.markdown(f'<div style="text-align:right;font-size:.82rem;color:var(--text-muted);padding-top:4px">{len(df_show)} 种食材可选</div>',
                    unsafe_allow_html=True)

    st.markdown("**🎲 随机探索**")
    rand_col1, rand_col2 = st.columns(2, gap="small")

    avail_set_lower = {n.lower(): n for n in df_show["name"].values}

    def try_classic(pairs):
        """从经典配对中找到数据库有的一组"""
        for a, b, desc in pairs:
            ra = avail_set_lower.get(a.lower())
            rb = avail_set_lower.get(b.lower())
            if ra and rb:
                return ra, rb, desc
        return None

    with rand_col1:
        if st.button("🟢 经典共振搭配", key="random_resonance", use_container_width=True):
            pair = try_classic(CLASSIC_RESONANCE_PAIRS)
            picked = [pair[0], pair[1]] if pair else (random.sample(sorted(df_show["name"].unique().tolist()), 2) if len(df_show) >= 2 else [])
            if picked:
                st.session_state["_force_defaults"] = picked
                st.session_state["selected_ingredients"] = picked
                st.session_state["_random_desc"] = f"🟢 {pair[2]}" if pair else ""
            st.rerun()

    with rand_col2:
        if st.button("🔴 经典对比碰撞", key="random_contrast", use_container_width=True):
            pair = try_classic(CLASSIC_CONTRAST_PAIRS)
            picked = [pair[0], pair[1]] if pair else (random.sample(sorted(df_show["name"].unique().tolist()), 2) if len(df_show) >= 2 else [])
            if picked:
                st.session_state["_force_defaults"] = picked
                st.session_state["selected_ingredients"] = picked
                st.session_state["_random_desc"] = f"🔴 {pair[2]}" if pair else ""
            st.rerun()

    # 显示经典配对的描述
    if st.session_state.get("_random_desc"):
        st.caption(st.session_state["_random_desc"])

    options = sorted(df_show["name"].unique().tolist())
    options_set = set(options)

    # 优先级：_force_defaults(随机/示例) > selected_ingredients(持久化) > 空
    force = st.session_state.pop("_force_defaults", None)
    st.session_state.pop("random_selection", None)        # 兼容旧代码，清除避免干扰
    st.session_state.pop("_pending_ingredient_list", None)

    if force:
        defaults = [n for n in force if n in options_set]
    else:
        defaults = [n for n in st.session_state.get("selected_ingredients", []) if n in options_set]

    selected = st.multiselect(
        "选择食材（2-4种）", options=options, default=defaults,
        format_func=display_name, help="最多支持4种食材同时分析",
        key="ing_select"
    )
    # 同步到持久化 state，让配方台/设置等其他标签能读到
    if selected:
        st.session_state["selected_ingredients"] = selected
    return selected

def render_formula_tab(selected):
    ratios = {}
    if len(selected) >= 2:
        st.markdown("""
        <div class="ratio-guide">
        <b>💡 比例设计思路</b><br>
        · <b>主风味（≥50%）</b>：设定核心香气基调<br>
        · <b>副风味（25-40%）</b>：丰富层次<br>
        · <b>提味（≤15%）</b>：点睛之笔
        </div>""", unsafe_allow_html=True)

        raw_total = 0
        for name in selected:
            pct_now = int(100 // len(selected))
            ratios[name] = st.slider(t_ingredient(name), 0, 100, pct_now, 5, key=f"r_{name}")
            raw_total += ratios[name]

        if raw_total > 0:
            ratios = {k: v/raw_total for k, v in ratios.items()}

        st.markdown("<div style='margin-top:12px;padding:10px;background:#F8FAFC;border-radius:8px;'>",
                    unsafe_allow_html=True)
        st.markdown("<div style='font-size:.78rem;color:var(--text-muted);margin-bottom:6px;'>当前比例：</div>",
                    unsafe_allow_html=True)
        for name in selected:
            pct = int(ratios.get(name, 1/len(selected))*100)
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:8px;margin:4px 0;'>"
                f"<div style='width:80px;font-size:.8rem;'>{t_ingredient(name)}</div>"
                f"<div style='flex:1;height:6px;background:#E5E7EB;border-radius:3px;'>"
                f"<div style='width:{pct}%;height:100%;background:linear-gradient(90deg,#00D2FF,#7B2FF7);border-radius:3px;'></div>"
                f"</div><div style='width:40px;text-align:right;font-size:.75rem;'>{pct}%</div></div>",
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("请选择至少2种食材以调整配方比例")
    return ratios

def render_settings_tab():
    st.markdown("### 🔑 API 配置")
    st.markdown("**通义千问（阿里云 DashScope）**")
    st.caption("每月赠送百万 Token 免费额度，适合商业化运营")

    manual_key = st.text_input(
        "粘贴你的 DashScope Key",
        value=st.session_state.get("manual_api_key", ""),
        type="password",
        placeholder="sk-xxxxxxxxxxxxxxxxx",
        key="manual_key_input",
        help="从 dashscope.console.aliyun.com 获取"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 保存 Key", key="save_key_btn", use_container_width=True):
            if manual_key and len(manual_key) > 20:
                st.session_state.manual_api_key = manual_key
                st.success("✅ 已保存")
                st.rerun()
            else:
                st.error("Key 格式不正确")
    with col2:
        if st.session_state.get("manual_api_key") and st.button("🗑 清除 Key", key="clear_key_btn", use_container_width=True):
            st.session_state.manual_api_key = ""
            st.rerun()

    st.caption("Key 仅保存在当前会话，关闭页面后自动清除")

    # ── 模型速度选择 ──
    st.markdown("---")
    st.markdown("**⚡ 模型速度**")
    model_options = {
        "🚀 qwen-turbo — 最快（3-8秒）推荐": "qwen-turbo",
        "⚖️ qwen-plus  — 均衡（10-20秒）":   "qwen-plus",
        "🧠 qwen-max   — 最强（20-40秒）":    "qwen-max",
    }
    current_model = st.session_state.get("manual_model", DEFAULT_MODEL)
    current_label = next((k for k,v in model_options.items() if v == current_model),
                         list(model_options.keys())[0])
    selected_label = st.radio(
        "选择模型", list(model_options.keys()),
        index=list(model_options.keys()).index(current_label),
        key="model_radio", label_visibility="collapsed"
    )
    new_model = model_options[selected_label]
    if new_model != st.session_state.get("manual_model"):
        st.session_state.manual_model = new_model
        st.warning("⚠️ 最多支持4种食材")
        st.rerun()

    st.caption("Secrets 中的 DASHSCOPE_MODEL 会覆盖此选择。如仍然很慢，请检查 Secrets 设置。")

    # 连接状态
    st.markdown("---")
    st.markdown("**📡 连接状态**")
    api_ok, api_config = check_api_status()

    if api_ok:
        model = api_config.get("model", DEFAULT_MODEL)
        speed_tip = {"qwen-turbo": "⚡ 极速", "qwen-plus": "⚖️ 均衡", "qwen-max": "🧠 最强"}.get(model, "")
        st.markdown(
            f'<div class="api-status ready"><span>✅</span>'
            f'<span>通义千问已连接 · {model} {speed_tip}</span></div>',
            unsafe_allow_html=True
        )
        if model == "qwen-max":
            st.warning("⚠️ 当前使用 qwen-max，响应较慢（20-40秒）。建议切换为 qwen-turbo 以获得最快响应。")
        st.caption("Key 格式正确。发送一条消息即可验证连通性。")
    elif api_config:
        st.markdown('<div class="api-status warning"><span>⚠️</span><span>Key 格式异常</span></div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="api-status error"><span>❌</span><span>未配置 Key</span></div>',
                    unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("🛠 部署说明（Streamlit Cloud）"):
        st.markdown("""
**在 Streamlit Cloud Secrets 中添加：**
```toml
DASHSCOPE_API_KEY = "sk-你的key"
DASHSCOPE_MODEL = "qwen-turbo"
```
⚠️ Secrets 中的模型设置会**覆盖**界面中的选择，建议设为 `qwen-turbo`

**获取 Key：** https://dashscope.console.aliyun.com/
        """)

def render_empty_state(df):
    st.markdown("""
    <div class="card" style="text-align:center;padding:36px 30px 28px">
      <div style="font-size:3rem;margin-bottom:12px">🧬</div>
      <h2 style="margin-bottom:8px;font-size:1.4rem;color:var(--text-primary)">味觉虫洞 · Flavor Lab</h2>
      <p style="color:var(--text-muted);font-size:.9rem;line-height:1.7;max-width:480px;margin:0 auto">
        基于 FlavorDB 分子数据库，探索食材之间的「分子共鸣」
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='card'><h4 class='card-title'>🚀 三步开始实验</h4>", unsafe_allow_html=True)
    st.markdown("""
    <div class="onboarding-step">
      <div class="num">1</div>
      <div class="text"><b>左侧实验台</b> 选择 2-4 种食材（或点下方示例快速开始）</div>
    </div>
    <div class="onboarding-step">
      <div class="num">2</div>
      <div class="text"><b>查看分析结果</b> 雷达图 · 分子共鸣指数 · 风味指纹 · 网络图</div>
    </div>
    <div class="onboarding-step">
      <div class="num">3</div>
      <div class="text"><b>咨询 AI 顾问</b> 在「设置」中填入千问 Key，解锁专业风味建议</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 共鸣指数说明卡片
    st.markdown("<div class='card'><h4 class='card-title'>🔬 读懂「分子共鸣指数」</h4>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:8px">
      <div style="background:linear-gradient(135deg,#0d2818,#0a3020);border-left:4px solid #22C55E;border-radius:10px;padding:14px">
        <div style="font-size:1.3rem;font-weight:900;color:#4ade80">73–97</div>
        <div style="font-size:.78rem;color:#4ade80;font-weight:700;margin:3px 0 6px">🟢 同源共振</div>
        <div style="font-size:.73rem;color:rgba(255,255,255,.6);line-height:1.55">
          大量共享香气分子，组合后风味<b style="color:#4ade80">叠加放大</b>，余韵绵长。适合主从搭配，以一种强化另一种。
          <br><br><i style="opacity:.65">例：咖啡 × 可可、草莓 × 覆盆子</i>
        </div>
      </div>
      <div style="background:linear-gradient(135deg,#1a1f2e,#1e2438);border-left:4px solid #F97316;border-radius:10px;padding:14px">
        <div style="font-size:1.3rem;font-weight:900;color:#fb923c">46–72</div>
        <div style="font-size:.78rem;color:#fb923c;font-weight:700;margin:3px 0 6px">🟡 平衡搭档</div>
        <div style="font-size:.73rem;color:rgba(255,255,255,.6);line-height:1.55">
          有交叠也有差异，最容易创造<b style="color:#fb923c">「1+1>2」</b>的复合香气。比例调整空间大，是最丰富的创作区间。
          <br><br><i style="opacity:.65">例：咖啡 × 草莓、番茄 × 罗勒</i>
        </div>
      </div>
      <div style="background:linear-gradient(135deg,#2d0d0d,#1a0808);border-left:4px solid #EF4444;border-radius:10px;padding:14px">
        <div style="font-size:1.3rem;font-weight:900;color:#f87171">18–45</div>
        <div style="font-size:.78rem;color:#f87171;font-weight:700;margin:3px 0 6px">🔴 对比碰撞</div>
        <div style="font-size:.73rem;color:rgba(255,255,255,.6);line-height:1.55">
          分子差异显著，产生强烈<b style="color:#f87171">对比张力</b>。少量点缀可创造惊喜，高手用它制造「味觉转折」。
          <br><br><i style="opacity:.65">例：黑巧克力 × 辣椒、蓝纹奶酪 × 蜂蜜</i>
        </div>
      </div>
    </div>
    <div style="font-size:.72rem;color:var(--text-faint);text-align:center;padding-top:4px">
      💡 基于 Jaccard 相似系数 × 双向覆盖率 × 差异惩罚因子计算，真实反映分子重叠程度
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── 三个示例卡片（共振 / 平衡 / 对比）──
    st.markdown("<div class='card'><h4 class='card-title'>✨ 选择一个示例开始体验</h4>", unsafe_allow_html=True)
    st.markdown('<p style="font-size:.82rem;color:var(--text-muted);margin-bottom:16px">三种搭配逻辑——点击卡片，立刻看到分子分析结果，亲身感受分数的含义</p>', unsafe_allow_html=True)

    # 用不区分大小写的匹配，确保食材名正确找到
    available_lower = {n.lower(): n for n in df["name"].values}
    def find_pair(candidates):
        for a, b in candidates:
            ra = available_lower.get(a.lower())
            rb = available_lower.get(b.lower())
            if ra and rb:
                return ra, rb
        return None

    # 候选列表：多备选确保能命中数据库中的真实食材名
    resonance_candidates = [
        ("Coffee","Cocoa"),("Coffee","dark chocolate"),
        ("Strawberry","Raspberry"),("Strawberry","Peach"),
        ("Lemon","Orange"),("Garlic","Onion"),
        ("Butter","Cream"),("Vanilla","Cinnamon"),
        ("Tomato","Garlic"),("Ginger","Cinnamon"),
    ]
    balance_candidates = [
        ("Coffee","Strawberry"),("Tomato","Strawberry"),
        ("Coffee","Lemon"),("Coffee","Cardamom"),
        ("Lemon","Strawberry"),("Vanilla","Strawberry"),
        ("Garlic","Tomato"),("Coffee","Vanilla"),
        ("Strawberry","Chocolate"),("Tomato","Basil"),
    ]
    contrast_candidates = [
        ("dark chocolate","Chili"),("Strawberry","Black pepper"),
        ("Coffee","Chili"),("Tomato","Vanilla"),
        ("Garlic","Strawberry"),("Coffee","Garlic"),
        ("Lemon","Garlic"),("Strawberry","Garlic"),
        ("Chili","Vanilla"),("Coffee","Black pepper"),
    ]

    res_pair = find_pair(resonance_candidates)
    bal_pair = find_pair(balance_candidates)
    ctr_pair = find_pair(contrast_candidates)

    col_res, col_bal, col_ctr = st.columns(3, gap="medium")

    def demo_card(col, pair, style, label_color, bg, border, grad, btn_key, icon, label, desc):
        with col:
            if pair:
                pa, pb = pair
                cna, cnb = t_ingredient(pa), t_ingredient(pb)
            else:
                cna, cnb = "—", "—"
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {border};border-radius:14px;
              padding:16px;text-align:center;min-height:148px;margin-bottom:8px">
              <div style="font-size:.68rem;color:{label_color};font-weight:700;
                letter-spacing:.08em;margin-bottom:8px">{icon} {label}</div>
              <div style="font-size:1.2rem;font-weight:900;background:{grad};
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                margin-bottom:8px;line-height:1.3">{cna}<br>× {cnb}</div>
              <div style="font-size:.73rem;color:rgba(255,255,255,.5);line-height:1.4">{desc}</div>
            </div>""", unsafe_allow_html=True)
            if pair:
                btn_label = f"{icon} 开始体验 {cna} × {cnb}"
                if st.button(btn_label, key=btn_key, use_container_width=True):
                    st.session_state["_force_defaults"] = [pa, pb]
                    st.session_state["selected_ingredients"] = [pa, pb]
                    st.session_state["sidebar_tab"] = "实验台"
                    st.rerun()
            else:
                st.button("暂无匹配食材", key=btn_key, use_container_width=True, disabled=True)

    demo_card(col_res, res_pair,
        style="green",
        label_color="#4ade80", bg="linear-gradient(135deg,#0d2818,#0a2a18)", border="#166534",
        grad="linear-gradient(90deg,#4ade80,#00D2FF)", btn_key="demo_resonance",
        icon="🟢", label="同源共振 73-97",
        desc="大量共享分子<br>风味叠加放大")

    demo_card(col_bal, bal_pair,
        style="orange",
        label_color="#fb923c", bg="linear-gradient(135deg,#1a1500,#1e1a00)", border="#92400e",
        grad="linear-gradient(90deg,#fbbf24,#fb923c)", btn_key="demo_balance",
        icon="🟡", label="平衡搭档 46-72",
        desc="交叠有差异<br>1+1>2 的最佳创作区")

    demo_card(col_ctr, ctr_pair,
        style="red",
        label_color="#f87171", bg="linear-gradient(135deg,#2d0d0d,#1a0808)", border="#7f1d1d",
        grad="linear-gradient(90deg,#f87171,#F97316)", btn_key="demo_contrast",
        icon="🔴", label="对比碰撞 18-45",
        desc="分子差异显著<br>产生惊喜张力")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;padding:16px;color:var(--text-faint);font-size:.75rem">🧬 FlavorDB · {len(df)} 种食材 · 分子风味科学</div>', unsafe_allow_html=True)

# ================================================================
# 11. 主函数
# ================================================================
def main():
    df = load_data()
    if df is None:
        st.error("❌ 找不到 flavordb_data.csv，请确保数据文件在同一目录下")
        st.stop()

    # ⚠️ 问题1修复：在渲染任何widget之前，先处理"加入实验"的食材更新
    # 不能在widget渲染循环中直接赋值widget的key，必须在rerun后、widget创建前处理
    if "_add_ingredient" in st.session_state:
        new_list = st.session_state.pop("_add_ingredient")
        st.session_state["_pending_ingredient_list"] = new_list
    if "_add_warn" in st.session_state:
        del st.session_state["_add_warn"]
        st.warning("⚠️ 最多支持4种食材")

    # Hero
    _, btn_col = st.columns([9, 1])
    with btn_col:
        lang_label = "中文" if st.session_state.language == "en" else "EN"
        if st.button(f"🌐 {lang_label}", key="lang_toggle"):
            st.session_state.language = "en" if st.session_state.language == "zh" else "zh"
            st.rerun()

    st.markdown(f"""
    <div class="hero-header">
      <div class="hero-left">
        <span class="hero-icon">🧬</span>
        <div>
          <p class="hero-title">味觉虫洞 · Flavor Lab</p>
          <p class="hero-sub">Molecular Flavor Pairing Engine · V2.1 · Powered by Qwen</p>
        </div>
      </div>
      <div class="hero-badge">
        <span class="hero-badge-pill"><b>{len(df)}</b> 种食材</span>
        <span class="hero-badge-pill">通义千问 × FlavorDB</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 侧边栏
    with st.sidebar:
        selected_tab = render_sidebar_tabs(df)

        if selected_tab == "实验台":
            selected = render_experiment_tab(df)
            ratios = {}
        elif selected_tab == "配方台":
            # 从持久化 state 读取食材（不依赖 ing_select widget key）
            selected = [n for n in st.session_state.get("selected_ingredients", [])
                       if n in df["name"].values]
            if len(selected) < 2:
                st.info("💡 请先在「实验台」选择 2-4 种食材，再来配方台调整比例")
                ratios = {}
            else:
                ratios = render_formula_tab(selected)
        else:
            selected = st.session_state.get("ing_select", [])
            ratios = {}
            render_settings_tab()

        st.divider()
        st.caption("数据来源：FlavorDB · 分子风味科学 · 通义千问")

    if len(selected) < 2:
        render_empty_state(df)
        return

    # 分析
    rows = {n: df[df["name"] == n].iloc[0] for n in selected}
    mol_sets = {n: rows[n]["mol_set"] for n in selected}
    n1, n2 = selected[0], selected[1]
    sim = calc_sim(mol_sets[n1], mol_sets[n2])
    cn1, cn2 = t_ingredient(n1), t_ingredient(n2)

    if not ratios:
        ratios = {n: 1/len(selected) for n in selected}

    # ── 行1：雷达图 | 共鸣指数 ──
    r1_left, r1_right = st.columns([1.2, 1], gap="large")

    with r1_left:
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
            hover_texts = [f"<b>{d.split(chr(10))[0]}</b><br>{RADAR_TOOLTIPS.get(d,'')}<br>分值: {vals_s[di]:.1f}/10" for di,d in enumerate(dims)] + [""]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals_s, theta=dims+[dims[0]], fill="toself", fillcolor=fc,
                line=dict(color=lc, width=2.5), name=f"{t_ingredient(name)} ({pct}%)",
                mode='lines+markers', marker=dict(size=4),
                text=hover_texts, hovertemplate="%{text}<extra></extra>"
            ))
        fig_radar.update_layout(
            polar=dict(bgcolor="rgba(248,249,255,0.4)",
                       radialaxis=dict(
                           visible=True, range=[0,10],
                           tickvals=[2, 4, 6, 8, 10],
                           ticktext=["2", "4", "6", "8", "10"],
                           tickfont=dict(size=9, color="#6B7280"),
                           gridcolor="rgba(107,114,128,0.2)",
                           linecolor="rgba(107,114,128,0.2)"
                       ),
                       angularaxis=dict(tickfont=dict(size=12, color="#6B7280"))),
            showlegend=True, legend=dict(orientation="h", y=-0.18, font=dict(size=11, color="#6B7280")),
            height=420, margin=dict(t=20, b=80, l=40, r=40), paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with r1_right:
        sc = sim["score"]
        sc_c = score_color(sc)
        detail = sim.get("detail", {})
        type_info = {
            "resonance": ("同源共振", "badge-resonance", "共享大量芳香分子，协同延长风味余韵"),
            "contrast":  ("对比碰撞", "badge-contrast", "差异显著，形成张力对比切割"),
            "neutral":   ("平衡搭档", "badge-neutral", "适度交叠，互补平衡"),
        }
        tlabel, tbadge, tdesc = type_info[sim["type"]]
        rr1 = int(ratios.get(n1, 0.5)*100); rr2 = int(ratios.get(n2, 0.5)*100)
        jpct = int(sim["jaccard"]*100)
        bar_color = "#22C55E" if sc >= 73 else ("#F97316" if sc >= 46 else "#EF4444")
        cov_a = detail.get("coverage_a", 0)
        cov_b = detail.get("coverage_b", 0)
        n_shared = detail.get("shared_count", len(sim["shared"]))
        n_only_a = detail.get("only_a_count", len(sim["only_a"]))
        n_only_b = detail.get("only_b_count", len(sim["only_b"]))

        # 得分段位说明
        if sc >= 73:
            tier_text = "🟢 高度共振区（73-97）"
            tier_guide = f"两者分子高度重叠，组合后香气叠加增强，适合主从搭配关系"
        elif sc >= 46:
            tier_text = "🟡 平衡搭档区（46-72）"
            tier_guide = f"有交叠有差异，层次丰富，最容易创造「1+1>2」的复合香气"
        else:
            tier_text = "🔴 对比碰撞区（18-45）"
            tier_guide = f"分子差异显著，形成强烈对比张力，适合少量点缀而非主体融合"

        st.markdown(f"""
        <div class="card-dark" style="text-align:left;padding:22px 26px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
            <div style="color:rgba(255,255,255,.5);font-size:.68rem;letter-spacing:.12em;text-transform:uppercase">🔬 分子共鸣指数</div>
            <span class="badge {tbadge}" style="font-size:.72rem">{tlabel}</span>
          </div>
          <div style="display:flex;align-items:baseline;gap:4px;margin-bottom:6px">
            <span style="font-size:4rem;font-weight:900;line-height:1;color:{sc_c}">{sc}</span>
            <span style="font-size:1.4rem;color:rgba(255,255,255,.45)">/ 97</span>
          </div>
          <div style="font-size:.72rem;color:{sc_c};font-weight:700;margin-bottom:8px">{tier_text}</div>
          <div style="background:rgba(255,255,255,.12);border-radius:6px;height:6px;margin-bottom:10px;overflow:hidden;position:relative">
            <div style="position:absolute;left:0;top:0;height:100%;width:100%;display:flex">
              <div style="width:28%;border-right:1px solid rgba(255,255,255,.15)"></div>
              <div style="width:28%;border-right:1px solid rgba(255,255,255,.15)"></div>
            </div>
            <div style="width:{sc}%;height:100%;background:linear-gradient(90deg,{bar_color},{sc_c});border-radius:6px;position:relative;z-index:1"></div>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:.65rem;color:rgba(255,255,255,.28);margin-bottom:10px">
            <span>对比 0</span><span>平衡 46</span><span>共振 73</span><span>97</span>
          </div>
          <div style="color:rgba(255,255,255,.65);font-size:.8rem;line-height:1.6;margin-bottom:12px;padding:8px 10px;background:rgba(255,255,255,.05);border-radius:8px">{tier_guide}</div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:12px">
            <div style="text-align:center;background:rgba(0,210,255,.1);border-radius:8px;padding:8px">
              <div style="font-size:1.4rem;font-weight:900;color:#00D2FF">{n_shared}</div>
              <div style="font-size:.65rem;color:rgba(255,255,255,.45)">共享分子</div>
            </div>
            <div style="text-align:center;background:rgba(123,47,247,.1);border-radius:8px;padding:8px">
              <div style="font-size:1.4rem;font-weight:900;color:#a78bfa">{n_only_a}</div>
              <div style="font-size:.65rem;color:rgba(255,255,255,.45)">{cn1}独有</div>
            </div>
            <div style="text-align:center;background:rgba(255,107,107,.1);border-radius:8px;padding:8px">
              <div style="font-size:1.4rem;font-weight:900;color:#FF6B6B">{n_only_b}</div>
              <div style="font-size:.65rem;color:rgba(255,255,255,.45)">{cn2}独有</div>
            </div>
          </div>
          <div style="color:rgba(255,255,255,.38);font-size:.7rem;border-top:1px solid rgba(255,255,255,.08);padding-top:8px;line-height:1.7">
            <b style="color:rgba(255,255,255,.55)">📐 算法</b>：Jaccard {jpct}% × 双向覆盖率（{cn1}覆盖 {cov_a}% · {cn2}覆盖 {cov_b}%）× 差异惩罚<br>
            比例：{cn1} <b style="color:rgba(255,255,255,.65)">{rr1}%</b> &nbsp;·&nbsp; {cn2} <b style="color:rgba(255,255,255,.65)">{rr2}%</b>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="card"><h4 class="card-title">🧪 风味指纹</h4>', unsafe_allow_html=True)
        for i, name in enumerate(selected):
            cn = t_ingredient(name)
            notes_cn = t_notes_list(rows[name]["mol_set"], top_n=10)
            pct = int(ratios.get(name, 1/len(selected))*100)
            cls = TAG_CLASSES[i % len(TAG_CLASSES)]
            dom = ""
            if pct >= 40: dom = '<span style="background:#FEF3C7;color:#92400E;font-size:.68rem;padding:1px 6px;border-radius:8px;margin-left:5px;font-weight:700">主导</span>'
            elif pct <= 15: dom = '<span style="background:#E0F2FE;color:#0369A1;font-size:.68rem;padding:1px 6px;border-radius:8px;margin-left:5px;font-weight:700">提味</span>'
            st.markdown(f"""
            <div style="margin-bottom:11px">
              <div style="font-weight:700;color:var(--text-primary);margin-bottom:2px">{cn}
                <span style="color:var(--text-faint);font-weight:400;font-size:.76rem">{pct}%</span>{dom}
              </div>
              <div class="pbar-bg"><div class="pbar-fill" style="width:{pct}%;background:linear-gradient(90deg,#00D2FF,#7B2FF7)"></div></div>
              <div style="margin-top:4px">{tags_html(notes_cn, cls, 8)}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 分子连线网络图 ──
    if sim["shared"]:
        st.markdown('<div class="card"><h4 class="card-title">🕸 分子连线网络图</h4>', unsafe_allow_html=True)
        shared_top = sim["shared"][:14]
        nx_l,ny_l,ntxt,nclr,nsz,ex,ey = [],[],[],[],[],[],[]
        nx_l += [-1.6, 1.6]; ny_l += [0, 0]
        ntxt += [cn1, cn2]; nclr += ["#00D2FF","#7B2FF7"]; nsz += [34, 34]
        for idx, note in enumerate(shared_top):
            angle = math.pi/2 + idx*2*math.pi/len(shared_top)
            px, py = 1.15*math.cos(angle), 1.15*math.sin(angle)
            nx_l.append(px); ny_l.append(py)
            ntxt.append(t_note(note)); nclr.append("#F97316"); nsz.append(14)
            for sx, sy in [(-1.6,0),(1.6,0)]:
                ex += [sx,px,None]; ey += [sy,py,None]
        fig_net = go.Figure()
        fig_net.add_trace(go.Scatter(x=ex, y=ey, mode="lines",
            line=dict(color="rgba(150,150,200,0.2)", width=1), hoverinfo="none", showlegend=False))
        fig_net.add_trace(go.Scatter(x=nx_l, y=ny_l, mode="markers+text",
            text=ntxt, textposition="top center", textfont=dict(size=10, color="#6B7280"),
            marker=dict(color=nclr, size=nsz, line=dict(width=2, color="white"), opacity=0.9),
            hoverinfo="text", showlegend=False))
        fig_net.update_layout(
            height=340, margin=dict(t=10, b=20, l=20, r=20),
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248,249,255,0.2)")
        st.plotly_chart(fig_net, use_container_width=True)
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:20px;justify-content:center;
             padding:8px 0 4px;font-size:.78rem;color:var(--text-muted)">
          <span>🔵 {cn1}</span><span>🟣 {cn2}</span>
          <span>🟠 共享节点 · {len(sim["shared"])} 个</span>
        </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 行3：深度诊断 | 介质推演+主厨建议 ──
    r3_left, r3_right = st.columns([1, 1.2], gap="large")

    with r3_left:
        st.markdown('<div class="card"><h4 class="card-title">🔬 深度诊断</h4>', unsafe_allow_html=True)
        if sim["type"] == "resonance":
            st.markdown(f"""<div class="diag diag-res">
              <b>✅ 高度共振</b> — 共享风味分子比例 {jpct}%<br>
              两者拥有大量相同的芳香分子，结合后将显著延长风味余韵。<br><br>
              <b>共享节点：</b><br>{shared_tags_html(sim["shared"][:10])}
            </div>""", unsafe_allow_html=True)
        elif sim["type"] == "contrast":
            a3 = " / ".join(t_notes_list(rows[n1]["mol_set"], 3))
            b3 = " / ".join(t_notes_list(rows[n2]["mol_set"], 3))
            st.markdown(f"""<div class="diag diag-ctr">
              <b>⚡ 对比碰撞</b> — 共享分子比例 {jpct}%<br>
              经典「切割平衡」结构。<b>{cn1}</b> 以 <b>{a3}</b> 主导，<b>{cn2}</b> 以 <b>{b3}</b> 抗衡。
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="diag diag-info">
              <b>🔵 平衡搭档</b> — 共享分子比例 {jpct}%<br>
              风味有交叠也有差异，形成良好互补。<br><br>
              <b>共享节点：</b><br>{shared_tags_html(sim["shared"][:8])}
            </div>""", unsafe_allow_html=True)

        oa = sim["only_a"][:6]; ob = sim["only_b"][:6]
        if oa or ob:
            ca2, cb2 = st.columns(2)
            with ca2:
                st.markdown(f"<div style='font-size:.82rem;font-weight:700;margin:10px 0 4px'>{cn1} 独有</div>", unsafe_allow_html=True)
                st.markdown(tags_html([t_note(n) for n in oa], "tag-blue"), unsafe_allow_html=True)
            with cb2:
                st.markdown(f"<div style='font-size:.82rem;font-weight:700;margin:10px 0 4px'>{cn2} 独有</div>", unsafe_allow_html=True)
                st.markdown(tags_html([t_note(n) for n in ob], "tag-purple"), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with r3_right:
        pol = polarity_analysis(mol_sets[n1] | mol_sets[n2])
        if pol["total"] > 0:
            st.markdown('<div class="card"><h4 class="card-title">💧 介质推演</h4>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="font-size:.78rem;color:var(--text-muted);margin-bottom:10px;line-height:1.6;
              border-left:3px solid #7B2FF7;padding-left:10px">
              <b style="color:var(--text-primary)">什么是介质推演？</b><br>
              香气分子分为「脂溶性」（溶于油脂）和「水溶性」（溶于水）两类。
              选择正确的烹饪介质，能让芳香分子最大程度释放。
              脂溶性组合适合油封/奶油烹调；水溶性组合适合水煮/清蒸；双亲性可乳化兼顾两者。
            </div>""", unsafe_allow_html=True)
            lp = int(pol["lipo"]/pol["total"]*100); hp = 100-lp
            bar_html = f'''<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;margin:8px 0">
              <div style="width:{lp}%;background:linear-gradient(90deg,#F97316,#FBBF24)"></div>
              <div style="width:{hp}%;background:linear-gradient(90deg,#3B82F6,#00D2FF)"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:.72rem;color:var(--text-muted)">
              <span>🫙 脂溶 {lp}%</span><span>💧 水溶 {hp}%</span>
            </div>'''
            if pol["type"] == "lipophilic":
                st.markdown(f"""<div class="diag diag-ctr">
                  <b>🫙 脂溶性主导</b><br>{bar_html}<br>
                  <b>为什么：</b>两种食材的主要芳香分子都偏向脂溶，油脂是最佳溶剂。<br><br>
                  <b>烹饪启发：</b><br>
                  · {tech_tip("Confit")} 油封 — 在低温油脂中缓慢萃取脂溶香气<br>
                  · {tech_tip("甘纳许")} 巧克力乳化 — 将香气锁入油脂结晶<br>
                  · 黄油收汁 — 高温焦化黄油载体，聚合脂溶风味<br>
                  · 避免：水煮会流失大量香气分子
                </div>""", unsafe_allow_html=True)
            elif pol["type"] == "hydrophilic":
                st.markdown(f"""<div class="diag diag-info">
                  <b>💧 水溶性主导</b><br>{bar_html}<br>
                  <b>为什么：</b>主要芳香分子偏向水溶，水性介质能最大程度展现香气。<br><br>
                  <b>烹饪启发：</b><br>
                  · {tech_tip("Consommé")} 澄清高汤 — 保留纯净水溶香气<br>
                  · {tech_tip("真空萃取")} — 低温保全热敏感水溶分子<br>
                  · 冰沙 / 冰激凌 — 低温延缓挥发，香气更持久<br>
                  · 避免：高温长时间油煎会破坏水溶分子结构
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="diag diag-res">
                  <b>⚖️ 双亲性平衡</b><br>{bar_html}<br>
                  <b>为什么：</b>脂溶与水溶各约一半，是最适合乳化工艺的组合。<br><br>
                  <b>烹饪启发：</b><br>
                  · {tech_tip("乳化酱汁")} — 同时释放两类香气，层次最丰富<br>
                  · {tech_tip("Espuma")} 泡沫 — 气泡界面放大嗅觉感知<br>
                  · 黄油白酱 Beurre Blanc — 乳化平衡，兼顾鲜爽与醇厚<br>
                  · 最佳比例：乳化剂用量约为油脂的 1.5-2%
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card"><h4 class="card-title">👨‍🍳 主厨工艺建议</h4>', unsafe_allow_html=True)
        tips_pool = {
            "resonance": [
                ("🔥 叠加放大", f"以 <b>{cn1}</b> 为基底，将 <b>{cn2}</b> {tech_tip('浓缩收汁')}后叠加，同一芳香维度形成「风味放大」效果。"),
                ("🌡️ 低温保留", f"共享分子通过 {tech_tip('低温慢煮')} 保留，避免高温氧化破坏共鸣节点。"),
                ("🍮 质地穿插", f"将 <b>{cn2}</b> 制成 {tech_tip('凝胶化')}，穿插在 <b>{cn1}</b> 的质地层间，延长风味余韵。"),
            ],
            "contrast": [
                ("✂️ 切割平衡", f"利用 <b>{cn2}</b> 的对比维度「切割」{cn1} 的厚重感，以提味剂形式在收尾引入。"),
                ("📈 分阶引入", f"先以 <b>{cn1}</b> 建立底味，后期通过 {tech_tip('低温慢煮')} 的 <b>{cn2}</b> 制造味觉转折。"),
                ("☁️ 泡沫覆盖", f"将 <b>{cn2}</b> 做成 {tech_tip('Espuma')}，轻盈覆盖 <b>{cn1}</b> 的厚重质地，创造对比张力。"),
            ],
            "neutral": [
                ("📊 比例递进", f"从 <b>{cn1}</b> 的纯净基调出发，逐步引入 <b>{cn2}</b>，通过 {tech_tip('乳化')} 融合。"),
                ("🔬 分子融合", f"{tech_tip('真空萃取')} 让两者在分子层面充分融合，实现比例可控的风味协同。"),
                ("❄️ 粉末跳跃", f"以 <b>{cn1}</b> 为主味，<b>{cn2}</b> 通过 {tech_tip('冷冻干燥')} 制成粉末，提供风味跳跃感。"),
            ],
        }
        all_tips = tips_pool[sim["type"]]
        type_guide = {
            "resonance": "同源共振 · 叠加放大——强化共同分子，深化香气维度",
            "contrast":  "对比碰撞 · 分阶切割——利用差异制造味觉节奏层次",
            "neutral":   "平衡搭档 · 比例调控——权重微调寻找最佳共鸣平衡",
        }
        tip_colors  = ["#EEF6FF", "#F0FDF4", "#FFF7ED"]
        tip_borders = ["#3B82F6", "#22C55E", "#F97316"]
        st.markdown(f"""<div style="background:linear-gradient(135deg,#F0F4FF,#F5F0FF);
        border-radius:10px;padding:10px 14px;margin-bottom:12px;border-left:4px solid #7B2FF7;
        font-size:.8rem;line-height:1.55"><b style="color:#7B2FF7">🧭 策略</b>&emsp;{type_guide[sim["type"]]}</div>""",
        unsafe_allow_html=True)
        tip_cols = st.columns(3)
        for i, (label, tip_text) in enumerate(all_tips):
            with tip_cols[i]:
                st.markdown(f"""<div style="background:{tip_colors[i]};border:1px solid {tip_borders[i]}44;
                border-top:3px solid {tip_borders[i]};border-radius:10px;padding:12px;min-height:130px">
                <div style="font-size:.76rem;font-weight:700;color:{tip_borders[i]};margin-bottom:6px">{label}</div>
                <div style="font-size:.77rem;color:#374151;line-height:1.6">{tip_text}</div>
                </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    cb, cc = st.columns([1,1], gap="large")

    with cb:
        st.markdown('<div class="card"><h4 class="card-title">🌉 风味桥接推荐</h4>', unsafe_allow_html=True)
        st.markdown(f"<p style='color:var(--text-muted);font-size:.82rem'>寻找能串联 <b>{cn1}</b> 与 <b>{cn2}</b> 的「第三食材」</p>", unsafe_allow_html=True)
        bridges = find_bridges(df, mol_sets[n1], mol_sets[n2], selected)
        if bridges:
            for bname, bsc, sa, sb in bridges:
                bcn = t_ingredient(bname)
                bcat_row = df[df["name"]==bname]
                bcat_zh = t_category(bcat_row.iloc[0]["category"]) if len(bcat_row)>0 else ""
                ps = min(100, int(bsc*100)); pa = min(100, int(sa*100)); pb = min(100, int(sb*100))
                st.markdown(f"""
                <div class="ing-row">
                  <div style="font-weight:700;color:var(--text-primary)">{bcn}
                    <span style="font-size:.75rem;color:var(--text-muted);font-weight:400"> {bname}</span>
                  </div>
                  <div style="font-size:.74rem;color:var(--text-muted)">{bcat_zh} · 连接力 {ps}% · 与{cn1} {pa}% | 与{cn2} {pb}%</div>
                  <div class="pbar-bg" style="margin-top:5px"><div class="pbar-fill" style="width:{ps}%;background:linear-gradient(90deg,#F97316,#FBBF24)"></div></div>
                </div>""", unsafe_allow_html=True)
                if st.button(f"➕ 加入实验", key=f"add_bridge_{bname}", use_container_width=True):
                    curr = list(st.session_state.get("selected_ingredients", []))
                    if bname not in curr and len(curr) < 4:
                        curr.append(bname)
                        st.session_state["selected_ingredients"] = curr
                        st.session_state["_force_defaults"] = curr  # 同步 multiselect default
                        st.rerun()
                    elif len(curr) >= 4:
                        st.warning("⚠️ 最多支持4种食材")
        else:
            st.info("未找到合适的桥接食材")
        st.markdown("</div>", unsafe_allow_html=True)

    with cc:
        st.markdown('<div class="card"><h4 class="card-title">⚡ 对比风味推荐</h4>', unsafe_allow_html=True)
        st.markdown(f"<p style='color:var(--text-muted);font-size:.82rem'>与 <b>{cn1}</b> × <b>{cn2}</b> 形成张力对比的食材</p>", unsafe_allow_html=True)
        contrasts = find_contrasts(df, mol_sets[n1], mol_sets[n2], selected)
        if contrasts:
            for cname, csc, da, db in contrasts:
                ccn = t_ingredient(cname)
                ccat_row = df[df["name"]==cname]
                ccat_zh = t_category(ccat_row.iloc[0]["category"]) if len(ccat_row)>0 else ""
                ps = min(100, int(csc*100))
                st.markdown(f"""
                <div class="ing-row">
                  <div style="font-weight:700;color:var(--text-primary)">{ccn}
                    <span style="font-size:.75rem;color:var(--text-muted);font-weight:400"> {cname}</span>
                  </div>
                  <div style="font-size:.74rem;color:var(--text-muted)">{ccat_zh} · 对比度 {ps}%</div>
                  <div class="pbar-bg" style="margin-top:5px"><div class="pbar-fill" style="width:{ps}%;background:linear-gradient(90deg,#EF4444,#F97316)"></div></div>
                </div>""", unsafe_allow_html=True)
                if st.button(f"➕ 加入实验", key=f"add_contrast_{cname}", use_container_width=True):
                    curr = list(st.session_state.get("selected_ingredients", []))
                    if cname not in curr and len(curr) < 4:
                        curr.append(cname)
                        st.session_state["selected_ingredients"] = curr
                        st.session_state["_force_defaults"] = curr
                        st.rerun()
                    elif len(curr) >= 4:
                        st.warning("⚠️ 最多支持4种食材")
        else:
            st.info("未找到合适的对比食材")
        st.markdown("</div>", unsafe_allow_html=True)

    # AI 对话区
    api_ok, api_config = check_api_status()
    render_chat_section(api_config if api_ok else None, cn1, cn2, selected, ratios, sim, mol_sets, df)

    st.markdown(f"""
    <div style="text-align:center;padding:14px;color:var(--text-faint);font-size:.76rem">
      🧬 FlavorDB · {len(df)} 种食材 · 共享分子 {len(sim['shared'])} 个 · Jaccard {int(sim['jaccard']*100)}%
    </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
