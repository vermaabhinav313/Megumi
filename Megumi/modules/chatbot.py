import html
# AI module using Intellivoid's Coffeehouse API by @TheRealPhoenix
from time import sleep, time

import Megumi.modules.sql.chatbot_sql as sql
from coffeehouse.api import API
from coffeehouse.exception import CoffeeHouseError as CFError
from coffeehouse.lydia import LydiaAI
from Megumi import AI_API_KEY, OWNER_ID, SUPPORT_CHAT, dispatcher
from Megumi.modules.helper_funcs.chat_status import user_admin
from Megumi.modules.helper_funcs.filters import CustomFilters
from Megumi.modules.log_channel import gloggable
from telegram import Update
from telegram.error import BadRequest, RetryAfter, Unauthorized
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, run_async)
from telegram.utils.helpers import mention_html

CoffeeHouseAPI = API(AI_API_KEY)
api_client = LydiaAI(CoffeeHouseAPI)


@run_async
@user_admin
@gloggable
def add_chat(update: Update, context: CallbackContext):
    global api_client
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    is_chat = sql.is_chat(chat.id)
    if not is_chat:
        ses = api_client.create_session()
        ses_id = str(ses.id)
        expires = str(ses.expires)
        sql.set_ses(chat.id, ses_id, expires)
        chat.send_message("AI successfully enabled for this chat!")
        message = (f"<b>{html.escape(chat.title)}:</b>\n"
                   f"#AI_ENABLED\n"
                   f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
        return message
    else:
        msg.reply_text("AI is already enabled for this chat!")
        return ""


@run_async
@user_admin
@gloggable
def remove_chat(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    is_chat = sql.is_chat(chat.id)
    if not is_chat:
        chat.send_message("AI isn't enabled here in the first place!")
        return ""
    else:
        sql.rem_chat(chat.id)
        chat.send_message("AI disabled successfully!")
        message = (f"<b>{html.escape(chat.title)}:</b>\n"
                   f"#AI_DISABLED\n"
                   f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
        return message


def check_message(context: CallbackContext, message):
    reply_msg = message.reply_to_message
    if message.text.lower() == "megumi":
        return True
    if reply_msg:
        if reply_msg.from_user.id == context.bot.get_me().id:
            return True
    else:
        return False


@run_async
def chatbot(update: Update, context: CallbackContext):
    global api_client
    msg = update.effective_message
    chat = update.effective_chat
    chat_id = update.effective_chat.id
    is_chat = sql.is_chat(chat_id)
    bot = context.bot
    if not is_chat:
        return
    if msg.text and not msg.document:
        if not check_message(context, msg):
            return
        sesh, exp = sql.get_ses(chat_id)
        query = msg.text
        try:
            if int(exp) < time():
                ses = api_client.create_session()
                ses_id = str(ses.id)
                expires = str(ses.expires)
                sql.set_ses(chat_id, ses_id, expires)
                sesh, exp = sql.get_ses(chat_id)
        except ValueError:
            pass
        try:
            bot.send_chat_action(chat_id, action='typing')
            rep = api_client.think_thought(sesh, query)
            sleep(0.3)
            msg.reply_text(rep, timeout=60)
        except CFError as e:
            bot.send_message(OWNER_ID,
                             f"Chatbot error: {e} occurred in {chat_id}!")


@run_async
def list_chatbot_chats(update: Update, context: CallbackContext):
    chats = sql.get_all_chats()
    text = "<b>AI-Enabled Chats</b>\n"
    for chat in chats:
        try:
            x = context.bot.get_chat(int(*chat))
            name = x.title if x.title else x.first_name
            text += f"• <code>{name}</code>\n"
        except BadRequest:
            sql.rem_chat(*chat)
        except Unauthorized:
            sql.rem_chat(*chat)
        except RetryAfter as e:
            sleep(e.retry_after)
    update.effective_message.reply_text(text, parse_mode="HTML")


__mod_name__ = "Chatbot"

__help__ = f"""
Chatbot utilizes the CoffeeHouse API and allows Megumi to talk and provides a more interactive group chat experience.

This is an ongoing upgrade and is only available in your chats if you reach out to {SUPPORT_CHAT} and ask for it.
In future we might make it open for any chat and controllable by group admins.

*Commands:* 
*These only work for Megumi Moderators:*
 • `/addchat`*:* Enables Chatbot mode in the chat.
 • `/rmchat`*:* Disables Chatbot mode in the chat.
 • `/listaichats`*:* Lists the chats the chatmode is enabled in.

*Powered by CoffeeHouse* (https://coffeehouse.intellivoid.net/) from @Intellivoid
"""

ADD_CHAT_HANDLER = CommandHandler("addchat", add_chat, filters=CustomFilters.sudo_filter)
REMOVE_CHAT_HANDLER = CommandHandler("rmchat", remove_chat, filters=CustomFilters.sudo_filter)
CHATBOT_REGEX_HANDLER = MessageHandler(Filters.regex(r"(?i)megumi"), chatbot, friendly="chatbot")
CHATBOT_HANDLER = MessageHandler(
    Filters.text & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!")
                    & ~Filters.regex(r"^\/")), chatbot)
LIST_CB_CHATS_HANDLER = CommandHandler(
    "listaichats", list_chatbot_chats, filters=CustomFilters.sudo_filter)
# Filters for ignoring #note messages, !commands and sed.

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(REMOVE_CHAT_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)
dispatcher.add_handler(CHATBOT_REGEX_HANDLER)
dispatcher.add_handler(LIST_CB_CHATS_HANDLER)
