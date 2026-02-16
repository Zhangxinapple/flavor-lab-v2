import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random
import os

# ==========================================
# 1. AI 引擎
# ==========================================
class TasteWormholeAgent:
    def __init__(self):
        self.name_map = {
            "coffee": "咖啡", "dark chocolate": "黑巧克力", "green tea": "绿茶", 
            "strawberry": "草莓", "apple": "苹果", "banana": "香蕉",
            "bread": "面包", "butter": "黄油", "cheese": "芝士", "tomato": "番茄",
            "pork": "猪肉", "beef": "牛肉", "chicken": "鸡肉", "onion": "洋葱",
            "garlic": "大蒜", "ginger": "生姜", "lemon": "柠檬"
        }

    def t(self, text):
        """翻译函数"""
        if not text or pd.isna(text):
            return "未知"
        text_lower = str(text).lower().strip()
        return self.name_map.get(text_lower, str(text).replace('_', ' ').title())

    def generate_report(self, n1, n2, score):
        """生成AI报告"""
        if score > 7:
            logic_title = "分子共鸣"
            logic_desc = "两者共享核心香气分子，味觉波形完美重叠"
        elif score > 4:
            logic_title = "维度补偿"
            logic_desc = "存在连接点但互补性更强，形成立体味觉结构"
        else:
            logic_title = "极光效应"
            logic_desc = "强烈的反差制造了鼻腔冲击力，打破味觉疲劳"
        
        reports = [
            f"入口瞬间，{self.t(n1)}与{self.t(n2)}的界限坍缩，中段口感致密。",
            f"{self.t(n1)}的基底与{self.t(n2)}的前调产生交织，味觉在3-5秒达到峰值。",
            f"两者在口腔中形成双螺旋结构，{self.t(n1)}提供主旋律。"
        ]
        
        apps = [
            "🥗 前菜建议：制作冷萃酱汁或分子泡沫，在室温下快速释放香气",
            "🥩 主菜搭配：利用油脂介质锁住低频香气，文火慢煨至味觉融合",
            "🍸 饮品创意：提取香气精粹，利用反差感制作分层口感"
        ]
        
        return f"""
        <div style="background:linear-gradient(135deg,#fbfbfd,#f8f9fa); border-radius:16px; padding:18px; border-left:4px solid #0071e3; margin-top:12px; box-shadow:0 2px 8px rgba(0,0,0,0.04);">
            <p><strong>🌀 关联逻辑：{logic_title}</strong></p>
            <p style="color:#666; font-size:0.85rem; margin-top:6px;">{logic_desc}</p>
            
            <p style="margin-top:12px;"><strong>🧪 实验报告：</strong></p>
            <p style="color:#666; font-size:0.85rem;">{random.choice(reports)}</p>
            
            <p style="margin-top:12px;"><strong>👨‍🍳 应用建议：</strong></p>
            <p style="font-size:0.85rem;">{random.choice(apps)}</p>
            
            <hr style="border:none; border-top:1px dashed #ddd; margin:12px 0;">
            <p style="font-size:0.75rem; color:#999;">
                <strong>配比建议:</strong> 1:{max(1, int(11-score))} | 
                <strong>技术路径:</strong> {'共融调和' if score > 7 else '对比触发' if score > 4 else '极限冲击'}
            </p>
        </div>
        """

ai = TasteWormholeAgent()

# ==========================================
# 2. 页面配置
# ==========================================
st.set_page_config(page_title="味觉虫洞 Flavor Lab", layout="wide")

st.markdown("""
<style>
    .stApp { 
        background: linear-gradient(135deg, #f5f7fa 0%, #f0f2f5 100%); 
    }
    .card { 
        background: white; 
        border-radius: 20px; 
        padding: 24px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.06); 
        margin-bottom: 20px;
        border: 1px solid rgba(0,0,0,0.04);
    }
    .score-badge { 
        background: linear-gradient(135deg, #0071e3 0%, #00c7be 100%); 
        color: white; 
        padding: 6px 14px; 
        border-radius: 14px; 
        font-weight: 700;
        font-size: 0.9rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 数据加载（稳定版）
# ==========================================
@st.cache_data
def load_data():
    """加载数据"""
    try:
        # 尝试多个路径
        df = None
        for path in ['flavordb_data.csv', './flavordb_data.csv']:
            if os.path.exists(path):
                df = pd.read_csv(path, encoding='utf-8')
                break
        
        if df is None:
            st.error("找不到数据文件 flavordb_data.csv")
            return None
        
        # 填充空值
        df = df.fillna('')
        
        # 创建分子集合（使用简单安全的方式）
        def create_mol_set(x):
            if not x or pd.isna(x):
                return set()
            return set(str(x).replace(',', ' ').split())
        
        df['mol_set'] = df['flavor_profiles'].apply(create_mol_set)
        
        # 过滤空数据（使用安全方式）
        def has_valid_profile(x):
            return len(str(x).strip()) > 10
        
        df = df[df['flavor_profiles'].apply(has_valid_profile)].copy()
        
        # 创建显示名称
        df['display_name'] = df['name'].apply(lambda x: f"{ai.t(x)} ({x})")
        
        return df
        
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return None

# ==========================================
# 4. 创建雷达图（核心功能）
# ==========================================
def create_radar_chart(profile_text):
    """创建风味雷达图"""
    # 定义6个维度
    dimensions = {
        "🌿草本": ["green", "herb", "grass", "leaf"],
        "🍎果香": ["fruit", "berry", "citrus", "apple"],
        "🔥烘焙": ["roast", "toast", "bake", "coffee"],
        "🌍大地": ["earth", "wood", "must", "soil"],
        "🌶️辛辣": ["spicy", "pepper", "hot", "pungent"],
        "🧈油脂": ["fatty", "butter", "cream", "oil"]
    }
    
    # 计算每个维度的分数
    values = []
    profile_lower = str(profile_text).lower()
    
    for dim, keywords in dimensions.items():
        score = 0
        for keyword in keywords:
            score += profile_lower.count(keyword) * 2.5
        values.append(min(score, 10))  # 最大10分
    
    # 如果全是0，设置最小值避免图表为空
    if sum(values) == 0:
        values = [1, 1, 1, 1, 1, 1]
    
    # 创建雷达图
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=list(dimensions.keys()),
        fill='toself',
        line=dict(color='#0071e3', width=2),
        fillcolor='rgba(0,113,227,0.2)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                showticklabels=False,
                ticks='',
                gridcolor='rgba(0,0,0,0.1)'
            ),
            bgcolor='rgba(0,0,0,0.02)'
        ),
        showlegend=False,
        height=200,
        margin=dict(t=30, b=20, l=30, r=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# ==========================================
# 5. 主界面
# ==========================================
df = load_data()

if df is not None and len(df) > 0:
    # 标题
    st.markdown(f"""
        <h1 style='text-align:center; background:linear-gradient(135deg,#0071e3,#00c7be); -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
            🌌 味觉虫洞 Flavor Lab
        </h1>
        <p style='text-align:center; color:#666; margin-bottom:30px;'>
            基于分子美食学的AI风味分析引擎 | 共收录 {len(df)} 种食材
        </p>
    """, unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.markdown("### 🎯 实验控制面板")
        
        # 食材选择
        all_items = sorted(df['display_name'].tolist())
        selected = st.multiselect(
            "🔬 选择 2-4 种食材开始实验",
            options=all_items,
            max_selections=4,
            help="选择至少2种食材，AI将分析它们之间的风味关联"
        )
        
        st.markdown("---")
        st.markdown("""
            <div style='font-size:0.75rem; color:#666; padding:10px; background:#f8f9fa; border-radius:8px;'>
            <strong>💡 使用提示：</strong><br>
            • 第一个食材为"味觉锚点"<br>
            • 分数越高，风味越相似<br>
            • 可用于创意菜品研发
            </div>
        """, unsafe_allow_html=True)

    # 主内容区
    if len(selected) >= 2:
        # 创建列布局
        cols = st.columns(len(selected))
        base_row = df[df['display_name'] == selected[0]].iloc[0]

        for i, d_name in enumerate(selected):
            curr_row = df[df['display_name'] == d_name].iloc[0]
            
            # 计算相似度分数
            if i > 0:
                common = base_row['mol_set'] & curr_row['mol_set']
                total = base_row['mol_set'] | curr_row['mol_set']
                score = round(len(common) / len(total) * 10, 1) if len(total) > 0 else 0.0
            else:
                score = 10.0
            
            with cols[i]:
                st.markdown(f"""
                <div class="card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                        <span style="font-size:1.2rem; font-weight:700;">{ai.t(curr_row['name'])}</span>
                        <span class="score-badge">{"🎯 锚点" if i == 0 else f"{score} 分"}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # 🌟 雷达图（核心功能）
                fig = create_radar_chart(curr_row['flavor_profiles'])
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                if i > 0:
                    # AI 专家报告
                    report_html = ai.generate_report(
                        base_row['name'], 
                        curr_row['name'], 
                        score
                    )
                    st.markdown(report_html, unsafe_allow_html=True)
                    
                    # 共有分子展示
                    common_mols = base_row['mol_set'] & curr_row['mol_set']
                    if common_mols and len(common_mols) > 0:
                        st.caption(f"🔬 共有风味分子: {len(common_mols)} 个")
                else:
                    st.info("🎯 已选定为味觉锚点\n\nAI将以此为核心进行虫洞推演")
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        st.markdown("""
        <div style="text-align:center; padding:80px 40px; color:#666; background:white; border-radius:20px; margin:40px;">
            <h2 style='color:#0071e3; margin-bottom:20px;'>🔭 正在扫描风味星图...</h2>
            <p style='font-size:1.1rem; line-height:1.8;'>
                请在左侧侧边栏选择至少 <strong>2 种食材</strong>，启动《味觉虫洞》AI 引擎<br>
                系统将基于分子美食学原理，分析食材间的风味关联度
            </p>
            <div style='margin-top:30px; padding:20px; background:#f8f9fa; border-radius:12px; display:inline-block;'>
                <strong>💡 推荐组合尝试：</strong><br>
                咖啡 + 黑巧克力 | 草莓 + 番茄 | 猪肉 + 苹果
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.error("❌ 数据加载失败，请检查 flavordb_data.csv 文件")

# 页脚
st.markdown("""
<div style='text-align:center; margin-top:40px; padding:20px; color:#999; font-size:0.75rem;'>
    <p>🌌 味觉虫洞 Flavor Lab v2.0 | 基于分子美食学的AI风味分析引擎</p>
</div>
""", unsafe_allow_html=True)
