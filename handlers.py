import logging
from aiogram import Bot
from aiogram.types import ChatMemberUpdated
from database import db
from config import config

logger = logging.getLogger(__name__)


async def on_chat_member_update(update: ChatMemberUpdated, bot: Bot):
    """
    Обработчик событий вступления/выхода пользователей
    """
    try:
        user = update.new_chat_member.user
        telegram_id = user.id
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = user.username

        old_status = update.old_chat_member.status
        new_status = update.new_chat_member.status

        print(f"📊 Статус изменился: {old_status} -> {new_status} для {full_name}")

        # Вступление в группу
        if new_status == "member":
            if old_status in ["left", "kicked", "restricted"]:
                await db.add_user(telegram_id, full_name, username)
                print(f"✅ {full_name} вступил в группу")

        # Выход из группы
        elif new_status in ["left", "kicked"]:
            if old_status == "member":
                user_record = await db.user_left(telegram_id)
                if user_record:
                    hours = user_record.duration_in_group / 3600 if user_record.duration_in_group else 0
                    print(f"❌ {full_name} вышел. Был в группе {hours:.2f} часов")

    except Exception as e:
        logger.error(f"Ошибка обработки события: {e}")


def format_daily_report(stats: dict) -> str:
    """Форматирование ежедневного отчета"""
    date_str = stats['date'].strftime("%d.%m.%Y")

    report = f"""
📊 {date_str} dan kundalik hisobot
━━━━━━━━━━━━━━━━━━━━

👥 Umumiy statistika:
├ Bugun guruhga qo'shilganlar: {stats['total_joins']}
├ Bugun guruhdan chiqqanlar: {stats['left_today']}
└ Hozir guruhda bo'lganlar: {stats['in_group']}

📈 Soatlik statistika:
├ Eng ko'p qo'shilgan soat: {stats['max_hour']['hour']}:00 – ({stats['max_hour']['joins']} ta)
└ Eng kam qo'shilgan soat: {stats['min_hour']['hour']}:00 – ({stats['min_hour']['joins']} ta)

━━━━━━━━━━━━━━━━━━━━
ℹ️ Telegram guruhi monitoring boti
"""
    return report


async def send_daily_report(bot: Bot):
    """Отправка ежедневного отчета"""
    try:
        if not config.ADMIN_ID:
            logger.warning("ADMIN_ID не задан")
            return

        stats = await db.get_daily_stats()
        report = format_daily_report(stats)

        await bot.send_message(
            chat_id=config.ADMIN_ID,
            text=report
        )

        logger.info(f"Отчет отправлен администратору {config.ADMIN_ID}")

    except Exception as e:
        logger.error(f"Ошибка отправки отчета: {e}")


def register_handlers(dp):
    """Регистрация обработчиков"""
    dp.chat_member.register(on_chat_member_update)
