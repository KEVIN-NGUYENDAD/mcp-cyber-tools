#!/usr/bin/env python3
"""
State Manager: Atomic write and safe read operations for concurrent file access.
Addresses TD-L3-001, TD-L3-002, TD-L3-003 race condition vulnerabilities.

Implements atomic write pattern using temporary files + os.replace() for POSIX-compliant
file system atomicity. Prevents JSON corruption from concurrent writes to state files.
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


def write_state_atomic(
    file_path: str,
    data: Any,
    indent: int = 2,
    timeout: float = 5.0,
    max_retries: int = 3
) -> None:
    """
    Write state data atomically to file using temporary file + os.replace().

    This pattern prevents JSON corruption from concurrent writes by:
    1. Writing to a temporary file on same filesystem
    2. Using os.replace() which is atomic at OS level
    3. Cleaning up temp file on error
    4. Retry mechanism for Windows file locking issues

    Args:
        file_path: Target state file path (e.g., state/incidents.json)
        data: Python object to serialize to JSON
        indent: JSON indentation level (default 2)
        timeout: Operation timeout in seconds (for future file locking)
        max_retries: Number of retries on file access errors (default 3)

    Returns:
        None

    Raises:
        IOError: If temp file creation or replacement fails after retries
        json.JSONEncodeError: If data is not JSON serializable

    Example:
        write_state_atomic('state/incidents.json', {'incidents': []})
    """
    import time
    file_path = Path(file_path)

    # AQ-040. Đóng dấu lần chạy ngay tại chỗ ghi, không ở từng script.
    #
    # 40 script ghi state qua hàm này. Sửa từng script là cách đã chứng minh
    # không scale ở AQ-014: một lần đổi khoá làm hỏng năm consumer và Builder
    # sửa được một. Ở đây có đúng một cửa ra, nên dấu lần chạy đặt ở cửa đó.
    #
    # `stamp()` không ghi đè `run_id` đã có, nên một payload cố ý mang lần chạy
    # khác vẫn giữ nguyên.
    try:
        import run_context
        data = run_context.stamp(data)
    except ImportError:
        # state_manager được import từ nhiều thư mục; thiếu run_context thì ghi
        # state vẫn phải chạy — mất dấu lần chạy, không mất dữ liệu.
        pass

    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        last_error = None
        for attempt in range(max_retries):
            temp_fd = None
            temp_path = None

            try:
                # Create temp file in same directory (ensures same filesystem)
                # This is critical for os.replace() atomicity on Windows and POSIX
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=str(file_path.parent),
                    prefix=f".{file_path.name}.",
                    suffix=".tmp"
                )

                # Write JSON data to temp file
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=indent)
                    temp_fd = None  # fdopen takes ownership, don't close again

                # Atomic replacement - this is the critical operation
                # On Windows: ReplaceFileW (via os.replace), on POSIX: rename() with overwrite
                os.replace(temp_path, str(file_path))
                logger.debug(f"[ATOMIC] Successfully wrote {file_path} (atomic, attempt {attempt + 1})")
                return

            except (OSError, PermissionError) as e:
                # Handle Windows file locking: retry with backoff
                last_error = e
                if attempt < max_retries - 1 and ("Access is denied" in str(e) or "Permission denied" in str(e)):
                    backoff = 0.001 * (2 ** attempt)  # Exponential backoff: 1ms, 2ms, 4ms
                    logger.debug(f"[RETRY] Atomic write attempt {attempt + 1} failed (Access denied), retrying in {backoff*1000:.1f}ms")
                    time.sleep(backoff)
                    continue

                # If not retryable, raise immediately
                raise

            except Exception as e:
                # JSON serialization or other errors - don't retry
                logger.error(f"[ERROR] Write failed (not retryable): {e}")
                raise IOError(f"Failed to write {file_path} atomically: {e}") from e

            finally:
                # Cleanup temp file if it still exists and wasn't closed properly
                if temp_path and os.path.exists(temp_path):
                    try:
                        if temp_fd is not None:
                            os.close(temp_fd)
                        os.remove(temp_path)
                        logger.debug(f"[CLEANUP] Removed temp file {temp_path}")
                    except Exception as cleanup_err:
                        logger.warning(f"[CLEANUP] Failed to cleanup temp {temp_path}: {cleanup_err}")

        # If we exhausted retries, raise the last error
        raise IOError(f"Failed to write {file_path} after {max_retries} attempts: {last_error}")

    except Exception as e:
        logger.error(f"[ERROR] Atomic write to {file_path} failed: {e}")
        raise


def read_state_safe(
    file_path: str,
    default_factory: Optional[Callable[[], Any]] = None
) -> Any:
    """
    Read state file safely with error handling and validation.

    Returns default value if file doesn't exist or is corrupted.
    Logs all errors for debugging.

    Args:
        file_path: State file path to read
        default_factory: Callable returning default value if read fails
                        (default: dict if not specified)

    Returns:
        Parsed JSON data, or default_factory() result on error

    Example:
        incidents = read_state_safe('state/incidents.json', lambda: {'total': 0})
    """
    file_path = Path(file_path)

    if default_factory is None:
        default_factory = dict

    try:
        if not file_path.exists():
            logger.debug(f"[READ] File not found: {file_path}, returning default")
            return default_factory()

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.debug(f"[READ] Successfully read {file_path}")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"[CORRUPT] JSON decode error in {file_path}: {e}")
        return default_factory()

    except Exception as e:
        logger.error(f"[ERROR] Failed to read {file_path}: {e}")
        return default_factory()


def validate_state_file(file_path: str) -> bool:
    """
    Validate that a state file contains valid JSON.

    Args:
        file_path: State file to validate

    Returns:
        True if file is valid JSON, False otherwise
    """
    file_path = Path(file_path)

    try:
        if not file_path.exists():
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)

        return True

    except (json.JSONDecodeError, IOError):
        return False


def backup_state_file(file_path: str, suffix: str = ".backup") -> Optional[str]:
    """
    Create backup of state file with timestamp suffix.

    Args:
        file_path: State file to backup
        suffix: Backup suffix (default: .backup)

    Returns:
        Path to backup file, or None if backup failed
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.warning(f"[BACKUP] File not found: {file_path}")
        return None

    try:
        backup_path = file_path.with_suffix(f"{file_path.suffix}{suffix}")
        file_path.rename(backup_path)
        logger.info(f"[BACKUP] Created backup: {backup_path}")
        return str(backup_path)

    except Exception as e:
        logger.error(f"[BACKUP] Failed to backup {file_path}: {e}")
        return None


# For compatibility with existing code patterns
def write_state(file_path: str, data: Any, indent: int = 2) -> None:
    """Alias for write_state_atomic for drop-in replacement."""
    write_state_atomic(file_path, data, indent=indent)


def read_state(file_path: str, default_factory: Optional[Callable[[], Any]] = None) -> Any:
    """Alias for read_state_safe for drop-in replacement."""
    return read_state_safe(file_path, default_factory=default_factory)


if __name__ == "__main__":
    # Basic test
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_file = Path("state") / "test_atomic.json"
    test_data = {"test": "atomic", "timestamp": "2026-09-13"}

    print(f"Writing test data to {test_file}...")
    write_state_atomic(str(test_file), test_data)

    print(f"Reading test data from {test_file}...")
    read_data = read_state_safe(str(test_file))
    print(f"Read data: {read_data}")

    print(f"Validating {test_file}...")
    is_valid = validate_state_file(str(test_file))
    print(f"Valid: {is_valid}")

    # Cleanup
    if test_file.exists():
        test_file.unlink()
        print("Test file cleaned up")
