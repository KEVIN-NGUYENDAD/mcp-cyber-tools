#!/usr/bin/env python3
"""
Stress Test: Atomic Writes Under Concurrent Access
Tests file safety improvements (TD-L3-001, TD-L3-002, TD-L3-003)

Validates:
- No JSON corruption with concurrent writes
- No file locking issues
- No race conditions in state file access
- Proper cleanup of temporary files

Test Scenario:
- 10 concurrent threads
- 100 writes per thread
- Target: 0 corrupted JSON files, 0 parse failures
"""

import json
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

# Import atomic write functions
from state_manager import write_state_atomic, read_state_safe, validate_state_file

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AtomicWriteStressTest:
    def __init__(self, test_dir="state", num_threads=10, writes_per_thread=100):
        self.test_dir = Path(test_dir)
        self.test_dir.mkdir(exist_ok=True)
        self.test_file = self.test_dir / "stress_test_state.json"
        self.num_threads = num_threads
        self.writes_per_thread = writes_per_thread
        self.success_count = 0
        self.failure_count = 0
        self.corruption_count = 0
        self.lock = threading.Lock()
        self.results = []

    def thread_worker(self, thread_id):
        """Single worker thread performing concurrent writes."""
        thread_results = {
            'thread_id': thread_id,
            'writes': 0,
            'errors': 0,
            'corruptions': 0
        }

        for i in range(self.writes_per_thread):
            try:
                # Generate test data with unique identifier
                test_data = {
                    'thread': thread_id,
                    'iteration': i,
                    'timestamp': datetime.now().isoformat(),
                    'write_count': i + 1,
                    'test_value': f'thread_{thread_id}_iteration_{i}'
                }

                # Atomic write
                write_state_atomic(str(self.test_file), test_data, indent=2)
                thread_results['writes'] += 1

                # Small delay to increase contention (optional)
                if i % 25 == 0:
                    time.sleep(0.001)

            except Exception as e:
                logger.error(f"[THREAD-{thread_id}] Write error at iteration {i}: {e}")
                thread_results['errors'] += 1

        # Final validation for this thread
        try:
            if validate_state_file(str(self.test_file)):
                logger.info(f"[THREAD-{thread_id}] Final validation PASSED")
            else:
                logger.warning(f"[THREAD-{thread_id}] Final validation FAILED")
                thread_results['corruptions'] += 1
        except Exception as e:
            logger.error(f"[THREAD-{thread_id}] Validation error: {e}")
            thread_results['corruptions'] += 1

        return thread_results

    def run(self):
        """Run concurrent stress test."""
        logger.info(f"[STRESS-TEST] Starting with {self.num_threads} threads, {self.writes_per_thread} writes each")
        logger.info(f"[STRESS-TEST] Expected total writes: {self.num_threads * self.writes_per_thread}")

        start_time = time.time()

        # Run threads
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [
                executor.submit(self.thread_worker, i)
                for i in range(self.num_threads)
            ]

            for future in as_completed(futures):
                result = future.result()
                with self.lock:
                    self.results.append(result)
                    self.success_count += result['writes']
                    self.failure_count += result['errors']
                    self.corruption_count += result['corruptions']

        elapsed = time.time() - start_time

        # Final state validation
        logger.info("[STRESS-TEST] Running final validation...")
        final_valid = validate_state_file(str(self.test_file))

        # Read final state
        final_data = read_state_safe(str(self.test_file))

        return {
            'status': 'completed',
            'duration_seconds': round(elapsed, 2),
            'total_writes': self.success_count,
            'total_errors': self.failure_count,
            'corruptions_detected': self.corruption_count,
            'final_validation': final_valid,
            'final_data_readable': final_data is not None,
            'threads': self.results,
            'test_passed': self.failure_count == 0 and self.corruption_count == 0 and final_valid
        }

    def cleanup(self):
        """Clean up test files."""
        if self.test_file.exists():
            self.test_file.unlink()
            logger.info(f"[CLEANUP] Removed test file {self.test_file}")


def main():
    """Run the stress test."""
    logger.info("=" * 80)
    logger.info("ATOMIC WRITES STRESS TEST - TD-L3-001, TD-L3-002, TD-L3-003")
    logger.info("=" * 80)

    # Test configuration
    test = AtomicWriteStressTest(
        test_dir="state",
        num_threads=10,
        writes_per_thread=100
    )

    try:
        # Run test
        result = test.run()

        # Print results
        logger.info("=" * 80)
        logger.info("STRESS TEST RESULTS")
        logger.info("=" * 80)
        logger.info(f"Duration: {result['duration_seconds']}s")
        logger.info(f"Total Writes: {result['total_writes']} (expected {10 * 100})")
        logger.info(f"Total Errors: {result['total_errors']}")
        logger.info(f"Corruptions Detected: {result['corruptions_detected']}")
        logger.info(f"Final Validation: {'✓ PASSED' if result['final_validation'] else '✗ FAILED'}")
        logger.info(f"Data Readable: {'✓ YES' if result['final_data_readable'] else '✗ NO'}")
        logger.info("")
        logger.info(f"TEST RESULT: {'✓ PASSED' if result['test_passed'] else '✗ FAILED'}")
        logger.info("=" * 80)

        # Per-thread results
        logger.info("PER-THREAD RESULTS:")
        for thread_result in result['threads']:
            logger.info(
                f"  Thread {thread_result['thread_id']}: "
                f"{thread_result['writes']} writes, "
                f"{thread_result['errors']} errors, "
                f"{thread_result['corruptions']} corruptions"
            )

        # Detailed output
        print("\n" + "=" * 80)
        print("STRESS TEST RESULTS (JSON)")
        print("=" * 80)
        print(json.dumps(result, indent=2))
        print("=" * 80)

        # Exit code
        return 0 if result['test_passed'] else 1

    finally:
        test.cleanup()


if __name__ == '__main__':
    sys.exit(main())
