"""Gunicorn configuration for Tagayev Methods (production).

Loaded by the systemd unit:
    gunicorn --config deploy/gunicorn.conf.py config.wsgi:application

Access/error logs go to stdout/stderr, which systemd captures in the journal
(``journalctl -u tagayev``). Tune workers via the GUNICORN_WORKERS env var —
the SQLite backend prefers a small pool to avoid write contention, so the
default is intentionally modest rather than the (2*CPU)+1 rule of thumb.
"""
import os

# Bind to a unix socket in the systemd RuntimeDirectory (/run/tagayev).
# nginx (www-data) reads it; see tagayev.service Group=www-data + umask below.
bind = os.environ.get("GUNICORN_BIND", "unix:/run/tagayev/gunicorn.sock")

workers = int(os.environ.get("GUNICORN_WORKERS", "3"))
worker_class = "sync"

# Socket created mode 0660 so the www-data nginx worker can read/write it.
umask = 0o007

# gunicorn 25+ opens a "control socket" for the `gunicornc` management tool. With
# no XDG_RUNTIME_DIR (systemd services don't get one), it defaults to
# $HOME/.gunicorn/gunicorn.ctl — but the unit sets ProtectHome=read-only, so that
# write fails with "Control server error: [Errno 30] Read-only file system". We
# don't use gunicornc, so turn the control socket off entirely.
control_socket_disable = True

timeout = 60
graceful_timeout = 30
keepalive = 5

# Recycle workers periodically to bound memory growth (Pillow/thumbnails).
max_requests = 1000
max_requests_jitter = 100

# "-" → stdout/stderr → journald.
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info")

proc_name = "tagayev"
