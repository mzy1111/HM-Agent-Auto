#!/usr/bin/env python3
import sys
from HarmonyAutoAgent import HarmonyAutoAgent

def interactive_app_launcher():
    """交互式应用启动器，支持自然语言输入打开应用"""
    print("===== 应用启动器 =====")
    
    # 创建代理实例
    agent = HarmonyAutoAgent()
    
    # 检查设备连接状态
    device_connected = agent.check_device_connected()
    if device_connected:
        print("✓ 设备已连接，可以执行实际操作")
    else:
        print("⚠ 设备未连接，将进入模拟模式")
    
    # 应用UI元素配置
    app_elements = [
        {
            "description": "设置",
            "position": {
                "x": 753,
                "y": 1923
            },
            "type": "icon"
        },
        {
            "description": "图库",
            "position": {
                "x": 1042,
                "y": 1923
            },
            "type": "icon"
        }
    ]
    
    print("\n支持的应用:")
    for i, app in enumerate(app_elements, 1):
        print(f"   {i}. {app['description']} - 位置: ({app['position']['x']}, {app['position']['y']})")
    
    print("\n开始使用")
    print("输入自然语言指令（如：'打开设置'、'点击图库'），输入'exit'退出")
    
    while True:
        # 获取用户输入
        user_input = input("\n请输入指令: ").strip()
        
        if user_input.lower() == 'exit':
            print("\n退出应用启动器")
            break
        
        if not user_input:
            print("请输入有效的指令")
            continue
        
        # 解析自然语言指令
        parsed_result = agent.parser.parse_instruction(user_input, app_elements)
        
        # 查找匹配的应用并执行点击
        found = False
        if isinstance(parsed_result, list):
            # 处理操作步骤列表
            for step in parsed_result:
                if isinstance(step, dict) and step.get("action") in ["tap", "click"]:
                    target = step.get("target", {})
                    if target and "description" in target and "position" in target:
                        # 获取点击坐标
                        pos = target["position"]
                        x = pos["x"] if isinstance(pos, dict) else pos[0]
                        y = pos["y"] if isinstance(pos, dict) else pos[1]
                        
                        print(f"执行操作: 打开{target['description']}")
                        
                        if device_connected:
                            # 实际执行点击命令
                            success = agent.device_manager.tap(x, y)
                            if success:
                                print(f"✓ 成功打开{target['description']}")
                            else:
                                print(f"✗ 打开{target['description']}失败")
                        else:
                            print(f"⚠ 模拟打开{target['description']}")
                        
                        found = True
                        break
        elif isinstance(parsed_result, dict) and parsed_result.get("action") in ["tap", "click"]:
            # 处理单个点击操作
            target = parsed_result.get("target", {})
            if target and "description" in target and "position" in target:
                # 获取点击坐标
                pos = target["position"]
                x = pos["x"] if isinstance(pos, dict) else pos[0]
                y = pos["y"] if isinstance(pos, dict) else pos[1]
                
                print(f"执行操作: 打开{target['description']}")
                
                if device_connected:
                    # 实际执行点击命令
                    success = agent.device_manager.tap(x, y)
                    if success:
                        print(f"✓ 成功打开{target['description']}")
                    else:
                        print(f"✗ 打开{target['description']}失败")
                else:
                    print(f"⚠ 模拟打开{target['description']}")
                
                found = True
        
        if not found:
            print("✗ 未找到匹配的应用，无法执行操作")

if __name__ == "__main__":
    interactive_app_launcher()
    sys.exit(0)