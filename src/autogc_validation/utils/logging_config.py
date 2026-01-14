# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 15:25:50 2026

@author: aengstrom
"""
import logging
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    
    Args:
        name: Usually __name__ of the calling module
    
    Returns:
        Logger instance
    
    """
    return logging.getLogger(name)