# Fractal Visualization Application

An interactive fractal visualization tool with a graphical user interface for exploring complex fractals using the escape-time algorithm. Create beautiful fractal images, zoom into intricate details, and generate animated GIFs from your explorations.

## Features

- **Interactive GUI**: Explore fractals with an intuitive Tkinter-based interface
- **Customizable Fractals**: Define your own fractal functions using Python expressions
- **Zoom & Pan**: Click and drag to select regions and zoom into fractal details
- **Frame Capture**: Save individual frames during your exploration
- **GIF Creation**: Generate animated GIFs from captured frames with smooth transitions
- **Parallel Processing**: Multi-core computation for fast fractal generation
- **Custom Color Maps**: Define gradient colors for fractal visualization
- **Security**: Built-in validation to prevent malicious code execution

## Requirements

- Python 3.8 or higher
- NumPy >= 1.21.0
- Pillow (PIL) >= 9.0.0
- Tkinter (usually included with Python)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/IHaveNoIdeaWhatImDo-ing/Fractal_zoom_and_save_as_GIF_python_project.git
cd python_project
```

2. Install dependencies:
```bash
pip install numpy pillow
```

Or using the project configuration:
```bash
pip install -e .
```

For development dependencies:
```bash
pip install -e ".[dev,test]"
```

## Usage

### Basic Usage

Run the application with a fractal function:

```bash
python main.py "z**2" -s 512 -i 50 -x -2 -2 2 2 -c 0 0 0 0 255 0
```

### Command-Line Arguments

- `function` (required): Complex function expression describing the fractal (e.g., `"z**2"`, `"z**3 + c"`)
- `-s, --size`: Image size in pixels (default: 512)
- `-i, --iterations`: Maximum iterations for escape-time algorithm (default: 50)
- `-x, --coordinates`: View coordinates as four floats: `x0 y0 x1 y1` (top-left and bottom-right corners)
- `-c, --color`: Color gradient as six integers: `r0 g0 b0 r1 g1 b1` (RGB values 0-255)

### Example Commands

**Mandelbrot Set (default):**
```bash
python main.py "z**2" -s 1024 -i 100 -x -2.5 -2 1.5 2 -c 0 0 0 255 255 255
```

**Julia Set variant:**
```bash
python main.py "z**2" -s 512 -i 50 -x -2 -2 2 2 -c 255 0 0 0 0 255
```

**Custom function:**
```bash
python main.py "z**3" -s 800 -i 75 -x -1.5 -1.5 1.5 1.5 -c 0 0 0 255 128 0
```

### Interactive Features

Once the GUI is open:

- **Zoom**: Click and drag to select a square region, then click "Zoom to Selection"
- **Reset**: Click "Reset View" to return to the initial view
- **Save Frame**: Click "Save Frame" to capture the current view
- **Make GIF**: After saving multiple frames, click "Make GIF" to create an animated GIF
- **Clear GIF**: Remove all saved frames

### Supported Functions

The fractal function can use:
- Basic operations: `+`, `-`, `*`, `/`, `**`
- Complex number `z` and constant `c`
- Math functions: `abs`, `cmath.sin`, `cmath.cos`, `cmath.tan`, `cmath.exp`, `cmath.log`, `cmath.sqrt`, `cmath.pi`, `cmath.e`, `cmath.phase`
- Additional: `math.floor`, `math.ceil`, `math.trunc`

## Testing

Run all tests:
```bash
python run_tests.py
```

Run specific test files:
```bash
python run_tests.py test_main
python run_tests.py test_compute
```

Or use pytest directly:
```bash
pytest
```

## Project Structure

```
python_project/
├── main.py              # Main application with GUI
├── compute.py           # Fractal computation engine
├── test_main.py         # Tests for main.py
├── test_compute.py      # Tests for compute.py
├── run_tests.py         # Test runner script
├── pyproject.yaml       # Project configuration and dependencies
├── .pylintrc            # Pylint configuration
└── README.md            # This file
```

## How It Works

The application uses the **escape-time algorithm** to generate fractals:

1. For each pixel in the image, a complex number `c` is calculated
2. Starting with `z = 0`, the function `f(z, c)` is iterated
3. If `|z|` exceeds a threshold (radius 2), the pixel is colored based on iteration count
4. If the maximum iterations are reached, the pixel is colored with the base color
5. Colors are interpolated using a gradient between two RGB values

The computation is parallelized across multiple CPU cores for performance.

## Development

### Code Quality

The project uses:
- **Pylint** for code linting
- **Black** for code formatting (optional)
- **MyPy** for type checking (optional)
- **Flake8** for style checking (optional)

Run linting:
```bash
pylint main.py compute.py
```

### Contributing

1. Follow the existing code style
2. Add tests for new features
3. Ensure all tests pass before submitting

## License

Nema bace

## Author

Az, sebe si i moq lichnost
