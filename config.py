# 风味虫洞 · 后台配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API 优先级：环境变量 > config.py > Streamlit Secrets
# 本地已配置 ~/.zshrc 中的 DASHSCOPE_API_KEY 时，此文件可留空
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 阿里云通义千问（推荐，稳定，国内无限制）
# 从 https://dashscope.console.aliyun.com/ 获取
DASHSCOPE_API_KEY = ""   # 留空则从环境变量 os.getenv("DASHSCOPE_API_KEY") 读取
DASHSCOPE_MODEL   = "qwen-turbo"   # 可选：qwen-turbo / qwen-plus / qwen-max

# Gemini（备用）
GEMINI_API_KEY = ""
GEMINI_MODEL   = "gemini-2.0-flash"
