#!/usr/bin/env python3
"""
快速测试设备扫描功能
测试 RealSense 和串口扫描是否正常工作
"""

import sys
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent))

from device_scanner import DeviceScanner
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_port_scan():
    """测试串口扫描"""
    print("\n" + "="*60)
    print("测试 1: 扫描串口")
    print("="*60)
    
    try:
        ports = DeviceScanner.find_available_ports()
        print(f"✅ 成功扫描串口")
        print(f"   找到 {len(ports)} 个串口:")
        for port in ports:
            print(f"   - {port}")
        return True
    except Exception as e:
        print(f"❌ 串口扫描失败: {e}")
        return False


def test_opencv_cameras():
    """测试 OpenCV 相机扫描"""
    print("\n" + "="*60)
    print("测试 2: 扫描 OpenCV 相机")
    print("="*60)
    
    try:
        cameras = DeviceScanner.find_opencv_cameras()
        print(f"✅ 成功扫描 OpenCV 相机")
        print(f"   找到 {len(cameras)} 个相机:")
        for cam in cameras:
            print(f"   - {cam['name']} (ID: {cam['id']}, {cam['width']}x{cam['height']}@{cam['fps']}fps)")
        return True
    except Exception as e:
        print(f"❌ OpenCV 相机扫描失败: {e}")
        return False


def test_realsense_cameras():
    """测试 RealSense 相机扫描"""
    print("\n" + "="*60)
    print("测试 3: 扫描 RealSense 相机")
    print("="*60)
    
    try:
        cameras = DeviceScanner.find_realsense_cameras()
        print(f"✅ 成功扫描 RealSense 相机（无错误）")
        print(f"   找到 {len(cameras)} 个相机:")
        for cam in cameras:
            print(f"   - {cam['name']} (ID: {cam['id']}, {cam['width']}x{cam['height']}@{cam['fps']}fps)")
        
        # 检查 pyrealsense2 是否可用
        try:
            import pyrealsense2 as rs
            print(f"   📦 pyrealsense2 已安装: {rs.__version__}")
        except ImportError:
            print(f"   ⚠️  pyrealsense2 未安装（这是可选的）")
        
        return True
    except Exception as e:
        print(f"❌ RealSense 相机扫描失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_cameras():
    """测试扫描所有相机"""
    print("\n" + "="*60)
    print("测试 4: 扫描所有相机（OpenCV + RealSense）")
    print("="*60)
    
    try:
        cameras = DeviceScanner.find_all_cameras()
        print(f"✅ 成功扫描所有相机")
        print(f"   总共找到 {len(cameras)} 个相机:")
        for cam in cameras:
            print(f"   - [{cam['type']}] {cam['name']} (ID: {cam['id']})")
        return True
    except Exception as e:
        print(f"❌ 扫描所有相机失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "🔍 设备扫描测试".center(60, "="))
    print("此脚本测试设备扫描功能是否正常工作")
    print("特别测试 RealSense 相机扫描的修复")
    print("="*60)
    
    results = []
    
    # 运行测试
    results.append(("串口扫描", test_port_scan()))
    results.append(("OpenCV 相机扫描", test_opencv_cameras()))
    results.append(("RealSense 相机扫描", test_realsense_cameras()))
    results.append(("所有相机扫描", test_all_cameras()))
    
    # 显示结果
    print("\n" + "="*60)
    print("测试结果摘要")
    print("="*60)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name:.<40} {status}")
    
    # 总体结果
    all_passed = all(success for _, success in results)
    print("="*60)
    if all_passed:
        print("🎉 所有测试通过！")
        return 0
    else:
        failed_count = sum(1 for _, success in results if not success)
        print(f"⚠️  {failed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中出现未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

