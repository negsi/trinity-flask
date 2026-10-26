"""Background Schedule Runner Module.

Periodically polls for due agent schedules and executes them within the Flask
application context using APScheduler.
"""

from datetime import datetime, timezone
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from app.domain.repositories.schedule_repository import ScheduleRepository
from app.services.schedule.schedule_service import ScheduleService

logger = logging.getLogger(__name__)


class ScheduleRunner:
    """Manages periodic background polling and execution of due schedules."""

    def __init__(
        self,
        schedule_repo: ScheduleRepository,
        schedule_service: ScheduleService,
        poll_interval_seconds: int = 30,
    ) -> None:
        self.schedule_repo = schedule_repo
        self.schedule_service = schedule_service
        self.poll_interval_seconds = poll_interval_seconds
        self._scheduler: BackgroundScheduler | None = None
        self._app: Flask | None = None

    def init_app(self, app: Flask) -> None:
        """Binds the Flask application instance for application context execution."""
        self._app = app

    def tick(self) -> int:
        """Checks for due schedules and executes them sequentially.

        Returns:
            int: Number of executed schedules during this tick.
        """
        if self._app is not None:
            with self._app.app_context():
                return self._process_due_schedules()
        return self._process_due_schedules()

    def _process_due_schedules(self) -> int:
        now = datetime.now(timezone.utc)
        due_schedules = self.schedule_repo.get_due_schedules(now)
        executed_count = 0

        for schedule in due_schedules:
            try:
                logger.info(
                    "Triggering due schedule '%s' (ID: %s) for agent '%s'.",
                    schedule.name,
                    schedule.id,
                    schedule.agent_id,
                )
                self.schedule_service.execute_schedule(
                    schedule_id=schedule.id, manual_trigger=False
                )
                executed_count += 1
            except Exception as exc:
                logger.error(
                    "Unexpected error executing due schedule '%s': %s",
                    schedule.id,
                    exc,
                    exc_info=True,
                )

        return executed_count

    def start_background(self, app: Flask | None = None) -> None:
        """Starts the non-blocking APScheduler BackgroundScheduler."""
        if app is not None:
            self.init_app(app)

        if self._scheduler and self._scheduler.running:
            logger.debug("ScheduleRunner background scheduler is already running.")
            return

        self._scheduler = BackgroundScheduler(timezone=timezone.utc)
        self._scheduler.add_job(
            func=self.tick,
            trigger="interval",
            seconds=self.poll_interval_seconds,
            id="trinity_schedule_poller",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.start()
        logger.info(
            "ScheduleRunner started in background (poll interval: %ds).",
            self.poll_interval_seconds,
        )

    def stop_background(self) -> None:
        """Gracefully stops the background scheduler if running."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("ScheduleRunner background scheduler stopped.")

    def run_blocking(self, app: Flask | None = None) -> None:
        """Runs the scheduler loop in the foreground (used by CLI worker)."""
        self.start_background(app=app)
        logger.info("ScheduleRunner CLI worker running. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.stop_background()
