#!/usr/bin/env python3
"""
Fractal generation module using escape-time algorithm.

This module provides functions for computing and visualizing fractals
using complex number iterations. It supports parallel processing for
efficient computation and customizable coloring.

Functions:
    default_fractal_function: Default z² + c fractal function
    create_fractal_function: Creates fractal function from string
    compute_pixel_batch: Computes fractal values for a batch of pixels
    compute: Main function to generate fractal images

Example:
    >>> from compute import compute
    >>> img = compute(func_str='z**2', size=512)
    >>> img.save('mandelbrot.png')
"""

from typing import Callable, Optional
from multiprocessing import Pool, cpu_count
import math
import numpy as np
from PIL import Image

def default_fractal_function(z: complex, c: complex) -> complex:
    """Default z² + c fractal function"""
    return z**2 + c

def create_fractal_function(func_str: str) -> Callable[[complex, complex], complex]:
    """Creates fractal function from string"""
    try:
        func = eval(f'lambda z, c: {func_str} + c')
        return func
    except:
        return default_fractal_function

def compute_pixel_batch(args: tuple) -> list:
    """Computes fractal values for a batch of pixels"""
    start_row, end_row, x_values, y_values, func_str, max_iterations, gradient = args

    func = create_fractal_function(func_str)

    results = []
    orbit_radius = 2

    for row_idx in range(start_row, end_row):
        y = y_values[row_idx]
        for col_idx, x in enumerate(x_values):
            z = 0
            c = complex(x, y)

            for iterator in range(max_iterations):
                if abs(z) > orbit_radius:
                    pixel_value = gradient[iterator]
                    break

                try:
                    z = func(z, c)
                except (ValueError, ZeroDivisionError):
                    z = c
            else:
                pixel_value = gradient[0]

            results.append((row_idx, col_idx, pixel_value))

    return results

def compute(
    func_str: str = 'z**2',
    size: int = 512,
    max_iterations: int = 50,
    x_ul: float = -2.0, y_ul: float = -2.0,
    x_dr: float = 2.0, y_dr: float = 2.0,
    colormap: list[tuple[int, int, int]] = [(0, 0, 0), (0, 255, 0)],
    image: Optional[Image.Image] = None
) -> Image.Image:

    """Main function to generate fractal images"""

    # if arguments are None
    if func_str is None:
        func_str = 'z**2'
    if size is None:
        size = 512
    if max_iterations is None:
        max_iterations = 50
    if x_ul is None:
        x_ul = -2.0
    if y_ul is None:
        y_ul = -2.0
    if x_dr is None:
        x_dr = 2.0
    if y_dr is None:
        y_dr = 2.0
    if colormap is None:
        colormap = [(0, 0, 0), (0, 255, 0)]

    if size < 0 or max_iterations < 0:
        raise ValueError('The size and max amount of iterations are positive')
    if x_ul >= x_dr or y_ul >= y_dr:
        raise ValueError('Incorrect coordinates')

    # creating the color gradient
    r = np.linspace(colormap[0][0], colormap[1][0], max_iterations)
    g = np.linspace(colormap[0][1], colormap[1][1], max_iterations)
    b = np.linspace(colormap[0][2], colormap[1][2], max_iterations)

    gradient = list(zip(r.astype(int), g.astype(int), b.astype(int)))

    # beginning the computation
    x_dom = np.linspace(x_ul, x_dr, size)
    y_dom = np.linspace(y_ul, y_dr, size)

    if image is None:
        image = Image.new('RGB', (size, size), color='black')

    # preparing arguments for parallel processing
    num_workers = max(1, cpu_count() - 1)  # one core free for UI
    rows_per_worker = math.ceil(size / num_workers)

    # batches
    worker_args = []
    for worker_idx in range(num_workers):
        start_row = worker_idx * rows_per_worker
        end_row = min((worker_idx + 1) * rows_per_worker, size)

        if start_row >= size:
            break

        worker_args.append((start_row, end_row, x_dom, y_dom, func_str, max_iterations, gradient))

    # parallel processing
    with Pool(processes=num_workers) as pool:
        results = pool.map(compute_pixel_batch, worker_args)

    # update the image with the new pixels
    for batch_result in results:
        for row_idx, col_idx, pixel_value in batch_result:
            image.putpixel((col_idx, row_idx), pixel_value)

    return image
