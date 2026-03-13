# orchestrator/classifier.py
import json
from typing import Dict
from config import Config

class IntentClassifier:
    """基于Qwen的意图分类器"""

    def __init__(self):
        self.client = Config.get_qwen_client()
        self.model = Config.QWEN_CHAT_MODEL
        self.intents = Config.DEFAULT_INTENTS
        self.threshold = Config.CONFIDENCE_THRESHOLD
        print(f"🔧 初始化意图分类器")
        print(f"   模型: {self.model}")
        print(f"   意图: {', '.join(self.intents)}")
        print(f"   阈值: {self.threshold}")

    def classify(self, query: str) -> Dict:
        """
        分类查询意图
        返回: {"intent": str, "confidence": float, "reason": str}
        """
        prompt = f"""你是一个专业的意图分类器。请将用户的查询分类到以下类别之一：{', '.join(self.intents)}

分类规则：
- HR: 人力资源相关问题（请假、考勤、薪酬、培训、招聘、绩效、员工关系）
- Legal: 法律相关问题（合同、保密协议、知识产权、合规、条款）
- Finance: 财务相关问题（报销、发票、采购、预算、差旅标准、付款）
- General: 以上类别都不符合的通用问题

请以JSON格式返回结果，包含三个字段：
- intent: 分类结果 (HR/Legal/Finance/General)
- confidence: 置信度 (0-1之间的小数)
- reason: 分类原因简述

用户查询: {query}"""

        try:
            print(f"   🤖 调用Qwen分类...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个精确的意图分类助手，只返回JSON格式。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            print(f"   原始结果: {result}")

            # 置信度低于阈值时归为General
            if result["confidence"] < self.threshold:
                old_intent = result["intent"]
                result["intent"] = "General"
                result["reason"] = f"置信度{result['confidence']}低于阈值{self.threshold}，从{old_intent}改为General"
                print(f"   低于阈值，改为General")

            return result

        except Exception as e:
            print(f"   ⚠️ 分类失败: {e}")
            return self._fallback_classify(query)

    def _fallback_classify(self, query: str) -> Dict:
        """降级方案：关键词匹配"""
        q = query.lower()
        hr_keywords = ["年假", "病假", "产假", "加班", "工资", "薪酬", "培训", "招聘", "考勤", "请假", "hr"]
        legal_keywords = ["合同", "保密", "协议", "法律", "合规", "条款", "违约", "起诉", "仲裁", "法务"]
        finance_keywords = ["报销", "发票", "采购", "预算", "财务", "差旅", "住宿", "补贴", "付款", "费用"]

        scores = {
            "HR": sum(1 for k in hr_keywords if k in q),
            "Legal": sum(1 for k in legal_keywords if k in q),
            "Finance": sum(1 for k in finance_keywords if k in q)
        }

        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]

        if max_score == 0:
            return {"intent": "General", "confidence": 0.5, "reason": "无关键词匹配"}

        total = sum(scores.values())
        confidence = max_score / total if total > 0 else 0.5

        return {
            "intent": max_intent,
            "confidence": min(confidence, 0.6),
            "reason": "关键词匹配（降级方案）"
        }