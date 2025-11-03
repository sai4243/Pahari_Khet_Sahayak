"""
Internet Connectivity Check Module
Provides utilities to check if internet connection is available.
"""
import socket
import requests
import time

def check_internet_connectivity(timeout: int = 3) -> bool:
    """
    Check if internet connection is available.
    
    Args:
        timeout: Timeout in seconds for the connection check
    
    Returns:
        True if internet is available, False otherwise
    """
    # First, try a quick DNS lookup (faster)
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except (socket.error, OSError):
        pass
    
    # Fallback: Try to reach a reliable server
    try:
        response = requests.get("https://www.google.com", timeout=timeout)
        return response.status_code == 200
    except (requests.RequestException, Exception):
        return False

def check_api_connectivity(api_url: str = "https://generativelanguage.googleapis.com", timeout: int = 5) -> bool:
    """
    Check if a specific API endpoint is reachable.
    
    Args:
        api_url: URL of the API endpoint to check
        timeout: Timeout in seconds
    
    Returns:
        True if API is reachable, False otherwise
    """
    try:
        response = requests.get(api_url, timeout=timeout)
        return response.status_code in [200, 401, 403]  # Even 401/403 means server is reachable
    except (requests.RequestException, Exception):
        return False

def is_online() -> bool:
    """
    Simple wrapper to check if the system is online.
    Uses a lightweight check first, then falls back to HTTP check.
    """
    return check_internet_connectivity()

