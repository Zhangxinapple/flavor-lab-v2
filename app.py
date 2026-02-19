import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import random
from math import sqrt

# ================================================================
# 0. 页面配置 (必须第一行)
# ================================================================
st.set_page_config(
    page_title="味觉虫洞 Flavor Lab",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================================================
# 1. 全局样式
# ================================================================
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .stApp { background: #F4F6FA; }

  /* 顶部标题栏 */
  .hero-header {
    background: linear-gradient(135deg, #0A0A1A 0%, #1A1A3E 50%, #0D2137 100%);
    padding: 28px 36px;
    border-radius: 20px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  }
  .hero-title {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #00D2FF, #7B2FF7, #FF6B6B);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
  }
  .hero-sub {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.5);
    margin: 0;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  /* 卡片 */
  .card {
    background: white;
    padding: 24px;
    border-radius: 18px;
    box-shadow: 0 2px 16px rgba(0,0,0,0.06);
    margin-bottom: 18px;
    border: 1px solid #E8EAED;
  }
  .card-dark {
    background: linear-gradient(135deg, #0A0A1A, #1A1A3E);
    padding: 24px;
    border-radius: 18px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.2);
    margin-bottom: 18px;
    border: 1px solid rgba(255,255,255,0.08);
  }

  /* 分数显示 */
  .score-ring {
    text-align: center;
    padding: 20px 0;
  }
  .score-number {
    font-size: 4.5rem;
    font-weight: 900;
    line-height: 1;
  }
  .score-label {
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #888;
    margin-top: 4px;
  }

  /* 风味标签 */
  .tag {
    display: inline-block;
    padding: 3px 11px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 2px 3px;
  }
  .tag-blue   { background: #EEF6FF; color: #1D6FDB; border: 1px solid #BDD7F5; }
  .tag-green  { background: #F0FDF4; color: #16A34A; border: 1px solid #BBF7D0; }
  .tag-orange { background: #FFF7ED; color: #C2410C; border: 1px solid #FECBA1; }
  .tag-purple { background: #F5F3FF; color: #7C3AED; border: 1px solid #DDD6FE; }
  .tag-pink   { background: #FDF2F8; color: #BE185D; border: 1px solid #FBCFE8; }
  .tag-shared { background: linear-gradient(90deg,#E0F7FA,#EDE7F6); color: #5B21B6; border: 1px solid #C4B5FD; font-weight: 600; }

  /* 诊断区块 */
  .diag-block {
    border-radius: 14px;
    padding: 16px 18px;
    margin: 10px 0;
    border-left: 4px solid;
  }
  .diag-resonance { background: #F0FDF4; border-color: #22C55E; }
  .diag-contrast  { background: #FFF7ED; border-color: #F97316; }
  .diag-info      { background: #EEF6FF; border-color: #3B82F6; }

  /* 食材条目 */
  .ingredient-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-radius: 10px;
    margin: 4px 0;
    background: #F8F9FB;
    border: 1px solid #EEE;
  }

  /* 进度条 */
  .progress-bar-bg {
    background: #E8EAED;
    border-radius: 8px;
    height: 8px;
    overflow: hidden;
    margin: 4px 0;
  }
  .progress-bar-fill {
    height: 100%;
    border-radius: 8px;
    transition: width 0.4s;
  }

  /* 侧边栏 */
  [data-testid="stSidebar"] {
    background: #FAFBFC;
    border-right: 1px solid #E8EAED;
  }

  /* 分割线 */
  .section-title {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #999;
    margin: 16px 0 8px;
  }

  /* 匹配类型徽章 */
  .badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
  }
  .badge-resonance { background: #D1FAE5; color: #065F46; }
  .badge-contrast  { background: #FEE2E2; color: #991B1B; }
  .badge-bridge    { background: #EDE9FE; color: #4C1D95; }
  .badge-neutral   { background: #F3F4F6; color: #374151; }

  /* 隐藏默认元素 */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


# ================================================================
# 2. 本地化引擎
# ================================================================
@st.cache_resource
def load_localization():
    """从 localization_zh.json 读取词典，如不存在则使用内置精简版"""
    if os.path.exists("localization_zh.json"):
        with open("localization_zh.json", "r", encoding="utf-8") as f:
            return json.load(f)
    # 内置精简回退
    return {
        "ingredients": {},
        "flavor_notes": {
            "sweet":"甜美","bitter":"苦涩","sour":"酸楚","fruity":"果香",
            "roasted":"烘焙","herbaceous":"草本","woody":"木质","spicy":"辛辣",
            "floral":"花香","nutty":"坚果","creamy":"奶香","smoky":"烟熏",
            "earthy":"大地气息","citrus":"柑橘","caramel":"焦糖","fatty":"油脂",
            "sulfurous":"硫质","pungent":"辛锐","malty":"麦芽"
        },
        "categories": {}
    }

LOC = load_localization()

def t_ingredient(name: str) -> str:
    """翻译食材名；优先精确匹配，再小写匹配"""
    imap = LOC.get("ingredients", {})
    return imap.get(name) or imap.get(name.lower()) or imap.get(name.title()) or name

def t_category(cat: str) -> str:
    return LOC.get("categories", {}).get(cat, cat)

def t_note(note: str) -> str:
    """翻译风味词"""
    nmap = LOC.get("flavor_notes", {})
    return nmap.get(note.strip().lower()) or nmap.get(note.strip()) or note.strip()

def t_notes_list(profile_str: str, top_n: int = 999) -> list:
    """将逗号分隔的风味字符串转为去重中文列表"""
    raw = [n.strip().lower() for n in str(profile_str).split(",") if n.strip()]
    translated = [t_note(n) for n in raw]
    # 去重保序
    seen = set()
    result = []
    for item in translated:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result[:top_n]

def display_name(name: str) -> str:
    """侧边栏显示名：中文 (英文) 或纯中文"""
    cn = t_ingredient(name)
    return f"{cn}（{name}）" if cn != name else name


# ================================================================
# 3. 数据加载与处理
# ================================================================
@st.cache_data
def load_data():
    path = "flavordb_data.csv"
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df["flavor_profiles"] = df["flavor_profiles"].fillna("")
    df = df[df["flavor_profiles"].str.len() > 2].copy()
    # 分子集合（小写词汇集）
    df["mol_set"] = df["flavor_profiles"].apply(
        lambda x: set(n.strip().lower() for n in x.split(",") if n.strip())
    )
    # 分子数量
    df["mol_count"] = df["mol_set"].apply(len)
    # 中文分类
    df["category_zh"] = df["category"].apply(t_category)
    return df


# ================================================================
# 4. 算法引擎
# ================================================================
# 风味极性分类（用于溶解度推演）
POLARITY_MAP = {
    "fat": "lipophilic", "fatty": "lipophilic", "oil": "lipophilic",
    "oily": "lipophilic", "waxy": "lipophilic", "buttery": "lipophilic",
    "butter": "lipophilic", "cream": "lipophilic", "creamy": "lipophilic",
    "lard": "lipophilic", "tallow": "lipophilic", "coconut": "lipophilic",
    "resin": "lipophilic", "woody": "lipophilic", "leather": "lipophilic",
    "smoky": "lipophilic", "smoke": "lipophilic",
    "sweet": "hydrophilic", "sour": "hydrophilic", "acid": "hydrophilic",
    "citrus": "hydrophilic", "fruity": "hydrophilic", "floral": "hydrophilic",
    "honey": "hydrophilic", "alcoholic": "hydrophilic", "wine": "hydrophilic",
    "vinegar": "hydrophilic", "fresh": "hydrophilic", "green": "hydrophilic",
    "sugar": "hydrophilic",
}

def calculate_similarity(set_a: set, set_b: set) -> dict:
    """多维风味相似度分析"""
    inter = set_a & set_b
    union = set_a | set_b
    jaccard = len(inter) / len(union) if union else 0

    # 加权分（共享分子越多权重越高）
    weighted = min(1.0, (len(inter) / max(len(set_a), len(set_b), 1)) * 1.5)
    score = int(min(97, max(50, jaccard * 250 + weighted * 120)))

    # 相似度类型
    if jaccard >= 0.35:
        sim_type = "resonance"
    elif jaccard >= 0.12:
        sim_type = "neutral"
    else:
        sim_type = "contrast"

    return {
        "score": score,
        "jaccard": jaccard,
        "shared": sorted(inter),
        "only_a": sorted(set_a - set_b),
        "only_b": sorted(set_b - set_a),
        "type": sim_type,
    }

def polarity_analysis(mol_set: set) -> dict:
    """极性分析——判断水溶性 vs 脂溶性主导"""
    lipo = sum(1 for m in mol_set if POLARITY_MAP.get(m) == "lipophilic")
    hydro = sum(1 for m in mol_set if POLARITY_MAP.get(m) == "hydrophilic")
    total = lipo + hydro
    if total == 0:
        return {"type": "balanced", "lipo": 0, "hydro": 0, "total": 0}
    return {
        "type": "lipophilic" if lipo > hydro else ("hydrophilic" if hydro > lipo else "balanced"),
        "lipo": lipo,
        "hydro": hydro,
        "total": total,
    }

def find_bridge_ingredients(df: pd.DataFrame, set_a: set, set_b: set, selected_names: list, top_n: int = 3) -> list:
    """寻找风味桥接食材"""
    results = []
    for _, row in df.iterrows():
        if row["name"] in selected_names:
            continue
        s = row["mol_set"]
        score_a = len(s & set_a) / max(len(set_a), 1)
        score_b = len(s & set_b) / max(len(set_b), 1)
        bridge_score = sqrt(score_a * score_b) * (1 + min(score_a, score_b))
        if bridge_score > 0.05:
            results.append((row["name"], bridge_score, score_a, score_b))
    results.sort(key=lambda x: -x[1])
    return results[:top_n]

def radar_values(mol_set: set) -> dict:
    """计算雷达图各维度得分（0-10）"""
    DIMS = {
        "甜味":    ["sweet", "caramel", "honey", "vanilla", "sugar", "butterscotch", "candy", "cotton candy"],
        "烘焙":    ["roasted", "baked", "toasted", "caramel", "coffee", "cocoa", "bread", "malt", "popcorn"],
        "果香":    ["fruity", "berry", "apple", "pear", "peach", "citrus", "tropical", "grape", "banana", "strawberry"],
        "草本":    ["herbaceous", "herbal", "green", "mint", "thyme", "rosemary", "basil", "dill", "leafy"],
        "木质烟熏": ["woody", "wood", "smoky", "smoke", "cedar", "oak", "leather", "tobacco", "resin"],
        "辛辣":    ["spicy", "pepper", "cinnamon", "ginger", "clove", "mustard", "pungent", "horseradish"],
        "花香":    ["floral", "rose", "jasmine", "lavender", "violet", "floral", "lily", "blossom"],
        "脂奶":    ["fatty", "creamy", "buttery", "butter", "cream", "dairy", "milky", "nutty"],
    }
    scores = {}
    for dim, keywords in DIMS.items():
        hit = sum(1 for k in keywords if k in mol_set)
        scores[dim] = min(10, hit * 2.0 + (1 if hit > 0 else 0))
    return scores


# ================================================================
# 5. 颜色工具
# ================================================================
TAG_COLORS = ["tag-blue", "tag-green", "tag-orange", "tag-purple", "tag-pink"]

def score_color(score: int) -> str:
    if score >= 80: return "#22C55E"
    if score >= 65: return "#3B82F6"
    if score >= 50: return "#F97316"
    return "#EF4444"

def render_tags(notes: list, color_class: str = "tag-blue", max_n: int = 8) -> str:
    tags = [f'<span class="tag {color_class}">{n}</span>' for n in notes[:max_n]]
    return " ".join(tags)

def render_shared_tags(notes: list, max_n: int = 10) -> str:
    tags = [f'<span class="tag tag-shared">⚡ {t_note(n)}</span>' for n in notes[:max_n]]
    return " ".join(tags)


# ================================================================
# 6. 主界面
# ================================================================
def main():
    df = load_data()
    if df is None:
        st.error("❌ 找不到 flavordb_data.csv，请确保文件与 app.py 在同一目录。")
        st.stop()

    # ── 顶部 Hero ──────────────────────────────────────────────
    st.markdown("""
    <div class="hero-header">
      <span style="font-size:2.4rem">🧬</span>
      <div>
        <p class="hero-title">味觉虫洞 · Flavor Lab</p>
        <p class="hero-sub">Professional Flavor Pairing Engine &nbsp;·&nbsp; V2.0 重构版</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 侧边栏 ─────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 🔬 实验参数")

        # 分类过滤手风琴
        with st.expander("🗂 按分类筛选食材", expanded=False):
            all_cats = sorted(df["category"].unique().tolist())
            cat_options = [f"{t_category(c)}（{c}）" for c in all_cats]
            selected_cats = st.multiselect("选择分类（不选 = 全部）", cat_options, key="cat_filter")
            if selected_cats:
                chosen_en = [c for c in all_cats if f"{t_category(c)}（{c}）" in selected_cats]
                df_show = df[df["category"].isin(chosen_en)]
            else:
                df_show = df

        # Vegan 开关
        is_vegan = st.toggle("🍃 仅植物基 Vegan", value=False)
        if is_vegan:
            exclude_kw = ["meat", "dairy", "fish", "seafood", "pork", "beef", "chicken", "egg"]
            mask = df_show["category"].str.lower().apply(
                lambda c: not any(kw in c for kw in exclude_kw)
            )
            df_show = df_show[mask]

        # 食材搜索 & 选择
        st.markdown(f"<div class='section-title'>已解锁 {len(df_show)} 种食材</div>", unsafe_allow_html=True)
        options = sorted(df_show["name"].unique().tolist())
        defaults = [n for n in ["coffee", "dark chocolate"] if n in options]

        selected = st.multiselect(
            "选择食材（2-4种）",
            options=options,
            default=defaults,
            format_func=display_name,
            help="最多支持4种食材同时分析"
        )

        # 比例滑块
        ratios = {}
        if len(selected) >= 2:
            st.markdown("<div class='section-title'>配方比例</div>", unsafe_allow_html=True)
            total_slider = 0
            for i, name in enumerate(selected):
                cn = t_ingredient(name)
                default_val = 100 // len(selected)
                ratios[name] = st.slider(
                    f"{cn}", 0, 100, default_val, 5, key=f"ratio_{name}"
                )
                total_slider += ratios[name]
            if total_slider > 0:
                ratios = {k: v / total_slider for k, v in ratios.items()}
            st.caption(f"💡 各食材比例已归一化 (总和=100%)")

        st.divider()
        st.caption("数据来源：FlavorDB | 共 555 种食材 · 464 个风味维度")

    # ── 主内容区 ───────────────────────────────────────────────
    if len(selected) < 2:
        st.markdown("""
        <div class="card" style="text-align:center; padding: 60px;">
          <div style="font-size:3.5rem">🌀</div>
          <h2 style="color:#999; font-weight:400; margin:12px 0">请在左侧选择 2-4 种食材</h2>
          <p style="color:#BBB">系统将自动分析分子相似度、风味维度与桥接路径</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # 获取数据
    rows = {n: df[df["name"] == n].iloc[0] for n in selected}
    mol_sets = {n: rows[n]["mol_set"] for n in selected}

    # 主要分析（取前两种做核心比较，多选则叠加展示）
    n1, n2 = selected[0], selected[1]
    sim = calculate_similarity(mol_sets[n1], mol_sets[n2])

    # ── 布局 ───────────────────────────────────────────────────
    col_left, col_right = st.columns([1.35, 1], gap="large")

    # ======================================================
    # 左栏：雷达图 + 分子网络
    # ======================================================
    with col_left:

        # 1) 雷达图
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 🔭 风味维度雷达图")

            fig = go.Figure()
            color_palette = [
                ("rgba(0,210,255,0.15)", "#00D2FF"),
                ("rgba(123,47,247,0.15)", "#7B2FF7"),
                ("rgba(255,107,107,0.15)", "#FF6B6B"),
                ("rgba(0,230,118,0.15)", "#00E676"),
            ]
            for i, name in enumerate(selected[:4]):
                rv = radar_values(mol_sets[name])
                dims = list(rv.keys())
                vals = list(rv.values())
                vals_closed = vals + [vals[0]]
                dims_closed = dims + [dims[0]]
                ratio_pct = int(ratios.get(name, 1/len(selected)) * 100)
                # 按比例缩放雷达
                scale = 0.5 + ratios.get(name, 1/len(selected)) * 0.5 * len(selected)
                vals_scaled = [min(10, v * scale) for v in vals_closed]

                fill_c, line_c = color_palette[i]
                fig.add_trace(go.Scatterpolar(
                    r=vals_scaled,
                    theta=dims_closed,
                    fill="toself",
                    fillcolor=fill_c,
                    line=dict(color=line_c, width=2.5),
                    name=f"{t_ingredient(name)} ({ratio_pct}%)",
                    hovertemplate="%{theta}: %{r:.1f}<extra>" + t_ingredient(name) + "</extra>"
                ))

            fig.update_layout(
                polar=dict(
                    bgcolor="rgba(248,249,255,0.5)",
                    radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(size=9, color="#999")),
                    angularaxis=dict(tickfont=dict(size=12, color="#333")),
                    gridshape="circular",
                ),
                showlegend=True,
                legend=dict(orientation="h", y=-0.12, font=dict(size=11)),
                height=420,
                margin=dict(t=20, b=60, l=40, r=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 2) 分子网络连线图（以共享节点为核心）
        if sim["shared"]:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("#### 🕸 分子连线网络图")

                cn1, cn2 = t_ingredient(n1), t_ingredient(n2)
                shared_top = sim["shared"][:12]

                node_x, node_y, node_text, node_color, node_size = [], [], [], [], []
                edge_x, edge_y = [], []

                # 核心食材节点
                node_x += [-1.5, 1.5]
                node_y += [0, 0]
                node_text += [cn1, cn2]
                node_color += ["#00D2FF", "#7B2FF7"]
                node_size += [28, 28]

                # 共享风味节点（圆形排列）
                import math
                for idx, note in enumerate(shared_top):
                    angle = math.pi / 2 + idx * 2 * math.pi / len(shared_top)
                    radius = 1.1
                    nx = radius * math.cos(angle)
                    ny = radius * math.sin(angle)
                    node_x.append(nx)
                    node_y.append(ny)
                    node_text.append(t_note(note))
                    node_color.append("#F97316")
                    node_size.append(14)
                    # 连线
                    for src_x, src_y in [(-1.5, 0), (1.5, 0)]:
                        edge_x += [src_x, nx, None]
                        edge_y += [src_y, ny, None]

                net_fig = go.Figure()
                net_fig.add_trace(go.Scatter(
                    x=edge_x, y=edge_y,
                    mode="lines",
                    line=dict(color="rgba(150,150,200,0.3)", width=1.2),
                    hoverinfo="none", showlegend=False
                ))
                net_fig.add_trace(go.Scatter(
                    x=node_x, y=node_y,
                    mode="markers+text",
                    text=node_text,
                    textposition="top center",
                    textfont=dict(size=10, color="#333"),
                    marker=dict(
                        color=node_color,
                        size=node_size,
                        line=dict(width=2, color="white"),
                        opacity=0.9,
                    ),
                    hoverinfo="text",
                    showlegend=False,
                ))
                net_fig.update_layout(
                    height=320,
                    margin=dict(t=10, b=10, l=10, r=10),
                    xaxis=dict(visible=False), yaxis=dict(visible=False),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(248,249,255,0.5)",
                )
                st.plotly_chart(net_fig, use_container_width=True)
                st.caption(f"🔵 {cn1}  🟣 {cn2}  🟠 共享风味节点（共 {len(sim['shared'])} 个）")
                st.markdown("</div>", unsafe_allow_html=True)

    # ======================================================
    # 右栏：评分 + 诊断 + 建议
    # ======================================================
    with col_right:

        # 1) 主评分
        sc = sim["score"]
        sc_color = score_color(sc)
        type_map = {
            "resonance": ("同源共振", "badge-resonance", "两者共享大量风味分子，和谐融合"),
            "contrast":  ("对比碰撞", "badge-contrast",  "风味分子差异显著，形成张力对比"),
            "neutral":   ("平衡搭档", "badge-neutral",    "风味有所交叠，适度互补"),
        }
        type_label, type_badge, type_desc = type_map[sim["type"]]

        cn1, cn2 = t_ingredient(n1), t_ingredient(n2)
        r1 = int(ratios.get(n1, 0.5) * 100)
        r2 = int(ratios.get(n2, 0.5) * 100)

        st.markdown(f"""
        <div class="card-dark" style="text-align:center">
          <div style="color:rgba(255,255,255,0.5); font-size:0.75rem; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:8px">
            分子共鸣指数
          </div>
          <div class="score-number" style="color:{sc_color}">{sc}<span style="font-size:2rem; font-weight:400">%</span></div>
          <div style="margin: 12px 0">
            <span class="badge {type_badge}">{type_label}</span>
          </div>
          <div style="color:rgba(255,255,255,0.6); font-size:0.82rem">{type_desc}</div>
          <div style="margin-top:14px; color:rgba(255,255,255,0.4); font-size:0.8rem">
            {cn1} {r1}% &nbsp;·&nbsp; {cn2} {r2}%
          </div>
        </div>
        """, unsafe_allow_html=True)

        # 2) 风味指纹（含比例权重高亮）
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🧪 风味指纹")

        for i, name in enumerate(selected):
            cn = t_ingredient(name)
            profile_str = str(rows[name]["flavor_profiles"])
            notes_cn = t_notes_list(profile_str, top_n=10)
            ratio_pct = int(ratios.get(name, 1/len(selected)) * 100)
            color_cls = TAG_COLORS[i % len(TAG_COLORS)]
            tags_html = render_tags(notes_cn, color_cls, max_n=8)

            # 主导色
            dominant_label = "主导" if ratio_pct >= 40 else ("提味" if ratio_pct <= 15 else "")
            dom_badge = f'<span style="background:#FEF3C7;color:#92400E;font-size:0.7rem;padding:1px 7px;border-radius:8px;margin-left:6px">{dominant_label}</span>' if dominant_label else ""

            st.markdown(f"""
            <div style="margin-bottom:12px">
              <div style="font-weight:600; color:#222; margin-bottom:4px">
                {cn} <span style="color:#999; font-weight:400; font-size:0.8rem">{ratio_pct}%</span>{dom_badge}
              </div>
              <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width:{ratio_pct}%; background:linear-gradient(90deg,#00D2FF,#7B2FF7)"></div>
              </div>
              <div style="margin-top:6px">{tags_html}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # 3) 深度诊断（共享 & 独有分子）
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🔬 深度诊断")

        shared_cn = sim["shared"]
        only_a_cn = sim["only_a"][:8]
        only_b_cn = sim["only_b"][:8]
        jaccard_pct = int(sim["jaccard"] * 100)

        if sim["type"] == "resonance":
            st.markdown(f"""
            <div class="diag-block diag-resonance">
              <b>✅ 高度共振</b> — 共享风味分子比例 {jaccard_pct}%<br>
              两者拥有大量相同的芳香分子，结合后将显著延长风味余韵，主副调高度协同。<br><br>
              <b>共享节点：</b><br>{render_shared_tags(shared_cn[:10])}
            </div>
            """, unsafe_allow_html=True)
        elif sim["type"] == "contrast":
            a_profiles = " / ".join(t_notes_list(str(rows[n1]["flavor_profiles"]), top_n=3))
            b_profiles = " / ".join(t_notes_list(str(rows[n2]["flavor_profiles"]), top_n=3))
            st.markdown(f"""
            <div class="diag-block diag-contrast">
              <b>⚡ 对比碰撞</b> — 共享分子比例 {jaccard_pct}%<br>
              这是经典的「切割平衡（Cut-through）」结构。{cn1} 以 <b>{a_profiles}</b> 为主导，
              {cn2} 以 <b>{b_profiles}</b> 抗衡，利用差异性创造层次感。
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="diag-block diag-info">
              <b>🔵 平衡搭档</b> — 共享分子比例 {jaccard_pct}%<br>
              风味有交叠也有差异，两者形成良好的互补关系，适合作为底味与提味的组合。<br><br>
              <b>共享节点：</b><br>{render_shared_tags(shared_cn[:8])}
            </div>
            """, unsafe_allow_html=True)

        # 独有风味
        if only_a_cn or only_b_cn:
            col_a, col_b = st.columns(2)
            with col_a:
                a_tags = render_tags([t_note(n) for n in only_a_cn[:6]], "tag-blue")
                st.markdown(f"**{cn1}** 独有<br>{a_tags}", unsafe_allow_html=True)
            with col_b:
                b_tags = render_tags([t_note(n) for n in only_b_cn[:6]], "tag-purple")
                st.markdown(f"**{cn2}** 独有<br>{b_tags}", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # 4) 介质推演（溶解度）
        combined_set = mol_sets[n1] | mol_sets[n2]
        pol = polarity_analysis(combined_set)
        if pol["total"] > 0:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 💧 介质推演")

            lipo_pct = int(pol["lipo"] / pol["total"] * 100)
            hydro_pct = 100 - lipo_pct

            if pol["type"] == "lipophilic":
                st.markdown(f"""
                <div class="diag-block diag-contrast">
                  <b>🫙 脂溶性主导</b>（脂溶 {lipo_pct}% / 水溶 {hydro_pct}%）<br>
                  推荐应用场景：<b>黄油乳化、油封（Confit）、慕斯基底、甘纳许</b>
                </div>
                """, unsafe_allow_html=True)
            elif pol["type"] == "hydrophilic":
                st.markdown(f"""
                <div class="diag-block diag-info">
                  <b>🫗 水溶性主导</b>（水溶 {hydro_pct}% / 脂溶 {lipo_pct}%）<br>
                  推荐应用场景：<b>清汤（Consommé）、澄清果冻、冰沙、浸泡萃取</b>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="diag-block diag-resonance">
                  <b>⚖️ 双亲性平衡</b>（脂溶 {lipo_pct}% / 水溶 {hydro_pct}%）<br>
                  推荐应用场景：<b>乳化酱汁（Emulsion）、泡沫（Espuma）、真空低温萃取</b>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 5) AI 厨师建议
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 👨‍🍳 主厨工艺建议")

        techniques_by_type = {
            "resonance": [
                f"以 **{cn1}** 为基底，用 **{cn2}** 层叠强化相同的芳香分子，在同一维度上形成「风味放大」效果。",
                f"两者共同的风味分子建议通过**低温慢煮（Sous Vide）**保留，避免高温破坏共鸣节点。",
                f"考虑将 **{cn2}** 制成浓缩精华（Reduction），以最小用量激活 **{cn1}** 的风味深度。",
            ],
            "contrast": [
                f"利用 **{cn2}** 的对比维度「切割」{cn1} 的厚重感，建议以 **{r2}%** 作为收尾提味而非前调。",
                f"对比型搭配可在不同阶段引入——先以 **{cn1}** 建立底味，后期用 **{cn2}** 制造味觉转折。",
                f"经典的「切割平衡」技术：将 **{cn2}** 做成细腻的凝胶（Gel），穿插在 **{cn1}** 的质地层间。",
            ],
            "neutral": [
                f"两者适度互补，建议采用**比例递进**——从 {cn1} 的纯净基调出发，逐步引入 {cn2} 的差异维度。",
                f"尝试**真空腌制**让两者在分子层面充分融合，实现比例可控的风味协同。",
                f"可将 **{cn1}** 作为主味质地，**{cn2}** 制成粉末或油脂以提供风味跳跃感。",
            ],
        }

        tip = random.choice(techniques_by_type[sim["type"]])
        st.info(f"💡 {tip}")

        proc_options = ["低温慢煮（Sous Vide）", "乳化（Emulsification）", "真空萃取", "发酵", "烟熏", "冷冻干燥"]
        proc = random.choice(proc_options)
        st.markdown(f"🔧 **推荐工艺**：{proc}")
        st.markdown("</div>", unsafe_allow_html=True)

    # ======================================================
    # 第二行：桥接食材推荐 + 多食材对比
    # ======================================================
    st.markdown("---")
    col_bridge, col_compare = st.columns([1, 1], gap="large")

    with col_bridge:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🌉 风味桥接推荐")
        st.caption(f"寻找能将 **{cn1}** 与 **{cn2}** 串联的「第三食材」")

        bridges = find_bridge_ingredients(df, mol_sets[n1], mol_sets[n2], selected, top_n=4)

        if bridges:
            for bname, bscore, sa, sb in bridges:
                bcn = t_ingredient(bname)
                bcat = t_category(rows[bname]["category"] if bname in [r["name"] for _, r in rows.items()] 
                                   else df[df["name"]==bname].iloc[0]["category"])
                bcat_en = df[df["name"] == bname].iloc[0]["category"] if len(df[df["name"]==bname]) > 0 else ""
                bcat_zh = t_category(bcat_en)
                pct_score = int(bscore * 100)
                pct_a = int(sa * 100)
                pct_b = int(sb * 100)

                st.markdown(f"""
                <div class="ingredient-row" style="margin-bottom:8px">
                  <div style="flex:1">
                    <div style="font-weight:600; color:#222">{bcn} <span style="color:#999; font-size:0.75rem">({bname})</span></div>
                    <div style="font-size:0.75rem; color:#888">{bcat_zh} · 连接力 {pct_score}%</div>
                    <div style="font-size:0.75rem; color:#888; margin-top:2px">
                      与{cn1}共鸣 {pct_a}% &nbsp;|&nbsp; 与{cn2}共鸣 {pct_b}%
                    </div>
                    <div class="progress-bar-bg" style="margin-top:4px">
                      <div class="progress-bar-fill" style="width:{pct_score}%; background:linear-gradient(90deg,#F97316,#FBBF24)"></div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("未找到合适的桥接食材")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_compare:
        if len(selected) > 2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 📊 多食材两两相似度矩阵")

            names = selected[:4]
            matrix_data = []
            for i, na in enumerate(names):
                row_data = []
                for j, nb in enumerate(names):
                    if i == j:
                        row_data.append(100)
                    elif j > i:
                        s = calculate_similarity(mol_sets[na], mol_sets[nb])
                        row_data.append(s["score"])
                    else:
                        s = calculate_similarity(mol_sets[nb], mol_sets[na])
                        row_data.append(s["score"])
                matrix_data.append(row_data)

            cn_names = [t_ingredient(n) for n in names]
            heatmap = go.Figure(go.Heatmap(
                z=matrix_data,
                x=cn_names,
                y=cn_names,
                colorscale=[[0,"#FEE2E2"],[0.5,"#DBEAFE"],[1,"#D1FAE5"]],
                text=[[f"{v}%" for v in row] for row in matrix_data],
                texttemplate="%{text}",
                showscale=False,
                hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>相似度: %{z}%<extra></extra>",
            ))
            heatmap.update_layout(
                height=280,
                margin=dict(t=10, b=30, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickfont=dict(size=11)),
                yaxis=dict(tickfont=dict(size=11)),
            )
            st.plotly_chart(heatmap, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # 显示食材详情卡片
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 📋 食材档案")
            for name in selected[:2]:
                cn = t_ingredient(name)
                row = rows[name]
                mol_count = row["mol_count"]
                cat_zh = t_category(row["category"])
                notes_top5 = t_notes_list(str(row["flavor_profiles"]), top_n=5)

                st.markdown(f"""
                <div style="padding:12px; background:#F8F9FB; border-radius:12px; margin-bottom:10px; border:1px solid #EEE">
                  <div style="font-weight:700; font-size:1rem; color:#111">{cn}</div>
                  <div style="color:#888; font-size:0.78rem; margin:2px 0">{cat_zh} · {mol_count} 个风味分子</div>
                  <div style="margin-top:6px">{render_tags(notes_top5, 'tag-blue')}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ======================================================
    # 底部：数据统计条
    # ======================================================
    st.markdown(f"""
    <div style="text-align:center; padding:16px; color:#BBB; font-size:0.78rem">
      🧬 FlavorDB · {len(df)} 种食材 · {len(LOC.get('flavor_notes',{}))} 个风味词已汉化 · 
      Jaccard 相似度: {int(sim['jaccard']*100)}% · 共享分子: {len(sim['shared'])} 个
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
