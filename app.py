import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random
import os

# ==========================================
# 1. 核心 AI 引擎与汉化配置
# ==========================================
class TasteWormholeAgent:
    def __init__(self):
        # 全链路汉化映射表
        self.name_map = {
            # --- 基础食材 ---
            "coffee": "咖啡", "dark chocolate": "黑巧克力", "white chocolate": "白巧克力",
            "milk": "牛奶", "butter": "黄油", "cheese": "芝士", "cream": "奶油",
            "egg": "鸡蛋", "honey": "蜂蜜", "vanilla": "香草",
            
            # --- 水果蔬菜 ---
            "strawberry": "草莓", "apple": "苹果", "banana": "香蕉", "lemon": "柠檬",
            "orange": "橙子", "grape": "葡萄", "mango": "芒果", "pineapple": "菠萝",
            "tomato": "番茄", "potato": "土豆", "carrot": "胡萝卜", "onion": "洋葱",
            "garlic": "大蒜", "ginger": "生姜", "cucumber": "黄瓜", "mushroom": "蘑菇",
            
            # --- 肉类海鲜 ---
            "pork": "猪肉", "beef": "牛肉", "chicken": "鸡肉", "lamb": "羊肉",
            "shrimp": "虾", "crab": "螃蟹", "salmon": "三文鱼", "tuna": "金枪鱼",
            
            # --- 调味与酒 ---
            "soy sauce": "酱油", "vinegar": "醋", "wine": "红酒", "beer": "啤酒",
            "black tea": "红茶", "green tea": "绿茶", "roasted hazelnut": "烤榛子",
            
            # --- 风味维度 (雷达图专用) ---
            "sweet": "甜美度", "roasted": "烘焙感", "fruity": "果香值",
            "herbaceous": "草本力", "woody": "木质调", "spicy": "辛辣感",
            "fatty": "油脂感", "floral": "花香", "sour": "酸度", "bitter": "苦度"
        }
        
        # 预设的专家建议模板
        self.templates = [
            "利用 {0} 的挥发性分子激发 {1} 的深层香气。",
            "{0} 中的醛类物质能完美平衡 {1} 的油腻感。",
            "这是一场经典的撞色实验：{0} 提供骨架，{1} 提供灵魂。",
            "在分子层面，{0} 与 {1} 共享关键的呈味基因。",
        ]

# 初始化 AI 助理
agent = TasteWormholeAgent()

# ==========================================
# 2. 数据加载与处理模块
# ==========================================
@st.cache_data
def load_data():
    # 尝试读取数据
    possible_paths = ["flavordb_data.csv"]
    df = None
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                break
            except:
                continue
    
    if df is None:
        return None

    # 数据清洗：使用 flavor_profiles 列
    df['flavor_profiles'] = df['flavor_profiles'].fillna('')
    # 创建分子集合用于计算相似度
    df['mol_set'] = df['flavor_profiles'].apply(
        lambda x: set(str(x).replace(',', ' ').lower().split()) if x else set()
    )
    # 过滤无效数据
    df = df[df['flavor_profiles'].str.len() > 2]
    return df

# ==========================================
# 3. 界面 UI 设置
# ==========================================
st.set_page_config(page_title="味觉虫洞 Flavor Lab", page_icon="🧬", layout="wide")

# 注入 Apple 风格 CSS
st.markdown("""
<style>
    .stApp { background-color: #F5F5F7; }
    h1, h2, h3 { font-family: -apple-system, BlinkMacSystemFont, sans-serif; letter-spacing: -0.5px; }
    .card {
        background: white; padding: 25px; border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05); margin-bottom: 20px;
        border: 1px solid rgba(0,0,0,0.02); transition: transform 0.2s;
    }
    .metric-box { text-align: center; padding: 10px; }
    .big-number { font-size: 2.5rem; font-weight: 700; color: #1D1D1F; }
    .label { font-size: 0.9rem; color: #86868B; text-transform: uppercase; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 主程序逻辑
# ==========================================
def main():
    st.markdown("# 🧬 味觉虫洞 Flavor Lab <span style='font-size:1.2rem; color:#86868B; font-weight:400'>v2.1</span>", unsafe_allow_html=True)
    
    df = load_data()
    
    if df is None:
        st.error("🚨 核心数据库丢失！请将 flavordb_data.csv 上传至 GitHub 仓库根目录。")
        st.stop()

    # --- 侧边栏 ---
    with st.sidebar:
        st.header("🔬 实验参数")
        
        # 汉化选择列表
        all_ingredients = sorted(df['name'].unique())
        
        # 汉化显示函数
        def format_func(name):
            cn = agent.name_map.get(name, name)
            return f"{cn} ({name})" if cn != name else name
            
        selected = st.multiselect(
            "选择食材 (建议 2-4 种)",
            options=all_ingredients,
            default=["coffee", "dark chocolate"] if "coffee" in all_ingredients else None,
            format_func=format_func
        )
        
        st.info(f"📚 当前数据库已收录 {len(df)} 种食材分子数据")

    # --- 主界面内容 ---
    if len(selected) < 2:
        st.warning("👈 请在左侧至少选择 2 种食材来启动虫洞引擎...")
        st.stop()

    # 布局：左侧雷达图，右侧 AI 报告
    col1, col2 = st.columns([1.2, 1])

    # --- 左侧：风味星图 ---
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🔭 风味维度星图")
        
        # 定义雷达图维度
        dims_map = {
            "sweet": "甜美度", "roasted": "烘焙感", "fruity": "果香值",
            "herbaceous": "草本力", "woody": "木质调", "spicy": "辛辣感"
        }
        
        fig = go.Figure()
        
        for name in selected:
            row = df[df['name'] == name]
            if row.empty: continue
            
            # 获取风味文本
            profile_text = str(row['flavor_profiles'].values[0]).lower()
            
            # 计算雷达图数值
            values = []
            for eng_key in dims_map.keys():
                count = profile_text.count(eng_key)
                # 算法：基础分 + 频率加权
                score = min(10.0, 3.0 + count * 2.0) if count > 0 else 1.5
                values.append(score)
            
            # 闭合图形
            values.append(values[0])
            labels = list(dims_map.values()) + [list(dims_map.values())[0]]
            
            # 获取中文名
            cn_name = agent.name_map.get(name, name)
            
            fig.add_trace(go.Scatterpolar(
                r=values, theta=labels, fill='toself', name=f"✨ {cn_name}"
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], showticklabels=False),
                angularaxis=dict(tickfont=dict(size=14, color="#333"))
            ),
            margin=dict(t=30, b=30, l=40, r=40),
            height=450,
            showlegend=True,
            legend=dict(orientation="h", y=-0.1)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 右侧：AI 实验报告 ---
    with col2:
        # 计算共鸣分 (基于 Jaccard 相似度)
        sets = [set(df[df['name']==n]['mol_set'].values[0]) for n in selected]
        intersection = set.intersection(*sets) if sets else set()
        union = set.union(*sets) if sets else set()
        
        score = int((len(intersection) / len(union)) * 100) if union else 0
        display_score = min(98, max(score * 5 + 40, 60)) # 调整分数显示让用户更开心

        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        # 分数展示
        st.markdown(f"""
        <div class="metric-box">
            <div class="label">MOLECULAR RESONANCE</div>
            <div class="big-number" style="color: {'#34C759' if display_score > 80 else '#FF9500'}">
                {display_score}%
            </div>
            <div class="label">分子共鸣指数</div>
        </div>
        <hr style="opacity:0.2">
        """, unsafe_allow_html=True)

        # 动态生成报告
        st.markdown("#### 🧪 实验结论")
        
        # 汉化食材名列表
        cn_names = [agent.name_map.get(n, n) for n in selected]
        names_str = " + ".join(cn_names)
        
        # 生成文案
        if display_score > 85:
            analysis = f"完美匹配！**{cn_names[0]}** 与 **{cn_names[1]}** 在分子层面存在极强的同源性。"
            effect = "极光效应：能产生如同交响乐般的和谐共鸣。"
        elif display_score > 70:
            analysis = f"这是一个有趣的平衡。**{cn_names[0]}** 提供了基调，而 **{cn_names[1]}** 带来了必要的跳跃感。"
            effect = "维度补偿：彼此填补了味觉频谱的空白。"
        else:
            analysis = f"**{cn_names[0]}** 和 **{cn_names[1]}** 属于大胆的冲突美学。"
            effect = "味觉撞击：建议通过低温慢煮融合风味差异。"

        st.write(analysis)
        st.info(f"🌀 **{effect}**")
        
        st.markdown("#### 👨‍🍳 厨师建议")
        suggestion = random.choice(agent.templates).format(cn_names[0], cn_names[1])
        st.write(suggestion)
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
