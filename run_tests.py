#!/usr/bin/env python3
"""
Test runner script for fractal application tests.
"""

import unittest
import sys
import os

def run_all_tests():
    """Discover and run all tests."""
    # add the current directory to the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir='.', pattern='test_*.py')
    
    # run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return 0 if result.wasSuccessful() else 1

def run_specific_test(test_name):
    """Run a specific test module or test case."""
    test_loader = unittest.TestLoader()
    
    if test_name.endswith('.py'):
        test_suite = test_loader.discover('.', pattern=test_name)
    else:
        try:
            test_suite = test_loader.loadTestsFromName(test_name)
        except (AttributeError, ImportError):
            print(f"Test '{test_name}' not found.")
            return 1
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # run specific test
        exit_code = run_specific_test(sys.argv[1])
    else:
        # run all tests
        exit_code = run_all_tests()
    
    sys.exit(exit_code)