import json
import websocket
import datetime
import hmac
import base64
import hashlib
import time
from urllib.parse import urlencode
import json
from database import fetch_query

class AIAdvisor:
    def __init__(self):
        # 科大讯飞 Spark API 配置
        self.app_id = "e581a35e"
        self.api_key = "9fe697f128e5eed4398708e4ed4353dd" 
        self.api_secret = "MGQ4MjM2OGUyNTFmYmM5NzNkNjMyYWQy"
        # Spark Lite的URL
        self.spark_url = "wss://spark-api.xf-yun.com/v1.1/chat"

    def _generate_url(self):
        # 生成鉴权url
        now = datetime.datetime.now(datetime.timezone.utc)
        date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # 修改为v1.1的正确路径
        signature_origin = f"host: spark-api.xf-yun.com\ndate: {date}\nGET /v1.1/chat HTTP/1.1"
        
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), 
                               signature_origin.encode('utf-8'),
                               digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode()
        
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode()
        
        params = {
            "authorization": authorization,
            "date": date,
            "host": "spark-api.xf-yun.com"
        }
        return self.spark_url + '?' + urlencode(params)

    def get_task_analysis(self):
        """分析待办事项并生成建议"""
        # 获取所有未删除的任务
        query = """
        SELECT title, description, priority, done, due_date, category 
        FROM todos 
        WHERE is_deleted = 0
        """
        tasks = fetch_query(query)
        
        # 格式化任务数据
        task_data = []
        for task in tasks:
            task_data.append({
                "title": task[0],
                "description": task[1],
                "priority": task[2],
                "status": "完成" if task[3] else "未完成",
                "due_date": task[4],
                "category": task[5]
            })

        # 构建提示语
        prompt = f"""
        作为一个任务管理专家，请分析以下待办事项列表并提供专业的建议：
        {json.dumps(task_data, ensure_ascii=False, indent=2)}
        
        请从以下几个方面提供建议：
        1. 任务优先级安排是否合理
        2. 时间管理建
        3. 任务分类分布分析
        4. 效率提升建议
        """

        try:
            # 调用讯飞星火API获取建议
            ws = websocket.create_connection(self._generate_url())
            ws.send(json.dumps({
                "header": {
                    "app_id": self.app_id
                },
                "parameter": {
                    "chat": {
                        "domain": "lite",    # Lite版本使用lite域名
                        "temperature": 0.5,
                        "max_tokens": 4096    # Lite版本最大4096
                    }
                },
                "payload": {
                    "message": {
                        "text": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                }
            }))
            
            # 修改响应处理逻辑
            response_text = ""
            while True:
                try:
                    result = ws.recv()
                    response = json.loads(result)
                    
                    if 'header' in response:
                        if response['header'].get('code') != 0:
                            ws.close()
                            return f"API调用失败: {response['header'].get('message', '未知错误')}"
                        
                        if response['header'].get('status') == 2:  # 所有数据接收完毕
                            ws.close()
                            break
                            
                    if 'payload' in response and 'choices' in response['payload']:
                        response_text += response['payload']['choices']['text'][0]['content']
                        
                except websocket.WebSocketConnectionClosedException:
                    break
                
            return response_text if response_text else "未获取到有效回复"
            
        except Exception as e:
            return f"获取AI建议失败: {str(e)}\n请检查网络连接或API配置。" 