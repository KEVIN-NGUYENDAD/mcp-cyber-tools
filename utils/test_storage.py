#!/usr/bin/env python3
"""Unit tests for atomic storage module."""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Handle both relative and absolute imports
try:
    from .storage import AtomicStorage
except ImportError:
    from storage import AtomicStorage


def test_basic_read_write():
    """Test basic JSON read/write operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = AtomicStorage(state_dir=tmpdir)

        # Write
        data = {'alerts': [{'id': 1, 'severity': 'critical'}]}
        success, error = storage.write_json('test.json', data)
        assert success, f'Write failed: {error}'

        # Read
        result = storage.read_json('test.json')
        assert result == data, f'Data mismatch: {result} != {data}'
        print('[OK] Basic read/write')


def test_backup_creation():
    """Test that backups are created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = AtomicStorage(state_dir=tmpdir)

        # Write initial
        storage.write_json('config.json', {'version': 1})

        # Write updated (should backup)
        storage.write_json('config.json', {'version': 2}, create_backup=True)

        # Check backup exists
        backups = list(Path(tmpdir).glob('.backups/config_*.json'))
        assert len(backups) > 0, 'No backup created'
        print('[OK] Backup creation')


def test_append_to_list():
    """Test appending to JSON array."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = AtomicStorage(state_dir=tmpdir)

        # Start with empty list
        storage.write_json('alerts.json', [])

        # Append items
        storage.append_to_list('alerts.json', {'id': 1, 'msg': 'Alert 1'})
        storage.append_to_list('alerts.json', {'id': 2, 'msg': 'Alert 2'})

        # Verify
        result = storage.read_json('alerts.json')
        assert len(result) == 2, f'Expected 2 items, got {len(result)}'
        assert result[1]['id'] == 2, 'Wrong item appended'
        print('[OK] Append to list')


def test_field_operations():
    """Test get/set field operations with dot notation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = AtomicStorage(state_dir=tmpdir)

        # Update nested field (auto-creates structure)
        storage.update_field('config.json', 'telegram.bot_token', 'abc123')
        storage.update_field('config.json', 'telegram.chat_id', '12345')

        # Read back
        token = storage.get_field('config.json', 'telegram.bot_token')
        assert token == 'abc123', f'Wrong token: {token}'

        chat_id = storage.get_field('config.json', 'telegram.chat_id')
        assert chat_id == '12345', f'Wrong chat_id: {chat_id}'

        # Full structure
        config = storage.read_json('config.json')
        assert config['telegram']['bot_token'] == 'abc123'
        print('[OK] Field operations')


def test_read_and_modify():
    """Test atomic read-modify-write."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = AtomicStorage(state_dir=tmpdir)

        # Initialize
        storage.write_json('counter.json', {'count': 0})

        # Increment via modifier
        def increment(data):
            data['count'] = data.get('count', 0) + 1
            return data

        success, result, error = storage.read_and_modify('counter.json', increment)
        assert success, f'Modify failed: {error}'
        assert result['count'] == 1, 'Counter not incremented'

        # Increment again
        success, result, error = storage.read_and_modify('counter.json', increment)
        assert result['count'] == 2, 'Second increment failed'
        print('[OK] Read and modify')


def test_missing_file_handling():
    """Test reading non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = AtomicStorage(state_dir=tmpdir)

        # Read missing file with default
        result = storage.read_json('missing.json', default={'status': 'ok'})
        assert result == {'status': 'ok'}, 'Default not returned'

        # Read missing file without default
        result = storage.read_json('missing.json')
        assert result == {}, 'Empty dict not returned'
        print('[OK] Missing file handling')


def test_corrupted_json():
    """Test reading corrupted JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = AtomicStorage(state_dir=tmpdir)
        filepath = Path(tmpdir) / 'corrupted.json'

        # Write corrupted JSON
        with open(filepath, 'w') as f:
            f.write('{invalid json}')

        # Should return default
        result = storage.read_json('corrupted.json', default=[])
        assert result == [], 'Default not used for corrupted file'
        print('[OK] Corrupted JSON handling')


def test_file_info():
    """Test file metadata retrieval."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = AtomicStorage(state_dir=tmpdir)

        # Write file
        storage.write_json('info.json', {'test': 'data'})

        # Get info
        info = storage.get_file_info('info.json')
        assert info['exists'] is True
        assert info['size'] > 0
        assert 'modified' in info
        print('[OK] File info')


def test_list_files():
    """Test listing state files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = AtomicStorage(state_dir=tmpdir)

        # Write multiple files
        storage.write_json('alerts.json', [])
        storage.write_json('incidents.json', {})
        storage.write_json('config.json', {})

        # List
        files = storage.list_files()
        assert len(files) >= 3, f'Expected >=3 files, got {len(files)}'
        assert 'alerts.json' in files
        assert 'incidents.json' in files
        print('[OK] List files')


def test_concurrent_writes():
    """Test concurrent write handling (sequential approximation)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = AtomicStorage(state_dir=tmpdir, lock_timeout=5)

        # Simulate concurrent writes
        storage.write_json('shared.json', {'version': 1})

        success1, error1 = storage.write_json('shared.json', {'version': 2})
        assert success1, f'First write failed: {error1}'

        success2, error2 = storage.write_json('shared.json', {'version': 3})
        assert success2, f'Second write failed: {error2}'

        # Final value should be latest
        result = storage.read_json('shared.json')
        assert result['version'] == 3, 'Wrong final version'
        print('[OK] Concurrent writes (sequential)')


def run_all_tests():
    """Run all tests."""
    print('\n[TESTING] Atomic Storage Module')
    print('=' * 50)

    tests = [
        test_basic_read_write,
        test_backup_creation,
        test_append_to_list,
        test_field_operations,
        test_read_and_modify,
        test_missing_file_handling,
        test_corrupted_json,
        test_file_info,
        test_list_files,
        test_concurrent_writes,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f'[FAIL] {test.__name__}: {e}')
            failed += 1
        except Exception as e:
            print(f'[ERROR] {test.__name__}: {e}')
            failed += 1

    print('=' * 50)
    print(f'[RESULTS] {passed} passed, {failed} failed')
    print()

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
