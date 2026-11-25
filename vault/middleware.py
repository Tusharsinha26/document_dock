import os
import sqlite3
import threading
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command


_init_lock = threading.Lock()
_sqlite_initialized = False


class VercelSQLiteInitMiddleware:
    """
    Lazily initializes /tmp/db.sqlite3 on Vercel serverless cold starts when
    an external DATABASE_URL is not yet configured.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if os.environ.get('VERCEL') and not os.environ.get('DATABASE_URL', '').strip():
            self._ensure_tmp_sqlite_ready()
        return self.get_response(request)

    @staticmethod
    def _ensure_tmp_sqlite_ready():
        global _sqlite_initialized
        if _sqlite_initialized:
            return

        with _init_lock:
            if _sqlite_initialized:
                return

            db_path = Path('/tmp/db.sqlite3')
            needs_migrate = True
            if db_path.exists():
                try:
                    with sqlite3.connect(db_path) as conn:
                        row = conn.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name='auth_user'"
                        ).fetchone()
                        needs_migrate = row is None
                except sqlite3.Error:
                    needs_migrate = True

            if needs_migrate:
                call_command('migrate', verbosity=0, interactive=False)

            User = get_user_model()
            user, created = User.objects.get_or_create(
                username='demo_reviewer',
                defaults={
                    'first_name': 'Eleanor',
                    'last_name': 'Vance',
                    'email': 'eleanor.vance@documentdock.io',
                },
            )
            if created:
                user.set_unusable_password()
                user.save()

            _sqlite_initialized = True
