#!/usr/bin/env python3
"""
测试直接点击功能的脚本
"""

from HarmonyDeviceManager import HarmonyDeviceManager

def test_tap_settings():
    """测试点击设置图标"""
    print("===== 测试点击设置图标 =====")
    
    # 创建设备管理器实例
    device_manager = HarmonyDeviceManager()
    
    # 检查设备连接
    if not device_manager.check_device_connected():
        print("错误: 设备未连接")
        return False
    
    # 点击设置图标坐标 (753, 1923)
    print("正在点击设置图标坐标 (753, 1923)...")
    success = device_manager.tap(753, 1923)
    
    if success:
        print("点击成功！")
    else:
        print("点击失败！")
    
    return success

if __name__ == "__main__":
    test_tap_settings()