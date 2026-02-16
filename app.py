import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random
import os

# ==========================================
# 1. 核心 AI 引擎：《味觉虫洞》 (优化版)
# ==========================================
class TasteWormholeAgent:
    def __init__(self):
        # 扩展汉化词典
        self.name_map = {
            "bamboo shoots": "竹笋", "coffee": "咖啡", "dark chocolate": "黑巧克力",
            "green tea": "绿茶", "strawberry": "草莓", "apple": "苹果", "banana": "香蕉",
            "bread": "面包", "butter": "黄油", "cheese": "芝士", "tomato": "番茄",
            "pork": "猪肉", "beef": "牛肉", "chicken": "鸡肉", "shrimp": "虾",
            "onion": "洋葱", "garlic": "大蒜", "ginger": "生姜", "lemon": "柠檬",
            "bakery products": "烘焙制品", "dairy": "乳制品", "meat": "肉类",
            "orange": "橙子", "grape": "葡萄", "milk": "牛奶", "egg": "鸡蛋",
            "wine": "葡萄酒", "beer": "啤酒", "tea": "茶", "rice": "米饭",
            "potato": "土豆", "carrot": "胡萝卜", "cabbage": "卷心菜",
            "mushroom": "蘑菇", "fish": "鱼", "lamb": "羊肉", "duck": "鸭肉",
            "honey": "蜂蜜", "vanilla": "香草", "cinnamon": "肉桂", "pepper": "胡椒"
        }
        self.flavor_cn = {
            "roasted": "烘焙", "sweet": "甜美", "earthy": "泥土", "fruity": "果香",
            "green": "青草", "spicy": "辛辣", "fatty": "油脂", "floral": "花香",
            "nutty": "坚果", "woody": "木质", "bitter": "苦味", "sulfurous": "硫味",
            "citrus": "柑橘", "creamy": "奶油", "smoky": "烟熏", "caramel": "焦糖",
            "sour": "酸味", "fresh": "清新", "herbal": "草本", "mint": "薄荷",
            "vanilla": "香草", "chocolate": "巧克力", "berry": "浆果", "tropical": "热带"
        }

    def t(self, text, type='name'):
        """智能翻译函数"""
        if pd.isna(text) or text == '':
            return "未知"
        t_low = str(text).lower().strip()
        if type == 'name': 
            return self.name_map.get(t_low, t_low.replace("_", " ").title())
        # 风味翻译
        for k, v in self.flavor_cn.items():
            if k in t_low: 
                return v
        return t_low.title()

    def analyze_frequency(self, profile_text):
        """分析食材频率属性"""
        if pd.isna(profile_text) or profile_text == '':
            return "中频·平衡型"
        
        profile_text = str(profile_text).lower()
        high = ["green", "citrus", "floral", "fruit", "herbal", "fresh", "mint", "berry"]
        low = ["roasted", "earthy", "fatty", "woody", "smoky", "nutty", "caramel", "chocolate"]
        
        h_score = sum(1 for k in high if k in profile_text)
        l_score = sum(1 for k in low if k in profile_text)
        
        if h_score > l_score + 2:
            return "高频·挥发性·上扬"
        elif l_score > h_score + 2:
            return "低频·沉降感·基底"
        else:
            return "中频·平衡型"

    def generate_report(self, n1, n2, score, common_count, profile1, profile2):
        """生成AI专家报告"""
        c1 = self.analyze_frequency(profile1)
        c2 = self.analyze_frequency(profile2)
        
        # 关联逻辑
        if score > 7.5:
            logic_t = "分子共鸣"
            logic_d = "两者共享核心香气分子，味觉波形完美重叠。这是一种'同频共振'效应。"
        elif score > 4.0:
            logic_t = "维度补偿"
            logic_d = "存在连接点但互补性更强。一方提供骨架，另一方提供血肉，形成立体味觉结构。"
        else:
            logic_t = "极光效应"
            logic_d = "强烈的反差制造了'鼻腔冲击力'，打破常规味觉疲劳，创造记忆点。"

        # 实验报告
        reports = [
            f"入口瞬间，{self.t(n1)}与{self.t(n2)}的界限坍缩。中段口感致密，尾韵在共鸣点处完成和解。",
            f"{self.t(n1)}的基底与{self.t(n2)}的前调产生交织。味觉在第3-5秒达到峰值平衡。",
            f"两者在口腔中形成双螺旋结构。{self.t(n1)}提供主旋律，{self.t(n2)}负责和声部分。"
        ]
        report = random.choice(reports)

        # 厨师应用
        apps = [
            "🥗 **前菜建议：** 利用高挥发性，做成冷萃酱汁或分子泡沫，在室温下快速释放香气。",
            "🥩 **主菜搭配：** 利用油脂介质锁住低频香气，作为主食材底色，文火慢煨至味觉融合。",
            "🍸 **饮品创意：** 提取其香气精粹，利用反差感制作分层口感，冰镇后风味更立体。",
            "🍰 **甜品设计：** 用温度差异控制风味释放节奏，热食突出前调，冷食保留尾韵。"
        ]
        chef_app = random.choice(apps)

        # 配比建议
        ratio = max(1, int(11 - score))
        technique = "共融调和" if score > 7 else "对比触发" if score > 4 else "极限冲击"

        return f"""
        <div class="wormhole-box">
            <p><strong>🛰️ 虫洞坐标：</strong><br>
            <span style="color:#0071e3;">[{self.t(n1)}: {c1}]</span> ⚡ 
            <span style="color:#00c7be;">[{self.t(n2)}: {c2}]</span></p>
            
            <p style="margin-top:10px;"><strong>🌀 关联逻辑：{logic_t}</strong><br>
            <span style="color:#666; font-size:0.8rem;">{logic_d}</span></p>
            
            <p style="margin-top:10px;"><strong>🧪 实验报告：</strong><br>
            <span style="color:#666; font-size:0.8rem;">{report}</span></p>
            
            <p style="margin-top:10px;"><strong>👨‍🍳 厨师应用：</strong><br>
            <span style="font-size:0.85rem;">{chef_app}</span></p>
            
            <hr style="border-top: 1px dashed #ddd; margin:12px 0;">
            
            <p style="font-size:0.75rem; color:#86868b">
            <strong>📊 风味星图参数：</strong> 
            共有分子: {common_count} | 
            配比建议: 1:{ratio} | 
            技术路径: {technique}
            </p>
        </div>
        """

ai = TasteWormholeAgent()

# ==========================================
# 2. 视觉样式优化
# ==========================================
st.set_page_config(
    page_title="味觉虫洞 Flavor Lab", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* 全局样式 */
    .stApp { 
        background: linear-gradient(135deg, #f5f7fa 0%, #f0f2f5 100%); 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
    }
    
    /* 卡片样式 */
    .apple-card { 
        background: white; 
        border-radius: 20px; 
        padding: 24px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.06); 
        margin-bottom: 20px; 
        height: 100%;
        border: 1px solid rgba(0,0,0,0.04);
        transition: all 0.3s ease;
    }
    .apple-card:hover {
        box-shadow: 0 8px 30px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    /* 分数徽章 */
    .score-badge { 
        background: linear-gradient(135deg, #0071e3 0%, #00c7be 100%); 
        color: white; 
        padding: 6px 14px; 
        border-radius: 14px; 
        font-weight: 700;
        font-size: 0.9rem;
        display: inline-block;
    }
    
    /* 虫洞报告盒子 */
    .wormhole-box { 
        background: linear-gradient(135deg, #fbfbfd 0%, #f8f9fa 100%);
        border-radius: 16px; 
        padding: 18px; 
        border-left: 4px solid #0071e3; 
        margin-top: 12px; 
        font-size: 0.85rem; 
        line-height: 1.6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    /* 分子标签 */
    .pill { 
        display: inline-block; 
        padding: 3px 10px; 
        margin: 3px; 
        border-radius: 8px; 
        font-size: 0.7rem; 
        background: linear-gradient(135deg, #e3f2fd 0%, #e1f5fe 100%);
        color: #0277bd; 
        border: 1px solid #b3e5fc;
        font-weight: 500;
    }
    
    /* 标题样式 */
    h1 { 
        background: linear-gradient(135deg, #0071e3 0%, #00c7be 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* 侧边栏 */
    .css-1d391kg { background: white !important; }
    
    /* 信息提示框 */
    .stAlert { border-radius: 12px; border-left: 4px solid #0071e3; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 数据加载优化
# ==========================================
@st.cache_data
def load_data():
    """加载并预处理数据"""
    try:
        # 尝试多个可能的路径
        possible_paths = [
            'flavordb_data.csv',
            './flavordb_data.csv',
            os.path.join(os.path.dirname(__file__), 'flavordb_data.csv')
        ]
        
        df = None
        for path in possible_paths:
            if os.path.exists(path):
                df = pd.read_csv(path)
                break
        
        if df is None:
            raise FileNotFoundError("找不到数据文件 flavordb_data.csv")
        
        # 填充空值
        df = df.fillna('')
        
        # 优化：使用 flavor_profiles 而不是 flavors（因为 flavors 列很多空值）
        df['mol_set'] = df['flavor_profiles'].apply(
            lambda x: set(str(x).replace(',', ' ').split()) if x else set()
        )
        
        # 只保留有风味描述的食材
        # 使用更安全的过滤方法
        df['profile_len'] = df['flavor_profiles'].astype(str).apply(len)
        df = df[df['profile_len'] > 0].copy()
        df = df.drop(columns=['profile_len'])
        
        # 创建显示名称
        df['display_name'] = df.apply(
            lambda row: f"{ai.t(row['name'])} ({row['name']})", axis=1
        )
        
        # 添加分类标签（便于筛选）
        df['category_cn'] = df['category'].apply(lambda x: ai.t(x, 'name'))
        
        return df
    except Exception as e:
        st.error(f"❌ 数据加载失败: {e}")
        st.info("请确保 flavordb_data.csv 文件在正确的位置")
        return None

# ==========================================
# 4. 主界面渲染
# ==========================================
df = load_data()

if df is not None and len(df) > 0:
    # 标题
    st.markdown("""
        <h1 style='text-align:center; margin-bottom:10px;'>
            🌌 味觉虫洞 <span style='font-weight:300; opacity:0.8;'>Flavor Lab</span>
        </h1>
        <p style='text-align:center; color:#666; margin-bottom:30px;'>
            基于分子美食学的AI风味分析引擎 | 共收录 {0} 种食材
        </p>
    """.format(len(df)), unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.markdown("### 🎯 实验控制面板")
        
        # 分类筛选
        categories = ['全部分类'] + sorted(df['category_cn'].unique().tolist())
        selected_category = st.selectbox("📁 食材分类", categories)
        
        # 根据分类筛选
        if selected_category != '全部分类':
            filtered_df = df[df['category_cn'] == selected_category]
        else:
            filtered_df = df
        
        # 食材选择（最多4个）
        selected = st.multiselect(
            "🔬 选择 2-4 种食材开始实验",
            options=sorted(filtered_df['display_name'].unique()),
            max_selections=4,
            help="选择至少2种食材，AI将分析它们之间的风味关联"
        )
        
        st.markdown("---")
        st.markdown(f"""
            <div style='font-size:0.75rem; color:#666; padding:10px; background:#f8f9fa; border-radius:8px;'>
            <strong>💡 使用提示：</strong><br>
            • 第一个食材为"味觉锚点"<br>
            • AI将分析其他食材与锚点的关联<br>
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
            
            # 计算共有分子和分数
            common = base_row['mol_set'].intersection(curr_row['mol_set'])
            common_count = len(common)
            
            # 优化评分算法
            if i > 0:
                base_total = len(base_row['mol_set'])
                curr_total = len(curr_row['mol_set'])
                if base_total > 0 and curr_total > 0:
                    # Jaccard相似度 * 10
                    score = round((common_count / (base_total + curr_total - common_count)) * 10, 1)
                else:
                    score = 0.0
            else:
                score = 10.0  # 锚点
            
            with cols[i]:
                st.markdown(f"""
                <div class="apple-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                        <span style="font-size:1.2rem; font-weight:700;">{ai.t(curr_row['name'])}</span>
                        <span class="score-badge">{"🎯 锚点" if i == 0 else f"{score} 分"}</span>
                    </div>
                    <div style="font-size:0.75rem; color:#86868b; margin-bottom:10px;">
                        分类: {curr_row['category_cn']}
                    </div>
                """, unsafe_allow_html=True)
                
                # 雷达图
                dims = {"🌿草本": "green", "🍎果香": "fruit", "🔥烘焙": "roasted", 
                        "🌍大地": "earthy", "🌶️辛辣": "spicy", "🧈油脂": "fatty"}
                profile_text = str(curr_row['flavor_profiles']).lower()
                vals = [min(profile_text.count(k) * 2.5, 10) for k in dims.values()]
                
                fig = go.Figure(data=go.Scatterpolar(
                    r=vals, 
                    theta=list(dims.keys()), 
                    fill='toself', 
                    line_color='#0071e3',
                    fillcolor='rgba(0,113,227,0.2)'
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 10], showticklabels=False),
                        bgcolor='rgba(0,0,0,0.02)'
                    ),
                    showlegend=False, 
                    height=180, 
                    margin=dict(t=20, b=20, l=20, r=20),
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                if i > 0:
                    # AI专家报告
                    report_html = ai.generate_report(
                        base_row['name'], 
                        curr_row['name'], 
                        score, 
                        common_count,
                        str(base_row['flavor_profiles']), 
                        str(curr_row['flavor_profiles'])
                    )
                    st.markdown(report_html, unsafe_allow_html=True)
                    
                    # 共有分子标签
                    if common:
                        st.markdown(
                            "<div style='font-size:0.75rem; color:#86868b; margin-top:8px;'>🔬 共有风味分子:</div>", 
                            unsafe_allow_html=True
                        )
                        mols_list = sorted(list(common))[:6]
                        pills_html = " ".join([f'<span class="pill">{ai.t(m, "flavor")}</span>' for m in mols_list])
                        st.markdown(pills_html, unsafe_allow_html=True)
                        
                        if len(common) > 6:
                            st.markdown(
                                f"<div style='font-size:0.7rem; color:#999; margin-top:4px;'>还有 {len(common)-6} 个共有分子...</div>",
                                unsafe_allow_html=True
                            )
                else:
                    st.info("🎯 **已选定为味觉锚点**\n\nAI将以此为核心进行虫洞推演，分析其他食材与之的风味关联度。")
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    elif len(selected) == 1:
        st.warning("⚠️ 请再选择至少1种食材进行对比分析")
    else:
        st.markdown("""
        <div style="text-align:center; padding:80px 40px; color:#86868b; background:white; border-radius:20px; margin:40px;">
            <h2 style='color:#0071e3; margin-bottom:20px;'>🔭 正在扫描风味星图...</h2>
            <p style='font-size:1.1rem; line-height:1.8;'>
                请在左侧侧边栏选择至少 <strong>2 种食材</strong>，启动《味觉虫洞》AI 引擎。<br>
                系统将基于分子美食学原理，分析食材间的风味关联度。
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
    <p>数据来源: FlavorDB | AI引擎: Claude Sonnet 4</p>
</div>
""", unsafe_allow_html=True)
