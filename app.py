import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random
import os

# ==========================================
# 1. 核心 AI 引擎与全链路汉化词典
# ==========================================
class TasteWormholeAgent:
    def __init__(self):
        # 汉化映射表：确保 555 种食材中的高频词显示中文
        self.name_map = {
            # 基础与常见食材
            "coffee": "咖啡", "dark chocolate": "黑巧克力", "white chocolate": "白巧克力",
            "milk": "牛奶", "butter": "黄油", "cheese": "芝士", "cream": "奶油",
            "egg": "鸡蛋", "honey": "蜂蜜", "vanilla": "香草", "bread": "面包",
            "strawberry": "草莓", "apple": "苹果", "banana": "香蕉", "lemon": "柠檬",
            "orange": "橙子", "grape": "葡萄", "mango": "芒果", "pineapple": "菠萝",
            "tomato": "番茄", "potato": "土豆", "carrot": "胡萝卜", "onion": "洋葱",
            "garlic": "大蒜", "ginger": "生姜", "cucumber": "黄瓜", "mushroom": "蘑菇",
            "pork": "猪肉", "beef": "牛肉", "chicken": "鸡肉", "lamb": "羊肉",
            "shrimp": "虾", "crab": "螃蟹", "salmon": "三文鱼", "tuna": "金枪鱼",
            "soy sauce": "酱油", "vinegar": "醋", "wine": "红酒", "beer": "啤酒",
            "black tea": "红茶", "green tea": "绿茶",
            # 雷达图维度汉化
            "sweet": "甜美度", "roasted": "烘焙感", "fruity": "果香值",
            "herbaceous": "草本力", "woody": "木质调", "spicy": "辛辣感"
        }
        
        # 专业建议库
        self.chef_templates = [
            "💡 **主厨灵感**：建议将 {0} 低温处理，利用其分子挥发性激发 {1} 的深层风味。",
            "💡 **分子技巧**：{0} 中的关键芳香烃能有效平衡 {1} 的油脂感，适合作为前菜基调。",
            "💡 **融合建议**：在分子层面，{0} 与 {1} 共享关键呈味基因，建议尝试乳化技术融合两者。",
            "💡 **感官体验**：这是一组经典的‘高共鸣’组合，{0} 提供骨架，{1} 负责风味的灵魂点缀。"
        ]

# 实例化对象
agent = TasteWormholeAgent()

# ==========================================
# 2. 增强型数据加载（锁定 555 种食材）
# ==========================================
@st.cache_data
def load_data():
    if not os.path.exists("flavordb_data.csv"):
        return None
    
    df = pd.read_csv("flavordb_data.csv")
    
    # 强制开启 555 模式：使用 flavor_profiles 列
    df['flavor_profiles'] = df['flavor_profiles'].fillna('')
    df = df[df['flavor_profiles'].str.len() > 1]
    
    # 构建分子集合用于相似度算法 (Jaccard)
    df['mol_set'] = df['flavor_profiles'].apply(
        lambda x: set(str(x).replace(',', ' ').lower().split())
    )
    return df

# ==========================================
# 3. 界面 UI 与 Apple 风格 CSS
# ==========================================
st.set_page_config(page_title="Flavor Lab Pro V5.0", page_icon="🧬", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F5F5F7; }
    .card {
        background: white; padding: 25px; border-radius: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.05); margin-bottom: 20px;
        border: 1px solid rgba(0,0,0,0.03);
    }
    .metric-value { font-size: 3rem; font-weight: 700; color: #0071E3; }
    .metric-label { font-size: 0.8rem; color: #86868B; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 主程序流程
# ==========================================
def main():
    st.markdown("# 🧬 味觉虫洞 Flavor Lab <span style='font-size:0.9rem; color:gray'>V5.0 合并版</span>", unsafe_allow_html=True)
    
    df = load_data()
    if df is None:
        st.error("🚨 找不到 flavordb_data.csv，请检查 GitHub 仓库。")
        st.stop()

    # --- 侧边栏：分类与筛选 ---
    with st.sidebar:
        st.header("🔬 实验室参数")
        
        # Vegan 过滤器功能
        show_vegan = st.toggle("🍃 仅植物基食材 (Vegan)", value=False)
        
        if show_vegan:
            # 排除含肉类、奶类、蛋类的类别
            exclude = ['meat', 'dairy', 'fish', 'seafood', 'egg']
            df_display = df[~df['category'].str.lower().isin(exclude)]
        else:
            df_display = df

        # 汉化显示逻辑
        def format_func(name):
            cn = agent.name_map.get(name, name)
            return f"{cn} ({name})" if cn != name else name

        selected = st.multiselect(
            f"已解锁 {len(df_display)} 种分子食材：",
            options=sorted(df_display['name'].unique()),
            default=["coffee", "dark chocolate"] if not show_vegan else None,
            format_func=format_func
        )
        
        st.divider()
        st.info(f"📊 引擎正在分析 {len(df_display)} 种食材的分子指纹。")

    # --- 主交互区 ---
    if len(selected) >= 2:
        col1, col2 = st.columns([1.2, 1])

        # A. 汉化雷达图
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🔭 风味维度星图")
            
            dims_map = {"sweet": "甜美度", "roasted": "烘焙感", "fruity": "果香值", 
                        "herbaceous": "草本力", "woody": "木质调", "spicy": "辛辣感"}
            
            fig = go.Figure()
            for name in selected:
                row = df[df['name'] == name]
                profile = str(row['flavor_profiles'].values[0]).lower()
                
                # 计算得分 (基于关键词密度)
                values = []
                for eng_k in dims_map.keys():
                    count = profile.count(eng_k)
                    score = min(10, 3.5 + count * 2) if count > 0 else 1.5
                    values.append(score)
                
                # 闭合雷达图
                values.append(values[0])
                fig.add_trace(go.Scatterpolar(
                    r=values, theta=list(dims_map.values()) + [list(dims_map.values())[0]],
                    fill='toself', name=agent.name_map.get(name, name)
                ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 10], showticklabels=False)),
                height=450, margin=dict(t=20, b=20), legend=dict(orientation="h", y=-0.1)
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # B. AI 实验报告（含主厨建议）
        with col2:
            st.markdown('<div class="card" style="text-align:center">', unsafe_allow_html=True)
            
            # 计算分子共鸣指数 (Jaccard Similarity)
            sets = [df[df['name']==n]['mol_set'].values[0] for n in selected]
            common = set.intersection(*sets)
            total = set.union(*sets)
            raw_score = (len(common) / len(total)) * 100 if total else 0
            
            # 视觉映射分（让用户更直观感受到匹配度）
            display_score = int(min(98, max(raw_score * 5 + 48, 60)))
            
            st.markdown(f'<div class="metric-value">{display_score}%</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">MOLECULAR RESONANCE / 分子共鸣</div>', unsafe_allow_html=True)
            st.divider()

            # 结论推演
            cn_names = [agent.name_map.get(n, n) for n in selected]
            if display_score >= 85:
                st.success(f"✨ **极光效应**：{cn_names[0]} 与 {cn_names[1]} 是天作之合。")
                st.write("它们共享极其相似的分子骨架，能够产生极其和谐的感官共振。")
            elif display_score >= 70:
                st.info(f"🌓 **维度补偿**：{cn_names[0]} 填补了 {cn_names[1]} 的风味空白。")
                st.write("这组搭配层次分明，一方提供结构，另一方提供高频风味点缀。")
            else:
                st.warning(f"💥 **冲突美学**：这是一场勇敢的味觉对撞。")
                st.write("分子结构差异较大，建议通过增加脂肪（如奶油）或酸度来建立风味桥梁。")

            st.markdown("#### 🧪 专家应用建议")
            advice = random.choice(agent.chef_templates).format(cn_names[0], cn_names[1])
            st.info(advice)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("👈 请在左侧侧边栏至少选择 2 种食材以启动分析引擎。")

if __name__ == "__main__":
    main()
