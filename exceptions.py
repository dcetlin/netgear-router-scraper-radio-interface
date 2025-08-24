"""
Custom exceptions for router controller.
"""


class RouterControllerError(Exception):
    """Base exception for router controller errors"""
    pass


class NetworkConnectionError(RouterControllerError):
    """Raised when not connected to target network"""
    pass


class AuthenticationError(RouterControllerError):
    """Raised when login fails"""
    pass


class RouterUIError(RouterControllerError):
    """Raised when router UI elements cannot be found or interacted with"""
    pass


class WebDriverError(RouterControllerError):
    """Raised when WebDriver initialization or operation fails"""
    pass