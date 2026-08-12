import asyncio
import logging
import re
from typing import List

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from bradescard_api import BradesAPI
from config import TELEGRAM_BOT_TOKEN, MAX_TARJETAS_PER_REQUEST, WORKER_LIMIT, is_allowed_user
from encryption import encriptar_tarjeta
from queue_manager import UserConcurrencyManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


async def procesar_tarjeta(tarjeta: str) -> str:
    encrypted = encriptar_tarjeta(tarjeta)
    data = await BradesAPI.filter_card(encrypted)
    if is_valid_filter_response(data or {}, 200 if data is not None else 500):
        return f"✅ {tarjeta}"
    return f"❌ {tarjeta}"


async def process_filter_batch(user_id: int, tarjetas: List[str]) -> List[str]:
    results: List[str] = []
    for tarjeta in tarjetas:
        valido, limpio = validar_tarjeta(tarjeta)
        if not valido:
            results.append(f"❌ {tarjeta}")
            continue
        results.append(await procesar_tarjeta(limpio))
    return results


async def filtrar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if not is_allowed_user(user_id):
        await update.message.reply_text("❌ No tienes permiso para usar este bot.")
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

    await update.message.reply_text(f"⏳ Revisando {len(tarjetas)} tarjeta(s)...")

    try:
        async with queue_manager.global_guard():
            async with queue_manager.user_guard(user_id):
                resultados = await process_filter_batch(user_id, tarjetas)
    except Exception as exc:
        logger.exception("Error en /filtrar")
        await update.message.reply_text(f"❌ Error interno: {exc}")
        return

    out = "\n".join(resultados)
    await update.message.reply_text(out)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Bot activo.")


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en el entorno")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("filtrar", filtrar))
    app.add_handler(CommandHandler("status", status))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
