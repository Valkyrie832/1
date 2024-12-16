import pyaudio
import wave
import os
import threading
import tkinter as tk
from vosk import Model, KaldiRecognizer
import json
import re  # 添加到文件开头的导入部分

class LocalVoiceRecognizer:
    def __init__(self):
        # 录音参数
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 5  # 每次录音5秒
        
        self.is_recording = False
        self._callback = None
        self._status_callback = None
        self._lock = threading.Lock()
        
        # 初始化语音识别模型
        try:
            # 检查多个可能的模型路径
            model_paths = [
                "model",                    # 当前目录
                ".venv/model",              # 相对于当前目录的虚拟环境
                os.path.join(os.path.dirname(__file__), ".venv/model"),  # 相对于脚本的虚拟环境
                os.path.join(os.path.dirname(__file__), "model"),        # 相对于脚本的model目录
                "../model",                 # 上级目录
            ]
            
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
                
            if not model_path:
                raise Exception(
                    "请先下载中文语音模型！\n"
                    "1. 访问 https://alphacephei.com/vosk/models\n"
                    "2. 下载 vosk-model-small-cn-0.22\n"
                    "3. 解压并将文件夹重命名为 model\n"
                    "4. 将 model 文件夹放在以下任一位置：\n"
                    "   - 程序根目录\n"
                    "   - .venv/model\n"
                    "   - 上级目录"
                )
            
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, self.RATE)
            
        except Exception as e:
            print(f"初始化语音识别模型失败: {str(e)}")
            self.model = None
            self.recognizer = None

    def start_recording(self, callback, status_callback=None):
        """开始录音"""
        if self.is_recording or not self.recognizer:
            return
            
        self.is_recording = True
        self._callback = callback
        self._status_callback = status_callback
        
        def record_thread():
            try:
                if self._status_callback:
                    self._status_callback("准备录音...")
                
                p = pyaudio.PyAudio()
                stream = p.open(format=self.FORMAT,
                              channels=self.CHANNELS,
                              rate=self.RATE,
                              input=True,
                              frames_per_buffer=self.CHUNK)
                
                if self._status_callback:
                    self._status_callback("开始录音...")
                
                frames = []
                # 持续录音直到 is_recording 被设置为 False
                while self.is_recording:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)
                
                if self._status_callback:
                    self._status_callback("录音结束，正在识别...")
                
                stream.stop_stream()
                stream.close()
                p.terminate()
                
                # 保存录音文件
                temp_wav = "temp_recording.wav"
                wf = wave.open(temp_wav, 'wb')
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(p.get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(frames))
                wf.close()
                
                # 本地识别音频
                self._recognize_audio(temp_wav)
                
                # 删除临时文件
                try:
                    os.remove(temp_wav)
                except:
                    pass
                    
            finally:
                self.is_recording = False
                if self._status_callback:
                    self._status_callback("")
        
        threading.Thread(target=record_thread, daemon=True).start()

    def _convert_chinese_numbers(self, text):
        """将中文数字转换为阿拉伯数字"""
        # 中文数字映射
        cn_nums = {
            '零': '0', '一': '1', '二': '2', '两': '2', '三': '3', '四': '4',
            '五': '5', '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'
        }
        
        # 处理"十"开头的数字
        text = text.replace('十一', '11')
        text = text.replace('十二', '12')
        text = text.replace('十三', '13')
        text = text.replace('十四', '14')
        text = text.replace('十五', '15')
        text = text.replace('十六', '16')
        text = text.replace('十七', '17')
        text = text.replace('十八', '18')
        text = text.replace('十九', '19')
        text = text.replace('二十', '20')
        text = text.replace('三十', '30')
        text = text.replace('四十', '40')
        text = text.replace('五十', '50')
        
        # 替换其他中文数字
        for cn, num in cn_nums.items():
            text = text.replace(cn, num)
        
        return text

    def _recognize_audio(self, audio_file):
        """使用vosk进行本地语音识别"""
        try:
            # 重置识别器
            self.recognizer.Reset()
            
            # 读取音频文件
            wf = wave.open(audio_file, "rb")
            
            # 识别音频
            result_text = []
            while True:
                data = wf.readframes(self.CHUNK)
                if len(data) == 0:
                    break
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    if result.get("text"):
                        result_text.append(result.get("text"))
            
            # 获取最后的结果
            final_result = json.loads(self.recognizer.FinalResult())
            if final_result.get("text"):
                result_text.append(final_result.get("text"))
            
            # 将所有结果连接并处理空格
            final_text = "".join(result_text)
            # 使用正则表达式替换多个空格为单个空格，并去除首尾空格
            final_text = re.sub(r'\s+', '', final_text).strip()
            
            # 转换中文数字为阿拉伯数字
            final_text = self._convert_chinese_numbers(final_text)
            
            if final_text and self._callback:
                try:
                    self._callback(final_text)
                    if self._status_callback:
                        self._status_callback("识别成功")
                except tk.TclError:
                    pass
                    
        except Exception as e:
            if self._status_callback:
                self._status_callback(f"识别失败: {str(e)}")
            if self._callback:
                try:
                    self._callback(f"错误：{str(e)}")
                except tk.TclError:
                    pass

    def stop_recording(self):
        """停止录音"""
        with self._lock:
            self.is_recording = False
            # 移除这两行，让回调函数在识别完成后再清除
            # self._callback = None
            # self._status_callback = None