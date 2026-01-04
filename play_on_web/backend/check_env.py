#!/usr/bin/env python3
"""
环境检查脚本
验证所有必需的依赖是否正确安装
"""

import sys
from typing import List, Tuple

def check_import(module_name: str, package_name: str = None) -> Tuple[bool, str]:
    """
    检查模块是否可以导入
    
    Args:
        module_name: 要导入的模块名
        package_name: 包名（用于显示，默认与 module_name 相同）
    
    Returns:
        (success, message) 元组
    """
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        return True, f"✅ {package_name} - 已安装"
    except ImportError as e:
        return False, f"❌ {package_name} - 未安装: {e}"

def main():
    print("=" * 60)
    print("XLerobot Web Teleop - 环境检查")
    print("=" * 60)
    print()
    
    checks: List[Tuple[bool, str]] = []
    
    print("📦 检查 lerobot 核心依赖:")
    print("-" * 60)
    checks.append(check_import("lerobot"))
    checks.append(check_import("cv2", "opencv-python"))
    checks.append(check_import("numpy"))
    checks.append(check_import("serial", "pyserial"))
    print()
    
    print("🌐 检查 Web 服务依赖:")
    print("-" * 60)
    checks.append(check_import("fastapi"))
    checks.append(check_import("uvicorn"))
    checks.append(check_import("websockets"))
    checks.append(check_import("pydantic"))
    checks.append(check_import("pydantic_settings"))
    checks.append(check_import("aiofiles"))
    print()
    
    # 打印所有检查结果
    for success, message in checks:
        print(message)
    
    print()
    print("=" * 60)
    
    # 统计结果
    total = len(checks)
    passed = sum(1 for success, _ in checks if success)
    failed = total - passed
    
    print(f"总计: {total} 项检查")
    print(f"通过: {passed} 项 ✅")
    print(f"失败: {failed} 项 ❌")
    print()
    
    if failed > 0:
        print("❌ 环境检查失败！")
        print()
        print("请执行以下命令安装缺失的依赖:")
        print()
        print("# 如果使用 conda 环境:")
        print("conda activate lerobot")
        print("cd /path/to/lerobot")
        print("pip install -e .[all]")
        print("cd /path/to/play_on_web/backend")
        print("pip install -r requirements.txt")
        print()
        print("详细说明请查看 SETUP_CONDA.md")
        sys.exit(1)
    else:
        print("✅ 环境检查通过！所有依赖已正确安装。")
        print()
        print("您可以开始使用 XLerobot Web Teleop 了:")
        print("  python main.py")
        sys.exit(0)

if __name__ == "__main__":
    main()

