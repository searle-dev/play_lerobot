#!/usr/bin/env python3
"""
串口检测测试脚本
用于测试串口自动检测功能是否正常工作
"""

import sys
from device_scanner import DeviceScanner

print("=" * 60)
print("串口自动检测测试")
print("=" * 60)
print()

# 步骤 1: 扫描当前所有串口
print("步骤 1: 扫描当前所有串口")
print("-" * 60)
ports_before = DeviceScanner.find_available_ports()
print(f"找到 {len(ports_before)} 个串口:")
for port in ports_before:
    print(f"  - {port}")
print()

# 步骤 2: 等待用户拔出 USB
print("步骤 2: 请拔出要检测的 USB 串口设备")
print("-" * 60)
input("拔出 USB 后按 Enter 继续...")
print()

# 步骤 3: 再次扫描并对比
print("步骤 3: 检测端口变化")
print("-" * 60)
result = DeviceScanner.find_port_after_disconnect(ports_before)

print(f"状态: {result['status']}")
print(f"消息: {result['message']}")
if result['status'] == 'success':
    print(f"检测到的端口: {result['port']}")
    print()
    print("✅ 测试成功！")
    print()
    print("现在可以重新插入 USB，该端口应该是:")
    print(f"  {result['port']}")
else:
    print()
    print("❌ 测试失败！")
    print()
    print("可能的原因:")
    print("1. 未拔出 USB 设备")
    print("2. 拔出了多个 USB 设备")
    print("3. 系统未及时更新端口列表")

print()
print("=" * 60)

