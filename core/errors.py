"""
Custom exceptions for the kernel log engine.
"""


class KernelLogError(Exception):
    """Base exception for kernel log engine errors."""
    pass


class SourceUnavailableError(KernelLogError):
    """Raised when all log sources are unavailable."""
    pass


class PermissionDeniedError(KernelLogError):
    """Raised when insufficient permissions to access kernel logs."""
    pass


class ParsingError(KernelLogError):
    """Raised when event parsing fails."""
    pass


class PluginError(KernelLogError):
    """Raised when plugin execution fails."""
    pass


class PluginLoadError(PluginError):
    """Raised when plugin cannot be loaded."""
    pass


class PluginVersionError(PluginError):
    """Raised when plugin version is incompatible."""
    pass
