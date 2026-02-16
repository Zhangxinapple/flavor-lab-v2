#!/usr/bin/env python3
"""
味觉虫洞 - 快速修复脚本
自动检测并修复常见部署问题
"""

import os
import sys
import subprocess

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_file_exists(filename):
    """检查文件是否存在"""
    if os.path.exists(filename):
        print(f"✅ {filename} 存在")
        return True
    else:
        print(f"❌ {filename} 不存在")
        return False

def check_dependencies():
    """检查依赖是否安装"""
    print_header("检查依赖包")
    
    required = ['pandas', 'streamlit', 'plotly']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            print(f"❌ {package} 未安装")
            missing.append(package)
    
    return missing

def install_dependencies(missing):
    """安装缺失的依赖"""
    if not missing:
        return
    
    print_header("安装缺失依赖")
    print(f"将安装: {', '.join(missing)}")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
        print("✅ 依赖安装成功")
    except subprocess.CalledProcessError:
        print("❌ 依赖安装失败，请手动运行: pip install -r requirements.txt")

def check_data_quality():
    """检查数据文件质量"""
    print_header("检查数据质量")
    
    try:
        import pandas as pd
        df = pd.read_csv('flavordb_data.csv')
        
        print(f"✅ 数据文件读取成功")
        print(f"   - 总行数: {len(df)}")
        print(f"   - 列名: {', '.join(df.columns.tolist())}")
        
        # 检查关键列
        if 'flavor_profiles' in df.columns:
            valid_rows = df[df['flavor_profiles'].notna() & (df['flavor_profiles'].str.len() > 0)]
            print(f"   - 有效风味数据: {len(valid_rows)} 行")
            
            if len(valid_rows) < 50:
                print("⚠️  警告: 有效数据太少，可能影响使用体验")
            else:
                print("✅ 数据质量良好")
        else:
            print("❌ 缺少 flavor_profiles 列")
        
        return True
    except FileNotFoundError:
        print("❌ 找不到 flavordb_data.csv")
        return False
    except Exception as e:
        print(f"❌ 数据检查失败: {e}")
        return False

def create_optimized_requirements():
    """创建优化的requirements.txt"""
    print_header("创建 requirements.txt")
    
    content = """pandas>=2.0.0
streamlit>=1.28.0
plotly>=5.17.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(content)
    
    print("✅ requirements.txt 已创建/更新")

def run_test():
    """运行测试"""
    print_header("运行测试")
    
    try:
        import pandas as pd
        import streamlit as st
        import plotly.graph_objects as go
        
        # 测试数据加载
        df = pd.read_csv('flavordb_data.csv')
        print(f"✅ 数据加载测试通过")
        
        # 测试数据处理
        df['mol_set'] = df['flavor_profiles'].apply(
            lambda x: set(str(x).replace(',', ' ').split()) if x else set()
        )
        valid_df = df[df['flavor_profiles'].notna() & (df['flavor_profiles'].str.len() > 0)]
        print(f"✅ 数据处理测试通过 ({len(valid_df)} 条有效记录)")
        
        # 测试Plotly
        fig = go.Figure(data=go.Scatterpolar(r=[1,2,3], theta=['A','B','C']))
        print(f"✅ Plotly图表测试通过")
        
        print("\n🎉 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    print("""
    ╔════════════════════════════════════════════╗
    ║   🌌 味觉虫洞 - 快速修复工具 v1.0       ║
    ║   Flavor Lab Quick Fix Tool               ║
    ╚════════════════════════════════════════════╝
    """)
    
    # 检查必要文件
    print_header("检查必要文件")
    files_ok = all([
        check_file_exists('flavordb_data.csv'),
        check_file_exists('app.py')
    ])
    
    if not files_ok:
        print("\n⚠️  缺少必要文件，请确保以下文件在当前目录：")
        print("   - flavordb_data.csv")
        print("   - app.py")
        return
    
    # 检查并安装依赖
    missing = check_dependencies()
    if missing:
        install = input("\n是否安装缺失的依赖? (y/n): ").lower()
        if install == 'y':
            install_dependencies(missing)
    
    # 创建requirements.txt
    create_optimized_requirements()
    
    # 检查数据质量
    check_data_quality()
    
    # 运行测试
    test_ok = run_test()
    
    # 总结
    print_header("修复完成")
    
    if test_ok:
        print("""
✅ 所有检查通过！现在可以运行应用：

    streamlit run app.py

或部署到云平台：
    1. Streamlit Cloud: https://share.streamlit.io
    2. Hugging Face Spaces: https://huggingface.co/spaces
    3. Railway: https://railway.app
        """)
    else:
        print("""
⚠️  仍有问题需要解决。请查看上面的错误信息。

常见解决方案：
    1. 确保所有文件都在正确位置
    2. 重新安装依赖: pip install -r requirements.txt
    3. 检查Python版本 (推荐 3.8+)
    4. 查看详细文档: DEPLOYMENT_GUIDE.md
        """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("请查看 DEPLOYMENT_GUIDE.md 获取更多帮助")
