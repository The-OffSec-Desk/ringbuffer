#!/usr/bin/env python3
"""
Test script to verify filtering logic works correctly
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.event_stream import EventStreamWidget


def test_filtering():
    """Test the filtering logic"""
    app = QApplication(sys.argv)
    
    # Create event stream
    stream = EventStreamWidget()
    
    # Test logs
    logs = [
        {'timestamp': '123.456', 'severity': 'INFO', 'subsystem': 'USB', 'message': 'test1', 'source': 'dmesg'},
        {'timestamp': '123.457', 'severity': 'WARN', 'subsystem': 'MEMORY', 'message': 'test2', 'source': 'dmesg'},
        {'timestamp': '123.458', 'severity': 'ERR', 'subsystem': 'USB', 'message': 'error test', 'source': 'journalctl'},
        {'timestamp': '123.459', 'severity': 'DEBUG', 'subsystem': 'NETWORK', 'message': 'debug message', 'source': 'dmesg'},
    ]
    
    print("=" * 60)
    print("FILTERING TEST SUITE")
    print("=" * 60)
    
    # Test 1: Populate without filters
    print("\n[Test 1] Populate without filters")
    stream.populate_logs(logs)
    assert len(stream.logs) == 4, f"Expected 4 logs, got {len(stream.logs)}"
    assert len(stream.displayed_logs) == 4, f"Expected 4 displayed, got {len(stream.displayed_logs)}"
    print(f"✓ Populated {len(stream.logs)} logs, displaying {len(stream.displayed_logs)}")
    
    # Test 2: Filter by subsystem (USB only)
    print("\n[Test 2] Filter by subsystem (USB only)")
    filters = {'severities': [], 'subsystems': ['USB'], 'sources': [], 'search_pattern': ''}
    stream.apply_filters(filters)
    assert len(stream.displayed_logs) == 2, f"Expected 2 USB entries, got {len(stream.displayed_logs)}"
    print(f"✓ USB filter: displaying {len(stream.displayed_logs)} logs")
    
    # Test 3: Filter by severity (INFO and WARN)
    print("\n[Test 3] Filter by severity (INFO and WARN)")
    filters = {'severities': ['INFO', 'WARN'], 'subsystems': [], 'sources': [], 'search_pattern': ''}
    stream.apply_filters(filters)
    assert len(stream.displayed_logs) == 2, f"Expected 2 (INFO+WARN), got {len(stream.displayed_logs)}"
    print(f"✓ Severity filter: displaying {len(stream.displayed_logs)} logs")
    
    # Test 4: Filter by regex pattern
    print("\n[Test 4] Filter by regex pattern (error)")
    filters = {'severities': [], 'subsystems': [], 'sources': [], 'search_pattern': 'error'}
    stream.apply_filters(filters)
    assert len(stream.displayed_logs) == 1, f"Expected 1 match, got {len(stream.displayed_logs)}"
    print(f"✓ Regex filter: displaying {len(stream.displayed_logs)} logs")
    
    # Test 5: Filter by source
    print("\n[Test 5] Filter by source (journalctl)")
    filters = {'severities': [], 'subsystems': [], 'sources': ['journalctl'], 'search_pattern': ''}
    stream.apply_filters(filters)
    assert len(stream.displayed_logs) == 1, f"Expected 1 journalctl entry, got {len(stream.displayed_logs)}"
    print(f"✓ Source filter: displaying {len(stream.displayed_logs)} logs")
    
    # Test 6: Combined filters
    print("\n[Test 6] Combined filters (USB subsystem + INFO/WARN severity)")
    filters = {'severities': ['INFO', 'WARN'], 'subsystems': ['USB'], 'sources': [], 'search_pattern': ''}
    stream.apply_filters(filters)
    assert len(stream.displayed_logs) == 1, f"Expected 1 match, got {len(stream.displayed_logs)}"
    print(f"✓ Combined filter: displaying {len(stream.displayed_logs)} logs")
    
    # Test 7: No filters (show all)
    print("\n[Test 7] Clear all filters (show all)")
    filters = {'severities': [], 'subsystems': [], 'sources': [], 'search_pattern': ''}
    stream.apply_filters(filters)
    assert len(stream.displayed_logs) == 4, f"Expected 4, got {len(stream.displayed_logs)}"
    print(f"✓ No filters: displaying {len(stream.displayed_logs)} logs")
    
    # Test 8: Append new logs respect filters
    print("\n[Test 8] Append logs with active filter")
    filters = {'severities': ['INFO'], 'subsystems': [], 'sources': [], 'search_pattern': ''}
    stream.apply_filters(filters)
    new_logs = [
        {'timestamp': '123.460', 'severity': 'INFO', 'subsystem': 'KERNEL', 'message': 'new info', 'source': 'dmesg'},
        {'timestamp': '123.461', 'severity': 'WARN', 'subsystem': 'KERNEL', 'message': 'new warn', 'source': 'dmesg'},
    ]
    stream.append_logs(new_logs)
    # Should only add the INFO log (1 INFO from before now replaced with 1 new INFO)
    assert len(stream.logs) == 6, f"Expected 6 total logs, got {len(stream.logs)}"
    assert len(stream.displayed_logs) == 2, f"Expected 2 displayed (2 INFO), got {len(stream.displayed_logs)}"
    print(f"✓ Append with filter: total {len(stream.logs)}, displaying {len(stream.displayed_logs)}")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == '__main__':
    test_filtering()
