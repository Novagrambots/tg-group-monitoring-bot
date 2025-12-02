from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


class TaskScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()

    def start(self):
        """Запуск планировщика"""

        # Ежедневный отчет
        hour, minute = map(int, config.REPORT_TIME.split(':'))
        self.scheduler.add_job(
            send_daily_report,
            trigger=CronTrigger(hour=hour, minute=minute),
            args=[self.bot],
            id="daily_report"
        )

        self.scheduler.start()
        print(f"Планировщик запущен. Отчет будет отправляться в {config.REPORT_TIME}")

    async def shutdown(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()
        print("Планировщик остановлен")


from config import config
from handlers import send_daily_report
