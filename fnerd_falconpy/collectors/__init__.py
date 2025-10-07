"""
Collector classes for forensic data collection.
"""

from fnerd_falconpy.collectors.collectors import (
    BrowserHistoryCollector,
    ForensicCollector
)
from fnerd_falconpy.collectors.uac_collector import UACCollector

__all__ = [
    "BrowserHistoryCollector",
    "ForensicCollector",
    "UACCollector",
]