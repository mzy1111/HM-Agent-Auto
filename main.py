#!/usr/bin/env python3
import argparse
import sys
import os
from HarmonyAutoAgent import HarmonyAutoAgent

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="鸿蒙自动操作代理 - 从自然语言指令到手机操作的自动化工具")
    
    # 命令行参数
    parser.add_argument(
        "--device-command", 
        type=str, 
        default="hdc", 
        help="设备管理命令路径，支持hdc, hdc_std, adb"
    )
    parser.add_argument(
        "--screenshot-path", 
        type=str, 
        default="screenshot.jpeg", 
        help="截图保存路径"
    )
    parser.add_argument(
        "--instruction", 
        type=str, 
        help="要执行的自然语言指令"
    )
    parser.add_argument(
        "--instruction-file", 
        type=str, 
        help="包含多条指令的文件路径"
    )
    parser.add_argument(
        "--interactive", 
        action="store_true", 
        help="进入交互模式"
    )
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="测试设备连接和基本功能"
    )
    
    args = parser.parse_args()
    
    # 创建自动操作代理实例
    agent = HarmonyAutoAgent(
        device_command=args.device_command, 
        screenshot_path=args.screenshot_path
    )
    
    # 检查命令是否可用
    if not agent.check_command_available():
        print(f"错误: 设备管理命令不可用，请确保已安装 {args.device_command} 并添加到环境变量")
        sys.exit(1)
    
    # 测试设备连接
    if not agent.check_device_connected():
        print("错误: 设备未连接，请确保已连接设备并授权调试")
        sys.exit(1)
    
    # 根据参数执行不同的功能
    if args.test:
        # 测试设备连接和基本功能
        print("===== 测试设备连接和基本功能 =====")
        results = agent.test_device_connection()
        print("测试结果:")
        for key, value in results.items():
            print(f"{key}: {value}")
        sys.exit(0 if results.get("device_connected") else 1)
    
    elif args.instruction:
        # 执行单条指令
        success = agent.execute_instruction(args.instruction)
        sys.exit(0 if success else 1)
    
    elif args.instruction_file:
        # 执行文件中的多条指令
        if not os.path.exists(args.instruction_file):
            print(f"错误: 文件不存在: {args.instruction_file}")
            sys.exit(1)
        
        with open(args.instruction_file, "r", encoding="utf-8") as f:
            instructions = [line.strip() for line in f if line.strip()]
        
        print(f"===== 执行文件中的 {len(instructions)} 条指令 =====")
        success = agent.execute_multiple_instructions(instructions)
        sys.exit(0 if success else 1)
    
    elif args.interactive:
        # 进入交互模式
        agent.interactive_mode()
        sys.exit(0)
    
    else:
        # 显示帮助信息
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()