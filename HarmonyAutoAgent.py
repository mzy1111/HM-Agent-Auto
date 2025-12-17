import os
import time
from HarmonyDeviceManager import HarmonyDeviceManager
from InstructionParser import InstructionParser
from OpenAICompatibleClient import OpenAICompatibleClient

class HarmonyAutoAgent:
    """鸿蒙自动操作代理，实现从自然语言指令到手机操作的自动化"""
    
    def __init__(self, device_command="hdc", screenshot_path="screenshot.jpeg"):
        """初始化自动操作代理
        
        Args:
            device_command (str): 设备管理命令路径，支持hdc, hdc_std, adb
            screenshot_path (str): 截图保存路径
        """
        self.device_manager = HarmonyDeviceManager(device_command)
        self.client = OpenAICompatibleClient()
        self.parser = InstructionParser(self.client)
        self.screenshot_path = screenshot_path
    
    def check_command_available(self):
        """检查设备管理命令是否可用
        
        Returns:
            bool: 命令是否可用
        """
        return self.device_manager.check_command_available()
    
    def check_device_connected(self):
        """检查设备是否已连接
        
        Returns:
            bool: 设备是否已连接
        """
        return self.device_manager.check_device_connected()
    
    def get_screenshot_and_elements(self):
        """获取屏幕截图并分析UI元素
        
        Returns:
            tuple: (截图路径, UI元素分析结果)
        """
        # 获取截图
        if not self.device_manager.get_screenshot(self.screenshot_path):
            return None, None
        
        # 分析UI元素
        elements = self.client.extract_elements_from_image(self.screenshot_path)
        return self.screenshot_path, elements
    
    def execute_instruction(self, instruction):
        """执行自然语言指令
        
        Args:
            instruction (str): 自然语言指令
            
        Returns:
            bool: 操作是否成功
        """
        print(f"\n===== 执行指令: {instruction} =====")
        
        # 检查设备连接
        if not self.check_device_connected():
            print("错误: 设备未连接")
            return False
        
        # 获取屏幕截图和UI元素
        screenshot_path, ui_elements = self.get_screenshot_and_elements()
        if not screenshot_path or not ui_elements:
            print("错误: 无法获取屏幕截图或分析UI元素")
            return False
        
        print("\n屏幕UI元素分析结果:")
        print(ui_elements)
        
        # 解析指令
        parsed_instruction = self.parser.parse_instruction(instruction, ui_elements)
        print(f"\n解析后的指令: {parsed_instruction}")
        
        # 执行操作
        if isinstance(parsed_instruction, list):
            # 如果返回的是操作步骤列表
            for step in parsed_instruction:
                if not self._execute_single_action(step):
                    return False
        elif isinstance(parsed_instruction, dict):
            # 如果返回的是单个操作
            return self._execute_single_action(parsed_instruction)
        else:
            print(f"错误: 解析结果格式不正确: {parsed_instruction}")
            return False
        
        return True
    
    def _execute_single_action(self, action):
        """执行单个操作
        
        Args:
            action (dict): 操作信息
            
        Returns:
            bool: 操作是否成功
        """
        if not isinstance(action, dict) or "action" not in action:
            print(f"错误: 操作格式不正确: {action}")
            return False
        
        action_type = action["action"]
        params = action.get("params", {})
        target = action.get("target", {})
        
        print(f"\n执行操作: {action_type}")
        print(f"操作参数: {params}")
        
        # 执行不同类型的操作
        if action_type == "click" or action_type == "tap":
            # 点击操作
            if "position" in target:
                # 如果目标包含位置信息
                x1, y1, x2, y2 = target["position"]
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
            elif "coordinates" in params:
                # 如果参数包含坐标
                center_x, center_y = params["coordinates"]
            else:
                # 尝试从UI元素中找到目标
                instruction = action.get("target", {}).get("description", "")
                screenshot_path, ui_elements = self.get_screenshot_and_elements()
                if not ui_elements:
                    print("错误: 无法获取UI元素")
                    return False
                target_element = self.parser.find_target_element(instruction, ui_elements)
                if not target_element:
                    print(f"错误: 无法找到目标元素: {instruction}")
                    return False
                center = self.parser.get_element_center(target_element)
                if not center:
                    print("错误: 无法计算目标元素中心坐标")
                    return False
                center_x, center_y = center
            
            # 执行点击
            return self.device_manager.tap(center_x, center_y)
            
        elif action_type == "swipe":
            # 滑动操作
            screen_size = self.device_manager.get_screen_size()
            if not screen_size:
                print("错误: 无法获取屏幕尺寸")
                return False
            
            swipe_params = self.parser.extract_swipe_params(
                action.get("description", ""), 
                screen_size
            ) or params
            
            start_x = swipe_params.get("start_x") or params.get("start_x")
            start_y = swipe_params.get("start_y") or params.get("start_y")
            end_x = swipe_params.get("end_x") or params.get("end_x")
            end_y = swipe_params.get("end_y") or params.get("end_y")
            duration = swipe_params.get("duration") or params.get("duration")
            
            if not all([start_x, start_y, end_x, end_y]):
                print("错误: 滑动操作参数不完整")
                return False
            
            # 执行滑动
            return self.device_manager.swipe(start_x, start_y, end_x, end_y, duration)
            
        elif action_type == "type":
            # 输入文本操作
            text = params.get("text") or action.get("target", {}).get("text", "")
            if not text:
                print("错误: 输入文本为空")
                return False
            
            # 执行输入
            return self.device_manager.send_text(text)
            
        elif action_type == "press_home":
            # 按下Home键
            return self.device_manager.press_home()
            
        elif action_type == "press_back":
            # 按下返回键
            return self.device_manager.press_back()
            
        elif action_type == "press_menu":
            # 按下菜单键
            return self.device_manager.press_menu()
            
        elif action_type == "screenshot":
            # 截图操作
            return self.device_manager.get_screenshot(self.screenshot_path)
            
        else:
            print(f"错误: 不支持的操作类型: {action_type}")
            return False
    
    def execute_multiple_instructions(self, instructions):
        """执行多条自然语言指令
        
        Args:
            instructions (list): 自然语言指令列表
            
        Returns:
            bool: 所有操作是否都成功
        """
        all_success = True
        for instruction in instructions:
            if not self.execute_instruction(instruction):
                all_success = False
        return all_success
    
    def interactive_mode(self):
        """进入交互模式，接收用户输入的指令"""
        print("===== 鸿蒙自动操作代理 - 交互模式 =====")
        print("输入'退出'或'quit'退出交互模式")
        
        while True:
            instruction = input("\n请输入指令: ").strip()
            if not instruction:
                continue
            
            if instruction.lower() in ["退出", "quit"]:
                print("退出交互模式")
                break
            
            try:
                self.execute_instruction(instruction)
            except Exception as e:
                print(f"执行指令时发生错误: {str(e)}")
    
    def test_device_connection(self):
        """测试设备连接和基本功能
        
        Returns:
            dict: 测试结果
        """
        results = {}
        
        # 检查设备连接
        results["device_connected"] = self.check_device_connected()
        
        if results["device_connected"]:
            # 获取屏幕尺寸
            results["screen_size"] = self.device_manager.get_screen_size()
            
            # 测试截图功能
            results["screenshot_taken"] = self.device_manager.get_screenshot(self.screenshot_path)
            
            # 测试UI元素分析
            if results["screenshot_taken"]:
                try:
                    elements = self.client.extract_elements_from_image(self.screenshot_path)
                    results["ui_elements_analyzed"] = True
                    results["ui_element_count"] = len(elements) if isinstance(elements, list) else 0
                except Exception:
                    results["ui_elements_analyzed"] = False
            else:
                results["ui_elements_analyzed"] = False
        
        return results