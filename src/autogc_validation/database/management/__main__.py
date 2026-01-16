# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 15:04:01 2026

@author: aengstrom
"""

# database/management/__main__.py
"""Command-line interface for database management."""

import argparse
import sys
import logging

from ..config import DatabaseConfig
from ...utils.logging_config import setup_logging
from .init_db import initialize_database


def main():
    parser = argparse.ArgumentParser(
        description='PAMS VOC Database Management',
        prog='python -m autogc_validation.database.management'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Management commands')
    
    # Initialize command
    init_parser = subparsers.add_parser('init', help='Initialize database')
    init_parser.add_argument(
        '--database', '-d',
        help='Database path (default: use config)'
    )
    init_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force reinitialization'
    )
    
    # Migrate command (for future)
    migrate_parser = subparsers.add_parser('migrate', help='Run migrations')
    migrate_parser.add_argument('--database', '-d')
    
    # Common arguments
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    setup_logging(log_level=log_level, log_to_console=True)
    
    # Get database path
    if hasattr(args, 'database') and args.database:
        db_path = args.database
    else:
        config = DatabaseConfig.from_env()
        db_path = str(config.path)
    
    # Execute command
    try:
        if args.command == 'init':
            initialize_database(db_path, force=args.force)
        elif args.command == 'migrate':
            print("Migrations not yet implemented")
        else:
            parser.print_help()
            return 1
    except Exception as e:
        logging.exception(f"Command failed: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())