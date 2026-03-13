# telegram_bot.py
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import os
from config import Config

# 配置
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"  # 替换为你的Bot Token
API_BASE = "http://localhost:8000"  # 本地API地址

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理/start命令"""
    await update.message.reply_text(
        "👋 欢迎使用 IntelliKnow KMS Bot!\n\n"
        "发送你的问题，我会从知识库中查找答案。\n"
        "例如：\n"
        "- 年假有多少天？\n"
        "- 报销流程是什么？\n"
        "- 合同有效期多久？"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理/help命令"""
    await update.message.reply_text(
        "🤖 使用帮助：\n"
        "直接发送问题即可查询知识库\n"
        "/start - 开始使用\n"
        "/help - 显示帮助\n"
        "/status - 查看系统状态"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理/status命令"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            await update.message.reply_text(
                f"✅ 系统正常运行\n"
                f"知识块数量: {data['kb_stats'].get('total_chunks', 0)}"
            )
        else:
            await update.message.reply_text("❌ API服务异常")
    except:
        await update.message.reply_text("❌ 无法连接到API服务")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户消息"""
    user_query = update.message.text
    user = update.effective_user

    print(f"收到来自 {user.first_name} 的消息: {user_query}")

    # 发送"正在输入"状态
    await update.message.chat.send_action(action="typing")

    try:
        # 调用KMS API
        response = requests.post(
            f"{API_BASE}/query",
            json={"query": user_query},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()

            # 格式化回复
            intent = result['intent']['intent']
            confidence = result['intent']['confidence']
            answer = result['response']

            reply = f"*分类: {intent}* (置信度: {confidence:.2f})\n\n{answer}"

            # Telegram支持Markdown
            await update.message.reply_text(reply, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ 查询失败: HTTP {response.status_code}")

    except Exception as e:
        await update.message.reply_text(f"❌ 发生错误: {str(e)}")

def main():
    """启动Bot"""
    if TELEGRAM_TOKEN == "YOUR_BOT_TOKEN":
        print("❌ 请先设置TELEGRAM_TOKEN")
        return

    # 创建Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # 注册处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 启动Bot
    print("🤖 Telegram Bot 启动中...")