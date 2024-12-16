from xf_voice import LocalVoiceRecognizer
import tkinter as tk
from tkinter import messagebox
import pyaudio
import platform
import subprocess
import os

class VoiceInput:
    def __init__(self):
        self.recognizer = LocalVoiceRecognizer()
        self.is_listening = False
        self._callback = None
        self._status_callback = None
        
    def start_listening(self, callback, status_callback=None, language='zh-CN'):
        """开始语音输入"""
        if self.is_listening:
            return
            
        self.is_listening = True
        self._callback = callback
        self._status_callback = status_callback
        
        self.recognizer.start_recording(callback, status_callback)
        
    def stop_listening(self):
        """停止语音输入"""
        self.is_listening = False
        self.recognizer.stop_recording()
        self._callback = None
        self._status_callback = None

    def check_microphone(self):
        """检查麦克风权限和可用性"""
        try:
            # 初始化 PyAudio
            p = pyaudio.PyAudio()
            
            # 获取默认输入设备信息
            device_info = p.get_default_input_device_info()
            
            # 测试打开麦克风
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            # 如果能打开流，说明麦克风可用
            stream.close()
            p.terminate()
            
        except Exception as e:
            # 根据操作系统提供不同的指导
            os_type = platform.system()
            if os_type == "Windows":
                msg = (
                    "无法访问麦克风。请按以下步骤检查：\n\n"
                    "1. 右键点击开始菜单 -> 设置\n"
                    "2. 点击'隐私和安全性' -> '麦克风'\n"
                    "3. 确保'麦克风访问'已开启\n"
                    "4. 在'允许应用访问麦克风'下，确保Python/应用程序已获得权限\n\n"
                    "是否现在打开麦克风设置？"
                )
                if messagebox.askyesno("麦克风权限", msg):
                    subprocess.run(['start', 'ms-settings:privacy-microphone'], shell=True)
                    
            elif os_type == "Darwin":  # macOS
                msg = (
                    "无法访问麦克风。请按以下步骤检查：\n\n"
                    "1. 点击苹果菜单 -> 系统偏好设置\n"
                    "2. 点击'安全性与隐私' -> '麦克风'\n"
                    "3. 确保应用程序已获得麦克风访问权限\n\n"
                    "是否现在打开系统偏好设置？"
                )
                if messagebox.askyesno("麦克风权限", msg):
                    subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone'])
                    
            elif os_type == "Linux":
                msg = (
                    "无法访问麦克风。请检查：\n\n"
                    "1. 确保麦克风已正确连接\n"
                    "2. 检查系统音频设置\n"
                    "3. 确保用户属于audio组\n"
                    "4. 检查PulseAudio配置"
                )
                messagebox.showerror("麦克风权限", msg)
                
            raise Exception(f"麦克风初始化失败: {str(e)}")