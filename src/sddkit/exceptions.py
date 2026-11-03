"""Custom exceptions for SDDKit.

All SDDKit exceptions inherit from SDDKitError so callers can catch the
entire family with a single except clause.
"""
from __future__ import annotations

__all__ = ["SDDKitError", "GenerateError", "TraceError", "GateError", "AuditError", "EvalError"]


class SDDKitError(Exception):
    """Base class for all SDDKit errors."""


class GenerateError(SDDKitError):
    """Raised when template rendering or file generation fails."""


class TraceError(SDDKitError):
    """Raised when the traceability checker encounters a fatal parse error."""


class GateError(SDDKitError):
    """Raised when an approval gate operation fails (e.g. prerequisite not met)."""


class AuditError(SDDKitError):
    """Raised when audit log reading/writing fails."""


class EvalError(SDDKitError):
    """Raised when the eval harness encounters an unrecoverable error."""
