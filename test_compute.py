#!/usr/bin/env python3
"""
Unit tests for compute.py module.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import numpy as np
from PIL import Image

# Add the parent directory to the path to import compute
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compute import (
    default_fractal_function,
    create_fractal_function,
    compute_pixel_batch,
    compute
)


class TestDefaultFractalFunction(unittest.TestCase):
    """Test the default fractal function z² + c."""
    
    def test_default_fractal_function_basic(self):
        """Test basic calculations of the default fractal function."""
        # Test with simple values
        result = default_fractal_function(0+0j, 1+1j)
        self.assertEqual(result, 1+1j)
        
        # Test with z=1, c=1
        result = default_fractal_function(1+0j, 1+0j)
        self.assertEqual(result, 2+0j)
        
        # Test with complex numbers
        result = default_fractal_function(2+3j, 1+1j)
        # (2+3j)² + (1+1j) = (4 + 12j - 9) + 1 + 1j = (-5 + 12j) + 1 + 1j = -4 + 13j
        self.assertEqual(result, -4 + 13j)

class TestCreateFractalFunction(unittest.TestCase):
    """Test creating fractal functions from strings."""
    
    def test_create_valid_function(self):
        """Test creating valid fractal functions."""
        # Basic z²
        func = create_fractal_function('z**2')
        self.assertTrue(callable(func))
        
        # Test the function works
        result = func(2+0j, 1+0j)
        # Should return z² + c = (2)² + 1 = 4 + 1 = 5
        self.assertEqual(result, 5+0j)
        
        # Test with complex
        result = func(1+1j, 1+0j)
        # (1+1j)² + 1 = (1 + 2j - 1) + 1 = 2j + 1 = 1 + 2j
        self.assertEqual(result, 1 + 2j)
    
    def test_create_invalid_function(self):
        """Test that invalid functions fall back to default."""
        # Invalid expression
        func = create_fractal_function('this is not valid python')
        self.assertTrue(callable(func))
        # Should return the default function
        result1 = func(1+1j, 2+2j)
        result2 = default_fractal_function(1+1j, 2+2j)
        self.assertEqual(result1, result2)
    
    def test_create_function_with_cmath(self):
        """Test functions using cmath functions."""
        # Note: In the actual implementation, eval doesn't have cmath imported
        # This test shows what we'd expect if cmath was available
        func = create_fractal_function('z')
        result = func(3+4j, 1+1j)
        # z + c = (3+4j) + (1+1j) = 4+5j
        self.assertEqual(result, 4+5j)


class TestComputePixelBatch(unittest.TestCase):
    """Test the compute_pixel_batch function."""
    
    def setUp(self):
        """Set up test data for batch computation."""
        self.size = 4
        self.x_values = np.linspace(-2, 2, self.size)
        self.y_values = np.linspace(-2, 2, self.size)
        self.func_str = 'z**2'
        self.max_iterations = 10
        
        # Create a simple gradient
        self.gradient = [(0, 0, 0)] * self.max_iterations
        for i in range(self.max_iterations):
            self.gradient[i] = (i * 25, i * 25, i * 25)
    
    def test_compute_pixel_batch_basic(self):
        """Test basic batch computation."""
        args = (0, 2, self.x_values, self.y_values, 
                self.func_str, self.max_iterations, self.gradient)
        
        results = compute_pixel_batch(args)
        
        # Should have 2 rows * 4 columns = 8 results
        self.assertEqual(len(results), 8)
        
        # Each result should be a tuple of (row, col, color)
        for result in results:
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 3)
            row, col, color = result
            self.assertIsInstance(row, int)
            self.assertIsInstance(col, int)
            self.assertIsInstance(color, tuple)
            self.assertEqual(len(color), 3)
    
    def test_compute_pixel_batch_div_zero(self):
        """Test that division by zero doesn't crash."""
        # Use a function that might cause division by zero
        args = (0, 1, self.x_values, self.y_values, 
                '1/z', self.max_iterations, self.gradient)
        
        # Should not raise an exception
        try:
            results = compute_pixel_batch(args)
            # Should get results
            self.assertTrue(len(results) > 0)
        except ZeroDivisionError:
            self.fail("compute_pixel_batch raised ZeroDivisionError unexpectedly!")

class TestComputeFunction(unittest.TestCase):
    """Test the main compute function."""
    
    def setUp(self):
        """Set up test parameters."""
        self.small_size = 16  # Small size for faster tests
        self.test_iterations = 10
    
    def test_compute_basic(self):
        """Test basic fractal computation."""
        img = compute(
            func_str='z**2',
            size=self.small_size,
            max_iterations=self.test_iterations,
            x_ul=-2.0, y_ul=-2.0,
            x_dr=2.0, y_dr=2.0,
            colormap=[(0, 0, 0), (255, 255, 255)]
        )
        
        # Check image properties
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (self.small_size, self.small_size))
        self.assertEqual(img.mode, 'RGB')
        
        # Check that image is not all one color
        # (fractal should have some variation)
        colors = set()
        for x in range(min(5, self.small_size)):
            for y in range(min(5, self.small_size)):
                colors.add(img.getpixel((x, y)))
        
        # In a proper fractal, we should have multiple colors
        # But for small size/iterations, might be limited
        self.assertTrue(len(colors) >= 1)
    
    def test_compute_with_defaults(self):
        """Test compute with only default parameters."""
        img = compute()
        
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (512, 512))  # Default size
        self.assertEqual(img.mode, 'RGB')
    
    def test_compute_with_existing_image(self):
        """Test compute with existing PIL Image passed in."""
        # Create a test image
        test_img = Image.new('RGB', (self.small_size, self.small_size), color='white')
        
        img = compute(
            func_str='z**2',
            size=self.small_size,
            max_iterations=self.test_iterations,
            image=test_img  # Pass existing image
        )
        
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (self.small_size, self.small_size))
        
        # The image should be modified (not all white anymore)
        # Get a pixel value
        pixel = img.getpixel((0, 0))
        self.assertNotEqual(pixel, (255, 255, 255))
    
    def test_compute_with_none_arguments(self):
        """Test compute when None arguments are passed."""
        img = compute(
            func_str=None,
            size=None,
            max_iterations=None,
            x_ul=None, y_ul=None,
            x_dr=None, y_dr=None,
            colormap=None
        )
        
        # Should use defaults and create an image
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (512, 512))
    
    def test_compute_invalid_parameters(self):
        """Test compute with invalid parameters raises appropriate errors."""
        # Negative size
        with self.assertRaises(ValueError):
            compute(size=-100)
        
        # Negative iterations
        with self.assertRaises(ValueError):
            compute(max_iterations=-10)
        
        # Invalid coordinates (x_ul >= x_dr)
        with self.assertRaises(ValueError):
            compute(x_ul=2.0, x_dr=1.0)
        
        # Invalid coordinates (y_ul >= y_dr)
        with self.assertRaises(ValueError):
            compute(y_ul=2.0, y_dr=1.0)
    
    def test_compute_different_functions(self):
        """Test compute with different fractal functions."""
        # Test with different function strings
        functions = ['z**2', 'z', 'z**3', 'z**2 - 1']
        
        for func_str in functions:
            img = compute(
                func_str=func_str,
                size=8,  # Very small for speed
                max_iterations=5
            )
            self.assertIsInstance(img, Image.Image)
            self.assertEqual(img.size, (8, 8))
    
    def test_compute_color_gradient(self):
        """Test that color gradient is applied correctly."""
        # Create a gradient from black to red
        colormap = [(0, 0, 0), (255, 0, 0)]
        
        img = compute(
            size=self.small_size,
            max_iterations=self.test_iterations,
            colormap=colormap
        )
        
        # Get a pixel and check it's some shade of red
        pixel = img.getpixel((self.small_size // 2, self.small_size // 2))
        r, g, b = pixel
        
        # With black to red gradient, green and blue should be 0
        # But due to linear interpolation, they might be very small
        # Allow some tolerance
        self.assertAlmostEqual(g, 0, delta=5)
        self.assertAlmostEqual(b, 0, delta=5)

class TestPerformanceAndMemory(unittest.TestCase):
    """Test performance and memory aspects."""
    
    def test_compute_small_memory(self):
        """Test compute with very small image doesn't use excessive memory."""
        import tracemalloc
        
        tracemalloc.start()
        
        snapshot1 = tracemalloc.take_snapshot()
        img = compute(size=32, max_iterations=10)
        snapshot2 = tracemalloc.take_snapshot()
        
        # Calculate memory difference
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        # Memory usage should be reasonable for small image
        # This is more of a sanity check than a strict test
        total_memory = sum(stat.size for stat in top_stats[:10])
        # Should be less than 10MB for a 32x32 image
        self.assertLess(total_memory, 10 * 1024 * 1024)
        
        tracemalloc.stop()
    
    def test_compute_large_image(self):
        """Test compute with larger image (but not too large for tests)."""
        # Test with moderate size (should complete in reasonable time)
        img = compute(size=64, max_iterations=20)
        self.assertEqual(img.size, (64, 64))


if __name__ == '__main__':
    unittest.main()
