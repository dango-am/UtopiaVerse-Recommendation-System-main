import pandas as pd
import joblib
import difflib
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==========================================================
# TELEGRAM TOKEN
# ==========================================================

import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# ==========================================================
# LOAD MODEL FILES
# ==========================================================

def load_artifacts():
    df             = pd.read_pickle("processed_new_df.pkl")
    feature_matrix = joblib.load("weighted_features.joblib")
    model          = joblib.load("knn_model_final.joblib")
    return df, feature_matrix, model

print("Loading recommendation system...")
df, feature_matrix, model = load_artifacts()
print("Recommendation system loaded successfully.")

# ==========================================================
# AVAILABLE PLATFORMS  (auto-detected from the dataframe)
# ==========================================================

PLATFORM_COLS = sorted(
    c.replace("parent_platforms_", "")
    for c in df.columns
    if c.startswith("parent_platforms_")
    and c.replace("parent_platforms_", "").strip()
)

# ==========================================================
# RECOMMENDATION FUNCTION
# ==========================================================

def get_recommendations(
    game_name,
    df_source,
    matrix_source,
    model_source,
    platform="Any",
    top_n=10,
):
    matches = df_source[df_source["name"].str.lower() == game_name.lower()]

    if not matches.empty:
        game_idx     = matches.index[0]
        matched_game = matches.iloc[0]["name"]
    else:
        all_game_names  = df_source["name"].tolist()
        closest_matches = difflib.get_close_matches(game_name, all_game_names, n=1, cutoff=0.6)
        if not closest_matches:
            return f"No match found for '{game_name}'.", None
        matched_game = closest_matches[0]
        game_idx     = df_source[df_source["name"] == matched_game].index[0]

    game_vector        = matrix_source[game_idx]
    distances, indices = model_source.kneighbors(game_vector, n_neighbors=60)

    similar_indices = indices.flatten()
    similar_indices = similar_indices[similar_indices != game_idx]
    recommendations = df_source.iloc[similar_indices].copy()

    if platform != "Any":
        platform_col = f"parent_platforms_{platform}"
        if platform_col in df_source.columns:
            recommendations = recommendations[recommendations[platform_col] == 1]

    recommendations = recommendations.head(top_n)

    if recommendations.empty:
        return f"No games found like '{matched_game}' on {platform}.", None

    def get_labels(row, prefix):
        cols = [c for c in df_source.columns if c.startswith(prefix)]
        return " | ".join([c.replace(prefix, "") for c in cols if row[c] == 1])

    recommendations["Platforms"] = recommendations.apply(
        lambda x: get_labels(x, "parent_platforms_"), axis=1
    )
    recommendations["Genres"] = recommendations.apply(
        lambda x: get_labels(x, "genres_"), axis=1
    )

    return matched_game, recommendations[["name", "rating", "Platforms", "Genres", "background_image"]]


# ==========================================================
# BUILD PLATFORM KEYBOARD  (3 buttons per row)
# ==========================================================

def build_platform_keyboard(game_name: str) -> InlineKeyboardMarkup:
    buttons = []
    row     = []

    # "Any" always first
    row.append(InlineKeyboardButton("🌐 Any", callback_data=f"plat|Any|{game_name}"))
    buttons.append(row)
    row = []

    for i, plat in enumerate(PLATFORM_COLS):
        row.append(InlineKeyboardButton(plat, callback_data=f"plat|{plat}|{game_name}"))
        if len(row) == 3:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    return InlineKeyboardMarkup(buttons)


# ==========================================================
# BUILD RANDOM PLATFORM KEYBOARD  (prefixed with "rand|")
# ==========================================================

def build_random_platform_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    row     = []

    row.append(InlineKeyboardButton("🌐 Any", callback_data="rand|Any"))
    buttons.append(row)
    row = []

    for plat in PLATFORM_COLS:
        row.append(InlineKeyboardButton(plat, callback_data=f"rand|{plat}"))
        if len(row) == 3:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    return InlineKeyboardMarkup(buttons)


# ==========================================================
# GET 3 RANDOM GAMES  (filtered by platform)
# ==========================================================

def get_random_games(df_source, platform="Any", n=3):
    if platform != "Any":
        platform_col = f"parent_platforms_{platform}"
        if platform_col in df_source.columns:
            pool = df_source[df_source[platform_col] == 1]
        else:
            pool = df_source
    else:
        pool = df_source

    if pool.empty:
        return None

    sample = pool.sample(n=min(n, len(pool)), random_state=None).copy()

    def get_labels(row, prefix):
        cols = [c for c in df_source.columns if c.startswith(prefix)]
        return " | ".join([c.replace(prefix, "") for c in cols if row[c] == 1])

    sample["Platforms"] = sample.apply(lambda x: get_labels(x, "parent_platforms_"), axis=1)
    sample["Genres"]    = sample.apply(lambda x: get_labels(x, "genres_"),           axis=1)

    return sample[["name", "rating", "Platforms", "Genres", "background_image"]]


# ==========================================================
# BUILD FOLLOW-UP KEYBOARD
# ==========================================================

def build_followup_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔁 Recommend another game",  callback_data="action|new_game"),
            InlineKeyboardButton("❓ Help",                    callback_data="action|help"),
        ],
        [
            InlineKeyboardButton("🔄 Change platform filter",  callback_data="action|change_platform"),
            InlineKeyboardButton("🎲 Roll random games",       callback_data="action|random"),
        ],
        [
            InlineKeyboardButton("✅ I'm good, thanks!",        callback_data="action|done"),
        ],
    ])


# ==========================================================
# SEND RECOMMENDATIONS  (with images if available)
# ==========================================================

async def send_recommendations(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    matched_game: str,
    recs,
    platform: str,
):
    # ── Header ──────────────────────────────────────────────────────────────────
    platform_label = platform if platform != "Any" else "all platforms"
    header = (
        f"🎯 Based on: *{matched_game}*\n"
        f"🕹️ Platform: *{platform_label}*\n"
        f"Found *{len(recs)}* recommendations!\n"
    )
    await update.effective_message.reply_text(header, parse_mode="Markdown")

    # ── Send each game ───────────────────────────────────────────────────────────
    for i, (_, row) in enumerate(recs.iterrows(), start=1):
        caption = (
            f"*{i}. {row['name']}*\n"
            f"⭐ Rating: `{row['rating']:.2f}`\n"
            f"🎮 Genres: {row['Genres'] or 'N/A'}\n"
            f"📱 Platforms: {row['Platforms'] or 'N/A'}"
        )

        img_url = row.get("background_image", None)

        if pd.notna(img_url) and isinstance(img_url, str) and img_url.startswith("http"):
            try:
                await update.effective_message.reply_photo(
                    photo=img_url,
                    caption=caption,
                    parse_mode="Markdown",
                )
                continue
            except Exception:
                pass  # Fall back to text if image fails

        # Text-only fallback
        await update.effective_message.reply_text(caption, parse_mode="Markdown")

    # ── Follow-up prompt ─────────────────────────────────────────────────────────
    await update.effective_message.reply_text(
        "💬 Is there anything else you'd like to do?",
        reply_markup=build_followup_keyboard(),
    )


# ==========================================================
# SEND RANDOM GAMES  (with images if available)
# ==========================================================

async def send_random_games(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    platform: str,
):
    platform_label = platform if platform != "Any" else "all platforms"
    games = get_random_games(df, platform=platform, n=3)

    if games is None or games.empty:
        await update.effective_message.reply_text(
            f"⚠️ No games found for platform *{platform_label}*.",
            parse_mode="Markdown",
        )
        return

    await update.effective_message.reply_text(
        f"🎲 *3 Random Games* — {platform_label}\n"
        f"Here are your picks for today!",
        parse_mode="Markdown",
    )

    for i, (_, row) in enumerate(games.iterrows(), start=1):
        caption = (
            f"*{i}. {row['name']}*\n"
            f"⭐ Rating: `{row['rating']:.2f}`\n"
            f"🎮 Genres: {row['Genres'] or 'N/A'}\n"
            f"📱 Platforms: {row['Platforms'] or 'N/A'}"
        )

        img_url = row.get("background_image", None)

        if pd.notna(img_url) and isinstance(img_url, str) and img_url.startswith("http"):
            try:
                await update.effective_message.reply_photo(
                    photo=img_url,
                    caption=caption,
                    parse_mode="Markdown",
                )
                continue
            except Exception:
                pass

        await update.effective_message.reply_text(caption, parse_mode="Markdown")

    # Re-roll button + full follow-up
    await update.effective_message.reply_text(
        "💬 Want to roll again or do something else?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🎲 Roll again ({platform_label})", callback_data=f"rand|{platform}")],
            [
                InlineKeyboardButton("🔁 Recommend by game", callback_data="action|new_game"),
                InlineKeyboardButton("✅ I'm good, thanks!", callback_data="action|done"),
            ],
        ]),
    )


# ==========================================================
# /random  COMMAND
# ==========================================================

async def random_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲 *Random Game Discovery!*\n\n"
        "Pick a platform and I'll roll 3 random games for you:",
        parse_mode="Markdown",
        reply_markup=build_random_platform_keyboard(),
    )


# ==========================================================
# /start  COMMAND
# ==========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 *Welcome to Utopiaverse Bot!*\n\n"
        "Just send me a game title and I'll recommend 10 similar games with images.\n\n"
        "*Commands:*\n"
        "/random — 🎲 Roll 3 random games by platform\n"
        "/help   — How to use this bot\n\n"
        "*Examples:*\n"
        "• GTA V\n"
        "• Elden Ring\n"
        "• Minecraft\n"
        "• Cyberpunk 2077",
        parse_mode="Markdown",
    )


# ==========================================================
# /help  COMMAND
# ==========================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 *Help — Utopiaverse Bot*\n\n"
        "📩 *How to use:*\n"
        "1. Send any game title (e.g. _Red Dead Redemption 2_)\n"
        "2. Choose your platform filter from the buttons\n"
        "3. Get 10 recommended games with images!\n\n"
        "🎲 *Random mode:*\n"
        "Use /random to discover 3 surprise games on any platform.\n\n"
        "📌 *Commands:*\n"
        "/start  — Welcome message\n"
        "/random — Roll 3 random games by platform\n"
        "/help   — This help screen\n\n"
        "💡 Tip: Type part of a game name — the bot will find the closest match.",
        parse_mode="Markdown",
    )


# ==========================================================
# HANDLE PLAIN TEXT  →  ask for platform
# ==========================================================

async def handle_game_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game_name = update.message.text.strip()

    # Quick existence check
    matches = df[df["name"].str.lower() == game_name.lower()]
    if matches.empty:
        all_names       = df["name"].tolist()
        closest_matches = difflib.get_close_matches(game_name, all_names, n=1, cutoff=0.6)
        if not closest_matches:
            await update.message.reply_text(
                f"❌ Couldn't find a game matching *{game_name}*.\n"
                "Try checking the spelling or a different title.",
                parse_mode="Markdown",
            )
            return

    await update.message.reply_text(
        f"🕹️ Great choice! Now pick a *platform filter* for your recommendations:",
        parse_mode="Markdown",
        reply_markup=build_platform_keyboard(game_name),
    )


# ==========================================================
# HANDLE INLINE BUTTON CALLBACKS
# ==========================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # ── Random platform selection ───────────────────────────────────────────────
    if data.startswith("rand|"):
        platform = data.split("|", 1)[1]
        await query.edit_message_text(
            f"🎲 Rolling 3 random games for *{platform if platform != 'Any' else 'all platforms'}*…",
            parse_mode="Markdown",
        )
        await send_random_games(update, context, platform)

    # ── Platform selection ──────────────────────────────────────────────────────
    elif data.startswith("plat|"):
        _, platform, game_name = data.split("|", 2)

        await query.edit_message_text(
            f"🔮 Scanning the game universe for *{game_name}* on *{platform}*…",
            parse_mode="Markdown",
        )

        matched_game, recs = get_recommendations(
            game_name, df, feature_matrix, model,
            platform=platform, top_n=10,
        )

        if recs is None:
            await query.message.reply_text(f"⚠️ {matched_game}")
            return

        await send_recommendations(update, context, matched_game, recs, platform)

    # ── Follow-up actions ───────────────────────────────────────────────────────
    elif data.startswith("action|"):
        action = data.split("|", 1)[1]

        if action == "new_game":
            await query.message.reply_text(
                "🎮 Sure! Send me another game title and I'll find recommendations for you."
            )

        elif action == "random":
            await query.message.reply_text(
                "🎲 *Random Game Discovery!*\n\n"
                "Pick a platform and I'll roll 3 random games for you:",
                parse_mode="Markdown",
                reply_markup=build_random_platform_keyboard(),
            )

        elif action == "help":
            await query.message.reply_text(
                "🆘 *Help — Utopiaverse Bot*\n\n"
                "📩 *How to use:*\n"
                "1. Send any game title (e.g. _Red Dead Redemption 2_)\n"
                "2. Choose your platform filter from the buttons\n"
                "3. Get 10 recommended games with images!\n\n"
                "📌 *Commands:*\n"
                "/start — Welcome message\n"
                "/help  — This help screen\n\n"
                "💡 Tip: Type part of a game name — the bot will find the closest match.",
                parse_mode="Markdown",
            )

        elif action == "change_platform":
            # Recover the last game from context if stored, otherwise ask again
            last_game = context.user_data.get("last_game")
            if last_game:
                await query.message.reply_text(
                    f"🕹️ Choose a new platform filter for *{last_game}*:",
                    parse_mode="Markdown",
                    reply_markup=build_platform_keyboard(last_game),
                )
            else:
                await query.message.reply_text(
                    "Please send me a game title first, then I'll let you choose a platform."
                )

        elif action == "done":
            await query.message.reply_text(
                "🎉 Happy gaming! Come back anytime you want new recommendations. 🚀"
            )


# ==========================================================
# MAIN
# ==========================================================

def main():
    print("Starting Telegram bot...")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("help",   help_command))
    app.add_handler(CommandHandler("random", random_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_game_input))

    print("Bot is ready. Polling for messages…")
    app.run_polling()


if __name__ == "__main__":
    main()
