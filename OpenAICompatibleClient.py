import os
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class OpenAICompatibleClient:
    """OpenAI兼容客户端，用于调用OpenAI、DeepSeek等兼容API"""

    def __init__(self, api_key=None, base_url=None, model_id=None):
        """初始化客户端

        Args:
            api_key (str, optional): API密钥
            base_url (str, optional): API基础URL
            model_id (str, optional): 模型ID
        """
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        self.model_id = model_id or os.getenv("LLM_MODEL_ID", "deepseek-chat")

        # 创建OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def generate(self, prompt, system_prompt=None):
        """生成文本回复

        Args:
            prompt (str): 用户输入的提示
            system_prompt (str, optional): 系统提示

        Returns:
            str: 生成的回复
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
        )

        return response.choices[0].message.content.strip()
    
    def generate_with_image(self, prompt, image_path, system_prompt=None):
        """生成带图片的回复

        Args:
            prompt (str): 用户输入的提示
            image_path (str): 图片路径
            system_prompt (str, optional): 系统提示

        Returns:
            str: 生成的回复
        """
        # 读取图片并转换为base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 构建消息内容
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        })

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = str(e)
            if "unknown variant `image_url`" in error_msg:
                raise Exception(f"当前API不支持多模态功能。错误信息: {error_msg}\n请检查以下几点:\n1. 模型ID是否正确\n2. 是否使用了支持多模态的API服务\n3. API端点是否正确")
            elif "Model Not Exist" in error_msg:
                raise Exception(f"当前模型 {self.model_id} 不存在。请检查模型ID是否正确。")
            raise Exception(f"调用多模态API时发生错误: {e}")
    

    
    def extract_elements_from_image(self, image_path):
        """从图片中提取元素及其位置

        Args:
            image_path (str): 图片路径

        Returns:
            dict: 包含图片中元素及其位置的字典
        """
        prompt = "请分析这张图片，识别所有可见的UI元素（如按钮、输入框、文本区域、图标等），并返回它们的位置信息。每个元素需要包含类型、位置（x, y坐标和宽度、高度）、以及描述。请以JSON格式返回结果，确保格式正确。"
        
        system_prompt = "你是一个精确的UI元素分析助手，能够准确识别图片中的UI元素及其位置。"
        
        try:
            result = self.generate_with_image(prompt, image_path, system_prompt)
            # 尝试解析JSON响应
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # 如果响应不是有效的JSON，返回原始文本
                return {"text": result}
        except Exception as e:
            return {"error": str(e)}
