import html
import re
import wikipedia
import random

import json
import urllib.request
import urllib.parse

import requests
from Megumi import CASH_API_KEY
from Megumi import (DEV_USERS, OWNER_ID, SUDO_USERS, SUPPORT_USERS,
                          TIGER_USERS, WHITELIST_USERS, dispatcher)
from Megumi.__main__ import STATS, TOKEN, USER_INFO
from Megumi.modules.disable import DisableAbleCommandHandler
from Megumi.modules.helper_funcs.filters import CustomFilters
from Megumi.modules.helper_funcs.chat_status import sudo_plus, user_admin
from Megumi.modules.helper_funcs.extraction import extract_user
from telegram import MessageEntity, ParseMode, Update
from telegram.error import BadRequest
from emoji import UNICODE_EMOJI
from googletrans import LANGUAGES, Translator
from wikipedia.exceptions import DisambiguationError, PageError
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

MARKDOWN_HELP = f"""
Markdown is a very powerful formatting tool supported by telegram. {dispatcher.bot.first_name} has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.

• <code>_italic_</code>*:* wrapping text with '_' will produce italic text
• <code>*bold*</code>*:* wrapping text with '*' will produce bold text
• <code>`code`</code>*:* wrapping text with '`' will produce monospaced text, also known as 'code'
• <code>[sometext](someURL)</code>*:* this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
<b>Example:</b>Example:<b>Example:</b> <code>[test](example.com)</code>

• <code>[buttontext](buttonurl:someURL)</code>*:* this is a special enhancement to allow users to have telegram \
buttons in their markdown. <code>buttontext</code> will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
<b>Example:</b> <code>[This is a button](buttonurl:example.com)</code>

If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
This will create two buttons on a single line, instead of one button per line.

Keep in mind that your message <b>MUST</b> contain some text other than just a button!
"""

normiefont = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
]
weebyfont = [
    '卂', '乃', '匚', '刀', '乇', '下', '厶', '卄', '工', '丁', '长', '乚', '从', '𠘨', '口',
    '尸', '㔿', '尺', '丂', '丅', '凵', 'リ', '山', '乂', '丫', '乙'
]

@run_async
def convert(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(" ")

    if len(args) == 4:
        try:
            orig_cur_amount = float(args[1])

        except ValueError:
            update.effective_message.reply_text("Invalid Amount Of Currency")
            return

        orig_cur = args[2].upper()

        new_cur = args[3].upper()

        request_url = (f"https://www.alphavantage.co/query"
                       f"?function=CURRENCY_EXCHANGE_RATE"
                       f"&from_currency={orig_cur}"
                       f"&to_currency={new_cur}"
                       f"&apikey={CASH_API_KEY}")
        response = requests.get(request_url).json()
        try:
            current_rate = float(
                response['Realtime Currency Exchange Rate']['5. Exchange Rate'])
        except KeyError:
            update.effective_message.reply_text("Currency Not Supported.")
            return
        new_cur_amount = round(orig_cur_amount * current_rate, 5)
        update.effective_message.reply_text(
            f"{orig_cur_amount} {orig_cur} = {new_cur_amount} {new_cur}")

    elif len(args) == 1:
        update.effective_message.reply_text(
            __help__, parse_mode=ParseMode.MARKDOWN)

    else:
        update.effective_message.reply_text(
            f"*Invalid Args!!:* Required 3 But Passed {len(args) -1}",
            parse_mode=ParseMode.MARKDOWN)

@run_async
def wiki(update: Update, context: CallbackContext):
    msg = update.effective_message.reply_to_message if update.effective_message.reply_to_message else update.effective_message
    res = ""
    if msg == update.effective_message:
        search = msg.text.split(" ", maxsplit=1)[1]
    else:
        search = msg.text
    try:
        res = wikipedia.summary(search)
    except DisambiguationError as e:
        update.message.reply_text(
            "Disambiguated pages found! Adjust your query accordingly.\n<i>{}</i>"
            .format(e),
            parse_mode=ParseMode.HTML)
    except PageError as e:
        update.message.reply_text(
            "<code>{}</code>".format(e), parse_mode=ParseMode.HTML)
    if res:
        result = f"<b>{search}</b>\n\n"
        result += f"<i>{res}</i>\n"
        result += f"""<a href="https://en.wikipedia.org/wiki/{search.replace(" ", "%20")}">Read more...</a>"""
        if len(result) > 4000:
            with open("result.txt", 'w') as f:
                f.write(f"{result}\n\nUwU OwO OmO UmU")
            with open("result.txt", 'rb') as f:
                context.bot.send_document(
                    document=f,
                    filename=f.name,
                    reply_to_message_id=update.message.message_id,
                    chat_id=update.effective_chat.id,
                    parse_mode=ParseMode.HTML)
        else:
            update.message.reply_text(
                result,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)

@run_async
def weebify(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    string = ""

    if message.reply_to_message:
        string = message.reply_to_message.text.lower().replace(" ", "  ")

    if args:
        string = '  '.join(args).lower()

    if not string:
        message.reply_text(
            "Usage is `/weebify <text>`", parse_mode=ParseMode.MARKDOWN)
        return

    for normiecharacter in string:
        if normiecharacter in normiefont:
            weebycharacter = weebyfont[normiefont.index(normiecharacter)]
            string = string.replace(normiecharacter, weebycharacter)

    if message.reply_to_message:
        message.reply_to_message.reply_text(string)
    else:
        message.reply_text(string)

@run_async
def react(update: Update, context: CallbackContext):
    message = update.effective_message
    react = random.choice(reactions)
    if message.reply_to_message:
        message.reply_to_message.reply_text(react)
    else:
        message.reply_text(react)

@run_async
def pat(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat_id = update.effective_chat.id
    msg = str(update.message.text)
    try:
        msg = msg.split(" ", 1)[1]
    except IndexError:
        msg = ""
    msg_id = update.effective_message.reply_to_message.message_id if update.effective_message.reply_to_message else update.effective_message.message_id
    pats = []
    pats = json.loads(urllib.request.urlopen(urllib.request.Request(
    'http://headp.at/js/pats.json',
    headers={'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) '
         'Gecko/20071127 Firefox/2.0.0.11'}
    )).read().decode('utf-8'))
    if "@" in msg and len(msg) > 5:
        bot.send_photo(chat_id, f'https://headp.at/pats/{urllib.parse.quote(random.choice(pats))}', caption=msg)
    else:
        bot.send_photo(chat_id, f'https://headp.at/pats/{urllib.parse.quote(random.choice(pats))}', reply_to_message_id=msg_id)

@run_async
def snipe(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    try:
        chat_id = str(args[0])
        del args[0]
    except TypeError:
        update.effective_message.reply_text(
            "Please give me a chat to echo to!")
    to_send = " ".join(args)
    if len(to_send) >= 2:
        try:
            bot.sendMessage(int(chat_id), str(to_send))
        except TelegramError:
            LOGGER.warning("Couldn't send to group %s", str(chat_id))
            update.effective_message.reply_text(
                "Couldn't send the message. Perhaps I'm not part of that group?")

@run_async
def ud(update: Update, context: CallbackContext):
    message = update.effective_message
    text = message.text[len('/ud '):]
    results = requests.get(
        f'https://api.urbandictionary.com/v0/define?term={text}').json()
    try:
        reply_text = f'ℹ️ *{text}*\n\n👉🏻 {results["list"][0]["definition"]}\n\n📌 _{results["list"][0]["example"]}_'
    except:
        reply_text = "No results found."
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

@run_async
def get_id(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    user_id = extract_user(msg, args)

    if user_id:

        if msg.reply_to_message and msg.reply_to_message.forward_from:

            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            msg.reply_text(
                f"The original sender, {html.escape(user2.first_name)},"
                f" has an ID of <code>{user2.id}</code>.\n"
                f"The forwarder, {html.escape(user1.first_name)},"
                f" has an ID of <code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML)

        else:

            user = bot.get_chat(user_id)
            msg.reply_text(
                f"{html.escape(user.first_name)}'s id is <code>{user.id}</code>.",
                parse_mode=ParseMode.HTML)

    else:

        if chat.type == "private":
            msg.reply_text(
                f"Your id is <code>{chat.id}</code>.",
                parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(
                f"This group's id is <code>{chat.id}</code>.",
                parse_mode=ParseMode.HTML)


@run_async
def gifid(update: Update, context: CallbackContext):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation:
        update.effective_message.reply_text(
            f"Gif ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML)
    else:
        update.effective_message.reply_text(
            "Please reply to a gif to get its ID.")

@run_async
def totranslate(update: Update, context: CallbackContext):
    msg = update.effective_message
    problem_lang_code = []
    for key in LANGUAGES:
        if "-" in key:
            problem_lang_code.append(key)
    try:
        if msg.reply_to_message and msg.reply_to_message.text:

            args = update.effective_message.text.split(None, 1)
            text = msg.reply_to_message.text
            message = update.effective_message
            dest_lang = None

            try:
                source_lang = args[1].split(None, 1)[0]
            except:
                source_lang = "en"

            if source_lang.count('-') == 2:
                for lang in problem_lang_code:
                    if lang in source_lang:
                        if source_lang.startswith(lang):
                            dest_lang = source_lang.rsplit("-", 1)[1]
                            source_lang = source_lang.rsplit("-", 1)[0]
                        else:
                            dest_lang = source_lang.split("-", 1)[1]
                            source_lang = source_lang.split("-", 1)[0]
            elif source_lang.count('-') == 1:
                for lang in problem_lang_code:
                    if lang in source_lang:
                        dest_lang = source_lang
                        source_lang = None
                        break
                if dest_lang is None:
                    dest_lang = source_lang.split("-")[1]
                    source_lang = source_lang.split("-")[0]
            else:
                dest_lang = source_lang
                source_lang = None

            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in text:
                    text = text.replace(emoji, '')

            trl = Translator()
            if source_lang is None:
                detection = trl.detect(text)
                tekstr = trl.translate(text, dest=dest_lang)
                return message.reply_text(
                    f"Translated from `{detection.lang}` to `{dest_lang}`:\n`{tekstr.text}`",
                    parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(text, dest=dest_lang, src=source_lang)
                message.reply_text(
                    f"Translated from `{source_lang}` to `{dest_lang}`:\n`{tekstr.text}`",
                    parse_mode=ParseMode.MARKDOWN)
        else:
            args = update.effective_message.text.split(None, 2)
            message = update.effective_message
            source_lang = args[1]
            text = args[2]
            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in text:
                    text = text.replace(emoji, '')
            dest_lang = None
            temp_source_lang = source_lang
            if temp_source_lang.count('-') == 2:
                for lang in problem_lang_code:
                    if lang in temp_source_lang:
                        if temp_source_lang.startswith(lang):
                            dest_lang = temp_source_lang.rsplit("-", 1)[1]
                            source_lang = temp_source_lang.rsplit("-", 1)[0]
                        else:
                            dest_lang = temp_source_lang.split("-", 1)[1]
                            source_lang = temp_source_lang.split("-", 1)[0]
            elif temp_source_lang.count('-') == 1:
                for lang in problem_lang_code:
                    if lang in temp_source_lang:
                        dest_lang = None
                        break
                    else:
                        dest_lang = temp_source_lang.split("-")[1]
                        source_lang = temp_source_lang.split("-")[0]
            trl = Translator()
            if dest_lang is None:
                detection = trl.detect(text)
                tekstr = trl.translate(text, dest=source_lang)
                return message.reply_text(
                    "Translated from `{}` to `{}`:\n`{}`".format(
                        detection.lang, source_lang, tekstr.text),
                    parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(text, dest=dest_lang, src=source_lang)
                message.reply_text(
                    "Translated from `{}` to `{}`:\n`{}`".format(
                        source_lang, dest_lang, tekstr.text),
                    parse_mode=ParseMode.MARKDOWN)

    except IndexError:
        update.effective_message.reply_text(
            "Reply to messages or write messages from other languages ​​for translating into the intended language\n\n"
            "Example: `/tr en-ml` to translate from English to Malayalam\n"
            "Or use: `/tr ml` for automatic detection and translating it into Malayalam.\n"
            "See [List of Language Codes](t.me/OnePunchSupport/12823) for a list of language codes.",
            parse_mode="markdown",
            disable_web_page_preview=True)
    except ValueError:
        update.effective_message.reply_text(
            "The intended language is not found!")
    else:
        return

@run_async
def info(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not message.reply_to_message and not args:
        user = message.from_user

    elif not message.reply_to_message and (
            not args or
        (len(args) >= 1 and not args[0].startswith("@") and
         not args[0].isdigit() and
         not message.parse_entities([MessageEntity.TEXT_MENTION]))):
        message.reply_text("I can't extract a user from this.")
        return

    else:
        return

    text = (f"<b>Characteristics:</b>\n"
            f"ID: <code>{user.id}</code>\n"
            f"First Name: {html.escape(user.first_name)}")

    if user.last_name:
        text += f"\nLast Name: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nUsername: @{html.escape(user.username)}"

    text += f"\nPermanent user link: {mention_html(user.id, 'link')}"

    disaster_level_present = False

    if user.id == OWNER_ID:
        text += "\nThis person is my owner - I would never do anything against them!."
    elif user.id in DEV_USERS:
        text += "\nThis person is my dev - I would never do anything against them!."
    elif user.id in SUDO_USERS:
        text += "\nThis person is one of my sudo users! Nearly as powerful as my owner - so watch it.."
    elif user.id in SUPPORT_USERS:
        text += "\nThis person is one of my sudo users! Nearly as powerful as my owner - so watch it.."
    elif user.id in TIGER_USERS:
        text += "\nThis person is one of my sudo users! Nearly as powerful as my owner - so watch it.."
    elif user.id in WHITELIST_USERS:
        text += "\nThis person is one of my sudo users! Nearly as powerful as my owner - so watch it.."

    try:
        user_member = chat.get_member(user.id)
        if user_member.status == 'administrator':
            result = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}"
            )
            result = result.json()["result"]
            if "custom_title" in result.keys():
                custom_title = result['custom_title']
                text += f"\n\nThis user holds the title <b>{custom_title}</b> here."
    except BadRequest:
        pass

    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    update.effective_message.reply_text(
        text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@run_async
@user_admin
def echo(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)

    message.delete()

@run_async
def markdown_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Try forwarding the following message to me, and you'll see!")
    update.effective_message.reply_text(
        "/save test This is a markdown test. _italics_, *bold*, `code`, "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)")

@run_async
def stats(update: Update, context: CallbackContext):
    stats = "Current stats:\n" + "\n".join([mod.__stats__() for mod in STATS])
    result = re.sub(r'(\d+)', r'<code>\1</code>', stats)
    update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)

__help__ = """
 • `/id`*:* get the current group id. If used by replying to a message, gets that user's id.
 • `/gifid`*:* reply to a gif to me to tell you its file ID.
 • `/pat`*:* give a headpat :)
 • `/weebify <text>`*:* returns a weebified text.
 • `/ud <word>`*:* Type the word or expression you want to search use.
 • `/info`*:* get information about a user.
 • `/wiki <query>`*:* wiki your query.
 • `/markdownhelp`*:* quick summary of how markdown works in telegram - can only be called in private chats.
 • `/tr` or `/tl` (language code) as reply to a long message.
*Example:* `/tr en`*:* translates something to english. 
   `/tr hi-en`*:* translates hindi to english.
• `/cash`*:* currency converter

 *Example syntax:*
 `/cash 1 USD INR`  _OR_   `/cash 1 usd inr`

 *Output:* `1.0 USD = 75.505 INR`

"""
ID_HANDLER = DisableAbleCommandHandler("id", get_id)
GIFID_HANDLER = DisableAbleCommandHandler("gifid", gifid)
INFO_HANDLER = DisableAbleCommandHandler(["info"], info)
UD_HANDLER = DisableAbleCommandHandler(["ud"], ud)
ECHO_HANDLER = DisableAbleCommandHandler("echo", echo, filters=Filters.group)
WEEBIFY_HANDLER = DisableAbleCommandHandler("weebify", weebify)
MD_HELP_HANDLER = CommandHandler(
    "markdownhelp", markdown_help, filters=Filters.private)
PAT_HANDLER = DisableAbleCommandHandler("pat", pat)
TRANSLATE_HANDLER = DisableAbleCommandHandler(["tr", "tl"], totranslate)
WIKI_HANDLER = DisableAbleCommandHandler("wiki", wiki)
CONVERTER_HANDLER = CommandHandler('cash', convert)
SNIPE_HANDLER = CommandHandler(
    "snipe",
    snipe,
    pass_args=True,
    filters=CustomFilters.sudo_filter)
STATS_HANDLER = CommandHandler(
    "stats",
    stats,
    filters=Filters.user(DEV_USERS))


dispatcher.add_handler(SNIPE_HANDLER)
dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(GIFID_HANDLER)
dispatcher.add_handler(WEEBIFY_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(PAT_HANDLER)
dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(WIKI_HANDLER)
dispatcher.add_handler(CONVERTER_HANDLER)

__mod_name__ = "Misc"
__command_list__ = ["id", "info", "echo", "pat", "snipe", "weebify", "ud", 
"runs", "slap", "roll", "toss", "shrug", "bluetext", "rlg", "decide",
    "table", "react", "wiki","tr", "cash"]
__handlers__ = [
    ID_HANDLER, GIFID_HANDLER, INFO_HANDLER, ECHO_HANDLER, MD_HELP_HANDLER,
    SNIPE_HANDLER, PAT_HANDLER, STATS_HANDLER, WEEBIFY_HANDLER, UD_HANDLER,
    WIKI_HANDLER, TRANSLATE_HANDLER, CONVERTER_HANDLER
]
