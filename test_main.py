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
            '__builtins__',
            'globals()',
            'locals()',
            'compile(',
            '__import__',
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
        
        # Mixed case function names
        self.assertTrue(verify_func_not_malicious('cmAth.SiN(z)'))
        
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
            'z**4 + c',
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


class TestFractalAppWithoutGUI(unittest.TestCase):
    """Test FractalApp without actually creating GUI windows."""
    
    def setUp(self):
        """Set up test parameters."""
        self.func_str = 'z**2'
        self.size = 100
        self.iters = 10
        self.x0, self.y0, self.x1, self.y1 = -2, -2, 2, 2
        self.colormap = ((0, 0, 0), (255, 255, 255))
        
        # Mock Tk root
        self.mock_root = MagicMock(spec=Tk)
        self.mock_root.title = MagicMock()
    
    @patch('main.compute')
    def test_fractal_app_initialization(self, mock_compute):
        """Test FractalApp initialization."""
        # Mock compute to return a dummy image
        mock_image = MagicMock(spec=Image.Image)
        mock_image.copy.return_value = mock_image
        mock_compute.return_value = mock_image
        
        app = FractalApp(
            self.mock_root, self.func_str, self.size, self.iters,
            self.x0, self.y0, self.x1, self.y1, self.colormap
        )
        
        # Check initialization
        self.assertEqual(app.func_str, self.func_str)
        self.assertEqual(app.size, self.size)
        self.assertEqual(app.iters, self.iters)
        self.assertEqual(app.colormap, self.colormap)
        self.assertEqual(app.x_ul, self.x0)
        self.assertEqual(app.y_ul, self.y0)
        self.assertEqual(app.x_dr, self.x1)
        self.assertEqual(app.y_dr, self.y1)
        
        # Check compute was called
        mock_compute.assert_called_once()
        
        # Check UI setup methods were called
        self.assertTrue(hasattr(app, 'canvas'))
        self.assertTrue(hasattr(app, 'zoom_button'))
    
    def test_fractal_app_save_frame(self):
        """Test saving frames."""
        app = FractalApp(
            self.mock_root, self.func_str, self.size, self.iters,
            self.x0, self.y0, self.x1, self.y1, self.colormap
        )
        
        # Mock the image
        mock_image = MagicMock(spec=Image.Image)
        mock_copy = MagicMock(spec=Image.Image)
        mock_image.copy.return_value = mock_copy
        app.image = mock_image
        
        # Initially no frames
        self.assertEqual(len(app.frames), 0)
        self.assertEqual(len(app.frames_coords), 0)
        
        # Save a frame
        app.save_frame()
        
        # Should have one frame now
        self.assertEqual(len(app.frames), 1)
        self.assertEqual(len(app.frames_coords), 1)
        self.assertEqual(app.frames_coords[0], (self.x0, self.y0, self.x1, self.y1))
        
        # The frame should be a copy
        mock_image.copy.assert_called_once()
    
    def test_fractal_app_clear_gif(self):
        """Test clearing saved frames."""
        app = FractalApp(
            self.mock_root, self.func_str, self.size, self.iters,
            self.x0, self.y0, self.x1, self.y1, self.colormap
        )
        
        # Add some frames
        app.frames = [MagicMock(), MagicMock()]
        app.frames_coords = [(1, 2, 3, 4), (5, 6, 7, 8)]
        
        # Clear frames
        app.clear_gif()
        
        # Should be empty
        self.assertEqual(len(app.frames), 0)
        self.assertEqual(len(app.frames_coords), 0)
    
    @patch('main.compute')
    @patch('main.ImageTk.PhotoImage')
    def test_update_fractal(self, mock_photoimage, mock_compute):
        """Test updating the fractal image."""
        app = FractalApp(
            self.mock_root, self.func_str, self.size, self.iters,
            self.x0, self.y0, self.x1, self.y1, self.colormap
        )
        
        # Mock compute and PhotoImage
        mock_image = MagicMock(spec=Image.Image)
        mock_compute.return_value = mock_image
        mock_tk_image = MagicMock()
        mock_photoimage.return_value = mock_tk_image
        
        # Mock canvas
        app.canvas = MagicMock()
        app.canvas.delete = MagicMock()
        app.canvas.create_image = MagicMock()
        app.canvas.config = MagicMock()
        
        # Update fractal
        app.update_fractal()
        
        # Check compute was called with correct parameters
        mock_compute.assert_called_once_with(
            func_str=self.func_str,
            size=self.size,
            max_iterations=self.iters,
            x_ul=self.x0,
            y_ul=self.y0,
            x_dr=self.x1,
            y_dr=self.y1,
            colormap=list(self.colormap),
            image=None
        )
        
        # Check canvas was updated
        app.canvas.delete.assert_called_once_with('all')
        app.canvas.create_image.assert_called_once()
        app.canvas.config.assert_called_once_with(width=self.size, height=self.size)
        
        # Check title was updated
        self.mock_root.title.assert_called()


class TestMouseEvents(unittest.TestCase):
    """Test mouse event handling in FractalApp."""
    
    def setUp(self):
        """Set up test app."""
        self.func_str = 'z**2'
        self.size = 100
        self.iters = 10
        self.x0, self.y0, self.x1, self.y1 = -2, -2, 2, 2
        self.colormap = ((0, 0, 0), (255, 255, 255))
        
        # Mock Tk root
        self.mock_root = MagicMock(spec=Tk)
        
        # Create app
        self.app = FractalApp(
            self.mock_root, self.func_str, self.size, self.iters,
            self.x0, self.y0, self.x1, self.y1, self.colormap
        )
        
        # Mock canvas
        self.app.canvas = MagicMock()
        self.app.canvas.delete = MagicMock()
        self.app.canvas.create_rectangle = MagicMock()
        self.app.zoom_button = MagicMock()
    
    def test_start_selection(self):
        """Test starting a selection."""
        # Mock event
        mock_event = MagicMock()
        mock_event.x = 10
        mock_event.y = 20
        
        # Initially no selection
        self.app.selection_start = None
        self.app.selection_rect = None
        
        # Start selection
        self.app.start_selection(mock_event)
        
        # Selection should be started
        self.assertEqual(self.app.selection_start, (10, 20))
        self.assertIsNone(self.app.selection_end)
        
        # Test with existing selection rectangle
        self.app.selection_rect = 'rect_id'
        self.app.start_selection(mock_event)
        
        # Canvas delete should be called
        self.app.canvas.delete.assert_called_with('rect_id')
    
    def test_update_selection(self):
        """Test updating selection during drag."""
        # Set starting point
        self.app.selection_start = (10, 20)
        
        # Mock event
        mock_event = MagicMock()
        mock_event.x = 50
        mock_event.y = 60
        
        # Call update selection
        self.app.update_selection(mock_event)
        
        # Canvas should create a rectangle
        self.app.canvas.create_rectangle.assert_called_once()
        
        # Selection end should be updated
        self.assertEqual(self.app.selection_end, (50, 60))
    
    def test_end_selection(self):
        """Test ending selection."""
        # Set starting point
        self.app.selection_start = (10, 20)
        self.app.zoom_button.config = MagicMock()
        
        # Mock event
        mock_event = MagicMock()
        mock_event.x = 50
        mock_event.y = 60
        
        # Call end selection
        self.app.end_selection(mock_event)
        
        # Zoom button should be enabled
        self.app.zoom_button.config.assert_called_with(state='normal')
        
        # Test with no selection start
        self.app.selection_start = None
        self.app.end_selection(mock_event)
        # Should not crash


class TestMainFunction(unittest.TestCase):
    """Test the main() function."""
    
    @patch('main.Tk')
    @patch('main.FractalApp')
    @patch('main.validate_arguments')
    @patch('main.verify_func_not_malicious')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_success(self, mock_parse_args, mock_verify_func, 
                          mock_validate_args, mock_fractal_app, mock_tk):
        """Test main function with successful execution."""
        # Mock command line arguments
        mock_args = MagicMock()
        mock_args.function = 'z**2'
        mock_args.size = 512
        mock_args.iterations = 50
        mock_args.coordinates = (-2, -2, 2, 2)
        mock_args.color = (0, 0, 0, 255, 255, 255)
        mock_parse_args.return_value = mock_args
        
        # Mock Tk root
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        # Mock FractalApp
        mock_app = MagicMock()
        mock_fractal_app.return_value = mock_app
        
        # Mock verification to return True
        mock_verify_func.return_value = True
        
        # Run main (but don't actually start mainloop)
        with patch.object(mock_root, 'mainloop'):
            main()
        
        # Check argument parser was used
        mock_parse_args.assert_called_once()
        
        # Check validation was called
        mock_validate_args.assert_called_once()
        
        # Check verification was called
        mock_verify_func.assert_called_once_with('z**2')
        
        # Check FractalApp was created
        mock_fractal_app.assert_called_once_with(
            mock_root, 'z**2', 512, 50, -2, -2, 2, 2, ((0, 0, 0), (255, 255, 255))
        )
        
        # Check mainloop was called
        mock_root.mainloop.assert_called_once()
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('main.verify_func_not_malicious')
    def test_main_malicious_function(self, mock_verify_func, mock_parse_args):
        """Test main with malicious function raises exception."""
        # Mock command line arguments
        mock_args = MagicMock()
        mock_args.function = '__import__("os").system("rm -rf /")'  # Malicious
        mock_args.size = 512
        mock_args.iterations = 50
        mock_args.coordinates = (-2, -2, 2, 2)
        mock_args.color = (0, 0, 0, 255, 255, 255)
        mock_parse_args.return_value = mock_args
        
        # Mock verification to return False
        mock_verify_func.return_value = False
        
        # Should raise exception
        with self.assertRaises(Exception) as context:
            main()
        
        self.assertIn('not a mathematical expression', str(context.exception))
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('main.validate_arguments')
    def test_main_invalid_arguments(self, mock_validate_args, mock_parse_args):
        """Test main with invalid arguments raises exception."""
        # Mock command line arguments
        mock_args = MagicMock()
        mock_args.function = 'z**2'
        mock_args.size = 512
        mock_args.iterations = None  # Missing but color is specified
        mock_args.coordinates = (-2, -2, 2, 2)
        mock_args.color = (0, 0, 0, 255, 255, 255)
        mock_parse_args.return_value = mock_args
        
        # Mock validation to raise exception
        mock_validate_args.side_effect = Exception('Invalid arguments')
        
        # Should raise exception
        with self.assertRaises(Exception):
            main()


class TestIntegration(unittest.TestCase):
    """Integration tests that combine multiple components."""
    
    @patch('main.compute')
    def test_complete_flow(self, mock_compute):
        """Test a complete flow from arguments to image generation."""
        from main import validate_arguments, verify_func_not_malicious
        
        # Valid arguments
        args_dict = {
            'function': 'z**2',
            'size': 512,
            'iterations': 50,
            'coordinates': (-2, -2, 2, 2),
            'color': (0, 0, 0, 255, 255, 255)
        }
        
        # Should validate successfully
        validate_arguments(args_dict)
        
        # Function should be verified as safe
        self.assertTrue(verify_func_not_malicious('z**2'))
        
        # Mock compute to return an image
        mock_image = MagicMock(spec=Image.Image)
        mock_image.size = (512, 512)
        mock_compute.return_value = mock_image
        
        # The actual computation would happen here in the real app


class TestEdgeCases(unittest.TestCase):
    """Test various edge cases."""
    
    def test_coordinate_transformation(self):
        """Test pixel to coordinate transformation logic."""
        # This tests the logic used in zoom_to_selection
        size = 100
        x_ul, y_ul = -2, -2
        x_dr, y_dr = 2, 2
        
        # Pixel (0, 0) should map to (x_ul, y_ul)
        pixel_x, pixel_y = 0, 0
        new_x = x_ul + (x_dr - x_ul) * (pixel_x / size)
        new_y = y_ul + (y_dr - y_ul) * (pixel_y / size)
        
        self.assertAlmostEqual(new_x, -2.0)
        self.assertAlmostEqual(new_y, -2.0)
        
        # Pixel (size, size) should map to (x_dr, y_dr)
        pixel_x, pixel_y = size, size
        new_x = x_ul + (x_dr - x_ul) * (pixel_x / size)
        new_y = y_ul + (y_dr - y_ul) * (pixel_y / size)
        
        self.assertAlmostEqual(new_x, 2.0)
        self.assertAlmostEqual(new_y, 2.0)
        
        # Pixel at center should map to center
        pixel_x, pixel_y = size / 2, size / 2
        new_x = x_ul + (x_dr - x_ul) * (pixel_x / size)
        new_y = y_ul + (y_dr - y_ul) * (pixel_y / size)
        
        self.assertAlmostEqual(new_x, 0.0)
        self.assertAlmostEqual(new_y, 0.0)


if __name__ == '__main__':
    unittest.main()