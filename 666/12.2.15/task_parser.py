import json
import websocket
import datetime
import hmac
import base64
import hashlib
from urllib.parse import urlencode
from datetime import datetime, timedelta
import re
import jieba
import jieba.posseg as pseg

class TaskParser:
    def __init__(self):
        # API 凭证
        self.app_id = "e581a35e"  # 替换为您的讯飞 APP ID
        self.api_key = "9fe697f128e5eed4398708e4ed4353dd"  # 替换为您的讯飞 API Key
        self.api_secret = "MGQ4MjM2OGUyNTFmYmM5NzNkNjMyYWQy"  # 替换为您的讯飞 API Secret
        self.spark_url = "wss://spark-api.xf-yun.com/v1.1/chat"  # 讯飞星火大模型 API 地址

        # 添加自定义词典
        self.time_patterns = {
            'date': r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?)',
            'time': r'(\d{1,2}[点时:：]\d{1,2}[分]?(?:\d{1,2}秒?)?)',
            'relative': r'(今天|明天|后天|下周[一二三四五六日]?|下个?月|今年|明年)(?:[早上午中下晚]午)?(?:\d{1,2}[点时])?',
            'fuzzy': r'([早上午中下晚]午\d{1,2}[点时])',
            'special': r'(月底|月初|周末|年底|年初|春节|元旦|五一|十一)'
        }
        
        self.priority_keywords = {
            3: ['紧急', '重要', '立即', '马上', 'urgent', 'asap', '优先级高', '火急',
                '限时', '截止', '必须', '赶快', '尽快', '越快越好'],
            2: ['适中', '普通', '一般', 'normal', '优先级中', '常规', '正常'],
            1: ['低优先级', '不急', 'low', '优先级低', '随时', '闲暇', '有空']
        }
        
        self.category_keywords = {
            '工作学习': ['工作', '学习', '会议', '项目', '作业', '考试', '报告', 
                     '培训', '课程', '研究', '实验', '论文', '汇报', '开会',
                     '面试', '述职', '答辩', '讲座', '备课'],
            '家庭生活': ['家庭', '生活', '购物', '打扫', '做饭', '洗衣', '收拾',
                     '整理', '维修', '装修', '搬家', '家具', '家电', '宠物'],
            '社交人际': ['社交', '朋友', '聚会', '约会', '拜访', '聚餐', '探望',
                     '联系', '沟通', '交流', '聊天', '团建', '派对'],
            '健康养生': ['健康', '运动', '锻炼', '吃药', '看医生', '体检', '就医',
                     '复查', '保养', '按摩', '瑜伽', '跑步', '游泳'],
            '财务理财': ['财务', '理���', '付款', '缴费', '报销', '投资', '记账',
                     '工资', '账单', '保险', '贷款', '还款', '储蓄'],
            '其他': []
        }

    def _generate_url(self):
        # 生成鉴权url
        # 使用 UTC 时间但不依赖 timezone
        now = datetime.utcnow()
        date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
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

    def parse_text(self, text):
        """分析文本并提取任务信息"""
        prompt = f"""
        作为一个任务分析助手，请分析以下文本并提取关键信息。
        当前时间是：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        请严格按照以下规则：

        1. 标题提取规则：
           - 提取最关键的动作/事件作为标题
           - 标题应简洁明了，不超过15字
           - 如果是会议/约会，应包含"参加"或"出席"等动词
        
        2. 日期时间处理规则（非常重要）：
           - 所有时间必须基于当前时间计算
           - "明天"表示当前日期+1天
           - "后天"表示当前日期+2天
           - "下周"表示当前日期+7天
           - 时间必须使用24小时制
           - 日期时间格式必须是：YYYY-MM-DD HH:MM:SS
        
        3. 分类规则：
           - 工作学习：会议、项目、学习、考试、作业等
           - 社交人际：聚会、约会、拜访、会友等
           - 家庭生活：购物、打扫、做饭、家庭活动等
           - 健康养生：运动、就医、体检、吃药等
           - 财务理财：缴费、理财、报销等
           - 其他：以上未包含的类别
        
        4. 优先级判断规则（1-3，3最高）：
           - 3级：包含"紧急"、"立即"、"马上"等词
           - 2级：通任务，无特殊时间要求
           - 1级：非紧急、长期性任务

        输入文本：{text}

        请以JSON格式返回，必须包含以下字段：
        {{
            "title": "任务标题",
            "description": "原始描述文本",
            "due_date": "YYYY-MM-DD HH:MM:SS",
            "category": "分类名称",
            "priority": 优先级数字
        }}
        """

        try:
            url = self._generate_url()
            print(f"正在连接API: {url}")
            
            ws = websocket.create_connection(url)
            request_data = {
                "header": {
                    "app_id": self.app_id
                },
                "parameter": {
                    "chat": {
                        "domain": "lite",
                        "temperature": 0.5,
                        "max_tokens": 4096
                    }
                },
                "payload": {
                    "message": {
                        "text": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                }
            }
            
            print("发送请求数据...")
            ws.send(json.dumps(request_data))
            
            response_text = ""
            while True:
                try:
                    print("等待响应...")
                    result = ws.recv()
                    response = json.loads(result)
                    print(f"收到响应: {response}")
                    
                    if 'header' in response:
                        if response['header'].get('code') != 0:
                            error_msg = response['header'].get('message', '未知错误')
                            print(f"API错误: {error_msg}")
                            ws.close()
                            return {}
                        
                        if response['header'].get('status') == 2:
                            ws.close()
                            break
                            
                    if 'payload' in response and 'choices' in response['payload']:
                        current_text = response['payload']['choices']['text'][0]['content']
                        response_text += current_text
                        print(f"积响应文本: {response_text}")
                        
                except websocket.WebSocketConnectionClosedException:
                    print("WebSocket连接已关闭")
                    break
                except Exception as e:
                    print(f"处理响应时出错: {str(e)}")
                    break
            
            # 清理响应文本，移除可能的 Markdown 标记
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text.split('\n', 1)[1]  # 移除第一行
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text.rsplit('\n', 1)[0]  # 移除最后一行
            if cleaned_text.startswith('json'):
                cleaned_text = cleaned_text.split('\n', 1)[1]  # 移除 json 标记行
            
            # 先移除所有换行符和多余空格，以便于检查属性
            normalized_text = ' '.join(line.strip() for line in cleaned_text.splitlines())
            
            # 确保 JSON ���式完整
            if normalized_text.endswith(',}'):
                normalized_text = normalized_text[:-2] + '}'
            elif not normalized_text.endswith('}'):
                normalized_text += '}'
            
            # 确保所有属性都在
            expected_keys = ['"title"', '"description"', '"due_date"', '"category"']
            for key in expected_keys:
                if key not in normalized_text:
                    print(f"缺少必要的属性: {key}")
                    return {}
            
            print(f"清理后的文本: {normalized_text}")
            
            try:
                result = json.loads(normalized_text)
                # 处理日期时间
                if result.get('due_date'):
                    now = datetime.now()
                    if '明天' in text:
                        due_date = now + timedelta(days=1)
                        due_date = due_date.replace(hour=21, minute=30, second=0)
                        result['due_date'] = due_date.strftime('%Y-%m-%d %H:%M:%S')
                    elif '后天' in text:
                        due_date = now + timedelta(days=2)
                        due_date = due_date.replace(hour=21, minute=30, second=0)
                        result['due_date'] = due_date.strftime('%Y-%m-%d %H:%M:%S')
                    elif '下周' in text:
                        due_date = now + timedelta(days=7)
                        due_date = due_date.replace(hour=21, minute=30, second=0)
                        result['due_date'] = due_date.strftime('%Y-%m-%d %H:%M:%S')

                print(f"解析后的结果: {result}")
                return result
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {str(e)}")
                # 尝试进一步清理文本
                try:
                    # 确保属性之间有逗号分隔
                    normalized_text = normalized_text.replace('} {', '}, {')
                    # 确保最后一个属性后没有多余的逗号
                    if normalized_text.endswith(',}'):
                        normalized_text = normalized_text[:-2] + '}'
                    result = json.loads(normalized_text)
                    print(f"二次解析成: {result}")
                    return result
                except json.JSONDecodeError as e:
                    print(f"二次解析失败: {str(e)}")
                    return {}
                
        except Exception as e:
            print(f"API调用错误: {str(e)}")
            return {} 

    def _validate_and_clean_result(self, result):
        """验证和清理解析结果"""
        cleaned_result = {}
        
        # 验证标题
        if result.get('title'):
            cleaned_result['title'] = result['title'].strip()[:30]  # 限制标题长���
        
        # 验证描述
        if result.get('description'):
            cleaned_result['description'] = result['description'].strip()
        
        # 验证日期时间
        if result.get('due_date'):
            try:
                # 尝试解析日期时间
                dt = datetime.strptime(result['due_date'], '%Y-%m-%d %H:%M:%S')
                # 确保日期不早于当前时间
                if dt < datetime.now():
                    dt = datetime.now()
                cleaned_result['due_date'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                # 如果日期格式无效，使用当前时间
                cleaned_result['due_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 验证分类
        valid_categories = ['工作学习', '社交人际', '家庭生活', '健康养生', '财务理财', '其他']
        if result.get('category') in valid_categories:
            cleaned_result['category'] = result['category']
        else:
            cleaned_result['category'] = '其他'
        
        # 验证优先级
        try:
            priority = int(result.get('priority', 2))
            cleaned_result['priority'] = max(1, min(3, priority))  # 确保在1-3之间
        except (ValueError, TypeError):
            cleaned_result['priority'] = 2  # 默认优先级
        
        return cleaned_result 

    def _enhance_result(self, result, text):
        """增强解析结果"""
        # 根据上下文推断优先级
        if not result.get('priority'):
            # 检查时间紧迫性
            if result.get('due_date'):
                due_date = datetime.strptime(result['due_date'], '%Y-%m-%d %H:%M:%S')
                time_diff = due_date - datetime.now()
                if time_diff.days < 1:  # 24小时内
                    result['priority'] = 3
                elif time_diff.days < 3:  # 3天内
                    result['priority'] = 2
                else:
                    result['priority'] = 1

        # 根据描述长度和复杂度推断优先级
        if len(text) > 100:  # 较长的描述可能是重要任务
            result['priority'] = max(result.get('priority', 1), 2)

        # 根据关键词组合提升优先级
        important_combinations = [
            ('会议', '总经理'),
            ('项目', '截止'),
            ('考试', '明天'),
            ('报告', '紧急')
        ]
        for kw1, kw2 in important_combinations:
            if kw1 in text and kw2 in text:
                result['priority'] = 3
                break

        return result