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
    
    # Phase 1: Core Abstraction and Registry
    if phase is None or phase == 1:
        logger.info("Running Phase 1 development tests...")
        logger.info("Running Phase 1 tests: Core Abstraction and Registry")
        try:
            from tests.dev_test_phase1_settings import run_phase1_tests
            if not run_phase1_tests():
            from tests.dev_test_llmprovider_base import run_llm_provider_base_tests
            from tests.dev_test_provider_registry import run_provider_registry_tests
            
            if not run_llm_provider_base_tests():
                success = False
                
            if not run_provider_registry_tests():
                success = False
                
        except ImportError as e:
            logger.error(f"Could not import Phase 1 development tests: {e}")
            success = False
        except Exception as e:
            logger.error(f"Phase 1 development tests failed: {e}")
            success = False
    
    # Phase 2: Provider Implementations
    if phase is None or phase == 2:
        logger.info("Running Phase 2 tests: Provider Implementations")
        try:
            from tests.dev_test_provider_implementations import TestProviderImplementations
            import unittest
            
            suite = unittest.TestLoader().loadTestsFromTestCase(TestProviderImplementations)
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            if not result.wasSuccessful():
                success = False
                logger.error(f"Phase 2 tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
            else:
                logger.info("Phase 2 tests passed successfully")
                
        except ImportError as e:
            logger.error(f"Could not import Phase 2 development tests: {e}")
            success = False
        except Exception as e:
            logger.error(f"Phase 2 development tests failed: {e}")
            success = False
    
    # Phase 3: Integration and End-to-End Testing
    if phase is None or phase == 3:
        logger.info("Running Phase 3 tests: Integration and End-to-End Testing")
        try:
            from tests.integration_test_ollama import run_ollama_integration_tests
            from tests.integration_test_openai import run_openai_integration_tests
            
            # Run Ollama integration tests
            logger.info("Running Ollama integration tests...")
            if not run_ollama_integration_tests():
                logger.warning("Ollama integration tests failed (may be due to missing configuration)")
                # Don't fail the entire test suite for integration test failures
                # as they may be due to missing API keys or services
            
            # Run OpenAI integration tests  
            # logger.info("Running OpenAI integration tests...")
            # if not run_openai_integration_tests():
            #     logger.warning("OpenAI integration tests failed (may be due to missing API key)")
            #     # Don't fail the entire test suite for integration test failures
                
            logger.info("Phase 3 integration tests completed (check individual results above)")
            
        except ImportError as e:
            logger.error(f"Could not import Phase 3 integration tests: {e}")
            success = False
        except Exception as e:
            logger.error(f"Phase 3 integration tests failed: {e}")
            success = False
    
    return success


def run_regression_tests():
    """Run regression tests to ensure existing functionality isn't broken."""
    logger.info("Running regression tests...")
    try:
        from tests.regression_test_persistent_settings import run_regression_tests as run_persistent_settings_regression_tests
        if not run_persistent_settings_regression_tests():
            return False
        
        from tests.test_versioning import run_regression_tests as run_versioning_regression_tests
        if not run_versioning_regression_tests():
            return False
    
    except ImportError as e:
        logger.error(f"Could not import regression tests: {e}")
        return False
    except Exception as e:
        logger.error(f"Regression tests failed: {e}")
        return False

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
