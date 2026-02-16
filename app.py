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
        # 基础食材
        "coffee": "咖啡", "dark chocolate": "黑巧克力", "strawberry": "草莓", 
        "tomato": "番茄", "garlic": "大蒜", "onion": "洋葱", "ginger": "生姜",
        "pork": "猪肉", "beef": "牛肉", "chicken": " chicken", "shrimp": "虾",
        "egg": "鸡蛋", "milk": "牛奶", "butter": "黄油", "cheese": "芝士",
        # 常见水果
        "apple": "苹果", "banana": "香蕉", "lemon": "柠檬", "orange": "橙子",
        "grape": "葡萄", "mango": "芒果", "pineapple": "菠萝",
        # 风味描述汉化 (这部分最关键，用于雷达图)
        "herbaceous": "草本", "fruity": "果香", "roasted": "烘焙/焦香", 
        "woody": "木质", "sweet": "甜美", "spicy": "辛辣", "floral": "花香",
        "fatty": "油脂", "sour": "酸味", "bitter": "苦味"
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

agent = TasteWormholeAgent()

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
    df = pd.read_csv('flavordb_data.csv')
    
    # 核心修正：使用 flavor_profiles 替代 flavors
    # 这样可用食材会从 60 瞬间变成 555
    df['mol_set'] = df['flavor_profiles'].apply(
        lambda x: set(str(x).replace(',', ' ').split()) if x else set()
    )
    
    # 过滤掉完全没数据的行
    df = df[df['flavor_profiles'].str.len() > 0]
    return df
        
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
# 4. 风味星图渲染 (请完整替换此部分)
# ==========================================
    st.markdown("### 📊 风味维度星图")
    
    # 定义雷达图维度
    flavor_dim_map = {
        "sweet": "甜美度", "roasted": "烘焙感", "fruity": "果香值",
        "herbaceous": "草本力", "woody": "木质调", "spicy": "辛辣感"
    }
    dims_eng = list(flavor_dim_map.keys())
    dims_cn = list(flavor_dim_map.values())
    
    if len(selected) > 0:
        fig = go.Figure()
        for name in selected:
            row = df[df['name'] == name]
            if row.empty: continue
                
            profile_text = str(row['flavor_profiles'].values[0]).lower()
            
            # 数值映射算法
            values = []
            for eng_key in dims_eng:
                count = profile_text.count(eng_key)
                score = min(10.0, 4.0 + (count - 1) * 2.5) if count > 0 else 1.5
                values.append(score)
            
            # 闭合雷达图
            values.append(values[0])
            labels_cn = dims_cn + [dims_cn[0]]
            
            # 关键修复点：使用安全的 get 方法获取中文名
            cn_label = agent.name_map.get(name, name)
            
            fig.add_trace(go.Scatterpolar(
                r=values, theta=labels_cn, fill='toself', name=f"✨ {cn_label}"
            ))
    
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], showticklabels=False),
                angularaxis=dict(tickfont=dict(size=14))
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("请在左侧侧边栏选择食材")
    
    # 2. 创建画布
    fig = go.Figure()
    
    if len(selected) > 0:
        for name in selected:
            # 安全获取数据
            row = df[df['name'] == name]
            if row.empty:
                continue
                
            # 提取风味描述文本
            profile_text = str(row['flavor_profiles'].values[0]).lower()
            
            # 算法：根据关键词出现频率计算 0-10 的分值
            values = []
            for eng_key in dims_eng:
                count = profile_text.count(eng_key)
                if count > 0:
                    # 匹配到关键词，基础分4分，每多一个描述+1.5分
                    score = min(10.0, 4.0 + (count - 1) * 1.5)
                else:
                    # 视觉保底分，防止图形塌陷
                    score = 1.5
                values.append(score)
            
            # 闭合曲线
            values.append(values[0])
            labels_with_closure = dims_cn + [dims_cn[0]]
            
            # 获取汉化名称（调用 agent 实例）
            # 注意：这里假设你的 agent 实例名叫 agent
            cn_name = agent.name_map.get(name, name)
            
            # 添加轨迹
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=labels_with_closure,
                fill='toself',
                name=f"✨ {cn_name}",
                line=dict(width=3)
            ))
    
        # 3. 样式美化
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], showticklabels=False, gridcolor="#E5E5E5"),
                angularaxis=dict(gridcolor="#E5E5E5", tickfont=dict(size=14))
            ),
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=450,
            margin=dict(l=50, r=50, t=30, b=30)
        )
        
        # 4. 渲染图表
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("请在左侧选择食材以生成风味星图")
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
        
    # 获取所有食材英文名
    all_ingredients = sorted(df['name'].tolist())
    
    # 创建一个映射函数：如果字典里有中文就显示中文，没有就显示英文
    def get_chinese_name(eng_name):
        cn_name = agent.name_map.get(eng_name, eng_name)
        return f"{cn_name} ({eng_name})" if cn_name != eng_name else eng_name
    
    # 修改 multiselect
    selected = st.sidebar.multiselect(
        "🔬 选择食材进行穿梭",
        options=all_ingredients,
        format_func=get_chinese_name  # 关键点：这一行负责把英文变成中文显示
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
