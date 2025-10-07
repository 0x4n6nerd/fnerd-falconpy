"""
API client module for CrowdStrike Falcon API interactions.
"""

from fnerd_falconpy.api.clients import (
    DiscoverAPIClient,
    RTRAPIClient
)

from fnerd_falconpy.api.clients_optimized import (
    OptimizedDiscoverAPIClient,
    OptimizedRTRAPIClient
)

__all__ = [
    "DiscoverAPIClient",
    "RTRAPIClient",
    "OptimizedDiscoverAPIClient",
    "OptimizedRTRAPIClient",
]