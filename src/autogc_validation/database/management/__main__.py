# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 15:04:01 2026

@author: aengstrom
"""

"""Command-line interface for database management."""

import argparse
import sys
import logging

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
        required=True,
        help='Database path'
    )
    init_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force reinitialization'
    )

    # Common arguments
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Execute command
    try:
        if args.command == 'init':
            initialize_database(args.database, force=args.force)
        else:
            parser.print_help()
            return 1
    except Exception as e:
        logging.exception(f"Command failed: {e}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
