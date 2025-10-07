"""
Host Response Actions module for network isolation and containment.
"""

from .isolation import (
    HostIsolationManager,
    IsolationStatus,
    IsolationAction,
    IsolationResult,
    BatchIsolationResult
)

from .policies import (
    ResponsePolicyManager,
    ResponsePolicy,
    PolicyAction
)

__all__ = [
    # Isolation
    "HostIsolationManager",
    "IsolationStatus",
    "IsolationAction",
    "IsolationResult",
    "BatchIsolationResult",
    
    # Policies
    "ResponsePolicyManager",
    "ResponsePolicy",
    "PolicyAction",
]