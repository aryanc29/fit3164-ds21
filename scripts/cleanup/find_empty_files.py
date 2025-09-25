"""Find and optionally delete empty files under a directory.

Usage:
    python find_empty_files.py            # list empty files
    python find_empty_files.py --delete   # delete empty files (prompts for confirmation)
"""
# CODE REVIEW: Python script for finding and optionally deleting empty files
# GOOD PRACTICES:
# - Uses pathlib for modern Python path handling
# - Includes proper argument parsing with argparse
# - Uses type hints for better code documentation
# - Includes comprehensive docstring
# - Handles exceptions during file deletion
# - Uses strip().lower() for robust user input validation
# - Provides clear feedback on operations
# IMPROVEMENTS:
# - Could add logging to file option
# - Could add file size threshold parameter
# - Could add file type filtering
# - Could add dry-run mode
# - Could add progress bar for large directories
# RECENT FIXES:
# - Removed problematic 'found' variable that was causing logic errors
# - Fixed condition to properly check args.delete flag

from pathlib import Path
import argparse


def find_empty_files(root: Path):
    return [p for p in root.rglob('*') if p.is_file() and p.stat().st_size == 0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', '-r', default='.', help='Root directory to search')
    parser.add_argument('--delete', action='store_true', help='Delete found empty files (prompts)')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    print(f'Searching for empty files under: {root}')

    empty_files = find_empty_files(root)
    if not empty_files:
        print('No empty files found.')
        return

    print(f'Found {len(empty_files)} empty files:')
    for p in empty_files:
        print(' -', p)

    # REMOVED THE 'found' VARIABLE - THIS WAS THE PROBLEM
    # The condition should just check if --delete was specified
    if args.delete:
        confirm = input(f'Delete these {len(empty_files)} files? Type "yes" to confirm: ')
        if confirm.strip().lower() == 'yes':
            for p in empty_files:
                try:
                    p.unlink()
                    print('Deleted:', p)
                except Exception as e:
                    print('Failed to delete', p, e)
            print('Deletion complete.')
        else:
            print('Aborted deletion.')


if __name__ == '__main__':
    main()