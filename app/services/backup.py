"""
Automatic Backup System for EU Trip Tracker
Provides automated database backups with configurable retention
"""
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


def get_backup_dir():
    """Get or create backup directory (persistent)."""
    # Prefer BACKUP_DIR env, else co-locate under DB directory
    backup_dir_env = os.getenv('BACKUP_DIR')
    if backup_dir_env:
        backup_dir = Path(backup_dir_env).expanduser().resolve()
    else:
        db_path = os.getenv('DATABASE_PATH', str(Path(__file__).resolve().parents[2] / 'data' / 'eu_tracker.db'))
        backup_dir = Path(db_path).resolve().parent / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def create_backup(database_path, reason='manual'):
    """
    Create a backup of the SQLite database
    
    Args:
        database_path: Path to the SQLite database file
        reason: Reason for backup ('manual', 'auto', 'shutdown', etc.)
    
    Returns:
        dict with success status and backup file path
    """
    try:
        if not os.path.exists(database_path):
            return {'success': False, 'error': 'Database file not found'}
        
        backup_dir = get_backup_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"eu_tracker_backup_{timestamp}_{reason}.db"
        backup_path = backup_dir / backup_filename
        
        # Use SQLite backup API for safe backup
        source_conn = sqlite3.connect(database_path)
        backup_conn = sqlite3.connect(str(backup_path))
        
        with backup_conn:
            source_conn.backup(backup_conn)
        
        source_conn.close()
        backup_conn.close()
        
        # Verify backup was created
        if not backup_path.exists():
            return {'success': False, 'error': 'Backup file was not created'}
        
        backup_size = backup_path.stat().st_size
        
        return {
            'success': True,
            'backup_path': str(backup_path),
            'backup_filename': backup_filename,
            'size_bytes': backup_size,
            'timestamp': timestamp,
            'reason': reason
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def cleanup_old_backups(max_backups=30, max_age_days=90):
    """
    Clean up old backup files
    
    Args:
        max_backups: Maximum number of backups to keep
        max_age_days: Maximum age of backups in days
    
    Returns:
        dict with cleanup statistics
    """
    try:
        backup_dir = get_backup_dir()
        backup_files = sorted(
            backup_dir.glob('eu_tracker_backup_*.db'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        deleted_count = 0
        deleted_size = 0
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        # Delete backups beyond max_backups limit
        for backup_file in backup_files[max_backups:]:
            file_size = backup_file.stat().st_size
            backup_file.unlink()
            deleted_count += 1
            deleted_size += file_size
        
        # Delete backups older than max_age_days
        for backup_file in backup_dir.glob('eu_tracker_backup_*.db'):
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                file_size = backup_file.stat().st_size
                backup_file.unlink()
                deleted_count += 1
                deleted_size += file_size
        
        remaining_backups = len(list(backup_dir.glob('eu_tracker_backup_*.db')))
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'deleted_size_bytes': deleted_size,
            'remaining_backups': remaining_backups
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def list_backups():
    """
    List all available backups
    
    Returns:
        list of backup info dictionaries
    """
    try:
        backup_dir = get_backup_dir()
        backup_files = sorted(
            backup_dir.glob('eu_tracker_backup_*.db'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        backups = []
        for backup_file in backup_files:
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'path': str(backup_file),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created_at': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'age_days': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
            })
        
        return {'success': True, 'backups': backups, 'count': len(backups)}
        
    except Exception as e:
        return {'success': False, 'error': str(e), 'backups': [], 'count': 0}


def restore_backup(backup_filename, database_path):
    """
    Restore a database from backup
    
    Args:
        backup_filename: Name of backup file to restore
        database_path: Path to current database file
    
    Returns:
        dict with success status
    """
    try:
        backup_dir = get_backup_dir()
        backup_path = backup_dir / backup_filename
        
        if not backup_path.exists():
            return {'success': False, 'error': 'Backup file not found'}
        
        # Create a safety backup of current database before restoring
        safety_backup = create_backup(database_path, reason='pre_restore')
        if not safety_backup['success']:
            return {'success': False, 'error': 'Could not create safety backup'}
        
        # Copy backup to database location
        shutil.copy2(backup_path, database_path)
        
        return {
            'success': True,
            'restored_from': backup_filename,
            'safety_backup': safety_backup['backup_filename']
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_last_backup_info(database_path):
    """Get information about the most recent backup"""
    backups = list_backups()
    if backups['success'] and backups['count'] > 0:
        return backups['backups'][0]
    return None


def auto_backup_if_needed(database_path, min_hours_between=24):
    """
    Automatically create backup if enough time has passed since last backup
    
    Args:
        database_path: Path to database file
        min_hours_between: Minimum hours between automatic backups
    
    Returns:
        dict with backup status
    """
    try:
        last_backup = get_last_backup_info(database_path)
        
        if last_backup is None:
            # No backups exist, create one
            return create_backup(database_path, reason='auto')
        
        # Parse last backup timestamp
        last_backup_time = datetime.strptime(last_backup['created_at'], '%Y-%m-%d %H:%M:%S')
        hours_since_backup = (datetime.now() - last_backup_time).total_seconds() / 3600
        
        if hours_since_backup >= min_hours_between:
            # Time for a new backup
            result = create_backup(database_path, reason='auto')
            if result['success']:
                # Clean up old backups
                cleanup_old_backups()
            return result
        else:
            return {
                'success': True,
                'skipped': True,
                'reason': f'Last backup was {round(hours_since_backup, 1)} hours ago',
                'next_backup_in_hours': round(min_hours_between - hours_since_backup, 1)
            }
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

