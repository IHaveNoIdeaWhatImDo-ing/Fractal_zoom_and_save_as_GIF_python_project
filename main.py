#!/usr/bin/env python3
"""
Fractal visualization application with interactive GUI.

This application provides a graphical interface for exploring fractals
with features like zooming, panning, frame capture, and GIF creation.

Classes:
    FractalApp: Main application class with UI and fractal operations

Functions:
    validate_arguments: Validates command-line arguments
    verify_func_not_malicious: Security check for fractal expressions
    main: Entry point for command-line interface

Usage:
    $ python main.py "z**2" -s 512 -i 50 -x -2 -2 2 2 -c 0 0 0 0 255 0
"""

import argparse
import re
from tkinter import Tk, Button, Canvas, filedialog, messagebox
from functools import reduce
from PIL import ImageTk, Image
import numpy as np
from compute import compute

# validation of the argument list because of compute() using default values
# (if an argument is specified all previous ones shuld be too)
def validate_arguments(args_dict: dict[str, str]) -> None:
    """Validates command-line arguments"""
    has_any_args = False
    for key, val in list(args_dict.items())[::-1]:
        if val is not None:
            has_any_args = True

        if has_any_args is True and val is None:
            raise Exception('If a command line argument is present all previous ones, in the order provided by the --help command must be present too')

# the lambda function could execute ANY code if not verified
def verify_func_not_malicious(func: str) -> bool:
    """Security check for fractal expressions"""
    allowed_functions = [
        'z', # this is the complex argument
        'abs',
        'cmath.sin',
        'cmath.cos',
        'cmath.tan',
        'cmath.exp',
        'cmath.log',
        'cmath.sqrt',
        'cmath.pi',
        'cmath.e',
        'cmath.phase',
        'math.floor',
        'math.ceil',
        'math.trunc'
    ]

    # matches words and 2 words separated by a dot (but not complex numbers)
    words = re.findall(r'\b[a-z]+(?:\.[a-z]+)?\b(?!j\b)', func, re.IGNORECASE)

    return reduce(lambda acc, word: acc and word in allowed_functions, words, True)

class FractalApp:
    """Main class for the program"""
    def __init__(self, root: Tk, func_str: str, size: int, iters: int,
                 x0: float, y0: float, x1: float, y1: float,
                 colormap: tuple[tuple[int, int, int], tuple[int, int, int]]):
        self.root = root
        self.func_str = func_str
        self.size = size
        self.iters = iters
        self.colormap = colormap

        # current view coordinates
        self.x_ul = x0
        self.y_ul = y0
        self.x_dr = x1
        self.y_dr = y1

        # store initial values for reset
        self.initial_params = (x0, y0, x1, y1)

        # selection
        self.selection_start = None
        self.selection_end = None
        self.selection_rect = None

        # current image and PhotoImage
        self.image = None
        self.tk_image = None

        # frames for GIF creation
        self.frames = []
        self.frames_coords = []

        # create UI
        self.setup_ui()

        # compute and display initial fractal
        self.update_fractal()

    def setup_ui(self) -> None:
        """Set up UI"""
        self.root.title('Fraktali maina')

        # main frame
        padding = 10
        button_height = 40

        self.canvas = Canvas(self.root, width=self.size, height=self.size, bg='white')
        self.canvas.pack(padx=padding, pady=(padding, 0))

        # mouse events for selection
        self.canvas.bind('<ButtonPress-1>', self.start_selection)
        self.canvas.bind('<B1-Motion>', self.update_selection)
        self.canvas.bind('<ButtonRelease-1>', self.end_selection)

        # button frame
        button_frame = Canvas(self.root, height=button_height)
        button_frame.pack(fill='x', padx=padding, pady=(5, padding))

        # zoom button
        self.zoom_button = Button(button_frame, text='Zoom to Selection',
                                 command=self.zoom_to_selection, state='disabled')
        self.zoom_button.place(relx=0.1, rely=0.5, anchor='center')

        # reset button
        self.reset_button = Button(button_frame, text='Reset View',
                                  command=self.reset_view)
        self.reset_button.place(relx=0.25, rely=0.5, anchor='center')

        # save Frame button
        self.save_frame_button = Button(button_frame, text='Save Frame',
                                       command=self.save_frame)
        self.save_frame_button.place(relx=0.4, rely=0.5, anchor='center')

        # make GIF button
        self.make_gif_button = Button(button_frame, text='Make GIF',
                                     command=self.make_gif)
        self.make_gif_button.place(relx=0.55, rely=0.5, anchor='center')

        # clear GIF button
        self.clear_gif_button = Button(button_frame, text='Clear GIF',
                                      command=self.clear_gif)
        self.clear_gif_button.place(relx=0.7, rely=0.5, anchor='center')

    def start_selection(self, event) -> None:
        """Draws the selecion square to the image"""
        self.selection_start = (event.x, event.y)
        self.selection_end = None

        # Remove previous selection rectangle if exists
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None

    def update_selection(self, event) -> None:
        """Change the selection when left mouse button does something"""
        if not self.selection_start:
            return

        # remove previous rectangle
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)

        # calculate square selection (use minimum of width and height)
        start_x, start_y = self.selection_start
        end_x, end_y = event.x, event.y

        # calculate width and height
        width = end_x - start_x
        height = end_y - start_y

        size = min(abs(width), abs(height))

        if width < 0:
            end_x = start_x - size
        else:
            end_x = start_x + size

        if height < 0:
            end_y = start_y - size
        else:
            end_y = start_y + size

        self.selection_end = (end_x, end_y)

        self.selection_rect = self.canvas.create_rectangle(
            start_x, start_y, end_x, end_y,
            outline='red', width=2, dash=(5, 5)
        )

    def end_selection(self, event) -> None:
        """Removes the selection"""
        self.update_selection(event)
        if self.selection_start and self.selection_end:
            self.zoom_button.config(state='normal')

    def zoom_to_selection(self) -> None:
        """Zooooooom"""
        if not self.selection_start or not self.selection_end:
            return

        self.root.update()  # update UI

        try:
            x1, y1 = self.selection_start
            x2, y2 = self.selection_end

            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1

            # pixel coordinates to complex plane coordinates
            new_x_ul = self.x_ul + (self.x_dr - self.x_ul) * (x1 / self.size)
            new_y_ul = self.y_ul + (self.y_dr - self.y_ul) * (y1 / self.size)
            new_x_dr = self.x_ul + (self.x_dr - self.x_ul) * (x2 / self.size)
            new_y_dr = self.y_ul + (self.y_dr - self.y_ul) * (y2 / self.size)

            self.x_ul = new_x_ul
            self.y_ul = new_y_ul
            self.x_dr = new_x_dr
            self.y_dr = new_y_dr

            # clear selection
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
                self.selection_rect = None

            self.selection_start = None
            self.selection_end = None
            self.zoom_button.config(state='disabled')

            self.update_fractal()
        except Exception as e:
            messagebox.showerror('Error', f'Zoom failed: {str(e)}')

    def reset_view(self) -> None:
        """Returns to the initial image"""
        self.root.update()

        try:
            self.x_ul, self.y_ul, self.x_dr, self.y_dr = self.initial_params

            # clear selection
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
                self.selection_rect = None

            self.selection_start = None
            self.selection_end = None
            self.zoom_button.config(state='disabled')

            self.update_fractal()
        except Exception as e:
            messagebox.showerror('Error', f'Reset failed: {str(e)}')

    def update_fractal(self) -> None:
        """Updates the image"""
        try:
            self.image = compute(
                func_str=self.func_str,
                size=self.size,
                max_iterations=self.iters,
                x_ul=self.x_ul,
                y_ul=self.y_ul,
                x_dr=self.x_dr,
                y_dr=self.y_dr,
                colormap=list(self.colormap),
                image=self.image
            )

            self.tk_image = ImageTk.PhotoImage(self.image)

            self.canvas.delete('all')
            self.canvas.create_image(0, 0, anchor='nw', image=self.tk_image)
            self.canvas.config(width=self.size, height=self.size)

            self.root.title(f'Fraktali maina - View: ({self.x_ul:.3f}, {self.y_ul:.3f}) to ({self.x_dr:.3f}, {self.y_dr:.3f}) | Frames: {len(self.frames)}')

        except Exception as e:
            messagebox.showerror('Error', f'Fractal computation failed: {str(e)}')

    def save_frame(self) -> None:
        """Saves the frame to the list of frames"""
        if self.image:
            # copy current image
            frame_copy = self.image.copy()
            self.frames.append(frame_copy)
            self.frames_coords.append((self.x_ul, self.y_ul, self.x_dr, self.y_dr))
            print(f'Frame saved. Total frames: {len(self.frames)}')

    # the gif will be 8 frames per second, so 125 ms dely between frames, cause I said so
    def make_gif(self) -> None:
        """Makes a GIF from the saved frames"""
        if len(self.frames) < 2:
            messagebox.showwarning('Warning', 'Need at least 2 frames to create a GIF')
            return

        self.root.update()

        # choose save location
        file_path = filedialog.asksaveasfilename(
            defaultextension='.gif',
            filetypes=[('GIF files', '*.gif'), ('All files', '*.*')]
        )

        if file_path:
            try:
                # make intermediate frames
                save_list = []
                for j in range(len(self.frames) - 1):
                    save_list.append(self.frames[j].copy())

                    x0_tuple = list(np.linspace(self.frames_coords[j][0],
                                                self.frames_coords[j + 1][0], 7))
                    y0_tuple = list(np.linspace(self.frames_coords[j][1],
                                                self.frames_coords[j + 1][1], 7))
                    x1_tuple = list(np.linspace(self.frames_coords[j][2],
                                                self.frames_coords[j + 1][2], 7))
                    y1_tuple = list(np.linspace(self.frames_coords[j][3],
                                                self.frames_coords[j + 1][3], 7))
                    coords_tuple = zip(x0_tuple, y0_tuple, x1_tuple, y1_tuple)

                    img = Image.new('RGB', (self.size, self.size), color='black')

                    for x0, y0, x1, y1 in coords_tuple:
                        compute(
                            func_str=self.func_str,
                            size=self.size,
                            max_iterations=self.iters,
                            x_ul=x0,
                            y_ul=y0,
                            x_dr=x1,
                            y_dr=y1,
                            colormap=list(self.colormap),
                            image=img
                        )
                        save_list.append(img.copy())

                save_list.append(self.frames[len(self.frames) - 1].copy())

                print('balls')

                # save the frames as a GIF
                save_list[0].save(
                    file_path,
                    save_all=True,
                    append_images=save_list[1:],
                    duration=125, # 8 fps
                    loop=0        # loop forever
                )
                messagebox.showinfo('Success', f'GIF saved to:\n{file_path}')
                print(f'GIF saved to {file_path}')
            except Exception as e:
                messagebox.showerror('Error', f'Error saving GIF: {str(e)}')

    def clear_gif(self) -> None:
        """Deletes the saved frames"""
        self.frames = []
        print('All frames cleared')
        self.root.title(f'Fraktali maina - View: ({self.x_ul:.3f}, {self.y_ul:.3f}) to ({self.x_dr:.3f}, {self.y_dr:.3f})')

def main() -> None:
    """Entry point for command-line interface"""
    parser = argparse.ArgumentParser()

    parser.add_argument('function',
                        help='Complex function which describes the fractal. Example: \'z**2\'')

    parser.add_argument('-s', '--size',
                        type=int,
                        help='The size of the image to compute')

    parser.add_argument('-i', '--iterations',
                        type=int,
                        help='The maximum number of iterations for the escape-time algorithm')

    parser.add_argument('-x', '--coordinates',
                        nargs=4,
                        type=float,
                        help='The coordinates of the top left and bottom right corner, placed on the complex plane. They are floating point numbers')

    parser.add_argument('-c', '--color',
                        nargs=6,
                        type=int,
                        help='Red, green and blue values of 2 colors from which a gradient is created. Values are from 0 to 255')

    args = parser.parse_args()

    validate_arguments(vars(args))

    # ----------------------------------------------------------------------------------------------------------------------------

    args_list = dict(vars(args).items())

    func_str = args_list['function']
    size = args_list['size']
    iters = args_list['iterations']
    coords = args_list['coordinates']
    color = args_list['color']

    if not verify_func_not_malicious(func_str):
        raise Exception('The function is not a mathematical expression')

    x0, y0, x1, y1 = coords
    r0, g0, b0, r1, g1, b1 = color
    colormap = ((r0, g0, b0), (r1, g1, b1))

    # run the UI builder
    root = Tk()
    app = FractalApp(root, func_str, size, iters, x0, y0, x1, y1, colormap)
    root.mainloop()

if __name__ == '__main__':
    main()
