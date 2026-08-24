"""Production-hardening checks for ``config.settings``.

The security block in settings.py only activates when ``DEBUG=False``. Django's
test runner forces ``DEBUG=False`` *after* settings import, so the block is never
exercised by the in-process test suite. These tests therefore spawn a child
``manage.py`` with the production environment to assert the real behaviour:

* ``check --deploy`` reports zero security issues, and
* the fail-fast guards reject the insecure dev SECRET_KEY / wildcard hosts.
"""
import os
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase

# A throwaway but non-"insecure" key so the SECRET_KEY guard passes.
_STRONG_KEY = "test-only-strong-key-" + "z" * 50

PROD_ENV = {
    "DEBUG": "False",
    "SECRET_KEY": _STRONG_KEY,
    "ALLOWED_HOSTS": "tagayev.uz,www.tagayev.uz",
}


def _run_manage(args, extra_env):
    """Run ``manage.py <args>`` in a child process with a production-like env."""
    env = dict(os.environ)
    env.update(extra_env)
    # The error messages contain U+02BB; force UTF-8 so capture never fails on
    # a cp1251 Windows console.
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(settings.BASE_DIR / "manage.py"), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(settings.BASE_DIR),
    )


class DeployHardeningTests(SimpleTestCase):
    def test_deploy_check_is_clean_in_production(self):
        proc = _run_manage(["check", "--deploy"], PROD_ENV)
        combined = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, msg=combined)
        # The four HTTPS warnings Django raises without our hardening block.
        for code in ("W004", "W008", "W012", "W016"):
            self.assertNotIn(code, combined, msg=f"{code} still raised:\n{combined}")

    def test_insecure_secret_key_is_rejected(self):
        proc = _run_manage(
            ["check"],
            {**PROD_ENV, "SECRET_KEY": "django-insecure-dev-only-key"},
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("SECRET_KEY", proc.stderr)

    def test_wildcard_allowed_hosts_is_rejected(self):
        proc = _run_manage(["check"], {**PROD_ENV, "ALLOWED_HOSTS": "*"})
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ALLOWED_HOSTS", proc.stderr)

    def test_debug_dev_keeps_http_cookies(self):
        """Sanity: with DEBUG=True the secure-cookie flags stay off (dev http)."""
        self.assertFalse(getattr(settings, "SESSION_COOKIE_SECURE", False))
        self.assertFalse(getattr(settings, "CSRF_COOKIE_SECURE", False))
