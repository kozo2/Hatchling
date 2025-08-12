"""Test decorators for standardized test categorization and tagging.

This module provides reusable decorators for marking tests with specific
characteristics, enabling selective test execution and proper organization.
"""

import functools


def slow_test(func):
    """Mark test as slow-running (>5 seconds).
    
    Usage:
        @slow_test
        def test_large_dataset_processing(self):
            pass
    """
    func._slow = True
    return func


def requires_api_key(func):
    """Mark test as requiring API credentials.
    
    Usage:
        @requires_api_key
        def test_openai_integration(self):
            pass
    """
    func._requires_api_key = True
    return func


def integration_test(func):
    """Mark test as integration test (testing component interactions).
    
    Usage:
        @integration_test
        def test_mcp_tool_execution_flow(self):
            pass
    """
    func._integration = True
    return func


def requires_external_service(service_name):
    """Mark test as requiring specific external service.
    
    Args:
        service_name (str): Name of the required service (e.g., 'ollama', 'openai', 'mcp_server')
    
    Usage:
        @requires_external_service("ollama")
        def test_ollama_streaming(self):
            pass
    """
    def decorator(func):
        func._requires_service = service_name
        return func
    return decorator


def development_test(phase=None):
    """Mark test as development test for temporary validation.
    
    Args:
        phase (int, optional): Development phase number
    
    Usage:
        @development_test(phase=1)
        def test_event_foundation(self):
            pass
    """
    def decorator(func):
        func._development = True
        if phase is not None:
            func._phase = phase
        return func
    return decorator


def regression_test(func):
    """Mark test as regression test (permanent, prevents breaking changes).
    
    Usage:
        @regression_test
        def test_existing_api_compatibility(self):
            pass
    """
    func._regression = True
    return func


def feature_test(func):
    """Mark test as feature test (permanent, validates new functionality).
    
    Usage:
        @feature_test
        def test_new_command_system(self):
            pass
    """
    func._feature = True
    return func


def requires_mcp_server(func):
    """Mark test as requiring MCP server functionality.
    
    Usage:
        @requires_mcp_server
        def test_tool_execution(self):
            pass
    """
    func._requires_mcp = True
    return func


def skip_in_ci(func):
    """Mark test to be skipped in CI environments.
    
    Usage:
        @skip_in_ci
        def test_interactive_feature(self):
            pass
    """
    func._skip_ci = True
    return func
