# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 15:25:50 2026

@author: aengstrom
"""
import logging
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    This is the recommended way to get loggers in application code.
    
    Args:
        name: Usually __name__ of the calling module
    
    Returns:
        Logger instance
    
    Example:
        from pams_voc.utils.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("This is a log message")
    """
    return logging.getLogger(name)