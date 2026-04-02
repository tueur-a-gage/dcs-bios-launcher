"""Module for custom exceptions related to configuration errors.
"""
class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""

class CommunicationError(Exception):
    """Raised when there is an error related to communication with ports."""