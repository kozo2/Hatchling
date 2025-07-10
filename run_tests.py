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
    success = True
    
    if phase is None or phase == 1:
        logger.info("Running Phase 1 development tests...")
        try:
            from tests.dev_test_phase1_settings import run_phase1_tests
            if not run_phase1_tests():
                success = False
        except ImportError as e:
            logger.error(f"Could not import Phase 1 tests: {e}")
            success = False
        except Exception as e:
            logger.error(f"Phase 1 tests failed: {e}")
            success = False
    
    # Add future phases here
    # if phase is None or phase == 2:
    #     ...
    
    return success


def run_regression_tests():
    """Run regression tests to ensure existing functionality isn't broken."""
    logger.info("Running regression tests...")
    
    # TODO: Implement regression tests for existing ChatSettings functionality
    logger.info("No regression tests implemented yet")
    return True


def run_feature_tests():
    """Run feature tests for new functionality."""
    logger.info("Running feature tests...")
    
    # TODO: Implement feature tests for the new settings system
    logger.info("No feature tests implemented yet")
    return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run Hatchling settings tests")
    parser.add_argument("--development", action="store_true", 
                       help="Run development tests")
    parser.add_argument("--regression", action="store_true",
                       help="Run regression tests")
    parser.add_argument("--feature", action="store_true",
                       help="Run feature tests")
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
