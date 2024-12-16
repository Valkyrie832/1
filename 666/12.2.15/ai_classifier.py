# ai_classifier.py
import jieba

class TaskClassifier:
    def __init__(self):
        # 分类关键词字典（使用动词为主）
        self.category_keywords = {
            "工作学习": ["学习", "复习", "备考", "写作", "编程", "开发", "研究", "设计", "规划", 
                     "汇报", "开会", "培训", "教学", "记笔记", "做实验", "写报告", "写论文",
                     "study", "review", "write", "code", "develop", "research", "design", 
                     "plan", "report", "teach", "experiment"],
            
            "家庭生活": ["打扫", "收拾", "整理", "购物", "做饭", "洗衣", "修理", "装修", "布置", 
                     "采购", "清洁", "烹饪", "照顾", "浇花", "遛狗",
                     "clean", "organize", "shop", "cook", "wash", "repair", "decorate", 
                     "maintain", "care"],
            
            "社交人际": ["约见", "拜访", "聚会", "联系", "沟通", "交流", "探望", "会面", "聚餐", 
                     "商谈", "协商", "讨论", "组织", "参加",
                     "meet", "visit", "contact", "communicate", "discuss", "organize", 
                     "attend", "gather", "chat"],
            
            "健康养生": ["运动", "锻炼", "跑步", "游泳", "健身", "吃药", "休息", "睡觉", "就医", 
                     "检查", "治疗", "康复", "调理", "养生",
                     "exercise", "run", "swim", "workout", "rest", "sleep", "treat", 
                     "recover", "heal", "medicate"],
            
            "财务理财": ["理财", "投资", "记账", "报销", "缴费", "存钱", "取钱", "转账", "还款", 
                     "记录", "统计", "分析", "规划",
                     "invest", "pay", "save", "withdraw", "transfer", "repay", "record", 
                     "analyze", "budget", "calculate"],
        }

        # 优先级关键词字典（更新为更多动词相关表述）
        self.priority_keywords = {
            3: ["立即", "马上", "赶快", "急需", "必须", "抓紧", "加急", "紧急", "限时", "截止",
                "immediately", "urgent", "must", "asap", "deadline", "rush", "critical"],
            
            2: ["尽快", "稍急", "需要", "准备", "安排", "计划", "处理", "完成",
                "soon", "need", "prepare", "arrange", "plan", "handle", "complete"],
            
            1: ["随时", "常规", "日常", "定期", "例行", "一般", "普通",
                "regular", "routine", "normal", "common", "usual", "general"]
        }

    def classify_task(self, title, description):
        """根据标题和描述自动分类任务"""
        text = f"{title} {description}"
        words = jieba.lcut(text)
        
        # 计算每个分类的匹配度
        category_scores = {category: 0 for category in self.category_keywords}
        for word in words:
            for category, keywords in self.category_keywords.items():
                if word in keywords:
                    category_scores[category] += 1

        # 选择得分最高的分类
        if max(category_scores.values()) > 0:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        return "其他"

    def determine_priority(self, title, description):
        """根据标题和描述自动判断优先级"""
        text = f"{title} {description}"
        words = jieba.lcut(text)
        
        # 计算每个优先级的匹配度
        for word in words:
            for priority, keywords in self.priority_keywords.items():
                if word in keywords:
                    return priority
        return 1  # 默认优先级
    
    # 确保类可以被正确导出
if __name__ == "__main__":
    classifier = TaskClassifier()