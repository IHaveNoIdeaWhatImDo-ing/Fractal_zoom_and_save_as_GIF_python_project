#!/usr/bin/env python3
"""
Unit tests for main.py module.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import argparse
from PIL import Image, ImageTk

# Add the parent directory to the path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Tkinter for tests (since it may not be available in CI)
try:
    from tkinter import Tk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    # Create mock Tk class
    class MockTk:
        def __init__(self):
            self.title_calls = []
            self.update_calls = []
            self.mainloop_calls = []
        
        def title(self, title):
            self.title_calls.append(title)
        
        def update(self):
            self.update_calls.append(True)
        
        def mainloop(self):
            self.mainloop_calls.append(True)
    
    Tk = MockTk

# Now import the modules (after setting up mock if needed)
from main import validate_arguments, verify_func_not_malicious, FractalApp, main


class TestValidateArguments(unittest.TestCase):
    """Test the validate_arguments function."""
    
    def test_validate_arguments_valid(self):
        """Test with valid argument combinations."""
        # All arguments present
        args = {
            'function': 'z**2',
            'size': 512,
            'iterations': 50,
            'coordinates': (-2, -2, 2, 2),
            'color': (0, 0, 0, 255, 255, 255)
        }
        
        # Should not raise any exception
        try:
            validate_arguments(args)
        except Exception as e:
            self.fail(f"validate_arguments raised {type(e).__name__} unexpectedly: {e}")
    
    def test_validate_arguments_none_at_end(self):
        """Test with None at the end (should be valid)."""
        # Missing color only
        args = {
            'function': 'z**2',
            'size': 512,
            'iterations': 50,
            'coordinates': (-2, -2, 2, 2),
            'color': None
        }
        
        # Should not raise any exception (None at end is OK)
        try:
            validate_arguments(args)
        except Exception as e:
            self.fail(f"validate_arguments raised {type(e).__name__} unexpectedly: {e}")
    
    def test_validate_arguments_invalid_missing_middle(self):
        """Test with missing argument in the middle (should raise Exception)."""
        # Missing iterations (but color is specified)
        args = {
            'function': 'z**2',
            'size': 512,
            'iterations': None,
            'coordinates': (-2, -2, 2, 2),
            'color': (0, 0, 0, 255, 255, 255)
        }
        
        with self.assertRaises(Exception) as context:
            validate_arguments(args)
        
        self.assertIn('If a command line argument is present', str(context.exception))
    
    def test_validate_arguments_all_none(self):
        """Test with all None arguments."""
        args = {
            'function': None,
            'size': None,
            'iterations': None,
            'coordinates': None,
            'color': None
        }
        
        # Should not raise any exception
        try:
            validate_arguments(args)
        except Exception as e:
            self.fail(f"validate_arguments raised {type(e).__name__} unexpectedly: {e}")
    
    def test_validate_arguments_empty_dict(self):
        """Test with empty dictionary."""
        args = {}
        
        # Should not raise any exception
        try:
            validate_arguments(args)
        except Exception as e:
            self.fail(f"validate_arguments raised {type(e).__name__} unexpectedly: {e}")


class TestVerifyFuncNotMalicious(unittest.TestCase):
    """Test the verify_func_not_malicious function."""
    
    def test_verify_safe_functions(self):
        """Test that safe mathematical functions pass verification."""
        safe_functions = [
            'z**2',
            'z**3 + z',
            'abs(z)',
            'cmath.sin(z)',
            'cmath.cos(z) + cmath.sin(z)',
            'cmath.exp(z)',
            'cmath.log(z)',
            'cmath.sqrt(z)',
            'z * cmath.pi',
            'z / cmath.e',
            'cmath.phase(z)',
            'math.floor(abs(z))',
            'math.ceil(abs(z))',
            'math.trunc(abs(z))'
        ]
        
        for func in safe_functions:
            with self.subTest(func=func):
                self.assertTrue(
                    verify_func_not_malicious(func),
                    f"Safe function '{func}' was incorrectly flagged as malicious"
                )
    
    def test_verify_unsafe_functions(self):
        """Test that unsafe/blacklisted functions fail verification."""
        unsafe_functions = [
            '__import__("os").system("ls")',
            'eval("1+1")',
            'exec("import os")',
            'open("test.txt", "w")',
            'import os',
            'os.system',
            'subprocess.call',
            'globals()',
            'locals()',
            'compile(',
            'getattr',
            'setattr',
            'delattr',
            'hasattr'
        ]
        
        for func in unsafe_functions:
            with self.subTest(func=func):
                self.assertFalse(
                    verify_func_not_malicious(func),
                    f"Unsafe function '{func}' was incorrectly allowed"
                )
    
    def test_verify_edge_cases(self):
        """Test edge cases and tricky function strings."""
        # Complex numbers shouldn't be parsed as functions
        self.assertTrue(verify_func_not_malicious('z**2 + 3j'))
        self.assertTrue(verify_func_not_malicious('1+2j'))
        
        # Function with spaces
        self.assertTrue(verify_func_not_malicious('abs(z) + cmath.sin(z)'))
        
        # Empty string
        self.assertTrue(verify_func_not_malicious(''))
        
        # Just 'z'
        self.assertTrue(verify_func_not_malicious('z'))
    
    def test_verify_real_world_examples(self):
        """Test with real-world fractal function examples."""
        fractal_functions = [
            'z**2',  # Mandelbrot
            'z**3 - 1',
            'z**4',
            'cmath.sin(z)**2',
            'cmath.cos(z * cmath.pi)',
            'cmath.exp(z) - 1'
        ]
        
        for func in fractal_functions:
            with self.subTest(func=func):
                self.assertTrue(
                    verify_func_not_malicious(func),
                    f"Valid fractal function '{func}' was incorrectly flagged"
                )

if __name__ == '__main__':
    unittest.main()
