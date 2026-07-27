"""
Scheduler per Pulse.
Genera briefing automaticamente ogni giorno alle 8:00 AM.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.agents.orchestrator import generate_briefing
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_scheduler = None


def _generate_daily_briefing():
    """Task: genera briefing alle 8 AM."""
    logger.info("🕐 Scheduler: generazione briefing delle 8 AM...")
    try:
        briefing = generate_briefing()
        logger.info(f"✅ Scheduler: generati {len(briefing)} articoli")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")


def start_scheduler():
    """Avvia lo scheduler in background."""
    global _scheduler
    
    if _scheduler is not None and _scheduler.running:
        logger.info("Scheduler già attivo")
        return
    
    _scheduler = BackgroundScheduler()
    
    # Ogni giorno alle 8:00 AM
    _scheduler.add_job(
        _generate_daily_briefing,
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_briefing",
        name="Generate daily briefing at 8 AM",
        replace_existing=True,
    )
    
    _scheduler.start()
    logger.info("⏰ Scheduler avviato — prossimo briefing alle 8:00 AM")


def stop_scheduler():
    """Ferma lo scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        logger.info("Scheduler fermato")


# Se eseguito direttamente, avvia subito
if __name__ == "__main__":
    start_scheduler()
    
    # Mantieni vivo
    import time
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop_scheduler()