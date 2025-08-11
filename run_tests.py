#!/usr/bin/env python3
"""Test runner for Hatchling test suite.

This script provides a centralized way to run different types of tests:
- Development tests: Deprecated (functionality moved to feature/regression tests)
- Regression tests: Permanent tests to ensure existing functionality isn't broken
- Feature tests: Permanent tests for new functionality
- Integration tests: Tests that validate component interactions

Usage:
    python run_tests.py [--development] [--regression] [--feature] [--integration] [--all]
    python run_tests.py [--file TEST_FILE] [--test TEST_METHOD] [--skip-slow]
"""

import sys
import logging
import argparse
import unittest
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_results.log")
    ]
)
logger = logging.getLogger("hatchling.test_runner")


def discover_tests(test_type=None, file=None, test_name=None, skip_tags=None):
    """Dynamically build test suites based on criteria.
    
    Args:
        test_type (str): Type of tests to discover ('development', 'regression', 'feature', 'integration')
        file (str): Specific test file to run
        test_name (str): Specific test method to run
        skip_tags (list): Tags to skip (e.g., ['slow'])
        
    Returns:
        unittest.TestSuite: Configured test suite
    """
    suite = unittest.TestSuite()
    
    if file:
        # Run specific file
        if test_name:
            # Run specific test method
            module_name = file.replace('.py', '').replace('/', '.').replace('\\', '.')
            if module_name.startswith('tests.'):
                module_name = module_name[6:]  # Remove 'tests.' prefix
            module = __import__(f'tests.{module_name}', fromlist=[module_name])
            
            # Find the test class and method
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, unittest.TestCase):
                    if hasattr(attr, test_name):
                        suite.addTest(attr(test_name))
                        break
        else:
            # Run all tests in file
            loader = unittest.TestLoader()
            tests_dir = Path(__file__).parent / 'tests'
            file_path = tests_dir / file
            if file_path.exists():
                module_name = file.replace('.py', '').replace('/', '.').replace('\\', '.')
                module = __import__(f'tests.{module_name}', fromlist=[module_name])
                suite.addTests(loader.loadTestsFromModule(module))
    else:
        # Discover tests by type
        tests_dir = Path(__file__).parent / 'tests'
        loader = unittest.TestLoader()
        
        if test_type == 'development':
            pattern = 'dev_test_*.py'
        elif test_type == 'regression':
            pattern = 'regression_test_*.py'
        elif test_type == 'feature':
            pattern = 'feature_test_*.py'
        elif test_type == 'integration':
            pattern = 'integration_test_*.py'
        else:
            pattern = '*test*.py'
        
        discovered = loader.discover(str(tests_dir), pattern=pattern)
        
        # Filter by tags if specified
        if skip_tags:
            filtered_suite = unittest.TestSuite()
            for test_group in discovered:
                for test_case in test_group:
                    if hasattr(test_case, '_testMethodName'):
                        method = getattr(test_case, test_case._testMethodName)
                        should_skip = False
                        for tag in skip_tags:
                            if hasattr(method, f'_{tag}'):
                                should_skip = True
                                break
                        if not should_skip:
                            filtered_suite.addTest(test_case)
            suite.addTests(filtered_suite)
        else:
            suite.addTests(discovered)
    
    return suite


def determine_type_from_args(args):
    """Determine test type from command line arguments."""
    if args.development:
        return 'development'
    elif args.regression:
        return 'regression'
    elif args.feature:
        return 'feature'
    elif args.integration:
        return 'integration'
    else:
        return None  # Run all types


def run_development_tests(phase=None):
    """Run development tests for specific phases.
    
    Note: Development tests are now deprecated. Most functionality has been
    moved to feature tests and regression tests. This function is kept for
    backward compatibility but logs a deprecation warning.
    
    Args:
        phase (int, optional): Specific phase to test. If None, runs all phases.
    """
    logger.warning("Development tests are deprecated. Most functionality has been moved to feature tests.")
    logger.info("Running development tests...")
    
    # No development tests remain - they have been converted to feature tests
    # or removed as obsolete
    logger.info("No development tests to run - functionality moved to feature and regression tests")
    return True


def run_regression_tests():
    """Run regression tests to ensure existing functionality isn't broken."""
    logger.info("Running regression tests...")
    success = True
    
    # Test existing event handling
    try:
        from tests.regression_test_existing_events import run_regression_tests as run_existing_events_regression_tests
        if not run_existing_events_regression_tests():
            logger.error("Existing events regression tests failed")
            success = False
    except ImportError as e:
        logger.error(f"Could not import existing events regression tests: {e}")
        success = False
    except Exception as e:
        logger.error(f"Existing events regression tests failed: {e}")
        success = False
    
    # Test existing MCP functionality
    try:
        from tests.regression_test_mcp_functionality import run_regression_tests as run_mcp_regression_tests
        if not run_mcp_regression_tests():
            logger.error("MCP functionality regression tests failed")
            success = False
    except ImportError as e:
        logger.error(f"Could not import MCP functionality regression tests: {e}")
        success = False
    except Exception as e:
        logger.error(f"MCP functionality regression tests failed: {e}")
        success = False
    
    # MCP Tooling regression tests - Phase 3
    logger.info("Running MCP Tooling Phase 3 regression tests...")
    try:
        from tests.regression_test_tool_management import run_regression_tests
        if not run_regression_tests():
            logger.error("MCP Tool Management regression tests failed")
            success = False
    except ImportError as e:
        logger.error(f"Could not import MCP Tool Management regression tests: {e}")
        success = False
    except Exception as e:
        logger.error(f"MCP Tool Management regression tests failed: {e}")
        success = False
    
    # Enhanced Tool Execution regression tests - Phase 4
    logger.info("Running Enhanced Tool Execution Phase 4 regression tests...")
    try:
        from tests.regression_test_enhanced_tool_execution import run_tool_execution_regression_tests
        if not run_tool_execution_regression_tests():
            logger.error("Enhanced Tool Execution regression tests failed")
            success = False
    except ImportError as e:
        logger.error(f"Could not import Enhanced Tool Execution regression tests: {e}")
        success = False
    except Exception as e:
        logger.error(f"Enhanced Tool Execution regression tests failed: {e}")
        success = False
    
    # Test persistent settings (commented out as these may not exist yet)
    # try:
    #     from tests.regression_test_persistent_settings import run_regression_tests as run_persistent_settings_regression_tests
    #     if not run_persistent_settings_regression_tests():
    #         return False
    #     
    #     from tests.regression_test_versioning import run_regression_tests as run_versioning_regression_tests
    #     if not run_versioning_regression_tests():
    #         return False
    # except ImportError as e:
    #     logger.error(f"Could not import persistent settings regression tests: {e}")
    #     return False
    # except Exception as e:
    #     logger.error(f"Regression tests failed: {e}")
    #     return False

    return success


def run_feature_tests():
    """Run feature tests for new functionality."""
    logger.info("Running feature tests...")
    success = True
    
    # LLM Provider Base feature tests
    logger.info("Running LLM Provider Base feature tests...")
    try:
        from tests.feature_test_llm_provider_base import run_llm_provider_base_feature_tests
        if not run_llm_provider_base_feature_tests():
            logger.error("LLM Provider Base feature tests failed")
            success = False
    except ImportError as e:
        logger.error(f"Could not import LLM Provider Base feature tests: {e}")
        success = False
    except Exception as e:
        logger.error(f"LLM Provider Base feature tests failed: {e}")
        success = False
    
    # Provider Registry feature tests
    logger.info("Running Provider Registry feature tests...")
    try:
        from tests.feature_test_provider_registry import run_provider_registry_feature_tests
        if not run_provider_registry_feature_tests():
            logger.error("Provider Registry feature tests failed")
            success = False
    except ImportError as e:
        logger.error(f"Could not import Provider Registry feature tests: {e}")
        success = False
    except Exception as e:
        logger.error(f"Provider Registry feature tests failed: {e}")
        success = False
    
    # Event System feature tests
    logger.info("Running Event System feature tests...")
    try:
        from tests.feature_test_event_system import run_event_system_tests
        if not run_event_system_tests():
            logger.error("Event System feature tests failed")
            success = False
    except ImportError as e:
        logger.error(f"Could not import Event System feature tests: {e}")
        success = False
    except Exception as e:
        logger.error(f"Event System feature tests failed: {e}")
        success = False
    
    return success


def run_integration_tests():
    """Run integration tests for command system and tool call flow."""
    logger.info("Running integration tests...")
    success = True
    
    # Command System Integration tests
    logger.info("Running Command System integration tests...")
    try:
        from tests.integration_test_command_system import run_command_system_integration_tests
        if not run_command_system_integration_tests():
            logger.error("Command System integration tests failed")
            success = False
    except ImportError as e:
        logger.error(f"Could not import Command System integration tests: {e}")
        success = False
    except Exception as e:
        logger.error(f"Command System integration tests failed: {e}")
        success = False
    
    # Tool Call Flow Integration tests  
    logger.info("Running Tool Call Flow integration tests...")
    try:
        from tests.integration_test_tool_call_flow import run_tool_call_flow_integration_tests
        if not run_tool_call_flow_integration_tests():
            logger.error("Tool Call Flow integration tests failed")
            success = False
    except ImportError as e:
        logger.error(f"Could not import Tool Call Flow integration tests: {e}")
        success = False
    except Exception as e:
        logger.error(f"Tool Call Flow integration tests failed: {e}")
        success = False
    
    return success


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run Hatchling test suite")
    parser.add_argument("--development", "--dev", action="store_true", 
                       help="Run development tests (deprecated)")
    parser.add_argument("--regression", action="store_true",
                       help="Run regression tests")
    parser.add_argument("--feature", action="store_true",
                       help="Run feature tests")
    parser.add_argument("--integration", action="store_true",
                       help="Run integration tests")
    parser.add_argument("--all", action="store_true",
                       help="Run all test types")
    parser.add_argument("--file", help="Run tests from specific file")
    parser.add_argument("--test", help="Run specific test method")
    parser.add_argument("--skip-slow", action="store_true",
                       help="Skip tests marked as slow")
    parser.add_argument("--phase", type=int,
                       help="Run development tests for specific phase only (deprecated)")
    
    args = parser.parse_args()
    
    # If no specific test type is specified, run all
    if not any([args.development, args.regression, args.feature, args.integration, args.all, args.file]):
        args.all = True
    
    success = True
    
    # Handle specific file or test
    if args.file or args.test:
        logger.info("=" * 50)
        if args.test:
            logger.info(f"RUNNING SPECIFIC TEST: {args.test}")
        else:
            logger.info(f"RUNNING TESTS FROM FILE: {args.file}")
        logger.info("=" * 50)
        
        skip_tags = ["slow"] if args.skip_slow else None
        suite = discover_tests(
            test_type=None,
            file=args.file,
            test_name=args.test,
            skip_tags=skip_tags
        )
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        success = result.wasSuccessful()
    else:
        # Run test types using existing functions for backward compatibility
        if args.all or args.development:
            logger.info("=" * 50)
            logger.info("DEVELOPMENT TESTS")
            logger.info("=" * 50)
            if not run_development_tests(args.phase):
                success = False
        
        if args.all or args.regression:
            logger.info("=" * 50)
            logger.info("REGRESSION TESTS")
            logger.info("=" * 50)
            if not run_regression_tests():
                success = False
        
        if args.all or args.feature:
            logger.info("=" * 50)
            logger.info("FEATURE TESTS")
            logger.info("=" * 50)
            if not run_feature_tests():
                success = False
        
        if args.all or args.integration:
            logger.info("=" * 50)
            logger.info("INTEGRATION TESTS")
            logger.info("=" * 50)
            if not run_integration_tests():
                success = False
    
    if success:
        logger.info("=" * 50)
        logger.info("ALL TESTS PASSED! [OK]")
        logger.info("=" * 50)
        sys.exit(0)
    else:
        logger.error("=" * 50)
        logger.error("SOME TESTS FAILED! [FAIL]")
        logger.error("=" * 50)
        sys.exit(1)


if __name__ == "__main__":
    main()
