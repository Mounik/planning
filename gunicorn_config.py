"""
Configuration Gunicorn pour le déploiement en production
"""

import os
import multiprocessing

# Configuration du serveur
bind = "127.0.0.1:5000"
workers = min(4, (multiprocessing.cpu_count() * 2) + 1)
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50

# Configuration de sécurité
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Configuration des logs
accesslog = "data/access.log"
errorlog = "data/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Configuration des processus
preload_app = True
daemon = False
pidfile = "data/gunicorn.pid"
tmp_upload_dir = None

# Configuration SSL (si nécessaire)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Variables d'environnement
raw_env = [
    'DEBUG=false',
    'SECURITY_HEADERS=true',
    'SESSION_COOKIE_SECURE=false',  # Mettre à true avec HTTPS
    'FORCE_HTTPS=false',  # Mettre à true en production avec HTTPS
]

# Gestion des signaux
def when_ready(server):
    """Appelée quand le serveur est prêt"""
    print("🚀 Serveur Gunicorn prêt")

def worker_int(worker):
    """Appelée lors de l'interruption d'un worker"""
    print(f"⚠️  Worker {worker.pid} interrompu")

def post_fork(server, worker):
    """Appelée après le fork d'un worker"""
    print(f"📍 Worker {worker.pid} démarré")

def pre_exec(server):
    """Appelée avant l'exécution"""
    print("🔧 Configuration Gunicorn chargée")