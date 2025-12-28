"""
Kernel log source adapters for dmesg and journalctl.
Handles both snapshot and live-stream modes.
"""

import asyncio
import logging
import subprocess
from typing import AsyncIterator, Optional
from core.event import KernelEvent
from core.parser import KernelLogParser
from core.permissions import PermissionChecker
from core.errors import SourceUnavailableError, PermissionDeniedError


logger = logging.getLogger(__name__)


class LogSource:
    """Abstract base for log sources."""
    
    async def get_snapshot(self) -> list[KernelEvent]:
        """Get initial snapshot of logs."""
        raise NotImplementedError
    
    async def stream_live(self) -> AsyncIterator[KernelEvent]:
        """Stream live logs indefinitely."""
        raise NotImplementedError


class DmesgSource(LogSource):
    """Adapter for dmesg log source."""
    
    def __init__(self, buffer_size: int = 100):
        self.buffer_size = buffer_size
        self.last_lines = []
    
    async def get_snapshot(self) -> list[KernelEvent]:
        """Get recent kernel logs from dmesg."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ['dmesg', '-L'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise PermissionDeniedError("Cannot read dmesg: permission denied")
            
            events = []
            for line in result.stdout.strip().split('\n'):
                event = KernelLogParser.parse_dmesg_line(line, source='dmesg')
                if event:
                    events.append(event)
            
            self.last_lines = result.stdout.strip().split('\n')[-self.buffer_size:]
            return events
        
        except FileNotFoundError:
            raise SourceUnavailableError("dmesg not found")
        except asyncio.TimeoutError:
            raise SourceUnavailableError("dmesg timeout")
    
    async def stream_live(self) -> AsyncIterator[KernelEvent]:
        """Stream live kernel logs using dmesg -w."""
        try:
            process = await asyncio.create_subprocess_exec(
                'dmesg', '-w', '-L',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=4096  # 4KB line buffer
            )
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                decoded = line.decode('utf-8', errors='replace').strip()
                event = KernelLogParser.parse_dmesg_line(decoded, source='dmesg')
                if event:
                    yield event
        
        except FileNotFoundError:
            raise SourceUnavailableError("dmesg -w not available")
        except Exception as e:
            logger.error(f"dmesg stream error: {e}")
            raise
        finally:
            if process:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=2)
                except asyncio.TimeoutError:
                    process.kill()


class JournalctlSource(LogSource):
    """Adapter for journalctl kernel log source."""
    
    def __init__(self, buffer_size: int = 100):
        self.buffer_size = buffer_size
    
    async def get_snapshot(self) -> list[KernelEvent]:
        """Get recent kernel logs from journalctl."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ['journalctl', '-k', '-n', str(self.buffer_size), '-o', 'short'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise PermissionDeniedError("Cannot read journalctl: permission denied")
            
            events = []
            for line in result.stdout.strip().split('\n'):
                # journalctl format differs, parse accordingly
                event = KernelLogParser.parse_dmesg_line(line, source='journal')
                if event:
                    events.append(event)
            
            return events
        
        except FileNotFoundError:
            raise SourceUnavailableError("journalctl not found")
        except asyncio.TimeoutError:
            raise SourceUnavailableError("journalctl timeout")
    
    async def stream_live(self) -> AsyncIterator[KernelEvent]:
        """Stream live kernel logs using journalctl -kf."""
        try:
            process = await asyncio.create_subprocess_exec(
                'journalctl', '-k', '-f', '-o', 'short',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=4096
            )
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                decoded = line.decode('utf-8', errors='replace').strip()
                event = KernelLogParser.parse_dmesg_line(decoded, source='journal')
                if event:
                    yield event
        
        except FileNotFoundError:
            raise SourceUnavailableError("journalctl not available")
        except Exception as e:
            logger.error(f"journalctl stream error: {e}")
            raise
        finally:
            if process:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=2)
                except asyncio.TimeoutError:
                    process.kill()
