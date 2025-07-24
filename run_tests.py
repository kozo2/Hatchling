#!/usr/bin/env python3
"""Test runner for Hatchling settings system development and regression tests.

This script provides a centralized way to run different types of tests:
- Development tests: Temporary tests to validate specific implementation phases
- Regression tests: Permanent tests to ensure existing functionality isn't broken
- Feature tests: Permanent tests for new functionality

Usage:
    python run_tests.py [--development] [--regression] [--feature] [--phase N]
"""

import sys
import logging
import argparse
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


def run_development_tests(phase=None):
    """Run development tests for specific phases.
    
    Args:
        phase (int, optional): Specific phase to test. If None, runs all phases.
    """
    logger.info("Running development tests...")
    
    success = True
    
    # Phase 1 tests
    if phase is None or phase == 1:
        logger.info("Running Phase 1 development tests...")
        
        try:
            from tests.dev_test_stream_events import run_stream_events_foundation_tests
            if not run_stream_events_foundation_tests():
                logger.error("Phase 1 stream events foundation tests failed")
                success = False
        except ImportError as e:
            logger.error(f"Could not import Phase 1 development tests: {e}")
            success = False
        except Exception as e:
            logger.error(f"Phase 1 development tests failed: {e}")
            success = False
    
    # Phase 2 tests
    if phase is None or phase == 2:
        logger.info("Running Phase 2 development tests...")
        
        try:
            from tests.dev_test_mcp_manager_events import run_mcp_manager_event_publishing_tests
            if not run_mcp_manager_event_publishing_tests():
                logger.error("Phase 2 MCPManager event publishing tests failed")
                success = False
        except ImportError as e:
            logger.error(f"Could not import Phase 2 development tests: {e}")
            success = False
        except Exception as e:
            logger.error(f"Phase 2 development tests failed: {e}")
            success = False
    
    # Phase 3 tests
    if phase is None or phase == 3:
        logger.info("Running Phase 3 development tests...")
        
        try:
            from tests.dev_test_tool_lifecycle import run_tool_lifecycle_management_tests
            if not run_tool_lifecycle_management_tests():
                logger.error("Phase 3 tool lifecycle management tests failed")
                success = False
        except ImportError as e:
            logger.error(f"Could not import Phase 3 development tests: {e}")
            success = False
        except Exception as e:
            logger.error(f"Phase 3 development tests failed: {e}")
            success = False
    
    # Phase 4 tests
    if phase is None or phase == 4:
        logger.info("Running Phase 4 development tests...")
        
        try:
            from tests.dev_test_enhanced_tool_execution import run_enhanced_tool_execution_tests
            if not run_enhanced_tool_execution_tests():
                logger.error("Phase 4 enhanced tool execution tests failed")
                success = False
        except ImportError as e:
            logger.error(f"Could not import Phase 4 development tests: {e}")
            success = False
        except Exception as e:
            logger.error(f"Phase 4 development tests failed: {e}")
            success = False
    
    return success


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
    
    # TODO: Implement feature tests for the new settings system
    logger.info("No feature tests implemented yet")
    return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run Hatchling settings tests")
    parser.add_argument("--development", "--dev", action="store_true", 
                       help="Run development tests")
    parser.add_argument("--regression", action="store_true",
                       help="Run regression tests")
    parser.add_argument("--feature", action="store_true",
                       help="Run feature tests")
    parser.add_argument("--integration", action="store_true",
                       help="Run integration tests")
    parser.add_argument("--phase", type=int,
                       help="Run development tests for specific phase only")
    parser.add_argument("--all", action="store_true",
                       help="Run all test types")
    
    args = parser.parse_args()
    
    # If no specific test type is specified, run all
    if not any([args.development, args.regression, args.feature, args.all]):
        args.all = True
    
    success = True
    
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
