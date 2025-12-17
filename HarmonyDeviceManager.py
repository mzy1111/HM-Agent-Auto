import os
import subprocess
import time
import json

class HarmonyDeviceManager:
    """鸿蒙设备管理器，用于执行设备管理命令与设备交互"""
    
    def __init__(self, device_command="hdc"):
        """初始化设备管理器
        
        Args:
            device_command (str): 设备管理命令路径，默认使用环境变量中的hdc
                                  支持的命令包括：hdc, hdc_std, adb（部分命令兼容）
        """
        self.device_command = device_command
        self.command_type = self._detect_command_type()
    
    def _detect_command_type(self):
        """检测命令类型（hdc系列或adb系列）
        
        Returns:
            str: 命令类型，"hdc"或"adb"
        """
        if "hdc" in self.device_command:
            return "hdc"
        elif "adb" in self.device_command:
            return "adb"
        else:
            return "hdc"  # 默认假设为hdc系列
    
    def execute_command(self, command, timeout=30):
        """执行设备管理命令
        
        Args:
            command (str): 要执行的命令
            timeout (int): 命令执行超时时间（秒）
            
        Returns:
            tuple: (返回码, 标准输出, 标准错误)
        """
        full_command = f"{self.device_command} {command}"
        print(f"执行命令: {full_command}")
        
        try:
            process = subprocess.Popen(
                full_command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            stdout, stderr = process.communicate(timeout=timeout)
            return process.returncode, stdout.strip(), stderr.strip()
        except subprocess.TimeoutExpired:
            process.kill()
            return -1, "", "命令执行超时"
        except FileNotFoundError:
            return -1, "", f"找不到命令: {self.device_command}，请确保已安装并添加到环境变量"
        except Exception as e:
            return -1, "", f"命令执行失败: {str(e)}"
    
    def check_command_available(self):
        """检查设备管理命令是否可用
        
        Returns:
            bool: 命令是否可用
        """
        # 测试执行help命令
        return_code, stdout, stderr = self.execute_command("help", timeout=10)
        return return_code == 0
    
    def check_device_connected(self):
        """检查设备是否已连接
        
        Returns:
            bool: 设备是否已连接
        """
        # 根据命令类型使用不同的命令检查设备连接
        if self.command_type == "hdc":
            # 只使用hdc list targets命令检查设备连接
            cmd = "list targets"
        else:  # adb
            cmd = "devices"
        
        return_code, stdout, stderr = self.execute_command(cmd)
        if return_code == 0:
            stdout = stdout.strip()
            if stdout and not stdout.lower().startswith("unknown operation"):
                # 对于单行输出的情况
                if "\n" not in stdout:
                    line = stdout.strip()
                    # 检查是否是设备ID（长度大于等于10的字母数字组合）
                    if line and len(line) >= 10 and line.isalnum():
                        print(f"检测到设备ID: {line}")
                        return True
                else:
                    # 多行输出的情况
                    lines = stdout.strip().split("\n")
                    for line in lines:
                        line = line.strip()
                        if line and not line.lower().startswith("unknown operation"):
                            # 排除明显的标题行
                            if not (line.lower().startswith("list of devices attached") or 
                                    line.lower() == "target list" or 
                                    line.lower() == "devices"):
                                if line and len(line) >= 10 and line.isalnum():
                                    print(f"检测到设备ID: {line}")
                                    return True
        
        return False
    
    def get_screenshot(self, save_path):
        """获取设备屏幕截图
        
        Args:
            save_path (str): 截图保存路径
            
        Returns:
            bool: 截图是否成功
        """
        # 确保保存路径在pictures目录下
        import os
        from datetime import datetime
        
        # 创建pictures目录（如果不存在）
        pictures_dir = os.path.join(os.getcwd(), "pictures")
        if not os.path.exists(pictures_dir):
            os.makedirs(pictures_dir)
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(save_path)
        name, ext = os.path.splitext(filename)
        timestamped_filename = f"{name}_{timestamp}{ext}"
        timestamped_path = os.path.join(pictures_dir, timestamped_filename)
        
        # 更新保存路径为带时间戳的路径
        save_path = timestamped_path
        if self.command_type == "hdc":
            # 只保留鸿蒙官方推荐的截图命令 - 使用snapshot_display（经过测试可正常工作）
            screenshot_commands = [
                (f"shell snapshot_display -f /data/local/tmp/screenshot.jpeg", 
                 f"file recv /data/local/tmp/screenshot.jpeg {save_path}", 
                 f"shell rm /data/local/tmp/screenshot.jpeg")
            ]
            
            for cmd in screenshot_commands:
                success = False
                
                if isinstance(cmd, tuple):
                    # 处理需要多个步骤的命令序列
                    print(f"尝试命令序列: {cmd[0]}")
                    step_success = True
                    for step in cmd:
                        return_code, stdout, stderr = self.execute_command(step)
                        if return_code != 0:
                            print(f"  步骤失败: {step}")
                            print(f"  错误: {stderr}")
                            step_success = False
                            break
                    if step_success:
                        success = True
                else:
                    # 处理单个命令
                    print(f"尝试命令: {cmd}")
                    return_code, stdout, stderr = self.execute_command(cmd)
                    if return_code == 0:
                        success = True
                    else:
                        print(f"  命令失败")
                        print(f"  错误: {stderr}")
                
                # 检查文件是否真的存在且大小大于0
                if success and os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                    print(f"截图成功，保存到: {save_path}")
                    return True
            
            print(f"所有hdc截图命令都失败了")
            return False
        else:  # adb
            # 使用adb命令获取截图
            print("尝试adb截图命令序列")
            
            # 先截图到设备
            return_code, stdout, stderr = self.execute_command(f"shell screencap -p /sdcard/screenshot.png")
            if return_code != 0:
                print(f"  设备截图失败: {stderr}")
                return False
                
            # 从设备复制到本地
            return_code, stdout, stderr = self.execute_command(f"pull /sdcard/screenshot.png {save_path}")
            if return_code != 0:
                print(f"  本地保存失败: {stderr}")
                return False
                
            # 删除设备上的临时文件
            self.execute_command("shell rm /sdcard/screenshot.png")
            
            # 检查文件是否真的存在且大小大于0
            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                print(f"截图成功，保存到: {save_path}")
                return True
        
        print(f"截图失败")
        return False
    
    def tap(self, x, y):
        """点击设备屏幕上的指定位置
        
        Args:
            x (int): x坐标
            y (int): y坐标
            
        Returns:
            bool: 点击是否成功
        """
        # 使用用户指定的uinput命令格式：uinput -T -d x y -u x y
        return_code, stdout, stderr = self.execute_command(f"shell uinput -T -d {x} {y} -u {x} {y}")
        if return_code != 0:
            print(f"点击失败: {stderr}")
            return False
        print(f"点击位置: ({x}, {y})")
        return True
    
    def swipe(self, start_x, start_y, end_x, end_y, duration=None):
        """在设备屏幕上滑动
        
        Args:
            start_x (int): 起始x坐标
            start_y (int): 起始y坐标
            end_x (int): 结束x坐标
            end_y (int): 结束y坐标
            duration (int, optional): 滑动持续时间（毫秒）
            
        Returns:
            bool: 滑动是否成功
        """
        if duration:
            command = f"shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}"
        else:
            command = f"shell input swipe {start_x} {start_y} {end_x} {end_y}"
        
        return_code, stdout, stderr = self.execute_command(command)
        if return_code != 0:
            print(f"滑动失败: {stderr}")
            return False
        print(f"滑动: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
        return True
    
    def press_home(self):
        """按下设备的Home键
        
        Returns:
            bool: 操作是否成功
        """
        return_code, stdout, stderr = self.execute_command("shell input keyevent 3")
        if return_code != 0:
            print(f"按下Home键失败: {stderr}")
            return False
        print("按下Home键")
        return True
    
    def press_back(self):
        """按下设备的返回键
        
        Returns:
            bool: 操作是否成功
        """
        return_code, stdout, stderr = self.execute_command("shell input keyevent 4")
        if return_code != 0:
            print(f"按下返回键失败: {stderr}")
            return False
        print("按下返回键")
        return True
    
    def press_menu(self):
        """按下设备的菜单键
        
        Returns:
            bool: 操作是否成功
        """
        return_code, stdout, stderr = self.execute_command("shell input keyevent 82")
        if return_code != 0:
            print(f"按下菜单键失败: {stderr}")
            return False
        print("按下菜单键")
        return True
    
    def send_text(self, text):
        """向设备发送文本
        
        Args:
            text (str): 要发送的文本
            
        Returns:
            bool: 操作是否成功
        """
        # 替换特殊字符
        text = text.replace(" ", "%s").replace("\n", "%n")
        return_code, stdout, stderr = self.execute_command(f"shell input text {text}")
        if return_code != 0:
            print(f"发送文本失败: {stderr}")
            return False
        print(f"发送文本: {text}")
        return True
    
    def get_screen_size(self):
        """获取设备屏幕尺寸
        
        Returns:
            tuple: (宽度, 高度)，如果获取失败则返回None
        """
        return_code, stdout, stderr = self.execute_command("shell wm size")
        if return_code != 0:
            print(f"获取屏幕尺寸失败: {stderr}")
            return None
        
        # 解析输出，格式类似：Physical size: 1080x2340
        try:
            # 检查是否包含错误信息
            if "inaccessible" in stdout.lower() or "not found" in stdout.lower():
                print(f"解析屏幕尺寸失败: {stdout.strip()}")
                return None
                
            # 尝试多种可能的格式解析
            size_str = stdout.strip()
            
            # 格式1: Physical size: 1080x2340
            if ":" in size_str:
                size_str = size_str.split(":")[-1].strip()
            
            # 格式2: 1080x2340
            if "x" in size_str:
                width, height = map(int, size_str.split("x"))
                return width, height
            
            # 格式3: 1080 2340 (空格分隔)
            elif " " in size_str and all(part.isdigit() for part in size_str.split()):
                width, height = map(int, size_str.split())
                return width, height
            else:
                print(f"解析屏幕尺寸失败: 输出格式无法识别: {stdout}")
                return None
                
        except Exception as e:
            print(f"解析屏幕尺寸失败: {str(e)}")
            return None