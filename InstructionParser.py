import json
from OpenAICompatibleClient import OpenAICompatibleClient

class InstructionParser:
    """指令解析器，将自然语言指令转换为操作步骤"""
    
    def __init__(self, client=None):
        """初始化指令解析器
        
        Args:
            client (OpenAICompatibleClient): LLM客户端实例
        """
        self.client = client or OpenAICompatibleClient()
    
    def parse_instruction(self, instruction, ui_elements=None):
        """解析自然语言指令
        
        Args:
            instruction (str): 自然语言指令
            ui_elements (dict): UI元素分析结果
            
        Returns:
            dict: 解析结果，包含操作类型和参数
        """
        system_prompt = "你是一个智能助手，能够将用户的自然语言指令转换为具体的手机操作步骤。"
        
        if ui_elements:
            # 如果提供了UI元素信息，使用它来确定操作目标
            prompt = f"用户指令: {instruction}\n\n当前屏幕UI元素:\n{json.dumps(ui_elements, ensure_ascii=False)}\n\n请将用户指令转换为具体的操作步骤。每个操作步骤应包含：\n- action: 操作类型（如click, swipe, tap, type等）\n- target: 目标UI元素（从提供的UI元素中选择）\n- params: 操作参数（如坐标、文本等）\n\n请以JSON格式返回结果，确保格式正确。"
        else:
            # 如果没有UI元素信息，只分析指令类型
            prompt = f"用户指令: {instruction}\n\n请分析这个指令，确定需要执行的操作类型和可能的参数。操作类型包括：click, swipe, tap, type, press_home, press_back, press_menu等。\n\n请以JSON格式返回结果，确保格式正确。"
        
        result = self.client.generate(prompt, system_prompt)
        
        # 处理可能包含在代码块中的JSON
        if result.startswith('```json') and result.endswith('```'):
            # 提取代码块中的JSON内容
            result = result[7:-3].strip()
        elif result.startswith('```') and result.endswith('```'):
            # 提取通用代码块中的内容
            result = result[3:-3].strip()
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            # 如果LLM返回的不是有效的JSON，尝试修复或返回错误
            print(f"LLM返回的结果不是有效的JSON: {result}")
            # 尝试简单解析
            return {"action": "unknown", "error": f"无法解析指令: {result}"}
    
    def find_target_element(self, instruction, ui_elements):
        """根据指令在UI元素中找到目标元素
        
        Args:
            instruction (str): 自然语言指令
            ui_elements (dict): UI元素分析结果
            
        Returns:
            dict: 目标UI元素信息
        """
        system_prompt = "你是一个精确的UI元素匹配助手，能够根据用户指令找到对应的UI元素。"
        
        prompt = f"用户指令: {instruction}\n\n当前屏幕UI元素:\n{json.dumps(ui_elements, ensure_ascii=False)}\n\n请从提供的UI元素中找到与用户指令最匹配的元素，只返回该元素的完整信息，不要添加任何其他内容。\n\n请以JSON格式返回结果，确保格式正确。"
        
        result = self.client.generate(prompt, system_prompt)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            print(f"无法解析目标元素: {result}")
            return None
    
    def get_element_center(self, element):
        """计算UI元素的中心点坐标
        
        Args:
            element (dict): UI元素信息
            
        Returns:
            tuple: (x, y) 中心点坐标
        """
        if isinstance(element, dict) and "position" in element:
            position = element["position"]
            if len(position) == 4:
                x1, y1, x2, y2 = position
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                return center_x, center_y
        return None
    
    def determine_action_type(self, instruction):
        """根据指令确定操作类型
        
        Args:
            instruction (str): 自然语言指令
            
        Returns:
            str: 操作类型
        """
        system_prompt = "你是一个操作类型分析助手，能够根据用户指令确定需要执行的手机操作类型。"
        
        prompt = f"用户指令: {instruction}\n\n请从以下操作类型中选择最匹配的类型：\n- click: 点击某个UI元素\n- swipe: 滑动屏幕\n- tap: 点击屏幕某个坐标\n- type: 输入文本\n- press_home: 按下Home键\n- press_back: 按下返回键\n- press_menu: 按下菜单键\n- screenshot: 截图\n\n只返回操作类型名称，不要添加任何其他内容。"
        
        result = self.client.generate(prompt, system_prompt)
        return result.strip()
    
    def extract_swipe_params(self, instruction, screen_size):
        """从指令中提取滑动操作参数
        
        Args:
            instruction (str): 自然语言指令
            screen_size (tuple): 屏幕尺寸 (宽度, 高度)
            
        Returns:
            dict: 滑动参数，包含起始坐标、结束坐标和持续时间
        """
        if not screen_size:
            return None
            
        system_prompt = "你是一个滑动操作参数提取助手，能够从用户指令中提取滑动操作的参数。"
        
        width, height = screen_size
        prompt = f"用户指令: {instruction}\n\n当前屏幕尺寸: {width}x{height}\n\n请根据指令提取滑动操作的参数，包括：\n- start_x: 起始x坐标\n- start_y: 起始y坐标\n- end_x: 结束x坐标\n- end_y: 结束y坐标\n- duration: 滑动持续时间（毫秒，可选）\n\n请以JSON格式返回结果，确保格式正确。"
        
        result = self.client.generate(prompt, system_prompt)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            print(f"无法解析滑动参数: {result}")
            return None