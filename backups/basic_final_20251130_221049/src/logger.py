import logging
import os

_configured = False

def _ensure_config():
    global _configured
    if _configured:
        return
    base = os.path.dirname(os.path.dirname(__file__))
    log_dir = os.path.join(base, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'app.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        handlers=[logging.FileHandler(log_file, encoding='utf-8')]
    )
    _configured = True

def get_logger(name: str) -> logging.Logger:
    _ensure_config()
    return logging.getLogger(name)