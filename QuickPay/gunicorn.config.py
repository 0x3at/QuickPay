from pathlib import Path
import multiprocessing

BASE_DIR = Path(__file__).resolve().parent.parent
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
workers = 1
timeout = 600
keepalive = 600
worker_class = "sync"
loglevel = "debug"
certfile = "/etc/ssl/certs/lifecorp_internal_crt.crt"
keyfile = "/etc/ssl/certs/lifecorp_internal_crt.key"
ca_certs = "/etc/ssl/certs/lifecorp_internal_crt_trusted_chain.crt"
