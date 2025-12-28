# RingBuffer User Manual

Complete guide to using RingBuffer for kernel log monitoring and analysis.

## Table of Contents

- [Getting Started](#getting-started)
- [Basic Operations](#basic-operations)
- [Filtering and Search](#filtering-and-search)
- [Event Details](#event-details)
- [Export and Saving](#export-and-saving)
- [Plugin Usage](#plugin-usage)
- [Advanced Features](#advanced-features)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Tips and Best Practices](#tips-and-best-practices)

---

## Getting Started

### First Launch

When you first launch RingBuffer:

1. The application initializes the kernel log engine
2. Attempts to connect to available log sources (dmesg or journalctl)
3. Loads recent kernel logs from the ring buffer (last 100 events)
4. Automatically starts live streaming of new kernel events
5. Events appear in the main table view with real-time updates

**Note:** If you see permission errors, refer to the [Installation Guide](INSTALL.md#permissions-setup).

### Understanding Kernel Logs

Kernel logs contain messages from:
- **Kernel core:** System initialization, memory management, scheduling
- **Device drivers:** USB, network, storage, graphics
- **Subsystems:** Networking, filesystem, security modules
- **Hardware events:** Device connections, errors, state changes

RingBuffer parses these logs into structured events with severity levels, subsystems, timestamps, and messages.

---

### Components

1. **Menu Bar:** File, Capture, View, Plugins, Settings, Help
2. **Toolbar:** Quick actions for common operations (not implemented in current version)
3. **Filter Panel (Left):** Severity, subsystem, source, and search filters
4. **Log View (Center):** Main table displaying kernel events
5. **Context Panel (Bottom):** Detailed information for selected events
6. **Status Bar (Bottom):** Source information and streaming status

---

## Basic Operations

### Starting and Stopping

**Start Streaming:**
- Automatically starts on application launch
- Menu → **Capture → Start Live Stream** (or `Space`)
- Streaming polls for new events every 150ms

**Pause Streaming:**
- Menu → **Capture → Pause Stream** (or `Ctrl+Space`)
- Stops polling for new events but keeps existing logs

**Resume Streaming:**
- Menu → **Capture → Resume Stream** (or `Ctrl+Shift+Space`)
- Resumes polling for new events

**Note:** Pausing only stops new event collection; the kernel continues generating logs.

### Clearing the Display

**Clear Kernel Buffer:**
- Menu → **File → Clear Kernel Buffer** (or `Ctrl+Shift+Delete`)
- **Warning:** This clears the actual kernel ring buffer, not just the display
- Requires elevated permissions and shows confirmation dialog

**Note:** This operation requires root privileges and cannot be undone.

### Auto-Scroll

**Toggle Auto-Scroll:**
- Menu → **View → Toggle Auto-Scroll** (or `Ctrl+A`)
- When enabled, view automatically scrolls to show newest events
- Default state: enabled

---

## Filtering and Search

### Severity Filtering

RingBuffer recognizes these kernel severity levels:

| Level | Priority | Description | Color |
|-------|----------|-------------|-------|
| EMERG | 0 | System is unusable | Red |
| ALERT | 1 | Action must be taken immediately | Red |
| CRIT | 2 | Critical conditions | Red |
| ERR | 3 | Error conditions | Red |
| WARN | 4 | Warning conditions | Yellow |
| NOTICE | 5 | Normal but significant | Blue |
| INFO | 6 | Informational | Blue |
| DEBUG | 7 | Debug-level messages | Green |

**To filter by severity:**
1. Use checkboxes in the left "Severity" panel
2. Check = Show, Uncheck = Hide
3. Changes apply in real-time to the table view

**Example Use Cases:**
- **Show only errors:** Check only ERR, CRIT, ALERT, EMERG
- **Hide debug noise:** Uncheck DEBUG and INFO
- **Critical events only:** Check only EMERG and ALERT

### Subsystem Filtering

Common subsystems detected (configurable list):
- **USB:** USB device events
- **MEMORY:** Memory management
- **NETWORK:** Network interface events
- **FILESYSTEM:** Filesystem operations
- **DRM:** Graphics/display
- **SECURITY:** Security-related events
- **AUDIO:** Audio device events
- **HID:** Human interface devices

**To filter by subsystem:**
1. Use checkboxes in the "Subsystem" panel
2. Multiple selections = OR logic (show if any match)
3. Subsystem matching is case-insensitive

### Source Filtering

RingBuffer can read from multiple sources:
- **dmesg:** Kernel ring buffer (default)
- **journalctl:** systemd journal

**To filter by source:**
1. Use checkboxes in the "Source" panel
2. Select which log sources to display

### Text Search

**Search for specific text:**
1. Use the "Search (Regex)" input box in the filter panel
2. Enter regex pattern or plain text
3. Search is case-insensitive and applies to the message content
4. "Clear" button resets the search

**Search examples:**
```
USB disconnect         # Find USB disconnection events
error.*timeout         # Regex: errors with timeout
segfault               # Find segmentation faults
oom.*kill              # Out of memory events
```

### Advanced Filtering

**Combine multiple filters:**
- All active filters are combined with AND logic
- Severity + Subsystem: Shows only events matching BOTH criteria
- Text search + Filters: Further narrows results

**Filter persistence:**
- Filters remain active until manually changed
- No preset saving in current version

---

## Event Details

### Viewing Event Information

**Click any event row to see details in the context panel:**
- **Timestamp (Monotonic):** Seconds since system boot (float)
- **Timestamp (Realtime):** Wall-clock time (ISO format)
- **Severity:** Log level with color coding
- **Subsystem:** Component that generated the message
- **PID:** Process ID (if available from parsing)
- **CPU:** CPU core number (if mentioned in message)
- **Message:** Parsed message content
- **Raw:** Original kernel log line
- **Source:** Log source (dmesg/journalctl)
- **Annotations:** Plugin-generated annotations (if any)

### Continuation Lines

Multi-line kernel messages (stack traces, hex dumps) are automatically merged:
```
[12345.678] kernel: BUG: unable to handle kernel paging request
[12345.678]   Code: 8b 45 f4 89 c2 ...
[12345.678]   Call Trace:
[12345.678]    ? some_function+0x42/0x100
```

These appear as single expandable events in the table.

### Context Menu

**Right-click context menu is not implemented in current version.**

---

## Export and Saving

### Export Logs

**Export Raw Logs:**
- Menu → **File → Export Logs (Raw)**
- Exports all currently loaded events
- Formats: Text (.txt), CSV (.csv)

**Export Filtered Logs:**
- Menu → **File → Export Logs (Filtered)**
- Exports only events matching current filters
- Same format options as raw export

**Note:** Export functionality is not fully implemented in current version.

### Session Management

**Session saving/loading is not implemented in current version.**

---

## Plugin Usage

### Available Plugins

RingBuffer includes example plugins demonstrating the plugin API:

#### USB Watcher Plugin
**Purpose:** Detect and annotate USB device events

**Features:**
- Monitors USB subsystem messages
- Annotates device connections: "🔌 USB device connected"
- Annotates disconnections: "❌ USB device disconnected"
- Annotates errors: "⚠️ USB error detected"

#### OOM Detector Plugin
**Purpose:** Identify out-of-memory killer events

**Features:**
- Detects OOM killer invocations
- Counts OOM events: "💀 OOM Kill #1"
- Monitors memory pressure warnings: "⚠️ Memory pressure"

#### KASAN Decoder Plugin
**Purpose:** Process Kernel Address Sanitizer reports

**Features:**
- Parses KASAN error reports
- Extracts memory corruption details
- Annotates with severity indicators

### Managing Plugins

**Plugin management UI is not implemented in current version.**

**Loading plugins:**
- Plugins are loaded automatically from the plugins/ directory
- Example plugins are included but may need activation

---

## Advanced Features

### Live Streaming

**Real-time event streaming:**
- Polls kernel sources every 150ms for new events
- Automatically appends new events to the table
- Respects current filters when adding events
- Auto-scrolls to bottom when enabled

### Timestamp Formats

**Toggle timestamp display:**
- Menu → **View → Toggle Timestamp Format** (or `Ctrl+T`)
- Switches between monotonic and realtime timestamps in table

### Theme Support

**Dark theme:**
- Applied automatically on startup
- Custom styling for table, panels, and status bar
- Consistent color scheme for severity levels

### Permission Checking

**Check system permissions:**
- Menu → **Settings → Check Permissions**
- Verifies access to dmesg and journalctl
- Shows available log sources

---

## Keyboard Shortcuts

### Global

| Shortcut | Action |
|----------|--------|
| `Ctrl+Q` | Exit application |
| `Space` | Start live stream |
| `Ctrl+Space` | Pause stream |
| `Ctrl+Shift+Space` | Resume stream |
| `Ctrl+Shift+Delete` | Clear kernel buffer |

### View

| Shortcut | Action |
|----------|--------|
| `Ctrl+T` | Toggle timestamp format |
| `Ctrl+A` | Toggle auto-scroll |

### Export

| Shortcut | Action |
|----------|--------|
| *(Not implemented)* | Export raw logs |
| *(Not implemented)* | Export filtered logs |

---

## Tips and Best Practices

### Performance Optimization

**For high-volume systems:**
1. **Enable filtering early:** Use severity filters to hide DEBUG/INFO
2. **Monitor resource usage:** High event rates may impact UI responsiveness
3. **Pause when analyzing:** Pause streaming to examine events without new data

### Effective Debugging Workflows

**Finding the root cause:**
1. Start with ERROR/CRIT only filters
2. Note timestamps of first errors
3. Expand time range by adjusting filters
4. Look for patterns in subsystem and message content

**USB debugging:**
1. Filter by USB subsystem
2. Enable USB Watcher plugin for annotations
3. Look for connection/disconnection patterns
4. Correlate with application errors

**Memory issues:**
1. Enable OOM Detector plugin
2. Filter for memory-related subsystems
3. Monitor for pressure warnings and OOM kills

### Security Monitoring

**Monitor for suspicious activity:**
1. Set up regex searches for security keywords
2. Filter for SECURITY subsystem events
3. Look for permission denials and access failures
4. Use plugins for automated alerting

### Kernel Development

**While testing drivers:**
1. Clear kernel buffer before testing
2. Monitor specific subsystems related to your driver
3. Use regex search for driver-specific messages
4. Export logs for documentation

---

## Common Use Cases

### Troubleshooting USB Device Issues

**Scenario:** USB device keeps disconnecting

**Steps:**
1. Start RingBuffer and enable USB subsystem filter
2. Load USB Watcher plugin for annotations
3. Reproduce the disconnect issue
4. Look for error patterns in USB messages
5. Check device enumeration failures

### Investigating System Crashes

**Scenario:** System instability or crashes

**Steps:**
1. Launch RingBuffer after boot
2. Filter for EMERG/CRIT/ERR severities
3. Look for kernel panic messages
4. Check for OOM killer events
5. Examine stack traces in continuation lines

### Monitoring Driver Initialization

**Scenario:** Testing new kernel driver

**Steps:**
1. Clear kernel buffer before loading driver
2. Start streaming with relevant subsystem filters
3. Load the driver module
4. Monitor for initialization messages
5. Check for probe failures or errors

### Network Performance Analysis

**Scenario:** Investigating network issues

**Steps:**
1. Filter for NETWORK subsystem
2. Search for error keywords in messages
3. Look for interface state changes
4. Monitor for packet drop indicators

---

## Troubleshooting

### No Events Appearing

**Check:**
1. Streaming status in status bar (should show "Streaming active ✓")
2. Permissions: Run `dmesg` or `journalctl -k` manually to verify access
3. Filters: Ensure filters aren't excluding all events
4. Source availability: Check Settings → Check Permissions

### High CPU Usage

**Solutions:**
1. Reduce polling frequency (not configurable in UI)
2. Enable more restrictive filters
3. Pause streaming when not actively monitoring

### Events Not Updating

**Causes:**
- Streaming is paused (check status bar)
- Auto-scroll disabled (toggle with Ctrl+A)
- Filters excluding new events
- Permission issues with log sources

### Permission Errors

**Solutions:**
1. Run RingBuffer with elevated privileges: `sudo ringbuffer`
2. Check Settings → Check Permissions for details
3. Ensure user is in appropriate groups (usually 'adm' or 'systemd-journal')

---

## Getting Help

**Resources:**
- [Installation Guide](INSTALL.md) - Setup and permissions
- [Plugin Development](PLUGINS.md) - Extending functionality
- Plugin source code in `plugins/` directory
- Core engine code in `core/` directory

**Community:**
- Check GitHub repository for issues and updates
- Review example plugins for API usage
- Examine core modules for internal architecture

---

**Happy kernel debugging! 🔍**