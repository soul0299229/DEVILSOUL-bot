"""
bot.py — Telegram admin bot for the Lua mod generator.
Only the OWNER_USER_ID can issue commands. Every generated file is named DEVILSOUL.lua
and always contains the bypass + menu layers.
"""

import io
import os
import sys
import traceback
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes,
)

import lua_features as LF

# ── config ──────────────────────────────────────────────────────
BOT_TOKEN      = os.environ.get("8311904929:AAGBHZMPppnSFoekbeAy5_FhuaDV47vZsAc")
OWNER_USER_ID  = int(os.environ.get("OWNER_USER_ID"))
OUTPUT_NAME    = "DEVILSOUL.lua"
DEFAULT_BRAND  = "DEVILSOUL"
DEFAULT_EXPIRY = (2026, 10, 29)

# optional GitHub upload
GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO    = os.environ.get("GITHUB_REPO", "")   # "user/repo"
GITHUB_PATH    = os.environ.get("GITHUB_PATH", "DEVILSOUL.lua")


def _is_owner(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == OWNER_USER_ID


async def _deny(update: Update):
    if update.message:
        await update.message.reply_text("not authorised.")


HELP_TEXT = """*DEVILSOUL mod builder*

/list — show available feature ids
/build `<a,b,c>` — build a mod with those features
/all — build with every feature
/upload — build with every feature and push to GitHub
/id — show your telegram user id
/help — this message

Every build automatically contains:
  • menu       — feature toggle table
  • bypass     — security function bypass
Output file is always `DEVILSOUL.lua`.
"""


async def cmd_start(update: Update, _ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update): return await _deny(update)
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_help(update: Update, _ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update): return await _deny(update)
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_id(update: Update, _ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else "?"
    await update.message.reply_text(f"your id: `{uid}`", parse_mode="Markdown")


async def cmd_list(update: Update, _ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update): return await _deny(update)
    lines = ["*available features:*"]
    for fid, label, deps in LF.list_features():
        dep = f"  ← {','.join(deps)}" if deps else ""
        forced = "  🔒 forced" if fid in LF.FORCED else ""
        lines.append(f"`{fid:<16}` {label}{dep}{forced}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


def _render(features):
    return LF.build_mod(features, brand=DEFAULT_BRAND,
                        expiry=DEFAULT_EXPIRY, filename=OUTPUT_NAME)


async def _send_lua(update: Update, lua: str, caption: str):
    buf = io.BytesIO(lua.encode("utf-8"))
    buf.name = OUTPUT_NAME
    await update.message.reply_document(document=buf, filename=OUTPUT_NAME,
                                        caption=caption)


async def cmd_build(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update): return await _deny(update)
    if not ctx.args:
        return await update.message.reply_text(
            "usage: `/build menu,fps165,aimbot,wallhack`", parse_mode="Markdown")
    feats = [a.strip() for a in " ".join(ctx.args).replace(",", " ").split() if a.strip()]
    unknown = [f for f in feats if f not in LF.REGISTRY]
    if unknown:
        return await update.message.reply_text(f"unknown: {', '.join(unknown)}")
    try:
        lua = _render(feats)
    except Exception as e:
        tb = traceback.format_exc()
        return await update.message.reply_text(f"build failed: {e}\n\n```\n{tb[-1500:]}\n```",
                                               parse_mode="Markdown")
    final = ["menu", "bypass"] + [f for f in feats if f not in LF.FORCED]
    cap = "DEVILSOUL.lua\nfeatures: " + ", ".join(dict.fromkeys(final))
    await _send_lua(update, lua, cap)


async def cmd_all(update: Update, _ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update): return await _deny(update)
    feats = list(LF.REGISTRY.keys())
    lua = _render(feats)
    await _send_lua(update, lua, "DEVILSOUL.lua — all features")


async def cmd_upload(update: Update, _ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update): return await _deny(update)
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return await update.message.reply_text(
            "GitHub not configured. Set GITHUB_TOKEN + GITHUB_REPO env vars.")
    try:
        from github import Github
        feats = list(LF.REGISTRY.keys())
        lua = _render(feats)
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        try:
            f = repo.get_contents(GITHUB_PATH)
            repo.update_file(GITHUB_PATH, f"update {OUTPUT_NAME}",
                             lua, f.sha)
            status = "updated"
        except Exception:
            repo.create_file(GITHUB_PATH, f"create {OUTPUT_NAME}", lua)
            status = "created"
        url = f"https://github.com/{GITHUB_REPO}/blob/main/{GITHUB_PATH}"
        await update.message.reply_text(f"{status}: {url}")
    except Exception as e:
        await update.message.reply_text(f"upload failed: {e}")


async def cmd_unknown(update: Update, _ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update): return await _deny(update)
    await update.message.reply_text("unknown command — try /help")


def main():
    if BOT_TOKEN.startswith("PUT_"):
        print("set BOT_TOKEN env var (or edit the file)", file=sys.stderr)
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("id",     cmd_id))
    app.add_handler(CommandHandler("list",   cmd_list))
    app.add_handler(CommandHandler("build",  cmd_build))
    app.add_handler(CommandHandler("all",    cmd_all))
    app.add_handler(CommandHandler("upload", cmd_upload))
    app.add_handler(MessageHandler(filters.COMMAND, cmd_unknown))

    print(f"[DEVILSOUL bot] running — admin id {OWNER_USER_ID}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
