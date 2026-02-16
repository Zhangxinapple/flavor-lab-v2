# 🌌 味觉虫洞 Flavor Lab

基于分子美食学的AI风味分析引擎 - 让食材搭配更科学

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red)

## ✨ 功能特性

- 🔬 **分子级风味分析** - 基于555+种食材的风味数据库
- 🎯 **智能配对推荐** - AI自动分析食材间的风味关联度
- 📊 **可视化雷达图** - 直观展示食材的六维风味特征
- 🧪 **专家级报告** - 生成详细的风味分析和应用建议
- 🌐 **中英双语** - 智能翻译食材和风味术语

## 🚀 快速开始

### 方法 1: 一键修复（推荐）

```bash
# 运行自动修复脚本
python fix_deployment.py
```

### 方法 2: 手动安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行应用
streamlit run app.py

# 3. 打开浏览器访问 http://localhost:8501
```

## 📦 文件说明

```
molecular-flavor-lab/
├── app.py                    # 主程序（使用优化版）
├── app_optimized.py          # 优化版本（推荐）
├── flavordb_data.csv         # 风味数据库（555种食材）
├── requirements.txt          # Python依赖
├── fix_deployment.py         # 自动修复脚本
├── DEPLOYMENT_GUIDE.md       # 详细部署文档
└── README.md                 # 本文件
```

## 🌐 在线部署

### Streamlit Cloud（推荐）

1. Fork本仓库到你的GitHub
2. 访问 [share.streamlit.io](https://share.streamlit.io)
3. 连接你的GitHub仓库
4. 选择 `app.py` 作为主文件
5. 点击 Deploy

### Hugging Face Spaces

1. 创建新Space，选择Streamlit SDK
2. 上传所有文件
3. 自动部署完成

详细步骤请查看 [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

## 🎯 使用方法

1. **选择锚点食材** - 在侧边栏选择第一个食材作为"味觉锚点"
2. **添加对比食材** - 继续选择2-3个食材进行对比
3. **查看分析结果** - AI会生成风味关联度评分和专家报告
4. **获取应用建议** - 根据报告进行创意菜品研发

### 推荐组合尝试

- 🍫 咖啡 + 黑巧克力（经典组合）
- 🍓 草莓 + 番茄（意外的和谐）
- 🍎 猪肉 + 苹果（传统智慧）
- 🧀 奶酪 + 葡萄（风味补偿）

## 🐛 问题排查

### 常见问题

**Q: 侧边栏没有食材显示？**
```bash
# 检查数据文件
python -c "import pandas as pd; print(len(pd.read_csv('flavordb_data.csv')))"
```

**Q: 显示"找不到数据文件"？**
- 确保 `flavordb_data.csv` 在与 `app.py` 同一目录
- 检查文件名大小写

**Q: 中文显示乱码？**
- 使用优化版 `app_optimized.py`
- 或将其重命名为 `app.py` 替换原文件

更多问题请查看 [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) 的"常见问题"部分

## 📊 技术栈

- **前端框架**: Streamlit 1.28+
- **数据处理**: Pandas 2.0+
- **可视化**: Plotly 5.17+
- **AI引擎**: 基于Jaccard相似度的风味匹配算法
- **数据来源**: FlavorDB（分子美食学数据库）

## 🔄 版本历史

### v2.0 (当前) - 优化版
- ✅ 修复数据加载问题（555种食材可用）
- ✅ 改进评分算法（Jaccard相似度）
- ✅ 优化UI/UX（渐变色、悬停效果）
- ✅ 添加分类筛选功能
- ✅ 提升部署兼容性

### v1.0 - 初始版本
- 基础风味分析功能
- 雷达图可视化
- AI报告生成

## 📝 开发计划

### 短期 (v2.1)
- [ ] 添加搜索功能
- [ ] 增加"随机推荐"按钮
- [ ] 优化移动端显示

### 中期 (v3.0)
- [ ] 引入真实分子数据库
- [ ] 添加用户收藏功能
- [ ] 配方保存/导出

### 长期 (v4.0)
- [ ] 用户账号系统
- [ ] 社区分享功能
- [ ] 移动App

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License - 自由使用，请保留原作者信息

## 🙏 致谢

- 数据来源: [FlavorDB](https://cosylab.iiitd.edu.in/flavordb/)
- AI引擎: Claude Sonnet 4
- 框架: Streamlit

## 📧 联系方式

- GitHub Issues: [提交问题](../../issues)
- 项目主页: [查看文档](../../)

---

**祝你探索美味！🍽️**
