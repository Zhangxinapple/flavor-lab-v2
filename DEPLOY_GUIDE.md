# 味觉虫洞 Flavor Lab - 部署指南

## 快速部署到 Streamlit Cloud

### 1. 准备代码

确保以下文件已推送到 GitHub 仓库：

```
├── app.py                 # 主应用文件
├── requirements.txt       # Python 依赖
├── localization_zh.json   # 中文本地化文件
├── flavordb_data.csv      # 食材分子数据（必需）
└── DEPLOY_GUIDE.md        # 本指南
```

### 2. 配置 API Key

#### 方式一：Streamlit Cloud Secrets（推荐）

1. 登录 [Streamlit Cloud](https://share.streamlit.io/)
2. 进入你的 App 设置页面
3. 点击左侧菜单的 **Secrets**
4. 添加以下配置（TOML 格式）：

```toml
# 阿里云 DashScope（推荐，国内访问稳定）
DASHSCOPE_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
DASHSCOPE_MODEL = "qwen-plus"  # 可选: qwen-turbo, qwen-max

# 或 Google Gemini（免费额度）
# GEMINI_API_KEY = "AIza..."
# GEMINI_MODEL = "gemini-2.0-flash"

# 或 OpenAI
# OPENAI_API_KEY = "sk-..."
# OPENAI_MODEL = "gpt-4o-mini"
```

5. 点击 **Save changes** 保存

#### 方式二：用户手动输入（临时使用）

用户可以在应用侧边栏的「设置」标签中手动粘贴 API Key，Key 仅保存在当前会话，页面关闭后自动清除。

### 3. 部署步骤

1. 在 Streamlit Cloud 点击 **New app**
2. 选择你的 GitHub 仓库
3. 选择分支（通常是 `main`）
4. 主文件路径填写：`app.py`
5. 点击 **Deploy**

### 4. 获取 DashScope API Key

1. 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录阿里云账号
3. 进入 **API-KEY 管理**
4. 点击 **创建新的 API-KEY**
5. 复制 Key（格式：`sk-...`）

### 5. 测试清单

部署完成后，请进行以下测试：

- [ ] 不配置 API Key 时，AI 区域显示友好引导
- [ ] 配置错误 Key 时，显示"Key 无效"具体提示
- [ ] 配置正确 Key 后，AI 能回复并包含"🛰️ 虫洞坐标"等五个模块
- [ ] 选择 2 种食材后，雷达图正常显示
- [ ] 点击"随机探索"按钮，自动填充食材并分析
- [ ] 在手机上打开，无横向滚动条
- [ ] 页面刷新后，已选择的食材保持选中

### 6. 故障排查

#### API 连接失败

1. 检查 Secrets 格式是否正确（TOML 格式）
2. 在侧边栏「设置」中开启「显示调试信息」查看日志
3. 确认 Key 格式为 `sk-` 开头（DashScope）
4. 检查网络连接

#### 食材数据缺失

确保 `flavordb_data.csv` 文件已上传到仓库根目录。

#### 中文显示异常

确保 `localization_zh.json` 文件编码为 UTF-8。

### 7. 技术规范

- **Python 版本**: 3.9+
- **Streamlit 版本**: 1.28.0+
- **单文件架构**: 所有代码在 `app.py` 中
- **状态管理**: 使用 `st.session_state`
- **API 优先级**: 手动输入 > Streamlit Secrets > 环境变量 > config.py

---

## 本地开发

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
streamlit run app.py
```

### 本地配置 API Key

创建 `config.py` 文件（已添加到 `.gitignore`）：

```python
DASHSCOPE_API_KEY = "sk-..."
DASHSCOPE_MODEL = "qwen-plus"
```

---

## 更新日志

### V2.0 (2024-XX-XX)

- ✅ 修复 API 连接问题，支持 DashScope OpenAI 兼容模式
- ✅ 升级系统 Prompt，包含五大模块（虫洞坐标、关联逻辑、实验报告、厨师应用、风味星图）
- ✅ 优化 AI 对话交互，快捷问题无刷新
- ✅ 重构 Sidebar 为分段式布局（实验台/配方台/设置）
- ✅ 添加空状态体验（热门实验卡片、使用流程）
- ✅ 桥接推荐支持一键加入实验
- ✅ 修复色彩对比度，符合 WCAG AA 标准
- ✅ 添加移动端适配
- ✅ 添加加载动画和过渡效果
- ✅ 优化上下文注入，AI 接收完整食材数据
- ✅ AI 回复术语高亮

---

**遇到问题？** 请检查：
1. Secrets 配置格式是否正确
2. API Key 是否有效
3. 网络连接是否正常
4. 浏览器控制台是否有错误信息
