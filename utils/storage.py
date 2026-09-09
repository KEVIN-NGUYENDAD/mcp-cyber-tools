"""Atomic storage operations for concurrent state file access.

Provides safe JSON read/write with file locking and atomic transactions.
Prevents data corruption when multiple processes access state files.

Thread-safe and process-safe operations for production deployment.
"""

import json
import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple
from datetime import datetime

if sys.platform != 'win32':
    import fcntl
else:
    fcntl = None


class AtomicStorage:
    """Atomic JSON read/write with file locking and backups."""

    def __init__(self, state_dir: str = 'state', lock_timeout: int = 30):
        """Initialize atomic storage.

        Args:
            state_dir: Directory for state files (default: 'state')
            lock_timeout: Max seconds to wait for file lock (default: 30)
        """
        self.state_dir = Path(state_dir)
        self.lock_timeout = lock_timeout
        self._ensure_dir()
        self.locks = {}  # Track open file handles for cleanup

    def _ensure_dir(self):
        """Ensure state directory exists."""
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _get_lock_file(self, filename: str) -> Path:
        """Get lock file path for a state file."""
        return self.state_dir / f'.{filename}.lock'

    def _acquire_lock(self, lock_file: Path) -> Optional[Any]:
        """Acquire file lock with timeout.

        Returns:
            File handle if lock acquired, None if timeout
        """
        start_time = time.time()

        while True:
            try:
                if sys.platform == 'win32':
                    # Windows: use open with exclusive access
                    lock_handle = open(lock_file, 'w', encoding='utf-8')
                    try:
                        os.flock(lock_handle.fileno(), os.LOCK_EX | os.LOCK_NB)
                    except (OSError, AttributeError):
                        # If flock not available on Windows, just use file existence
                        lock_handle.close()
                        time.sleep(0.1)
                        if (time.time() - start_time) > self.lock_timeout:
                            return None
                        continue
                    return lock_handle
                else:
                    # Unix: use fcntl file locking
                    lock_handle = open(lock_file, 'w', encoding='utf-8')
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return lock_handle

            except (IOError, OSError) as e:
                elapsed = time.time() - start_time
                if elapsed > self.lock_timeout:
                    return None
                time.sleep(0.05)

    def _release_lock(self, lock_handle: Any):
        """Release file lock."""
        if lock_handle:
            try:
                if sys.platform != 'win32':
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
                lock_handle.close()
            except:
                pass

    def _create_backup(self, filepath: Path) -> Optional[Path]:
        """Create timestamped backup of existing file.

        Returns:
            Path to backup file, or None if file doesn't exist
        """
        if not filepath.exists():
            return None

        backup_dir = self.state_dir / '.backups'
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f'{filepath.stem}_{timestamp}.json'

        try:
            shutil.copy2(filepath, backup_path)
            return backup_path
        except Exception:
            return None

    def read_json(self, filename: str, default: Optional[Any] = None) -> Any:
        """Atomically read JSON file.

        Args:
            filename: File in state directory
            default: Value to return if file missing or invalid

        Returns:
            Parsed JSON, or default value
        """
        filepath = self.state_dir / filename
        lock_file = self._get_lock_file(filename)
        lock_handle = None

        try:
            lock_handle = self._acquire_lock(lock_file)
            if not lock_handle:
                # Lock timeout - return default
                return default if default is not None else {}

            if not filepath.exists():
                return default if default is not None else {}

            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)

        except (json.JSONDecodeError, IOError, OSError):
            # Corrupted or unreadable - return default
            return default if default is not None else {}
        finally:
            self._release_lock(lock_handle)

    def write_json(self, filename: str, data: Any, create_backup: bool = True) -> Tuple[bool, Optional[str]]:
        """Atomically write JSON file with backup and validation.

        Uses temp file + rename pattern to ensure atomicity:
        1. Write to temp file
        2. Validate JSON is readable
        3. Create backup of existing file
        4. Atomic rename temp → target

        Args:
            filename: File in state directory
            data: Data to write (must be JSON serializable)
            create_backup: Whether to backup existing file

        Returns:
            Tuple of (success: bool, error_msg: Optional[str])
        """
        filepath = self.state_dir / filename
        lock_file = self._get_lock_file(filename)
        lock_handle = None
        temp_file = None

        try:
            # Acquire lock
            lock_handle = self._acquire_lock(lock_file)
            if not lock_handle:
                return False, f'Lock timeout after {self.lock_timeout}s'

            # Write to temp file first
            try:
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=self.state_dir,
                    suffix='.tmp',
                    text=True
                )
                temp_file = temp_path

                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)

            except Exception as e:
                return False, f'Write to temp failed: {str(e)}'

            # Validate temp file is readable
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    json.load(f)
            except Exception as e:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                return False, f'JSON validation failed: {str(e)}'

            # Backup existing file
            backup_path = None
            if create_backup and filepath.exists():
                backup_path = self._create_backup(filepath)

            # Atomic rename
            try:
                if sys.platform == 'win32':
                    # Windows requires removing target first
                    if filepath.exists():
                        os.replace(temp_file, filepath)
                    else:
                        shutil.move(temp_file, filepath)
                else:
                    os.replace(temp_file, filepath)

                return True, None

            except Exception as e:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                return False, f'Rename failed: {str(e)}'

        finally:
            self._release_lock(lock_handle)

    def read_and_modify(self, filename: str, modifier_func, default: Optional[Any] = None) -> Tuple[bool, Any, Optional[str]]:
        """Read file, apply modifier function, atomically write result.

        Useful for updates like appending to list, incrementing counters, etc.

        Args:
            filename: File in state directory
            modifier_func: Function(data) -> modified_data
            default: Initial value if file missing

        Returns:
            Tuple of (success: bool, result: Any, error_msg: Optional[str])
        """
        lock_file = self._get_lock_file(filename)
        lock_handle = None

        try:
            # Single lock for read + write
            lock_handle = self._acquire_lock(lock_file)
            if not lock_handle:
                return False, None, f'Lock timeout after {self.lock_timeout}s'

            # Read
            filepath = self.state_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    data = default if default is not None else {}
            else:
                data = default if default is not None else {}

            # Modify
            try:
                modified = modifier_func(data)
            except Exception as e:
                return False, None, f'Modifier failed: {str(e)}'

            # Write (reuse atomic write logic)
            success, error = self.write_json(filename, modified, create_backup=True)
            if success:
                return True, modified, None
            else:
                return False, None, error

        finally:
            self._release_lock(lock_handle)

    def append_to_list(self, filename: str, item: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Append item to JSON array file.

        Args:
            filename: File in state directory (should contain list)
            item: Object to append

        Returns:
            Tuple of (success: bool, error_msg: Optional[str])
        """
        def append_func(data):
            if not isinstance(data, list):
                data = []
            data.append(item)
            return data

        success, _, error = self.read_and_modify(filename, append_func, default=[])
        return success, error

    def update_field(self, filename: str, field_path: str, value: Any) -> Tuple[bool, Optional[str]]:
        """Update single field in JSON object (supports dot notation).

        Examples:
            update_field('config.json', 'database.host', 'localhost')
            update_field('status.json', 'timestamp', datetime.now().isoformat())

        Args:
            filename: File in state directory
            field_path: Dot-separated path (e.g., 'database.host')
            value: Value to set

        Returns:
            Tuple of (success: bool, error_msg: Optional[str])
        """
        def update_func(data):
            if not isinstance(data, dict):
                data = {}

            keys = field_path.split('.')
            current = data

            # Navigate/create nested structure
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Set final value
            current[keys[-1]] = value
            return data

        success, _, error = self.read_and_modify(filename, update_func, default={})
        return success, error

    def get_field(self, filename: str, field_path: str, default: Optional[Any] = None) -> Any:
        """Get single field from JSON object (supports dot notation).

        Args:
            filename: File in state directory
            field_path: Dot-separated path
            default: Value if path not found

        Returns:
            Field value or default
        """
        data = self.read_json(filename, default={})

        if not isinstance(data, dict):
            return default

        keys = field_path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def list_files(self, pattern: str = '*.json') -> List[str]:
        """List state files matching pattern.

        Args:
            pattern: Glob pattern (default: all .json files)

        Returns:
            List of filenames
        """
        return [f.name for f in self.state_dir.glob(pattern) if not f.name.startswith('.')]

    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get file metadata (size, modified time, exists).

        Args:
            filename: File in state directory

        Returns:
            Dict with 'exists', 'size', 'modified' keys, or None
        """
        filepath = self.state_dir / filename

        if not filepath.exists():
            return {'exists': False}

        try:
            stat = filepath.stat()
            return {
                'exists': True,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'path': str(filepath)
            }
        except Exception:
            return None


# Singleton instance for convenience
_storage = None

def get_storage(state_dir: str = 'state') -> AtomicStorage:
    """Get or create singleton storage instance.

    Args:
        state_dir: State directory (only used on first call)

    Returns:
        AtomicStorage instance
    """
    global _storage
    if _storage is None:
        _storage = AtomicStorage(state_dir=state_dir)
    return _storage
