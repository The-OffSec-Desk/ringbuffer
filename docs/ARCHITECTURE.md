# RingBuffer Architecture

This document describes the architecture and design of RingBuffer, a real-time kernel log monitoring and analysis application.

## Table of Contents

- [Overview](#overview)
- [Architecture Principles](#architecture-principles)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [UI Architecture](#ui-architecture)
- [Plugin System](#plugin-system)
- [Error Handling](#error-handling)
- [Performance Considerations](#performance-considerations)
- [Security Model](#security-model)

---

## Overview

RingBuffer is a Python-based GUI application for monitoring and analyzing Linux kernel logs in real-time. It uses PySide6 (Qt for Python) for the user interface and provides both live streaming and historical analysis capabilities.

### Key Features

- **Real-time kernel log streaming** from dmesg or systemd journal
- **Advanced filtering** by severity, subsystem, source, and regex patterns
- **Structured event parsing** with automatic subsystem detection
- **Extensible plugin system** for custom analysis and alerting
- **Dark theme UI** optimized for long-term monitoring
- **Cross-platform compatibility** via AppImage distribution

### Technology Stack

- **Language:** Python 3.13
- **GUI Framework:** PySide6 (Qt 6 bindings)
- **Async Runtime:** asyncio
- **Packaging:** AppImage (self-contained bundles)
- **Architecture:** Event-driven, producer-consumer pattern

---

## Architecture Principles

### 1. Asynchronous Design

RingBuffer uses asyncio throughout the core engine to ensure non-blocking operation:

- Kernel log reading never blocks the UI
- Event processing is pipelined and concurrent
- Plugin execution is isolated and async

### 2. Event-Driven Architecture

The system is built around KernelEvent objects that flow through the pipeline:

- **Ingestion:** Raw logs → structured events
- **Processing:** Events → filtering → display
- **Extension:** Events → plugins → annotations/alerts

### 3. Separation of Concerns

Clear boundaries between components:

- **Core:** Engine, sources, parsing (business logic)
- **UI:** Widgets, themes, interaction (presentation)
- **Plugins:** Extensions, analysis (customization)

### 4. Error Isolation

Failures in one component don't crash the entire system:

- Plugin errors are caught and logged
- Source failures trigger fallbacks
- UI errors are contained to individual widgets

---

## Core Components

### KernelLogEngine

**Location:** `core/engine.py`

The central orchestrator that manages the entire log processing pipeline.

```python
class KernelLogEngine:
    def __init__(self, buffer_size: int = 10000)
    async def initialize(self) -> bool
    async def load_snapshot(self) -> list[KernelEvent]
    async def start_streaming(self) -> None
    async def stop_streaming(self) -> None
    def pause(self) -> None
    def resume(self) -> None
    def get_buffer(self) -> list[KernelEvent]
    def flush_buffer(self) -> None
```

**Responsibilities:**
- Source selection and initialization
- Event buffering with backpressure
- Streaming lifecycle management
- Callback registration for plugins

**Key Features:**
- Circular buffer with configurable size (default: 10,000 events)
- Pause/resume support for UI responsiveness
- Multi-source fallback (dmesg → journalctl)
- Async event distribution to subscribers

### Log Sources

**Location:** `core/sources.py`

Abstract interface and implementations for kernel log sources.

```python
class LogSource(ABC):
    async def get_snapshot(self) -> list[KernelEvent]
    async def stream_live(self) -> AsyncIterator[KernelEvent]

class DmesgSource(LogSource): ...
class JournalctlSource(LogSource): ...
```

**DmesgSource:**
- Reads from `/dev/kmsg` via `dmesg -w` (live) and `dmesg` (snapshot)
- Handles monotonic timestamp conversion
- Supports colorized output parsing

**JournalctlSource:**
- Uses `journalctl -k` for kernel logs
- Supports both snapshot and live streaming modes
- Handles systemd timestamp formats

### KernelLogParser

**Location:** `core/parser.py`

Robust parser that converts raw kernel log lines into structured KernelEvent objects.

**Supported Formats:**
- `[timestamp] subsystem: message` (standard dmesg)
- `[timestamp] process[pid]: message` (process logs)
- `<level>subsystem: message` (kernel prefix format)

**Features:**
- Automatic severity inference from message content
- Monotonic-to-realtime timestamp conversion
- CPU and PID extraction
- Continuation line detection (stack traces, hex dumps)
- Subsystem normalization

### KernelEvent

**Location:** `core/event.py`

The central data structure representing a kernel log event.

```python
@dataclass
class KernelEvent:
    timestamp_monotonic: Optional[float]  # Seconds since boot
    timestamp_realtime: Optional[datetime]  # Wall-clock time
    severity: str                          # EMERG, ALERT, CRIT, ERR, WARN, NOTICE, INFO, DEBUG
    subsystem: Optional[str]               # USB, NET, KERNEL, etc.
    message: str                           # Parsed message text
    raw: str                               # Original log line
    source: str                           # 'dmesg' or 'journal'

    # Metadata
    event_id: str = field(default_factory=lambda: str(uuid4()))
    cpu: Optional[int] = None
    pid: Optional[int] = None
    annotations: dict = field(default_factory=dict)
    plugin_metadata: dict = field(default_factory=dict)
```

**Design Decisions:**
- UUID-based event IDs for uniqueness
- Separate monotonic/realtime timestamps
- Extensible annotation system for plugins
- JSON-serializable for export

### PermissionChecker

**Location:** `core/permissions.py`

Handles system permission checking and source availability detection.

```python
class PermissionChecker:
    @staticmethod
    def can_read_dmesg() -> bool
    @staticmethod
    def can_watch_dmesg() -> bool
    @staticmethod
    def can_use_journalctl() -> bool
    @staticmethod
    def get_available_sources() -> list[str]
```

**Checks:**
- File access permissions for `/dev/kmsg`
- Command execution permissions for `dmesg` and `journalctl`
- Live streaming capability (`dmesg -w`)

---

## Data Flow

### 1. Initialization Phase

```
main.py → KernelLogMainWindow.__init__() → KernelLogReader.__init__()
    ↓
KernelLogReader._initialize_engine_sync() → KernelLogEngine.initialize()
    ↓
PermissionChecker.get_available_sources() → [dmesg, journal]
    ↓
DmesgSource() or JournalctlSource() → engine.source
```

### 2. Snapshot Loading

```
UI startup → KernelLogReader.get_recent_logs(limit=100)
    ↓
KernelLogEngine.load_snapshot() → source.get_snapshot()
    ↓
subprocess.run(['dmesg', '-L']) → raw lines
    ↓
KernelLogParser.parse_dmesg_line() → KernelEvent objects
    ↓
engine.buffer.extend(events) → UI display
```

### 3. Live Streaming

```
QTimer (150ms) → KernelLogReader.get_new_logs()
    ↓
KernelLogEngine.get_buffer() → new events since last call
    ↓
EventStreamWidget.append_logs() → UI update
    ↓
FiltersPanel.apply_filters() → filtered display
```

### 4. Event Processing Pipeline

```
Raw log line → KernelLogParser → KernelEvent
    ↓
Engine buffer → PluginManager.process_event()
    ↓
Plugin.on_event() → annotations + alerts
    ↓
UI display with annotations
```

---

## UI Architecture

### Main Window Layout

**Location:** `ui/main_window.py`

```
┌─────────────────────────────────────────────────┐
│ Menu Bar (File, Capture, View, Plugins, Settings, Help) │
├─────────────────────────────────────────────────┤
│ ┌─────────────┬─────────────────────┬─────────┐ │
│ │             │                     │         │ │
│ │ Filter      │   Event Stream       │ Context │ │
│ │ Panel       │   (Table View)       │ Panel   │ │
│ │ (Left)      │   (Center)           │ (Right) │ │
│ │             │                     │         │ │
│ └─────────────┴─────────────────────┴─────────┘ │
├─────────────────────────────────────────────────┤
│ Status Bar (Source: dmesg | Streaming active ✓)  │
└─────────────────────────────────────────────────┘
```

### Component Responsibilities

**KernelLogMainWindow:**
- Application lifecycle management
- Component orchestration
- Menu/action handling
- Status bar updates

**FiltersPanel (`ui/filters_panel.py`):**
- Severity checkboxes (EMERG, ALERT, CRIT, ERR, WARN, NOTICE, INFO, DEBUG)
- Subsystem filters (USB, MEMORY, NETWORK, etc.)
- Source filters (dmesg, journalctl)
- Regex search input
- Real-time filter application

**EventStreamWidget (`ui/event_stream.py`):**
- QTableWidget-based event display
- Severity-based color coding
- Auto-scroll functionality
- Row selection handling
- Filter application to displayed events

**ContextPanel (`ui/context_panel.py`):**
- Detailed event information display
- Event metadata (timestamps, PID, CPU, etc.)
- Annotation display
- Raw log line viewing

**MenuBarManager (`ui/menu_bar.py`):**
- Menu construction and action handling
- Keyboard shortcuts
- Export functionality (placeholder)
- Settings dialogs

### Theme System

**Location:** `themes/dark_theme.py`

Custom dark theme optimized for log monitoring:
- Dark color scheme (#0B0F14 background, #E5E7EB text)
- Severity-based color coding
- Monospace fonts for log display
- Consistent styling across all widgets

---

## Plugin System

### Architecture

**Location:** `plugins/`

```
plugins/
├── base.py          # Plugin interfaces and base classes
├── manager.py       # Plugin lifecycle management
├── example_plugin.py # Working examples
└── __init__.py      # Package initialization
```

### Plugin Lifecycle

```
1. Discovery: PluginManager.discover_plugins()
2. Loading: PluginManager.load_plugin(name)
3. Initialization: plugin.on_load(context)
4. Active: plugin.on_event(event) for each event
5. Unloading: plugin.on_unload()
```

### PluginContext

Safe interface for plugins to interact with the system:

```python
class PluginContext:
    def register_annotation(self, event_id: str, text: str) -> None
    def emit_warning(self, text: str) -> None
    def add_panel(self, widget: Any) -> None  # Future
    def get_event_by_id(self, event_id: str) -> Optional[KernelEvent]
```

### Plugin Capabilities

```python
class PluginCapability:
    ANALYZE_EVENTS = "analyze_events"      # Process events
    ANNOTATE_EVENTS = "annotate_events"    # Add annotations
    EMIT_ALERTS = "emit_alerts"           # Show warnings
    PROVIDE_UI_PANEL = "provide_ui_panel"  # Add UI panels (future)
```

### Current Status

**Note:** The plugin system is fully implemented but not yet integrated into the main application. Plugins exist as example code demonstrating the API.

---

## Error Handling

### Error Hierarchy

**Location:** `core/errors.py`

```python
class RingBufferError(Exception): ...

class SourceUnavailableError(RingBufferError): ...
class PermissionDeniedError(RingBufferError): ...
class PluginError(RingBufferError): ...
class PluginLoadError(PluginError): ...
class PluginVersionError(PluginError): ...
```

### Error Isolation

- **Source errors:** Automatic fallback to alternative sources
- **Plugin errors:** Isolated, logged, don't affect core functionality
- **UI errors:** Contained to individual widgets
- **Parsing errors:** Logged, event skipped, processing continues

### Logging Strategy

- **Core components:** Structured logging with context
- **Plugins:** Isolated logger instances per plugin
- **UI:** Error dialogs for user-facing issues
- **Performance:** Debug logging for development, info/warn/error for production

---

## Performance Considerations

### Memory Management

- **Circular buffer:** Fixed size (10,000 events) prevents unbounded growth
- **Event filtering:** Applied at display level, not ingestion
- **Plugin isolation:** Each plugin runs in separate async context
- **UI updates:** Batched updates, auto-scroll optimization

### CPU Optimization

- **Async I/O:** Non-blocking log reading and processing
- **Timer-based polling:** 150ms intervals balance responsiveness vs. CPU usage
- **Lazy parsing:** Events parsed only when needed
- **Filter caching:** Regex patterns compiled once

### Scalability Limits

- **Event volume:** Tested with 100+ events/second
- **Memory usage:** ~50MB base + ~1KB per buffered event
- **UI responsiveness:** Maintained up to 10,000 displayed events
- **Plugin count:** Designed for 10-20 concurrent plugins

---

## Security Model

### Principle of Least Privilege

- **No root requirement:** Works with user permissions when possible
- **Permission checking:** Validates access before attempting operations
- **Fallback sources:** Uses journalctl when dmesg unavailable
- **Safe execution:** Plugins run in isolated contexts

### Permission Levels

1. **Full access (recommended):**
   - User in `systemd-journal` group
   - Read access to journalctl and dmesg

2. **Limited access:**
   - User in `kmsg` group
   - Read access to `/dev/kmsg` only

3. **Basic access:**
   - Run with `sudo`
   - Full system access (not recommended)

### Data Handling

- **No external network access:** All processing local
- **No persistent storage:** Logs kept in memory only
- **No credential handling:** System access only
- **Safe parsing:** Regex-based parsing prevents injection

---

## Deployment Architecture

### AppImage Structure

```
RingBuffer-x86_64.AppImage
├── AppRun (launcher script)
├── ringbuffer.png (icon)
├── ringbuffer.desktop (menu entry)
└── squashfs-root/
    ├── opt/
    │   ├── python/     # Python 3.13 runtime
    │   └── ringbuffer/ # Application code
    └── usr/
        ├── bin/        # Executables
        └── share/      # Icons, desktop files
```

### Runtime Dependencies

- **Bundled:** Python 3.13, PySide6, all libraries
- **System:** FUSE (for AppImage), kernel log access
- **Optional:** systemd-journal group membership

### Installation Process

1. **Download:** Single AppImage file
2. **Execute:** `chmod +x RingBuffer-x86_64.AppImage`
3. **Optional:** Run install script for desktop integration
4. **Permissions:** Configure group membership if needed

---

## Future Architecture

### Planned Enhancements

- **Plugin integration:** Load plugins from main application
- **Export system:** CSV, JSON, database export
- **Session management:** Save/restore filter states
- **Advanced filtering:** Time-based, complex queries
- **Network features:** Remote log collection
- **Performance monitoring:** System resource tracking

### Scalability Improvements

- **Database backend:** For large event volumes
- **Distributed processing:** Multi-host log aggregation
- **Real-time analytics:** Statistical analysis and alerting
- **Plugin marketplace:** Community plugin ecosystem

---

## Development Guidelines

### Code Organization

- **core/:** Business logic, no UI dependencies
- **ui/:** PySide6 widgets, theme integration
- **plugins/:** Extension system
- **themes/:** Styling and appearance
- **tools/:** Utilities and helpers
- **docs/:** Documentation

### Testing Strategy

- **Unit tests:** Core components (parser, engine)
- **Integration tests:** UI interaction
- **Plugin tests:** Extension compatibility
- **Performance tests:** High-volume event handling

### Contributing

1. Follow async patterns throughout
2. Maintain error isolation
3. Add comprehensive logging
4. Update documentation
5. Test on multiple distributions

---

This architecture provides a solid foundation for real-time kernel log monitoring while maintaining extensibility, performance, and reliability.
