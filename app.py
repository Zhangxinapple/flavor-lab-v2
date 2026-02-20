import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import random
import math
from math import sqrt

# ================================================================
# 0. 页面配置（必须第一行）
# ================================================================
st.set_page_config(
    page_title="味觉虫洞 Flavor Lab",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================================================
# 1. 全局样式 — 修复字体颜色与背景同色问题
#    强制所有自定义 HTML 使用明确的颜色，不依赖主题继承
# ================================================================
st.markdown("""
<style>
  /* ── 基础重置 ── */
  .stApp { background: #F4F6FA !important; }
  [data-testid="stSidebar"] {
    background: #FAFBFC !important;
    border-right: 1px solid #E8EAED;
  }
  /* 强制所有卡片文字为深色，防止深色主题下消失 */
  .card, .card * { color: #1A1A2E !important; }
  .card-dark, .card-dark * { color: #FFFFFF !important; }

  /* ── Hero 头部 ── */
  .hero-header {
    background: linear-gradient(135deg, #0A0A1A 0%, #1A1A3E 50%, #0D2137 100%);
    padding: 24px 32px;
    border-radius: 18px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 14px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.25);
  }
  .hero-title {
    font-size: 1.9rem;
    font-weight: 800;
    background: linear-gradient(90deg, #00D2FF, #7B2FF7, #FF6B6B);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
  }
  .hero-sub {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.45) !important;
    margin: 0;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  /* ── 白色卡片 ── */
  .card {
    background: #FFFFFF;
    padding: 22px;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    margin-bottom: 16px;
    border: 1px solid #E8EAED;
  }
  .card h4, .card h3, .card b, .card strong { color: #111827 !important; }
  .card p, .card span, .card div { color: #374151 !important; }

  /* ── 深色卡片（分数区域）── */
  .card-dark {
    background: linear-gradient(135deg, #0A0A1A, #1A1A3E);
    padding: 22px;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    margin-bottom: 16px;
    border: 1px solid rgba(255,255,255,0.1);
    text-align: center;
  }
  .card-dark * { color: #FFFFFF !important; }

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
    font-size: 0.76rem;
    font-weight: 600;
    margin: 2px 2px;
  }
  .tag-blue   { background:#EEF6FF; color:#1D6FDB !important; border:1px solid #BDD7F5; }
  .tag-green  { background:#F0FDF4; color:#16A34A !important; border:1px solid #BBF7D0; }
  .tag-orange { background:#FFF7ED; color:#C2410C !important; border:1px solid #FECBA1; }
  .tag-purple { background:#F5F3FF; color:#7C3AED !important; border:1px solid #DDD6FE; }
  .tag-pink   { background:#FDF2F8; color:#BE185D !important; border:1px solid #FBCFE8; }
  .tag-shared {
    background: linear-gradient(90deg,#E0F7FA,#EDE7F6);
    color: #5B21B6 !important;
    border: 1px solid #C4B5FD;
    font-weight: 700;
  }

  /* ── 徽章 ── */
  .badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 700;
  }
  .badge-resonance { background:#D1FAE5; color:#065F46 !important; }
  .badge-contrast  { background:#FEE2E2; color:#991B1B !important; }
  .badge-neutral   { background:#F3F4F6; color:#374151 !important; }

  /* ── 诊断区块 ── */
  .diag {
    border-radius: 12px;
    padding: 14px 16px;
    margin: 8px 0;
    border-left: 4px solid;
  }
  .diag-res  { background:#F0FDF4; border-color:#22C55E; }
  .diag-ctr  { background:#FFF7ED; border-color:#F97316; }
  .diag-info { background:#EEF6FF; border-color:#3B82F6; }
  .diag b, .diag strong { color: #111827 !important; }

  /* ── 进度条 ── */
  .pbar-bg   { background:#E8EAED; border-radius:6px; height:7px; overflow:hidden; margin:3px 0; }
  .pbar-fill { height:100%; border-radius:6px; }

  /* ── 食材行 ── */
  .ing-row {
    background: #F8F9FB;
    border: 1px solid #EEE;
    border-radius: 10px;
    padding: 10px 14px;
    margin: 5px 0;
  }
  .ing-row * { color: #1A1A2E !important; }

  /* ── section 标题 ── */
  .sec-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9CA3AF !important;
    margin: 14px 0 6px;
  }

  /* ── 隐藏默认元素 ── */
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


def t_ingredient(name: str) -> str:
    m = LOC.get("ingredients", {})
    return m.get(name) or m.get(name.strip()) or name


def t_category(cat: str) -> str:
    return LOC.get("categories", {}).get(cat, cat)


def t_note(note: str) -> str:
    m = LOC.get("flavor_notes", {})
    n = note.strip().lower()
    return m.get(n) or m.get(note.strip()) or note.strip()


def t_notes_list(mol_input, top_n: int = 999) -> list:
    import re as _re2
    if isinstance(mol_input, set):
        raw = sorted(mol_input)
    else:
        raw = [n.strip().lower() for n in _re2.split(r"[@,]+", str(mol_input)) if n.strip()]
    seen, result = set(), []
    for item in (t_note(n) for n in raw):
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result[:top_n]


def display_name(name: str) -> str:
    """食材下拉显示：中文（英文）或纯中文"""
    cn = t_ingredient(name)
    return f"{cn}（{name}）" if cn != name else cn


# ================================================================
# 3. 数据加载
#    数据库有两个风味列，需要同时解析后取并集：
#    - flavor_profiles：逗号分隔，50条（主要是酒类/烘焙）
#    - flavors：@ 和 , 混合分隔，501条（绝大多数食材）
# ================================================================
import re as _re

def _parse_fp(s) -> set:
    """解析 flavor_profiles 列（逗号分隔）"""
    if not s or str(s).strip() in ("", "nan"):
        return set()
    return set(t.strip().lower() for t in str(s).split(",") if t.strip())

def _parse_fl(s) -> set:
    """解析 flavors 列（@ 和 , 混合分隔）"""
    if not s or str(s).strip() in ("", "nan"):
        return set()
    return set(t.strip().lower() for t in _re.split(r"[@,]+", str(s)) if t.strip())

@st.cache_data
def load_data():
    path = "flavordb_data.csv"
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df["flavor_profiles"] = df["flavor_profiles"].fillna("")

    # 核心修复：合并两列取并集，解锁全部 551 种食材
    def merge_mol(row):
        return _parse_fp(row["flavor_profiles"]) | _parse_fl(row.get("flavors", ""))

    df["mol_set"] = df.apply(merge_mol, axis=1)
    df["mol_count"] = df["mol_set"].apply(len)

    # 只保留有风味数据的行
    df = df[df["mol_count"] > 0].copy()
    return df


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

def calc_sim(a: set, b: set) -> dict:
    inter = a & b
    union = a | b
    j = len(inter) / len(union) if union else 0
    w = min(1.0, (len(inter) / max(len(a), len(b), 1)) * 1.5)
    score = int(min(97, max(50, j * 250 + w * 120)))
    typ = "resonance" if j >= 0.35 else ("contrast" if j < 0.12 else "neutral")
    return {"score": score, "jaccard": j, "shared": sorted(inter),
            "only_a": sorted(a - b), "only_b": sorted(b - a), "type": typ}


def polarity_analysis(mol_set: set) -> dict:
    lipo = sum(1 for m in mol_set if POLARITY.get(m) == "L")
    hydro = sum(1 for m in mol_set if POLARITY.get(m) == "H")
    total = lipo + hydro
    if total == 0:
        return {"type": "balanced", "lipo": 0, "hydro": 0, "total": 0}
    t = "lipophilic" if lipo > hydro else ("hydrophilic" if hydro > lipo else "balanced")
    return {"type": t, "lipo": lipo, "hydro": hydro, "total": total}


def find_bridges(df, set_a, set_b, selected, top_n=4):
    results = []
    for _, row in df.iterrows():
        if row["name"] in selected:
            continue
        s = row["mol_set"]
        sa = len(s & set_a) / max(len(set_a), 1)
        sb = len(s & set_b) / max(len(set_b), 1)
        score = sqrt(sa * sb) * (1 + min(sa, sb))
        if score > 0.04:
            results.append((row["name"], score, sa, sb))
    results.sort(key=lambda x: -x[1])
    return results[:top_n]


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

def radar_vals(mol_set: set) -> dict:
    result = {}
    for dim, kws in RADAR_DIMS.items():
        hit = sum(1 for k in kws if k in mol_set)
        result[dim] = min(10, hit * 2.0 + (0.8 if hit > 0 else 0))
    return result


# ================================================================
# 5. HTML 辅助
# ================================================================
TAG_CLASSES = ["tag-blue","tag-green","tag-orange","tag-purple","tag-pink"]

def score_color(s):
    return "#22C55E" if s >= 80 else ("#3B82F6" if s >= 65 else ("#F97316" if s >= 50 else "#EF4444"))

def tags_html(notes, cls="tag-blue", max_n=8):
    return " ".join(f'<span class="tag {cls}">{n}</span>' for n in notes[:max_n])

def shared_tags_html(notes, max_n=10):
    return " ".join(f'<span class="tag tag-shared">⚡ {t_note(n)}</span>' for n in notes[:max_n])


# ================================================================
# 6. 主界面
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

        # BUG FIX 1：分类筛选改为普通 multiselect（不用 expander），确保全部34个分类正常显示
        all_cats = sorted(df["category"].unique().tolist())

        # 构建 中文（英文）→ 英文 的映射
        cat_display = {f"{t_category(c)}（{c}）": c for c in all_cats}
        cat_labels = list(cat_display.keys())

        st.markdown('<div class="sec-label">🗂 按分类筛选（不选 = 全部）</div>', unsafe_allow_html=True)
        selected_cat_labels = st.multiselect(
            label="分类",
            options=cat_labels,
            default=[],
            label_visibility="collapsed",
            key="cat_filter"
        )
        if selected_cat_labels:
            chosen_en = [cat_display[l] for l in selected_cat_labels]
            df_show = df[df["category"].isin(chosen_en)]
        else:
            df_show = df

        # Vegan 开关
        is_vegan = st.toggle("🍃 仅植物基 Vegan", value=False)
        if is_vegan:
            excl = ["meat","dairy","fish","seafood","pork","beef","chicken","egg"]
            df_show = df_show[~df_show["category"].str.lower().apply(
                lambda c: any(kw in c for kw in excl)
            )]

        # BUG FIX 2：食材选择 — format_func 用 display_name 确保全部汉化
        total_n = len(df_show)
        st.markdown(f'<div class="sec-label">已解锁 {total_n} 种食材</div>', unsafe_allow_html=True)
        options = sorted(df_show["name"].unique().tolist())
        defaults = [n for n in ["Coffee","Strawberry"] if n in options]
        if not defaults:
            defaults = options[:2]

        selected = st.multiselect(
            label="选择食材（2-4种）",
            options=options,
            default=defaults,
            format_func=display_name,   # ← 每个选项都经过翻译
            help="最多支持4种食材同时分析",
            key="ing_select"
        )

        # 比例滑块
        ratios = {}
        if len(selected) >= 2:
            st.markdown('<div class="sec-label">⚖️ 配方比例</div>', unsafe_allow_html=True)
            raw_total = 0
            for name in selected:
                cn = t_ingredient(name)
                default_v = 100 // len(selected)
                ratios[name] = st.slider(cn, 0, 100, default_v, 5, key=f"r_{name}")
                raw_total += ratios[name]
            if raw_total > 0:
                ratios = {k: v / raw_total for k, v in ratios.items()}

        st.divider()
        st.caption("数据来源：FlavorDB · 555 种食材 · 464 个风味维度")

    # ── 主区域 ──
    if len(selected) < 2:
        st.markdown("""
        <div class="card" style="text-align:center;padding:60px 20px">
          <div style="font-size:3.5rem">🌀</div>
          <h2 style="color:#9CA3AF;font-weight:400;margin:12px 0">请在左侧选择 2-4 种食材</h2>
          <p style="color:#D1D5DB">系统将自动分析分子相似度、风味维度与桥接路径</p>
        </div>
        """, unsafe_allow_html=True)
        return

    rows = {n: df[df["name"] == n].iloc[0] for n in selected}
    mol_sets = {n: rows[n]["mol_set"] for n in selected}
    n1, n2 = selected[0], selected[1]
    sim = calc_sim(mol_sets[n1], mol_sets[n2])
    cn1, cn2 = t_ingredient(n1), t_ingredient(n2)

    col_left, col_right = st.columns([1.35, 1], gap="large")

    # ===== 左栏 =====
    with col_left:

        # 雷达图
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🔭 风味维度雷达图")
        palette = [("#00D2FF","rgba(0,210,255,0.15)"),
                   ("#7B2FF7","rgba(123,47,247,0.15)"),
                   ("#FF6B6B","rgba(255,107,107,0.15)"),
                   ("#00E676","rgba(0,230,118,0.15)")]
        fig_radar = go.Figure()
        dims = list(RADAR_DIMS.keys())
        for i, name in enumerate(selected[:4]):
            rv = radar_vals(mol_sets[name])
            vals = [rv[d] for d in dims]
            ratio_scale = 0.5 + ratios.get(name, 1/len(selected)) * 0.5 * len(selected)
            vals_s = [min(10, v * ratio_scale) for v in vals]
            vals_s += [vals_s[0]]
            lc, fc = palette[i]
            pct = int(ratios.get(name, 1/len(selected)) * 100)
            fig_radar.add_trace(go.Scatterpolar(
                r=vals_s, theta=dims + [dims[0]],
                fill="toself", fillcolor=fc,
                line=dict(color=lc, width=2.5),
                name=f"{t_ingredient(name)} ({pct}%)"
            ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor="rgba(248,249,255,0.6)",
                radialaxis=dict(visible=True, range=[0,10], tickfont=dict(size=9,color="#9CA3AF")),
                angularaxis=dict(tickfont=dict(size=12,color="#374151")),
            ),
            showlegend=True,
            legend=dict(orientation="h", y=-0.15, font=dict(size=11,color="#374151")),
            height=420, margin=dict(t=20,b=70,l=40,r=40),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 分子网络图
        if sim["shared"]:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 🕸 分子连线网络图")
            shared_top = sim["shared"][:14]
            nx_list, ny_list, ntxt, nclr, nsz = [], [], [], [], []
            ex, ey = [], []

            nx_list += [-1.6, 1.6];  ny_list += [0, 0]
            ntxt += [cn1, cn2];  nclr += ["#00D2FF","#7B2FF7"];  nsz += [30, 30]

            for idx, note in enumerate(shared_top):
                angle = math.pi/2 + idx * 2 * math.pi / len(shared_top)
                r = 1.15
                px, py = r * math.cos(angle), r * math.sin(angle)
                nx_list.append(px);  ny_list.append(py)
                ntxt.append(t_note(note));  nclr.append("#F97316");  nsz.append(13)
                for sx, sy in [(-1.6,0),(1.6,0)]:
                    ex += [sx, px, None];  ey += [sy, py, None]

            fig_net = go.Figure()
            fig_net.add_trace(go.Scatter(x=ex, y=ey, mode="lines",
                line=dict(color="rgba(150,150,200,0.25)", width=1.2),
                hoverinfo="none", showlegend=False))
            fig_net.add_trace(go.Scatter(
                x=nx_list, y=ny_list, mode="markers+text",
                text=ntxt, textposition="top center",
                textfont=dict(size=10, color="#374151"),
                marker=dict(color=nclr, size=nsz,
                    line=dict(width=2, color="white"), opacity=0.92),
                hoverinfo="text", showlegend=False))
            fig_net.update_layout(
                height=300, margin=dict(t=10,b=10,l=10,r=10),
                xaxis=dict(visible=False), yaxis=dict(visible=False),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(248,249,255,0.5)",
            )
            st.plotly_chart(fig_net, use_container_width=True)
            st.caption(f"🔵 {cn1}  🟣 {cn2}  🟠 共享节点（共 {len(sim['shared'])} 个）")
            st.markdown("</div>", unsafe_allow_html=True)

    # ===== 右栏 =====
    with col_right:

        # 评分卡
        sc = sim["score"]
        sc_c = score_color(sc)
        type_info = {
            "resonance": ("同源共振", "badge-resonance", "共享大量芳香分子，协同延长风味余韵"),
            "contrast":  ("对比碰撞", "badge-contrast",  "差异显著，形成张力对比切割"),
            "neutral":   ("平衡搭档", "badge-neutral",   "适度交叠，互补平衡"),
        }
        tlabel, tbadge, tdesc = type_info[sim["type"]]
        r1 = int(ratios.get(n1, 0.5)*100)
        r2 = int(ratios.get(n2, 0.5)*100)

        # BUG FIX 3：深色卡片内所有文字明确写白色，不依赖继承
        st.markdown(f"""
        <div class="card-dark">
          <div style="color:rgba(255,255,255,0.5);font-size:0.72rem;letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px">
            分子共鸣指数
          </div>
          <span class="score-big" style="color:{sc_c}">{sc}<span style="font-size:2rem;font-weight:400;color:{sc_c}">%</span></span>
          <div style="margin:12px 0">
            <span class="badge {tbadge}">{tlabel}</span>
          </div>
          <div style="color:rgba(255,255,255,0.65);font-size:0.82rem">{tdesc}</div>
          <div style="margin-top:12px;color:rgba(255,255,255,0.4);font-size:0.78rem">
            {cn1} {r1}% &nbsp;·&nbsp; {cn2} {r2}%
          </div>
        </div>
        """, unsafe_allow_html=True)

        # 风味指纹
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h4 style='color:#111827'>🧪 风味指纹</h4>", unsafe_allow_html=True)
        for i, name in enumerate(selected):
            cn = t_ingredient(name)
            notes_cn = t_notes_list(rows[name]["mol_set"], top_n=10)
            pct = int(ratios.get(name, 1/len(selected))*100)
            cls = TAG_CLASSES[i % len(TAG_CLASSES)]
            dom = ""
            if pct >= 40:
                dom = '<span style="background:#FEF3C7;color:#92400E;font-size:.69rem;padding:1px 7px;border-radius:8px;margin-left:6px;font-weight:700">主导</span>'
            elif pct <= 15:
                dom = '<span style="background:#E0F2FE;color:#0369A1;font-size:.69rem;padding:1px 7px;border-radius:8px;margin-left:6px;font-weight:700">提味</span>'
            st.markdown(f"""
            <div style="margin-bottom:12px">
              <div style="font-weight:700;color:#111827;margin-bottom:3px">
                {cn} <span style="color:#9CA3AF;font-weight:400;font-size:.78rem">{pct}%</span>{dom}
              </div>
              <div class="pbar-bg">
                <div class="pbar-fill" style="width:{pct}%;background:linear-gradient(90deg,#00D2FF,#7B2FF7)"></div>
              </div>
              <div style="margin-top:5px">{tags_html(notes_cn, cls, 8)}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 深度诊断
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h4 style='color:#111827'>🔬 深度诊断</h4>", unsafe_allow_html=True)
        jpct = int(sim["jaccard"]*100)
        shared_cn = sim["shared"]
        if sim["type"] == "resonance":
            st.markdown(f"""
            <div class="diag diag-res">
              <b>✅ 高度共振</b> — 共享风味分子比例 {jpct}%<br>
              <span style="color:#374151">两者拥有大量相同的芳香分子，结合后将显著延长风味余韵，主副调高度协同。</span><br><br>
              <b>共享节点：</b><br>{shared_tags_html(shared_cn[:10])}
            </div>
            """, unsafe_allow_html=True)
        elif sim["type"] == "contrast":
            a3 = " / ".join(t_notes_list(rows[n1]["mol_set"], 3))
            b3 = " / ".join(t_notes_list(rows[n2]["mol_set"], 3))
            st.markdown(f"""
            <div class="diag diag-ctr">
              <b>⚡ 对比碰撞</b> — 共享分子比例 {jpct}%<br>
              <span style="color:#374151">经典「切割平衡（Cut-through）」结构。{cn1} 以 <b>{a3}</b> 为主导，{cn2} 以 <b>{b3}</b> 抗衡，差异性创造层次感。</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="diag diag-info">
              <b>🔵 平衡搭档</b> — 共享分子比例 {jpct}%<br>
              <span style="color:#374151">风味有交叠也有差异，形成良好的互补关系，适合底味与提味组合。</span><br><br>
              <b>共享节点：</b><br>{shared_tags_html(shared_cn[:8])}
            </div>
            """, unsafe_allow_html=True)

        # 独有分子
        oa = sim["only_a"][:6];  ob = sim["only_b"][:6]
        if oa or ob:
            ca2, cb2 = st.columns(2)
            with ca2:
                st.markdown(f"<div style='color:#111827;font-size:.82rem;font-weight:700;margin-bottom:4px'>{cn1} 独有</div>", unsafe_allow_html=True)
                st.markdown(tags_html([t_note(n) for n in oa], "tag-blue"), unsafe_allow_html=True)
            with cb2:
                st.markdown(f"<div style='color:#111827;font-size:.82rem;font-weight:700;margin-bottom:4px'>{cn2} 独有</div>", unsafe_allow_html=True)
                st.markdown(tags_html([t_note(n) for n in ob], "tag-purple"), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 介质推演
        combined = mol_sets[n1] | mol_sets[n2]
        pol = polarity_analysis(combined)
        if pol["total"] > 0:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h4 style='color:#111827'>💧 介质推演</h4>", unsafe_allow_html=True)
            lp = int(pol["lipo"]/pol["total"]*100)
            hp = 100 - lp
            if pol["type"] == "lipophilic":
                st.markdown(f"""
                <div class="diag diag-ctr">
                  <b style="color:#111827">🫙 脂溶性主导</b>
                  <span style="color:#6B7280">（脂溶 {lp}% / 水溶 {hp}%）</span><br>
                  <span style="color:#374151">推荐：<b>黄油乳化、油封 Confit、慕斯基底、甘纳许</b></span>
                </div>
                """, unsafe_allow_html=True)
            elif pol["type"] == "hydrophilic":
                st.markdown(f"""
                <div class="diag diag-info">
                  <b style="color:#111827">🫗 水溶性主导</b>
                  <span style="color:#6B7280">（水溶 {hp}% / 脂溶 {lp}%）</span><br>
                  <span style="color:#374151">推荐：<b>清汤 Consommé、澄清冻、冰沙、浸泡萃取</b></span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="diag diag-res">
                  <b style="color:#111827">⚖️ 双亲性平衡</b>
                  <span style="color:#6B7280">（脂溶 {lp}% / 水溶 {hp}%）</span><br>
                  <span style="color:#374151">推荐：<b>乳化酱汁、泡沫 Espuma、真空低温萃取</b></span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 主厨建议
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h4 style='color:#111827'>👨‍🍳 主厨工艺建议</h4>", unsafe_allow_html=True)
        tips_pool = {
            "resonance": [
                f"以 **{cn1}** 为基底，将 **{cn2}** 浓缩后叠加，在同一芳香维度形成「风味放大」效果。",
                f"两者共享的芳香分子建议通过 **低温慢煮（Sous Vide）** 保留，避免高温破坏共鸣节点。",
                f"将 **{cn2}** 制成浓缩精华 Reduction，以最小用量激活 **{cn1}** 的风味深度。",
            ],
            "contrast": [
                f"利用 **{cn2}** 的对比维度「切割」{cn1} 的厚重感，建议作为收尾提味而非前调。",
                f"对比型搭配分阶段引入——先以 **{cn1}** 建立底味，后期用 **{cn2}** 制造味觉转折。",
                f"将 **{cn2}** 做成凝胶 Gel，穿插在 **{cn1}** 的质地层间制造对比。",
            ],
            "neutral": [
                f"比例递进策略：从 {cn1} 的纯净基调出发，逐步引入 {cn2} 的差异维度。",
                f"真空腌制让两者在分子层面充分融合，实现比例可控的风味协同。",
                f"将 **{cn1}** 作为主味质地，**{cn2}** 制成粉末或油脂提供风味跳跃感。",
            ],
        }
        tip = random.choice(tips_pool[sim["type"]])
        procs = ["低温慢煮（Sous Vide）","乳化（Emulsification）","真空萃取","发酵","烟熏","冷冻干燥"]
        proc = random.choice(procs)
        st.info(f"💡 {tip}")
        st.markdown(f"<p style='color:#374151'>🔧 <b>推荐工艺：</b>{proc}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 第二行：桥接 + 对比 ──
    st.markdown("---")
    cb, cc = st.columns([1, 1], gap="large")

    with cb:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"<h4 style='color:#111827'>🌉 风味桥接推荐</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#6B7280;font-size:.82rem'>寻找能串联 <b>{cn1}</b> 与 <b>{cn2}</b> 的「第三食材」</p>", unsafe_allow_html=True)
        bridges = find_bridges(df, mol_sets[n1], mol_sets[n2], selected)
        if bridges:
            for bname, bsc, sa, sb in bridges:
                bcn = t_ingredient(bname)
                bcat_en = df[df["name"]==bname].iloc[0]["category"] if len(df[df["name"]==bname]) > 0 else ""
                bcat_zh = t_category(bcat_en)
                ps = int(bsc*100); pa = int(sa*100); pb = int(sb*100)
                st.markdown(f"""
                <div class="ing-row">
                  <div style="font-weight:700;color:#111827">{bcn}
                    <span style="color:#9CA3AF;font-size:.75rem;font-weight:400"> {bname}</span>
                  </div>
                  <div style="font-size:.74rem;color:#6B7280">{bcat_zh} · 连接力 {ps}%</div>
                  <div style="font-size:.74rem;color:#6B7280">与{cn1} {pa}% | 与{cn2} {pb}%</div>
                  <div class="pbar-bg" style="margin-top:5px">
                    <div class="pbar-fill" style="width:{ps}%;background:linear-gradient(90deg,#F97316,#FBBF24)"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("未找到合适的桥接食材")
        st.markdown("</div>", unsafe_allow_html=True)

    with cc:
        if len(selected) > 2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h4 style='color:#111827'>📊 多食材相似度矩阵</h4>", unsafe_allow_html=True)
            names = selected[:4]
            mat = []
            for na in names:
                row_d = []
                for nb in names:
                    if na == nb:
                        row_d.append(100)
                    else:
                        s = calc_sim(mol_sets[na], mol_sets[nb])
                        row_d.append(s["score"])
                mat.append(row_d)
            cn_names = [t_ingredient(n) for n in names]
            hm = go.Figure(go.Heatmap(
                z=mat, x=cn_names, y=cn_names,
                colorscale=[[0,"#FEE2E2"],[0.5,"#DBEAFE"],[1,"#D1FAE5"]],
                text=[[f"{v}%" for v in r] for r in mat],
                texttemplate="%{text}", showscale=False,
                hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>%{z}%<extra></extra>",
            ))
            hm.update_layout(height=270, margin=dict(t=10,b=30,l=10,r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickfont=dict(size=11,color="#374151")),
                yaxis=dict(tickfont=dict(size=11,color="#374151")),
            )
            st.plotly_chart(hm, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # 食材档案
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h4 style='color:#111827'>📋 食材档案</h4>", unsafe_allow_html=True)
            for i, name in enumerate(selected[:2]):
                cn = t_ingredient(name)
                row = rows[name]
                mc = row["mol_count"]
                cz = t_category(row["category"])
                n5 = t_notes_list(row["mol_set"], 5)
                cls = TAG_CLASSES[i % len(TAG_CLASSES)]
                st.markdown(f"""
                <div class="ing-row" style="margin-bottom:10px">
                  <div style="font-weight:700;font-size:.95rem;color:#111827">{cn}</div>
                  <div style="color:#6B7280;font-size:.76rem;margin:2px 0">{cz} · {mc} 个风味分子</div>
                  <div style="margin-top:5px">{tags_html(n5, cls)}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # 底部统计条
    st.markdown(f"""
    <div style="text-align:center;padding:14px;color:#9CA3AF;font-size:.76rem">
      🧬 FlavorDB · {len(df)} 种食材 · {len(LOC.get('ingredients',{}))} 个食材已汉化 ·
      共享分子 {len(sim['shared'])} 个 · Jaccard {int(sim['jaccard']*100)}%
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
