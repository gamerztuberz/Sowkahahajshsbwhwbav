import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 配置 (需要修改!)
BOT_TOKEN = "7582219841:AAHTu6cnKByYNTfQNux2q8RwtIiK29jDfs8"  # 从 @BotFather 获取
OWNER_ID = 7688309426  # 你的Telegram用户ID (从 @userinfobot 获取)

# 对话状态
GET_MESSAGE, GET_GROUP_ID = range(2)

def is_owner(update: Update) -> bool:
    """检查用户是否是所有者"""
    return update.effective_user.id == OWNER_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """发送欢迎消息(仅限所有者)"""
    if is_owner(update):
        await update.message.reply_text(
            '👑 所有者命令:\n'
            '/broadcast - 向群组发送广播消息\n'
            '此机器人仅响应您的命令。'
        )
    else:
        await update.message.reply_text("⛔ 检测到您非玄武科技授权人员，无法访问该机器人，请联系管理员确认（玄武 @xuanwu)")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """开始广播流程(仅限所有者)"""
    if not is_owner(update):
        await update.message.reply_text("⛔ 检测到您非玄武科技授权人员，无法访问该机器人，请联系管理员确认（玄武 @xuanwu)")
        return ConversationHandler.END
        
    await update.message.reply_text(
        '📢 广播模式 (仅限所有者)\n\n'
        '请发送您要广播的消息 (文字/图片/文件)\n'
        '输入 /cancel 取消操作。'
    )
    return GET_MESSAGE

async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """存储消息并请求群组ID(仅限所有者)"""
    if not is_owner(update):
        await update.message.reply_text("⛔ 检测到您非玄武科技授权人员，无法访问该机器人，请联系管理员确认（玄武 @xuanwu)")
        return ConversationHandler.END

    # 根据类型存储消息
    if update.message.text:
        context.user_data['message_type'] = 'text'
        context.user_data['content'] = update.message.text
    elif update.message.photo:
        context.user_data['message_type'] = 'photo'
        context.user_data['content'] = update.message.photo[-1].file_id
        context.user_data['caption'] = update.message.caption
    elif update.message.document:
        context.user_data['message_type'] = 'document'
        context.user_data['content'] = update.message.document.file_id
        context.user_data['caption'] = update.message.caption
    else:
        await update.message.reply_text("❌ 不支持的消息类型")
        return ConversationHandler.END

    await update.message.reply_text(
        "✅ 消息已接收!\n"
        "现在请发送要广播的群组ID\n"
        "(ID不会被保存)\n"
        "输入 /cancel 取消操作。"
    )
    return GET_GROUP_ID

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """向指定群组发送消息(仅限所有者)"""
    if not is_owner(update):
        await update.message.reply_text("⛔ 检测到您非玄武科技授权人员，无法访问该机器人，请联系管理员确认（玄武 @xuanwu)")
        return ConversationHandler.END

    try:
        group_id = update.message.text
        msg_type = context.user_data.get('message_type')
        
        if msg_type == 'text':
            await context.bot.send_message(
                chat_id=group_id,
                text=context.user_data['content']
            )
        elif msg_type == 'photo':
            await context.bot.send_photo(
                chat_id=group_id,
                photo=context.user_data['content'],
                caption=context.user_data.get('caption', '')
            )
        elif msg_type == 'document':
            await context.bot.send_document(
                chat_id=group_id,
                document=context.user_data['content'],
                caption=context.user_data.get('caption', '')
            )
            
        await update.message.reply_text(f"✅ 消息已成功发送到群组 {group_id}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ 广播失败: {str(e)}")
    
    # 清除临时数据
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """取消当前操作(仅限所有者)"""
    if is_owner(update):
        await update.message.reply_text("❌ 操作已取消。")
        context.user_data.clear()
    return ConversationHandler.END

def main() -> None:
    """启动机器人"""
    # 创建应用
    application = Application.builder().token(BOT_TOKEN).build()

    # 仅限所有者的命令处理器
    application.add_handler(CommandHandler("start", start))
    
    # 广播对话(仅限所有者)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('broadcast', broadcast_command)],
        states={
            GET_MESSAGE: [
                MessageHandler(
                    filters.TEXT | filters.PHOTO | filters.Document.ALL,
                    receive_message
                ),
                CommandHandler('cancel', cancel)
            ],
            GET_GROUP_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast),
                CommandHandler('cancel', cancel)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(conv_handler)

    # 忽略所有非所有者消息
    application.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        lambda update, _: update.message.reply_text("⛔ 检测到您非玄武科技授权人员，无法访问该机器人，请联系管理员确认（玄武 @xuanwu)")
        if not is_owner(update) else None
    ))

    # 运行机器人
    application.run_polling()

if __name__ == '__main__':
    main()