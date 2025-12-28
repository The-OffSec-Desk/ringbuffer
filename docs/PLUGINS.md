# Plugin Development Guide

Learn how to create custom plugins to extend RingBuffer's functionality.

## Table of Contents

- [Introduction](#introduction)
- [Plugin Architecture](#plugin-architecture)
- [Quick Start](#quick-start)
- [Plugin API Reference](#plugin-api-reference)
- [Event Handling](#event-handling)
- [Capabilities](#capabilities)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Testing](#testing)
- [Distribution](#distribution)

---

## Introduction

### What Are Plugins?

Plugins extend RingBuffer by:
- **Analyzing** kernel events in real-time
- **Annotating** events with additional information
- **Emitting alerts** for important conditions
- **Providing UI panels** (future capability)

### Current Status

**Note:** The plugin system is implemented but not yet integrated into the main RingBuffer application. Plugins are currently available as example code that demonstrates the API.

---

## Plugin Architecture

### Plugin Structure
```
plugins/
├── __init__.py
├── base.py              # Base plugin classes and interfaces
├── manager.py           # Plugin manager (not yet integrated)
├── example_plugin.py    # Example plugin implementations
└── your_plugin.py       # Your custom plugin
```

### Plugin Lifecycle
```
1. Discovery   → PluginManager scans plugins/ directory
2. Loading     → Plugin class is instantiated
3. Initialize  → on_load() method called with PluginContext
4. Active      → Events streamed to on_event()
5. Cleanup     → on_unload() method called
```

### Plugin Context

Plugins receive a `PluginContext` object that provides safe access to RingBuffer functionality:

- `register_annotation(event_id, text)` - Add annotations to events
- `emit_warning(text)` - Show warnings to the user
- `add_panel(widget)` - Add UI panels (future)
- `get_event_by_id(event_id)` - Retrieve events by ID

---

## Quick Start

### Minimal Plugin

Create `plugins/your_plugin.py`:
```python
from plugins.base import KernelPlugin, PluginMetadata, PluginCapability
from core.event import KernelEvent

class YourPlugin(KernelPlugin):
    """Your custom plugin."""

    def _get_metadata(self):
        return PluginMetadata(
            name="Your Plugin",
            version="1.0.0",
            author="Your Name",
            description="Does something useful",
            capabilities={PluginCapability.ANALYZE_EVENTS}
        )

    async def on_load(self, context):
        """Called when plugin is loaded."""
        self.context = context
        print("Your plugin loaded!")
        return True

    async def on_event(self, event: KernelEvent):
        """Called for each kernel event."""
        if "error" in event.message.lower():
            if self.context:
                self.context.register_annotation(
                    event.event_id,
                    "🚨 Error detected"
                )

    async def on_unload(self):
        """Called when plugin is unloaded."""
        print("Your plugin unloaded!")
```

### Testing Your Plugin

Create a simple test script:
```python
import asyncio
from plugins.your_plugin import YourPlugin
from plugins.base import PluginContext
from core.event import KernelEvent
from datetime import datetime

class TestContext(PluginContext):
    def register_annotation(self, event_id, text):
        print(f"Annotation: {text}")

    def emit_warning(self, text):
        print(f"Warning: {text}")

async def test_plugin():
    plugin = YourPlugin()
    context = TestContext()

    # Load plugin
    success = await plugin.on_load(context)
    if not success:
        print("Plugin failed to load")
        return

    # Test with sample event
    test_event = KernelEvent(
        event_id="test-123",
        timestamp_monotonic=123.456,
        timestamp_realtime=datetime.now(),
        severity="ERR",
        subsystem="TEST",
        message="Test error message",
        raw="[123.456] TEST: Test error message",
        source="dmesg"
    )

    await plugin.on_event(test_event)

    # Unload plugin
    await plugin.on_unload()

if __name__ == "__main__":
    asyncio.run(test_plugin())
```

---

## Plugin API Reference

### KernelPlugin Base Class

All plugins must inherit from `KernelPlugin`:

```python
from plugins.base import KernelPlugin

class MyPlugin(KernelPlugin):
    def _get_metadata(self):
        # Required: Return plugin metadata
        pass

    async def on_load(self, context):
        # Optional: Initialize plugin
        pass

    async def on_event(self, event):
        # Optional: Process events
        pass

    async def on_unload(self):
        # Optional: Cleanup
        pass
```

### PluginMetadata

```python
@dataclass
class PluginMetadata:
    name: str                    # Plugin name
    version: str                 # Version string (e.g., "1.0.0")
    author: str                  # Author name
    description: str             # Short description
    min_engine_version: str = "1.0"  # Minimum RingBuffer version
    capabilities: set = None     # Set of PluginCapability flags
```

### PluginCapability Flags

```python
class PluginCapability:
    ANALYZE_EVENTS = "analyze_events"      # Can process events
    ANNOTATE_EVENTS = "annotate_events"    # Can add annotations
    EMIT_ALERTS = "emit_alerts"           # Can emit warnings
    PROVIDE_UI_PANEL = "provide_ui_panel"  # Can add UI panels (future)
```

### KernelEvent Structure

```python
@dataclass
class KernelEvent:
    event_id: str                          # Unique event identifier
    timestamp_monotonic: Optional[float]   # Seconds since boot
    timestamp_realtime: datetime           # Wall-clock time
    severity: str                          # EMERG, ALERT, CRIT, ERR, WARN, NOTICE, INFO, DEBUG
    subsystem: str                         # USB, NET, KERNEL, etc.
    message: str                           # Event message
    raw: str                               # Original log line
    source: str = 'dmesg'                  # Event source (dmesg/journalctl)
    pid: Optional[int] = None              # Process ID
    cpu: Optional[int] = None              # CPU number
    annotations: dict = field(default_factory=dict)
```

---

## Event Handling

### Processing Events

```python
async def on_event(self, event: KernelEvent):
    # Filter by severity
    if event.severity in ['EMERG', 'ALERT', 'CRIT']:
        await self.handle_critical_event(event)

    # Filter by subsystem
    if event.subsystem == 'USB':
        await self.handle_usb_event(event)

    # Filter by message content
    if 'error' in event.message.lower():
        await self.handle_error_event(event)
```

### Adding Annotations

```python
async def on_event(self, event: KernelEvent):
    if 'usb' in event.subsystem.lower():
        if 'new device' in event.message.lower():
            self.context.register_annotation(
                event.event_id,
                "🔌 USB device connected"
            )
        elif 'disconnect' in event.message.lower():
            self.context.register_annotation(
                event.event_id,
                "❌ USB device disconnected"
            )
```

### Emitting Warnings

```python
async def on_event(self, event: KernelEvent):
    if 'oom killer' in event.message.lower():
        self.context.emit_warning(
            "Out of Memory killer activated!"
        )
```

---

## Capabilities

### ANALYZE_EVENTS

Basic event processing capability. All plugins should have this.

```python
capabilities={PluginCapability.ANALYZE_EVENTS}
```

### ANNOTATE_EVENTS

Allows adding annotations to events that appear in the UI.

```python
capabilities={PluginCapability.ANALYZE_EVENTS, PluginCapability.ANNOTATE_EVENTS}
```

### EMIT_ALERTS

Allows showing warning messages to the user.

```python
capabilities={PluginCapability.ANALYZE_EVENTS, PluginCapability.EMIT_ALERTS}
```

### PROVIDE_UI_PANEL (Future)

Will allow plugins to add custom UI panels to RingBuffer.

```python
capabilities={PluginCapability.ANALYZE_EVENTS, PluginCapability.PROVIDE_UI_PANEL}
```

---

## Best Practices

### Performance

**DO:**
- ✅ Keep `on_event()` fast (< 1ms per event)
- ✅ Use async operations for I/O
- ✅ Filter events early to avoid unnecessary processing
- ✅ Handle exceptions gracefully

**DON'T:**
- ❌ Block in `on_event()` - it's async for a reason
- ❌ Make network calls synchronously
- ❌ Write to disk for every event
- ❌ Create complex objects repeatedly

### Error Handling

```python
async def on_event(self, event: KernelEvent):
    try:
        # Your plugin logic
        await self.process_event(event)
    except Exception as e:
        # Log error but don't crash
        self.logger.error(f"Plugin error: {e}")
        # Optionally disable plugin after too many errors
```

### State Management

```python
class StatefulPlugin(KernelPlugin):
    async def on_load(self, context):
        self.event_count = 0
        self.error_sequences = []
        self.last_usb_event = None
        return True

    async def on_event(self, event):
        self.event_count += 1

        if event.severity == 'ERR':
            self.error_sequences.append({
                'timestamp': event.timestamp_realtime,
                'message': event.message
            })

            # Limit memory usage
            if len(self.error_sequences) > 1000:
                self.error_sequences = self.error_sequences[-1000:]
```

### Logging

```python
async def on_load(self, context):
    self.logger.info("Plugin initialized")
    return True

async def on_event(self, event):
    self.logger.debug(f"Processing event: {event.event_id}")
```

---

## Examples

### USB Device Monitor

```python
from plugins.base import KernelPlugin, PluginMetadata, PluginCapability
from core.event import KernelEvent

class USBMonitorPlugin(KernelPlugin):
    def _get_metadata(self):
        return PluginMetadata(
            name="USB Monitor",
            version="1.0.0",
            author="Example Author",
            description="Monitor USB device connections and disconnections",
            capabilities={PluginCapability.ANALYZE_EVENTS, PluginCapability.ANNOTATE_EVENTS}
        )

    async def on_load(self, context):
        self.context = context
        self.logger.info("USB Monitor loaded")
        return True

    async def on_event(self, event: KernelEvent):
        if not event.subsystem or 'usb' not in event.subsystem.lower():
            return

        message = event.message.lower()

        if 'new' in message and 'device' in message:
            self.context.register_annotation(
                event.event_id,
                "🔌 USB device connected"
            )
        elif 'disconnect' in message or 'removed' in message:
            self.context.register_annotation(
                event.event_id,
                "❌ USB device disconnected"
            )
        elif 'error' in message or 'failed' in message:
            self.context.register_annotation(
                event.event_id,
                "⚠️ USB error detected"
            )
            self.context.emit_warning("USB error detected")
```

### OOM Killer Detector

```python
class OOMDetectorPlugin(KernelPlugin):
    def _get_metadata(self):
        return PluginMetadata(
            name="OOM Detector",
            version="1.0.0",
            author="Example Author",
            description="Detect out-of-memory killer events",
            capabilities={PluginCapability.ANALYZE_EVENTS, PluginCapability.ANNOTATE_EVENTS, PluginCapability.EMIT_ALERTS}
        )

    async def on_load(self, context):
        self.context = context
        self.oom_count = 0
        return True

    async def on_event(self, event: KernelEvent):
        message = event.message.lower()

        if 'oom killer' in message or 'oom-kill' in message:
            self.oom_count += 1
            annotation = f"💀 OOM Kill #{self.oom_count}"

            self.context.register_annotation(event.event_id, annotation)
            self.context.emit_warning(
                f"Out-of-memory killer triggered (#{self.oom_count})"
            )
        elif 'memory' in message and ('pressure' in message or 'low' in message):
            self.context.register_annotation(event.event_id, "⚠️ Memory pressure")
```

### Security Event Monitor

```python
import re

class SecurityMonitorPlugin(KernelPlugin):
    def _get_metadata(self):
        return PluginMetadata(
            name="Security Monitor",
            version="1.0.0",
            author="Example Author",
            description="Monitor security-related kernel events",
            capabilities={PluginCapability.ANALYZE_EVENTS, PluginCapability.ANNOTATE_EVENTS}
        )

    async def on_load(self, context):
        self.context = context
        self.denial_patterns = [
            re.compile(r'apparmor.*denied', re.IGNORECASE),
            re.compile(r'selinux.*denied', re.IGNORECASE),
            re.compile(r'permission denied', re.IGNORECASE),
        ]
        return True

    async def on_event(self, event: KernelEvent):
        message = event.message

        for pattern in self.denial_patterns:
            if pattern.search(message):
                self.context.register_annotation(
                    event.event_id,
                    "🔒 Security denial detected"
                )
                break
```

---

## Testing

### Unit Testing

```python
import unittest
import asyncio
from plugins.your_plugin import YourPlugin
from plugins.base import PluginContext
from core.event import KernelEvent
from datetime import datetime

class MockContext(PluginContext):
    def __init__(self):
        self.annotations = []
        self.warnings = []

    def register_annotation(self, event_id, text):
        self.annotations.append((event_id, text))

    def emit_warning(self, text):
        self.warnings.append(text)

class TestYourPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = YourPlugin()
        self.context = MockContext()

    async def asyncSetUp(self):
        success = await self.plugin.on_load(self.context)
        self.assertTrue(success)

    def test_error_detection(self):
        async def run_test():
            await self.asyncSetUp()

            event = KernelEvent(
                event_id="test-123",
                timestamp_monotonic=123.456,
                timestamp_realtime=datetime.now(),
                severity="ERR",
                subsystem="TEST",
                message="Test error occurred",
                raw="[123.456] TEST: Test error occurred",
                source="dmesg"
            )

            await self.plugin.on_event(event)

            # Check that annotation was added
            self.assertEqual(len(self.context.annotations), 1)
            self.assertIn("error", self.context.annotations[0][1].lower())

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
```

### Manual Testing

```python
# test_plugin.py
import asyncio
from plugins.your_plugin import YourPlugin
from plugins.base import PluginContext
from core.event import KernelEvent
from datetime import datetime

class TestContext(PluginContext):
    def register_annotation(self, event_id, text):
        print(f"📝 Annotation: {text}")

    def emit_warning(self, text):
        print(f"⚠️ Warning: {text}")

async def test():
    plugin = YourPlugin()
    context = TestContext()

    print("Loading plugin...")
    success = await plugin.on_load(context)
    if not success:
        print("❌ Plugin failed to load")
        return

    print("✅ Plugin loaded successfully")

    # Test events
    test_events = [
        KernelEvent(
            event_id="1",
            timestamp_monotonic=100.0,
            timestamp_realtime=datetime.now(),
            severity="INFO",
            subsystem="USB",
            message="usb 1-2: new high-speed USB device",
            raw="[100.0] usb 1-2: new high-speed USB device",
            source="dmesg"
        ),
        KernelEvent(
            event_id="2",
            timestamp_monotonic=200.0,
            timestamp_realtime=datetime.now(),
            severity="ERR",
            subsystem="KERNEL",
            message="error occurred in kernel",
            raw="[200.0] KERNEL: error occurred in kernel",
            source="dmesg"
        )
    ]

    for event in test_events:
        print(f"\nProcessing event: {event.message}")
        await plugin.on_event(event)

    print("\nUnloading plugin...")
    await plugin.on_unload()
    print("✅ Test complete")

if __name__ == "__main__":
    asyncio.run(test())
```

---

## Distribution

### Plugin File Structure

```
your-plugin-name.py
├── Plugin class implementation
├── Metadata definition
├── Event handling logic
└── Optional: Helper functions
```

### Sharing Plugins

1. Create a GitHub repository: `ringbuffer-plugin-name`
2. Include in the plugin file:
   - Clear documentation/comments
   - Example usage
   - Test cases
3. Add to repository description:
   - What the plugin does
   - Installation instructions
   - Requirements

### Installation by Users

Users can install your plugin by:
```bash
# Download the plugin file
curl -O https://raw.githubusercontent.com/yourname/ringbuffer-plugin-name/main/your_plugin.py

# Place in plugins directory
mv your_plugin.py ~/path/to/ringbuffer/plugins/

# The plugin will be loaded automatically when RingBuffer supports plugins
```

### Future Integration

When RingBuffer integrates plugin support, plugins will be loaded from:
- `~/.local/share/ringbuffer/plugins/`
- `/usr/share/ringbuffer/plugins/`
- The `plugins/` directory in the RingBuffer installation

---

## Getting Help

- **API Questions:** Check the `plugins/base.py` and `plugins/example_plugin.py` files
- **Bug Reports:** [GitHub Issues](https://github.com/The-OffSec-Desk/ringbuffer/issues)
- **Examples:** See `plugins/example_plugin.py` for complete working examples

---

**Happy plugin development! 🔌**