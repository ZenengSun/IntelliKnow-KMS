# # feishu_ws.py
# import os
# import json
# import asyncio
# import requests
# from lark_oapi import ws, LogLevel, EventDispatcherHandler, JSON
# from lark_oapi.api.im.v1 import *
# from dotenv import load_dotenv

# load_dotenv()

# # 飞书配置（从.env读取）
# APP_ID = os.getenv("FEISHU_APP_ID")
# APP_SECRET = os.getenv("FEISHU_APP_SECRET")
# KMS_API_URL = "http://localhost:8000/query"

# class FeishuWebSocketClient:
#     def __init__(self):
#         self.app_id = APP_ID
#         self.app_secret = APP_SECRET
#         # 初始化事件处理器
#         self.event_handler = EventDispatcherHandler.builder("", "") \
#             .register_p2_im_message_receive_v1(self.handle_message) \
#             .build()
#         self.client = None

#     async def query_kms(self, user_message: str) -> str:
#         """调用 KMS API 获取回答"""
#         try:
#             response = requests.post(
#                 KMS_API_URL,
#                 json={"query": user_message, "platform": "feishu"},
#                 timeout=10
#             )
#             if response.status_code == 200:
#                 result = response.json()
#                 intent = result['intent']['intent']
#                 confidence = result['intent']['confidence']
#                 answer = result['response']
#                 return f"**{intent}** (置信度: {confidence:.2f})\n\n{answer}"
#             else:
#                 return f"❌ 服务暂时不可用 (错误码: {response.status_code})"
#         except Exception as e:
#             print(f"调用KMS失败: {e}")
#             return "❌ 无法连接到知识库服务"

#     def handle_message(self, data: P2ImMessageReceiveV1) -> None:
#         """处理收到的飞书消息"""
#         print("=" * 50)
#         print("🔥 收到消息事件！")
        
#         try:
#             # 正确访问消息内容
#             event = data.event
#             message = event.message
            
#             message_id = message.message_id
#             chat_id = message.chat_id
#             content_str = message.content
            
#             print(f"消息ID: {message_id}")
#             print(f"聊天ID: {chat_id}")
#             print(f"消息类型: {message.message_type}")
#             print(f"消息内容原始: {content_str}")
            
#             # 解析 JSON 内容
#             import json
#             content = json.loads(content_str)
#             user_message = content.get("text", "")
#             print(f"用户消息: {user_message}")
            
#             if not user_message:
#                 print("⚠️ 消息内容为空")
#                 return
            
#             # 异步回复
#             async def reply():
#                 print("调用KMS API...")
#                 reply_text = await self.query_kms(user_message)
#                 print(f"KMS返回: {reply_text}")
                
#                 # 获取 tenant access token
#                 print("获取tenant access token...")
#                 token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
#                 token_data = {"app_id": self.app_id, "app_secret": self.app_secret}
#                 token_resp = requests.post(token_url, json=token_data)
#                 print(f"Token响应状态: {token_resp.status_code}")
                
#                 if token_resp.status_code == 200:
#                     token = token_resp.json().get("tenant_access_token")
#                     print(f"获取到token: {token[:20]}...")
                    
#                     # 发送回复
#                     msg_url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
#                     headers = {
#                         "Authorization": f"Bearer {token}",
#                         "Content-Type": "application/json"
#                     }
#                     msg_data = {
#                         "content": json.dumps({"text": reply_text}),
#                         "msg_type": "text"
#                     }
#                     print(f"发送回复到: {msg_url}")
#                     msg_resp = requests.post(msg_url, headers=headers, json=msg_data)
#                     print(f"回复响应状态: {msg_resp.status_code}")
#                     if msg_resp.status_code != 200:
#                         print(f"回复失败: {msg_resp.text}")
#                     else:
#                         print("✅ 回复成功！")
#                 else:
#                     print(f"获取token失败: {token_resp.text}")
            
#             # 获取当前事件循环
#             loop = asyncio.get_running_loop()
#             # 创建任务
#             loop.create_task(reply())
            
#         except Exception as e:
#             print(f"处理消息时出错: {e}")
#             import traceback
#             traceback.print_exc()

#     def start(self):
#         """启动长连接客户端"""
#         print(f"🚀 启动飞书长连接客户端...")
#         print(f"   App ID: {self.app_id}")
        
#         self.client = ws.Client(
#             self.app_id,
#             self.app_secret,
#             event_handler=self.event_handler,
#             log_level=LogLevel.INFO
#         )
#         print("✅ 长连接客户端已启动，等待飞书事件...")
#         self.client.start()

# if __name__ == "__main__":
#     client = FeishuWebSocketClient()
#     client.start()

# feishu_ws.py
import requests
import json
import time
import socket
from lark_oapi import EventDispatcherHandler, ws, JSON, im, LogLevel
from dotenv import load_dotenv
import os

load_dotenv()

# ===== 自动获取本机 IP =====
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()
KMS_API_URL = f"http://{LOCAL_IP}:8000/query"
print("=" * 50)
print("🚀 飞书长连接客户端启动")
print(f"📡 本机IP: {LOCAL_IP}")
print(f"📡 KMS地址: {KMS_API_URL}")
print("=" * 50)

# 飞书配置
APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")

class FeishuApi:
    '''FeishuApi类用于处理与飞书API的交互'''
    TOKEN_URL = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    REPLY_MESSAGE_URL_TEMPLATE = 'https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply'
    HEADERS = {'Content-Type': 'application/json; charset=utf-8'}

    def __init__(self):
        self.session = requests.Session()
        self.token = self.get_token()

    def get_token(self):
        '''获取飞书API的访问令牌'''
        data = {'app_id': APP_ID, 'app_secret': APP_SECRET}
        response = self.session.post(self.TOKEN_URL, headers=self.HEADERS, json=data)
        response.raise_for_status()
        return response.json().get('tenant_access_token')

    def reply_message(self, message_id, message):
        '''回复飞书消息'''
        url = self.REPLY_MESSAGE_URL_TEMPLATE.format(message_id=message_id)
        data = {"content": json.dumps({"text": message}), "msg_type": "text"}
        headers = {'Authorization': 'Bearer ' + self.token, **self.HEADERS}
        response = self.session.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

def handle_p2_im_message(data: im.v1.P2ImMessageReceiveV1):
    '''处理接收到的消息（官方推荐方式）'''
    print("🔥 收到消息事件！")
    
    # 关键步骤：先序列化为字典再操作
    data_dict = json.loads(JSON.marshal(data))
    
    # 提取消息信息
    message_id = data_dict["event"]["message"]["message_id"]
    content_str = data_dict["event"]["message"]["content"]
    
    # 解析消息内容
    try:
        content = json.loads(content_str)
        user_message = content.get("text", "")
        print(f"用户消息: {user_message}")
        
        if not user_message:
            return
            
        # 调用KMS API
        print(f"调用KMS: {KMS_API_URL}")
        try:
            kms_resp = requests.post(
                KMS_API_URL,
                json={"query": user_message, "platform": "feishu"},
                timeout=15  # 增加超时时间
            )
            
            if kms_resp.status_code == 200:
                result = kms_resp.json()
                intent = result['intent']['intent']
                confidence = result['intent']['confidence']
                answer = result['response']
                
                reply_text = f"**{intent}** (置信度: {confidence:.2f})\n\n{answer}"
                
                # 添加来源
                sources = result.get('sources', [])
                if sources:
                    filenames = list(set([s['filename'] for s in sources]))
                    if filenames:
                        reply_text += f"\n\n📚 来源: {', '.join(filenames[:2])}"
            else:
                reply_text = f"❌ KMS返回错误: {kms_resp.status_code}"
                
        except requests.exceptions.Timeout:
            print(f"❌ KMS超时 (15秒)")
            reply_text = f"❌ KMS服务响应超时，请稍后再试"
        except requests.exceptions.ConnectionError as e:
            print(f"❌ KMS连接错误: {e}")
            reply_text = f"❌ 无法连接到KMS服务"
        except Exception as e:
            print(f"❌ KMS调用异常: {e}")
            reply_text = f"❌ KMS处理异常: {str(e)[:50]}"
            
        # 回复消息
        feishu = FeishuApi()
        feishu.reply_message(message_id=message_id, message=reply_text)
        print("✅ 回复成功")
        
    except Exception as e:
        print(f"❌ 处理异常: {e}")
        import traceback
        traceback.print_exc()

def main():
    '''启动飞书长连接 WebSocket客户端'''
    print("🚀 启动飞书长连接客户端...")
    
    # 初始化事件处理器（官方推荐方式）
    event_handler = EventDispatcherHandler.builder("", "") \
        .register_p2_im_message_receive_v1(handle_p2_im_message) \
        .build()

    # 创建WebSocket客户端
    cli = ws.Client(
        APP_ID, 
        APP_SECRET, 
        event_handler=event_handler, 
        log_level=LogLevel.INFO
    )
    
    print("✅ 长连接客户端已启动，等待飞书事件...")
    cli.start()

if __name__ == "__main__":
    main()