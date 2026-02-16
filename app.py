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
        # --- 全链路汉化映射表 (这里定义了显示的名字) ---
        self.name_map = {
            # 基础食材
            "coffee": "咖啡", "dark chocolate": "黑巧克力", "white chocolate": "白巧克力",
            "milk": "牛奶", "butter": "黄油", "cheese": "芝士", "cream": "奶油",
            "egg": "鸡蛋", "honey": "蜂蜜", "vanilla": "香草", "bread": "面包",
            
            # 水果蔬菜
            "strawberry": "草莓", "apple": "苹果", "banana": "香蕉", "lemon": "柠檬",
            "orange": "橙子", "grape": "葡萄", "mango": "芒果", "pineapple": "菠萝",
            "tomato": "番茄", "potato": "土豆", "carrot": "胡萝卜", "onion": "洋葱",
            "garlic": "大蒜", "ginger": "生姜", "cucumber": "黄瓜", "mushroom": "蘑菇",
            "corn": "玉米", "spinach": "菠菜", "pumpkin": "南瓜", "lime": "青柠",
            
            # 肉类海鲜
            "pork": "猪肉", "beef": "牛肉", "chicken": "鸡肉", "lamb": "羊肉",
            "shrimp": "虾", "crab": "螃蟹", "salmon": "三文鱼", "tuna": "金枪鱼",
            "bacon": "培根", "ham": "火腿", "oyster": "生蚝",
            
            # 坚果与酒
            "almond": "杏仁", "peanut": "花生", "walnut": "核桃", "hazelnut": "榛子",
            "wine": "红酒", "beer": "啤酒", "rum": "朗姆酒", "whisky": "威士忌",
            "soy sauce": "酱油", "vinegar": "醋", "black tea": "红茶", "green tea": "绿茶",
            
            # --- 风味维度 (雷达图专用) ---
            "sweet": "甜美度", "roasted": "烘焙感", "fruity": "果香值",
            "herbaceous": "草本力", "woody": "木质调", "spicy": "辛辣感",
            "fatty": "油脂感", "floral": "花香", "sour": "酸度", "bitter": "苦度"
        }
        
        # --- 厨师建议模板 ---
        self.templates = [
            "💡 **主厨灵感**：利用 {0} 的挥发性分子激发 {1} 的深层香气，建议尝试低温慢煮。",
            "💡 **分子技巧**：{0} 中的醛类物质能完美平衡 {1} 的油脂感，适合制作前菜。",
            "💡 **结构重组**：这是一场经典的撞色实验：以 {0} 为骨架，让 {1} 充当风味的灵魂。",
            "💡 **融合建议**：在分子层面，{0} 与 {1} 共享关键的呈味基因，可以尝试制作慕斯或泡沫。",
        ]

# 初始化 AI 助理
agent = TasteWormholeAgent()

# ==========================================
# 2. 数据加载与处理模块 (修正 555 种食材问题)
# ==========================================
@st.cache_data
def load_data():
    # 强制读取 CSV
    if os.path.exists("flavordb_data.csv"):
        df = pd.read_csv("flavordb_data.csv")
    else:
        return None

    # --- 关键修正：使用 flavor_profiles 列而不是 flavors ---
    # 这一步决定了你能看到 555 个食材还是 60 个
    df['flavor_profiles'] = df['flavor_profiles'].fillna('')
    
    # 过滤：只要风味描述长度大于2的都保留
    df = df[df['flavor_profiles'].str.len() > 2]
    
    # 创建分子集合 (用于计算相似度)
    df['mol_set'] = df['flavor_profiles'].apply(
        lambda x: set(str(x).replace(',', ' ').lower().split()) if x else set()
    )
    return df

# ==========================================
# 3. 界面 UI 设置
# ==========================================
st.set_page_config(page_title="味觉虫洞 Flavor Lab V3.0", page_icon="🧬", layout="wide")

# 注入 Apple 风格 CSS
st.markdown("""
<style>
    .stApp { background-color: #F5F5F7; }
    .card {
        background: white; padding: 25px; border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .metric-title { font-size: 0.9rem; color: #86868B; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 2.5rem; font-weight: 700; color: #1D1D1F; }
    .highlight { background-color: #e3f2fd; padding: 2px 6px; border-radius: 4px; color: #007aff; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 主程序逻辑
# ==========================================
def main():
    st.markdown("# 🧬 味觉虫洞 Flavor Lab <span style='font-size:1rem; color:#86868B;'>V3.0 Pro</span>", unsafe_allow_html=True)
    
    df = load_data()
    
    if df is None:
        st.error("🚨 数据库丢失！请检查 GitHub 根目录是否有 flavordb_data.csv")
        st.stop()

    # --- 侧边栏 (全汉化逻辑) ---
    with st.sidebar:
        st.header("🔬 实验参数")
        
        # 1. 获取所有食材
        all_ingredients = sorted(df['name'].unique())
        
        # 2. 定义显示格式：中文 (英文)
        def format_func(name):
            cn = agent.name_map.get(name, name) # 查字典，查不到就用原名
            return f"{cn} ({name})" if cn != name else name
            
        # 3. 选择框
        selected = st.multiselect(
            f"已加载 {len(df)} 种分子食材，请选择配对：",
            options=all_ingredients,
            default=["coffee", "dark chocolate"] if "coffee" in all_ingredients else None,
            format_func=format_func
        )
        
        if len(selected) < 2:
            st.info("👈 请至少选择 2 种食材启动分析")

    # --- 主界面内容 ---
    if len(selected) >= 2:
        col1, col2 = st.columns([1.3, 1])

        # === 左侧：汉化雷达图 ===
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🔭 风味维度星图")
            
            # 定义雷达图维度映射
            dims_map = {
                "sweet": "甜美度", "roasted": "烘焙感", "fruity": "果香值",
                "herbaceous": "草本力", "woody": "木质调", "spicy": "辛辣感"
            }
            
            fig = go.Figure()
            
            for name in selected:
                row = df[df['name'] == name]
                if row.empty: continue
                
                # 读取描述文本
                profile_text = str(row['flavor_profiles'].values[0]).lower()
                
                # 计算数值
                values = []
                for eng_key in dims_map.keys():
                    count = profile_text.count(eng_key)
                    # 算法：有词就给分，词越多分越高
                    score = min(10.0, 3.0 + count * 2.0) if count > 0 else 1.5
                    values.append(score)
                
                # 闭合
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
                    angularaxis=dict(tickfont=dict(size=14))
                ),
                margin=dict(t=20, b=20, l=40, r=40),
                height=450,
                legend=dict(orientation="h", y=-0.1)
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # === 右侧：AI 实验报告 (含专业建议) ===
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            # 1. 计算共鸣分
            sets = [set(df[df['name']==n]['mol_set'].values[0]) for n in selected]
            intersection = set.intersection(*sets) if sets else set()
            union = set.union(*sets) if sets else set()
            
            # 基础分
            raw_score = (len(intersection) / len(union)) * 100 if union else 0
            # 视觉优化分 (让分数更好看)
            display_score = int(min(98, max(raw_score * 5 + 45, 60)))

            # 2. 分数展示
            color = '#34C759' if display_score > 80 else ('#FF9500' if display_score > 70 else '#FF3B30')
            st.markdown(f"""
            <div style="text-align:center">
                <div class="metric-title">MOLECULAR RESONANCE</div>
                <div class="metric-value" style="color: {color}">{display_score}%</div>
                <div class="metric-title">分子共鸣指数</div>
            </div>
            <hr style="opacity:0.2; margin: 20px 0;">
            """, unsafe_allow_html=True)

            # 3. 动态分析文案 (针对你提到的“引导建议”)
            cn_names = [agent.name_map.get(n, n) for n in selected]
            names_str = " + ".join(cn_names)
            
            st.markdown("#### 🧪 实验结论")
            
            if display_score >= 85:
                st.success(f"**极光效应 (Harmony)**：{names_str} 在分子层面高度重合。")
                st.markdown(f"这是一组**完美的同源搭配**。它们共享大量的挥发性化合物，入口后会产生如同“和弦”般的共振感。")
            elif display_score >= 70:
                st.warning(f"**维度补偿 (Contrast)**：{names_str} 构成了有趣的平衡。")
                st.markdown(f"这是一组**互补型搭配**。一方提供风味骨架，另一方提供必要的跳跃感，适合想要增加层次感的料理。")
            else:
                st.error(f"**冲突美学 (Clash)**：{names_str} 是一次大胆的冒险。")
                st.markdown(f"这属于**对比强烈的撞色搭配**。分子重合度低，建议通过酱汁或乳化剂（如奶油、蛋黄）来进行风味桥接。")

            # 4. 厨师建议
            st.markdown("#### 👨‍🍳 主厨应用指南")
            if len(cn_names) >= 2:
                template = random.choice(agent.templates)
                advice = template.format(cn_names[0], cn_names[1])
                st.info(advice)
            
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
