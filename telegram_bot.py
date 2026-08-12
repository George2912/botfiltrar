import asyncio
import logging
import re
from typing import List

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from bradescard_api import BradesAPI
from config import TELEGRAM_BOT_TOKEN, MAX_TARJETAS_PER_REQUEST, WORKER_LIMIT, is_allowed_user
from encryption import encriptar_tarjeta
from queue_manager import UserConcurrencyManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

unauthorized_attempts = {}
queue_manager = UserConcurrencyManager(max_global_workers=WORKER_LIMIT)


def limpiar_tarjeta(raw: str) -> str:
    return re.sub(r"[^0-9]", "", raw)


def validar_tarjeta(raw: str):
    limpio = limpiar_tarjeta(raw)
    if len(limpio) != 16 or not limpio.isdigit():
        return False, ""
    return True, limpio


def is_valid_filter_response(data: dict, status: int) -> bool:
    if status != 200 or not data:
        return False

    description = str(data.get("description", "")).lower()
    if description == "ok":
        return True

    if "no esta dada de alta" in description:
        return False

    if data.get("code") == 2:
        return False

    if data.get("code") == 0 and description == "ok":
        return True

    return False


async def procesar_tarjeta(tarjeta: str) -> bool:
    encrypted = encriptar_tarjeta(tarjeta)
    data = await BradesAPI.filter_card(encrypted)
    return is_valid_filter_response(data or {}, 200 if data is not None else 500)


def build_progress_message(tarjetas: List[str], estados: List[str]) -> str:
    lines = []
    for idx, tarjeta in enumerate(tarjetas):
        lines.append(f"{estados[idx]} {tarjeta}")
    return "\n".join(lines)


async def process_filter_batch_live(user_id: int, tarjetas: List[str], progress_message) -> List[str]:
    estados = ["⏳" for _ in tarjetas]
    await progress_message.edit_text(build_progress_message(tarjetas, estados))

    resultados: List[str] = []
    for idx, tarjeta in enumerate(tarjetas):
        valido, limpio = validar_tarjeta(tarjeta)
        if not valido:
            estados[idx] = "❌"
            await progress_message.edit_text(build_progress_message(tarjetas, estados))
            resultados.append(f"❌ {tarjeta}")
            continue

        estados[idx] = "⏳"
        await progress_message.edit_text(build_progress_message(tarjetas, estados))

        ok = await procesar_tarjeta(limpio)
        if ok:
            estados[idx] = "✅"
            resultados.append(f"✅ {limpio}")
        else:
            estados[idx] = "❌"
            resultados.append(f"❌ {limpio}")

        await progress_message.edit_text(build_progress_message(tarjetas, estados))

    aprobadas = [item.replace("✅ ", "").strip() for item in resultados if item.startswith("✅")]
    if aprobadas:
        final_text = "✅ Tarjetas aprobadas:\n\n" + "\n".join(aprobadas)
        await progress_message.edit_text(final_text)
        return aprobadas

    await progress_message.edit_text("❌ No se encontraron tarjetas aprobadas.")
    return []


async def handle_unauthorized_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "amigo"
    attempts = unauthorized_attempts.get(user_id, 0) + 1
    unauthorized_attempts[user_id] = attempts

    logger.warning(f"Usuario no autorizado intentó interactuar: {user_id} ({user_name}) intento #{attempts}")

    if attempts == 1:
        await update.message.reply_text(
            f"❌ {user_name}, no estás en la lista de usuarios permitidos. "
            "Sal del bot y no vuelvas a molestar, aquí no entra cualquiera."
        )
        return

    if attempts == 2:
        await update.message.reply_text(
            f"❌ {user_name}, ya te avisé. Sigue intentando y te ignoro."
        )
        return

    # Tercera vez en adelante: silencio total para evitar spam.
    logger.warning(f"Ignorando usuario no autorizado por spam: {user_id} ({user_name})")
    return


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_allowed_user(user_id):
        await handle_unauthorized_user(update, context)
        return

    await update.message.reply_text(
        "✅ Bienvenido. Puedes usar /filtrar con tarjetas separadas por espacio."
    )


async def filtrar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if not is_allowed_user(user_id):
        await handle_unauthorized_user(update, context)
        return

    if not context.args:
        await update.message.reply_text("Uso: /filtrar 4766841234567890 4444333322221111")
        return

    tarjetas = [arg.strip() for arg in context.args if arg.strip()]
    if not tarjetas:
        await update.message.reply_text("❌ No se recibieron tarjetas válidas.")
        return

    if len(tarjetas) > MAX_TARJETAS_PER_REQUEST:
        await update.message.reply_text(f"❌ Máximo {MAX_TARJETAS_PER_REQUEST} tarjetas por lote.")
        return

    status_message = await update.message.reply_text(f"⏳ Revisando {len(tarjetas)} tarjeta(s)...")

    try:
        async with queue_manager.global_guard():
            async with queue_manager.user_guard(user_id):
                resultados = await process_filter_batch_live(user_id, tarjetas, status_message)
    except Exception as exc:
        logger.exception("Error en /filtrar")
        await status_message.edit_text(f"❌ Error interno: {exc}")
        return

    if not resultados:
        await status_message.edit_text("❌ No se encontraron tarjetas aprobadas.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Bot activo.")


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en el entorno")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("filtrar", filtrar))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.ALL, handle_unauthorized_user))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
