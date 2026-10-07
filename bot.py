# bot.py — Devil Menu Telegram bot
import os, io, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from lua_generator import generate_lua, PROFILES, ESP_STYLES, CROSSHAIRS

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_NAME  = os.environ.get("BOT_NAME", "devil_menu")

DEFAULT_SETTINGS = {
    "profile": "safe",
    "aimbot": 35,
    "mb_on": True,
    "mb_range": 20,
    "mb_chance": 15,
    "esp_style": "auto",
    "esp_rotate": 30,
    "esp_name": True,
    "loot_esp": True,
    "crosshair": "cross",
}

def get_settings(ctx): 
    s = ctx.user_data.get("settings")
    if not s:
        s = dict(DEFAULT_SETTINGS); ctx.user_data["settings"] = s
    return s

def settings_text(s):
    return (
        f"*Profile:* `{s['profile']}`\n"
        f"*Aimbot:* `{s['aimbot']}/100`\n"
        f"*Magic Bullet:* `{'ON' if s['mb_on'] else 'OFF'}` @ `{s['mb_range']}m` ({s['mb_chance']}% roll)\n"
        f"*ESP Style:* `{s['esp_style']}` · *Name ESP:* `{'ON' if s['esp_name'] else 'OFF'}`\n"
        f"*Loot ESP:* `{'ON' if s['loot_esp'] else 'OFF'}`\n"
        f"*Crosshair:* `{s['crosshair']}`"
    )

def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔴 Full", callback_data="preset:full"),
         InlineKeyboardButton("🟢 Safe", callback_data="preset:safe"),
         InlineKeyboardButton("🎲 Random", callback_data="preset:random")],
        [InlineKeyboardButton("🎯 Aimbot 1–100", callback_data="menu:aimbot"),
         InlineKeyboardButton("💥 Magic Bullet", callback_data="menu:mb")],
        [InlineKeyboardButton("👁 ESP Style", callback_data="menu:esp"),
         InlineKeyboardButton("📛 Name ESP", callback_data="menu:name"),
         InlineKeyboardButton("📦 Loot ESP", callback_data="menu:loot")],
        [InlineKeyboardButton("➕ Crosshair", callback_data="menu:crosshair"),
         InlineKeyboardButton("⚙️ Settings", callback_data="menu:settings")],
        [InlineKeyboardButton("🛠 Generate .lua", callback_data="generate")],
    ])

async def start(update, ctx):
    s = get_settings(ctx)
    txt = f"*{BOT_NAME}* — Devil Menu .lua builder\n\n{settings_text(s)}\n\nUse presets or menu below."
    if update.message:
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=main_menu_kb())
    else:
        await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=main_menu_kb())

async def cmd_full(update, ctx):
    s = get_settings(ctx); s.update(PROFILES["full"]); s["profile"]="full"
    await update.message.reply_text("🔴 *Full preset.*\n\n"+settings_text(s), parse_mode="Markdown", reply_markup=main_menu_kb())

async def cmd_safe(update, ctx):
    s = get_settings(ctx); s.update(PROFILES["safe"]); s["profile"]="safe"
    await update.message.reply_text("🟢 *Safe preset.*\n\n"+settings_text(s), parse_mode="Markdown", reply_markup=main_menu_kb())

async def cmd_random(update, ctx):
    s = get_settings(ctx); s.update(PROFILES["random"]); s["profile"]="random"
    await update.message.reply_text("🎲 *Random preset.*\n\n"+settings_text(s), parse_mode="Markdown", reply_markup=main_menu_kb())

async def cmd_aimbot(update, ctx):
    s = get_settings(ctx)
    if not ctx.args: await update.message.reply_text("`/aimbot 1-100`", parse_mode="Markdown"); return
    try: v = int(ctx.args[0])
    except: await update.message.reply_text("Number 1-100."); return
    if not 1 <= v <= 100: await update.message.reply_text("1-100 only."); return
    s["aimbot"] = v
    await update.message.reply_text(f"🎯 Aimbot: `{v}/100`", parse_mode="Markdown")

async def cmd_mb(update, ctx):
    s = get_settings(ctx)
    if not ctx.args or ctx.args[0].lower() not in ("on","off"):
        await update.message.reply_text("`/mb on` or `/mb off`", parse_mode="Markdown"); return
    s["mb_on"] = ctx.args[0].lower()=="on"
    await update.message.reply_text(f"💥 MB: `{'ON' if s['mb_on'] else 'OFF'}`", parse_mode="Markdown")

async def cmd_range(update, ctx):
    s = get_settings(ctx)
    if not ctx.args: await update.message.reply_text("`/range <m>` 1-50", parse_mode="Markdown"); return
    try: v = float(ctx.args[0])
    except: await update.message.reply_text("Number do."); return
    if not 1 <= v <= 50: await update.message.reply_text("1-50m only."); return
    s["mb_range"] = v
    await update.message.reply_text(f"💥 MB range: `{v}m`", parse_mode="Markdown")

async def cmd_esp(update, ctx):
    s = get_settings(ctx)
    if not ctx.args or (ctx.args[0] not in ESP_STYLES and ctx.args[0] != "auto"):
        await update.message.reply_text("Styles: "+", ".join(f"`{k}`" for k in ESP_STYLES)+", `auto`", parse_mode="Markdown"); return
    s["esp_style"] = ctx.args[0]
    await update.message.reply_text(f"👁 ESP: `{s['esp_style']}`", parse_mode="Markdown")

async def cmd_name(update, ctx):
    s = get_settings(ctx)
    if not ctx.args or ctx.args[0].lower() not in ("on","off"):
        await update.message.reply_text("`/name on` or `/name off`", parse_mode="Markdown"); return
    s["esp_name"] = ctx.args[0].lower()=="on"
    await update.message.reply_text(f"📛 Name ESP: `{'ON' if s['esp_name'] else 'OFF'}`", parse_mode="Markdown")

async def cmd_loot(update, ctx):
    s = get_settings(ctx)
    if not ctx.args or ctx.args[0].lower() not in ("on","off"):
        await update.message.reply_text("`/loot on` or `/loot off`", parse_mode="Markdown"); return
    s["loot_esp"] = ctx.args[0].lower()=="on"
    await update.message.reply_text(f"📦 Loot ESP: `{'ON' if s['loot_esp'] else 'OFF'}`", parse_mode="Markdown")

async def cmd_crosshair(update, ctx):
    s = get_settings(ctx)
    if not ctx.args or ctx.args[0] not in CROSSHAIRS:
        await update.message.reply_text("Styles: "+", ".join(f"`{k}`" for k in CROSSHAIRS), parse_mode="Markdown"); return
    s["crosshair"] = ctx.args[0]
    await update.message.reply_text(f"➕ Crosshair: `{s['crosshair']}`", parse_mode="Markdown")

async def cmd_settings(update, ctx):
    await update.message.reply_text(settings_text(get_settings(ctx)), parse_mode="Markdown", reply_markup=main_menu_kb())

async def cmd_generate(update, ctx):
    await _send_lua(update, ctx, get_settings(ctx))

async def _send_lua(update, ctx, s):
    try:
        lua = generate_lua(s, bot_name=BOT_NAME)
    except Exception as e:
        t = update.message or update.callback_query.message
        await t.reply_text(f"Error: `{e}`", parse_mode="Markdown"); return
    fname = f"BRPlayerCharacterBase_{s['profile']}_{s['aimbot']}_{int(time.time())}.lua"
    buf = io.BytesIO(lua.encode("utf-8")); buf.name = fname
    cap = f"📦 *{fname}*\n\n{settings_text(s)}"
    t = update.message or update.callback_query.message
    await t.reply_document(document=InputFile(buf, filename=fname), caption=cap, parse_mode="Markdown")

async def on_callback(update, ctx):
    q = update.callback_query; await q.answer()
    d = q.data; s = get_settings(ctx)
    if d.startswith("preset:"):
        p = d.split(":",1)[1]
        if p in PROFILES: s.update(PROFILES[p]); s["profile"]=p
        await q.edit_message_text(f"*{p.upper()}* applied.\n\n{settings_text(s)}", parse_mode="Markdown", reply_markup=main_menu_kb())
    elif d == "menu:aimbot":     await q.edit_message_text("`/aimbot 1-100`", parse_mode="Markdown")
    elif d == "menu:mb":         await q.edit_message_text("`/mb on|off` · `/range <m>`", parse_mode="Markdown")
    elif d == "menu:esp":        await q.edit_message_text("`/esp <style>` — "+", ".join(f"`{k}`" for k in ESP_STYLES), parse_mode="Markdown")
    elif d == "menu:name":       await q.edit_message_text("`/name on|off`", parse_mode="Markdown")
    elif d == "menu:loot":       await q.edit_message_text("`/loot on|off`", parse_mode="Markdown")
    elif d == "menu:crosshair":  await q.edit_message_text("`/crosshair <style>` — "+", ".join(f"`{k}`" for k in CROSSHAIRS), parse_mode="Markdown")
    elif d == "menu:settings":   await q.edit_message_text(settings_text(s), parse_mode="Markdown", reply_markup=main_menu_kb())
    elif d == "generate":
        await q.edit_message_text("Generating…"); await _send_lua(update, ctx, s)

async def cmd_help(update, ctx):
    await update.message.reply_text(
        "*Devil Menu Commands*\n"
        "/start — menu\n/full /safe /random — presets\n"
        "/aimbot 1-100\n/mb on|off\n/range <m>\n"
        "/esp <style>\n/name on|off\n/loot on|off\n"
        "/crosshair <style>\n/settings\n/generate\n",
        parse_mode="Markdown")

def main():
    if not BOT_TOKEN: raise SystemExit("Set BOT_TOKEN env.")
    app = Application.builder().token(BOT_TOKEN).build()
    for cmd, fn in [("start",start),("full",cmd_full),("safe",cmd_safe),("random",cmd_random),
                    ("aimbot",cmd_aimbot),("mb",cmd_mb),("range",cmd_range),("esp",cmd_esp),
                    ("name",cmd_name),("loot",cmd_loot),("crosshair",cmd_crosshair),
                    ("settings",cmd_settings),("generate",cmd_generate),("help",cmd_help)]:
        app.add_handler(CommandHandler(cmd, fn))
    app.add_handler(CallbackQueryHandler(on_callback))
    print(f"[{BOT_NAME}] running…")
    app.run_polling()

if __name__ == "__main__":
    main()