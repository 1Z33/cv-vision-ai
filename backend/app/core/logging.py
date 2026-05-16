"""
Configuration du logging structuré pour l'application.
"""

import logging
import sys
from typing import Any


def setup_logging() -> logging.Logger:
    """
    Configure le logger principal de l'application.
    
    Returns:
        Logger configuré
    """
    logger = logging.getLogger("cv_vision_ai")
    logger.setLevel(logging.INFO)
    
    # Handler console
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    # Format simple et lisible
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger


# Logger global
logger = setup_logging()