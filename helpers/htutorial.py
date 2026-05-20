"""
Utility functions for MSML610 course tutorials.

Import as:

import helpers.htutorial as htutori
"""

import copy
import logging
import os
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple, Union

import matplotlib.axes
import matplotlib.pyplot as plt
import matplotlib.text

if TYPE_CHECKING:
    import ipywidgets
    import pandas as pd

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# Notebook configuration.


def set_notebook_style() -> None:
    """
    Set default matplotlib style for notebooks.
    """
    _LOG.info("Setting notebook style")
    import seaborn as sns

    sns.set_style("whitegrid")
    plt.rcParams["figure.figsize"] = [8, 3]


# TODO(gp): Merge with hnotebook
def notebook_signature() -> None:
    """
    Display Python environment information including version and module versions.
    """
    _LOG.info("Notebook signature")
    cmd = "python --version"
    os.system(cmd)
    cmd = "uname -a"
    os.system(cmd)
    modules = ["numpy", "pymc", "matplotlib", "arviz", "preliz", "sns"]
    for module in modules:
        try:
            exec(f"import {module}")
            version = eval(f"{module}.__version__")
            _LOG.info("%s version=%s", module, version)
        except ImportError:
            _LOG.warning("%s is not installed", module)


# TODO(gp): Merge with hnotebook
def config_notebook() -> None:
    """
    Configure notebook with default style and display environment signature.
    """
    set_notebook_style()
    notebook_signature()


def obj_to_str(var_name: str, val: Any, *, top_n: int = 3) -> str:
    """
    Convert object to string representation showing name, type, and preview.

    :param var_name: Name of the variable
    :param val: Value to convert
    :param top_n: Number of elements to show from start and end for arrays
    :return: String representation of the object
    """
    import numpy as np

    txt = []
    txt_tmp = "var_name=%s (type=%s)" % (var_name, str(type(val)))
    txt.append(txt_tmp)
    if isinstance(val, np.ndarray):
        txt.append("shape=%s" % val.shape)
        if len(val.shape) == 1:
            txt_tmp = "%s ... %s" % (val[:top_n], val[-top_n:])
            txt_tmp = txt_tmp.replace("[", "")
            txt_tmp = txt_tmp.replace("]", "")
            txt_tmp = f"[{txt_tmp}]"
            txt.append(txt_tmp)
    return "\n".join(txt)


def print_obj(*args: Any, **kwargs: Any) -> None:
    """
    Print object information using `obj_to_str()`.
    """
    _LOG.info(obj_to_str(*args, **kwargs))


def convert_to_filename(string: str) -> str:
    """
    Convert string to sanitized filename path in figures directory.

    E.g., `"Lesson 09.1: Reasoning Over Time"` -> `"Lesson_09.1_Reasoning_Over_Time.png"`

    :param string: Input string to convert
    :return: Full path to PNG file
    """
    dst_dir = os.path.join(
        os.environ["CSFY_GIT_ROOT_PATH"], "lectures_source/figures"
    )
    dst_dir = os.path.normpath(dst_dir)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    file_name = string
    file_name = file_name.replace(":", "")
    file_name = file_name.replace(" ", "_")
    file_name = file_name.replace(".", "_")
    file_name = os.path.join(dst_dir, file_name)
    file_name += ".png"
    return file_name


def print_figure(file_name: str) -> None:
    """
    Print markdown image reference with fixed width.

    :param file_name: Path to image file
    """
    txt = f"![]({file_name})" + "{ width=100px }"
    _LOG.info(txt)


def process_figure(title: str) -> None:
    """
    Save current figure with title-based filename.

    :param title: Title used to generate filename
    """
    file_name = convert_to_filename(title)
    plt.savefig(file_name, dpi=300)


# Widget Builder Utilities.


def _create_slider_widget(
    name: str,
    description: str,
    min_val: float,
    max_val: float,
    step: float,
    initial_value: float,
    *,
    is_float: bool = True,
) -> Tuple:
    """
    Create a slider widget with text field and +/- buttons.

    Creates a complete widget control with slider, text input field, and
    increment/decrement buttons following the notebook conventions.

    :param name: Variable name (e.g., "mu", "N", "seed")
    :param description: Human-readable description (e.g., "prob of success")
    :param min_val: Minimum value for the slider
    :param max_val: Maximum value for the slider
    :param step: Step size for slider and buttons
    :param initial_value: Initial value
    :param is_float: If True, create FloatSlider/FloatText, else IntSlider/IntText
    :return: Tuple of (slider, text, minus_button, plus_button)
    """
    import ipywidgets

    _ = description
    # Create widgets based on type.
    if is_float:
        slider = ipywidgets.FloatSlider(
            min=min_val,
            max=max_val,
            step=step,
            value=initial_value,
            # description=f"{name} = {description}",
            description=name,
            continuous_update=False,
            style={"description_width": "150px"},
            layout={"width": "500px"},
        )
        text = ipywidgets.FloatText(
            value=initial_value,
            step=step,
            description="",
            layout={"width": "80px"},
        )
    else:
        slider = ipywidgets.IntSlider(
            min=int(min_val),
            max=int(max_val),
            step=int(step),
            value=int(initial_value),
            # description=f"{name} = {description}",
            description=name,
            continuous_update=False,
            style={"description_width": "150px"},
            layout={"width": "500px"},
        )
        text = ipywidgets.IntText(
            value=int(initial_value),
            step=int(step),
            description="",
            layout={"width": "80px"},
        )
    # Create buttons.
    minus_button = ipywidgets.Button(description="-", layout={"width": "40px"})
    plus_button = ipywidgets.Button(description="+", layout={"width": "40px"})
    return slider, text, minus_button, plus_button


def _link_slider_widgets(
    slider: Union["ipywidgets.FloatSlider", "ipywidgets.IntSlider"],
    text: Union["ipywidgets.FloatText", "ipywidgets.IntText"],
    minus_button: "ipywidgets.Button",
    plus_button: "ipywidgets.Button",
) -> None:
    """
    Link slider, text field, and buttons together.

    Sets up bidirectional sync between slider and text field, and connects
    buttons to increment/decrement the slider value.

    :param slider: The slider widget (FloatSlider or IntSlider)
    :param text: The text input widget (FloatText or IntText)
    :param minus_button: The decrement button
    :param plus_button: The increment button
    """

    def slider_changed(change):
        text.value = change["new"]

    def text_changed(change):
        if slider.min <= change["new"] <= slider.max:
            slider.value = change["new"]

    def minus_clicked(_b):
        slider.value = max(slider.min, slider.value - slider.step)

    def plus_clicked(_b):
        slider.value = min(slider.max, slider.value + slider.step)

    # Connect observers.
    slider.observe(slider_changed, names="value")
    text.observe(text_changed, names="value")
    minus_button.on_click(minus_clicked)
    plus_button.on_click(plus_clicked)


def build_widget_control(
    name: str,
    description: str,
    min_val: float,
    max_val: float,
    step: float,
    initial_value: float,
    *,
    is_float: bool = True,
) -> Tuple[
    Union["ipywidgets.FloatSlider", "ipywidgets.IntSlider"], "ipywidgets.HBox"
]:
    """
    Build a complete widget control with slider, text field, and +/- buttons.

    Convenience function that creates, links, and lays out all widget
    components in a single call.

    :param name: Variable name (e.g., "mu", "N", "seed")
    :param description: Human-readable description (e.g., "prob of success")
    :param min_val: Minimum value for the slider
    :param max_val: Maximum value for the slider
    :param step: Step size for slider and buttons
    :param initial_value: Initial value
    :param is_float: If True, create FloatSlider/FloatText, else IntSlider/IntText
    :return: Tuple of (slider, box) where slider is the control widget and box
        is the HBox layout containing all components
    """
    import ipywidgets

    # Create widgets with sliders, text fields, and +/- buttons.
    slider, text, minus_button, plus_button = _create_slider_widget(
        name=name,
        description=description,
        min_val=min_val,
        max_val=max_val,
        step=step,
        initial_value=initial_value,
        is_float=is_float,
    )
    # Link sliders and text fields.
    _link_slider_widgets(slider, text, minus_button, plus_button)
    # Create layout.
    box = ipywidgets.HBox([slider, minus_button, text, plus_button])
    return slider, box


def build_log_widget_control(
    name: str,
    description: str,
    min_exp: int,
    max_exp: int,
    initial_exp: int,
    *,
    base: int = 2,
) -> Tuple["ipywidgets.IntSlider", "ipywidgets.HBox"]:
    """
    Build a logarithmic widget control that displays true values.

    Creates a slider that operates on exponents but displays actual values.
    For base=2: exponent 2->4, 3->8, 4->16, etc.
    Clicking + doubles the value, clicking - halves it.

    :param name: Variable name (e.g., "log(N)")
    :param description: Human-readable description
    :param min_exp: Minimum exponent (e.g., 2 for min value of 4 when base=2)
    :param max_exp: Maximum exponent (e.g., 10 for max value of 1024 when base=2)
    :param initial_exp: Initial exponent
    :param base: Base for logarithm (default 2)
    :return: Tuple of (slider, box) where slider controls the exponent and box
        is the HBox layout containing all components
    """
    import ipywidgets

    # Create slider that operates on exponents.
    exp_slider = ipywidgets.IntSlider(
        min=min_exp,
        max=max_exp,
        step=1,
        value=initial_exp,
        description=name,
        continuous_update=False,
        style={"description_width": "150px"},
        layout={"width": "500px"},
    )
    # Create text field that displays actual values.
    value_text = ipywidgets.IntText(
        value=base**initial_exp,
        description="",
        layout={"width": "80px"},
    )
    # Create buttons.
    minus_button = ipywidgets.Button(description="-", layout={"width": "40px"})
    plus_button = ipywidgets.Button(description="+", layout={"width": "40px"})

    # Link widgets.
    def exp_slider_changed(change):
        """Update text field with actual value when slider changes."""
        value_text.value = base ** change["new"]

    def value_text_changed(change):
        """
        Update slider exponent when text field changes.
        """
        try:
            # Find the closest exponent for the entered value.
            import math

            new_exp = round(math.log(change["new"], base))
            # Clamp to valid range.
            new_exp = max(min_exp, min(max_exp, new_exp))
            exp_slider.value = new_exp
        except (ValueError, ZeroDivisionError):
            # Invalid value, reset to current slider value.
            value_text.value = base**exp_slider.value

    def minus_clicked(_b):
        """
        Decrement exponent (halve value for base=2).
        """
        exp_slider.value = max(min_exp, exp_slider.value - 1)

    def plus_clicked(_b):
        """
        Increment exponent (double value for base=2).
        """
        exp_slider.value = min(max_exp, exp_slider.value + 1)

    # Connect observers.
    exp_slider.observe(exp_slider_changed, names="value")
    value_text.observe(value_text_changed, names="value")
    minus_button.on_click(minus_clicked)
    plus_button.on_click(plus_clicked)
    # Create layout.
    box = ipywidgets.HBox([exp_slider, minus_button, value_text, plus_button])
    return exp_slider, box


def add_fitted_text_box(
    ax: matplotlib.axes.Axes,
    text: str,
    box_xy: Tuple[float, float] = (0.02, 0.98),
    box_height: float = 0.96,
    *,
    max_fontsize: int = 16,
    min_fontsize: int = 8,
) -> Optional[matplotlib.text.Text]:
    """
    Add a text box that fills a given axes region and automatically scales font size to fit vertically.

    :param ax: Matplotlib axes to add text to
    :param text: Text content to display
    :param box_xy: Position of text box as (x, y) in axes coordinates
    :param box_height: Height of box as fraction of axes height
    :param max_fontsize: Maximum font size to try
    :param min_fontsize: Minimum font size to use
    """
    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()  # type: ignore[attr-defined]
    for fontsize in range(max_fontsize, min_fontsize - 1, -1):
        txt = ax.text(
            box_xy[0],
            box_xy[1],
            text,
            transform=ax.transAxes,
            ha="left",
            va="top",
            wrap=True,
            fontsize=fontsize,
            family="monospace",
            bbox=dict(
                boxstyle="round,pad=1.0",
                facecolor="wheat",
                alpha=0.3,
            ),
        )
        bbox = txt.get_window_extent(renderer=renderer)
        ax_bbox = ax.get_window_extent(renderer=renderer)
        if bbox.height <= box_height * ax_bbox.height:
            return txt
        txt.remove()
    # Fallback (smallest font).
    ax.text(
        box_xy[0],
        box_xy[1],
        text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        wrap=True,
        fontsize=min_fontsize,
        family="monospace",
        bbox=dict(
            boxstyle="round,pad=1.0",
            facecolor="wheat",
            alpha=0.3,
        ),
    )


# Animation generation utilities.


def generate_animation_values(
    mode: str,
    sweep_variable: str,
    const_variable: Optional[str] = None,
    const_value: Optional[Any] = None,
    *,
    n_steps: int = 11,
    sweep_min: float = 0.0,
    sweep_max: float = 1.0,
    **extra_constants: Any,
) -> List[dict]:
    """
    Generate a list of values for a given mode, sweep variable, and constant variable(s).

    :param mode: Mode of the sweep variable.
    :param sweep_variable: Name of the sweep variable.
    :param const_variable: Name of the constant variable (optional).
    :param const_value: Value of the constant variable (optional).
    :param n_steps: Number of steps in the sweep.
    :param sweep_min: Minimum value for the sweep variable.
    :param sweep_max: Maximum value for the sweep variable.
    :param extra_constants: Additional constant variables as keyword arguments.
    :return: List of values.
    """
    import numpy as np

    if mode == "linear":
        sweep_values = np.linspace(sweep_min, sweep_max, n_steps)
    else:
        raise ValueError(f"Invalid mode: {mode}")
    # Generate list of parameter dictionaries.
    values = []
    for val in sweep_values:
        entry = {sweep_variable: val}
        if const_variable is not None:
            entry[const_variable] = const_value
        entry.update(extra_constants)
        values.append(entry)
    return values


def generate_animation(
    functor: Callable,
    values: List[dict],
    dst_dir: str,
    *,
    incremental: bool = True,
    figsize: Optional[Tuple[int, int]] = None,
    dpi: int = 150,
    convert_to_movie: bool = False,
) -> None:
    """
    Generate animation frames by calling a functor with different parameter values.

    The function creates a directory for frames, then iterates through the
    provided values, calling the functor with each set of kwargs. Each frame
    is saved as a PNG file with the naming pattern frame_000.png,
    frame_001.png, etc.

    :param functor: Function to call for each frame (should use plt.show())
    :param values: List of dictionaries containing kwargs to pass to functor
    :param dst_dir: Directory path where frames will be saved
    :param incremental: If False, directory is recreated from scratch; if
        True, existing directory is reused
    :param figsize: Optional figure size as (width, height) to pass to
        functor (if functor accepts figsize parameter)
    :param dpi: Resolution for saved frames in dots per inch
    :param convert_to_movie: If True, convert PNG frames to movie using
        convert_png_dir_to_movie.py script
    """
    # Create directory for frames.
    hio.create_dir(dst_dir, incremental=incremental)
    n_steps = len(values)
    _LOG.info("Generating %s frames...", n_steps)
    # Generate frames by calling the function with different parameter values.
    for i, kwargs in enumerate(values):
        _LOG.debug("Frame %s/%s: %s", i + 1, n_steps, kwargs)
        # Add figsize to kwargs if provided and not already present.
        if figsize is not None and "figsize" not in kwargs:
            kwargs = {**kwargs, "figsize": figsize}
        # Save the original plt.show.
        original_show = plt.show

        # Create a custom show function that saves the figure.
        def save_figure():
            frame_path = os.path.join(dst_dir, f"frame_{i:03d}.png")
            plt.savefig(
                frame_path,
                dpi=dpi,
                bbox_inches=None,
                facecolor="white",
            )
            plt.close()

        # Replace plt.show temporarily.
        plt.show = save_figure
        try:
            # Call the visualization function.
            functor(**kwargs)
        finally:
            # Restore original plt.show.
            plt.show = original_show
    # Report completion.
    frame_files = sorted([f for f in os.listdir(dst_dir) if f.endswith(".png")])
    _LOG.info("Frames saved to %s/", dst_dir)
    _LOG.debug("Total frames generated: %s", len(frame_files))
    # Validate that all frames have the same dimensions.
    if frame_files:
        dimensions = []
        for frame_file in frame_files:
            frame_path = os.path.join(dst_dir, frame_file)
            from PIL import Image as PILImage

            with PILImage.open(frame_path) as img:
                dimensions.append((frame_file, img.size))
        # Check if all dimensions are the same.
        unique_dimensions = set(dim[1] for dim in dimensions)
        if len(unique_dimensions) == 1:
            width, height = dimensions[0][1]
            _LOG.info(
                "All frames have consistent dimensions: %sx%s pixels",
                width,
                height,
            )
            # Convert frames to movie if requested.
            if convert_to_movie:
                _LOG.info("Converting frames to movie...")
                cmd = f"convert_png_dir_to_movie.py --input_dir {dst_dir}"
                hsystem.system(cmd)
        else:
            _LOG.warning("Inconsistent frame dimensions detected:")
            for frame_file, size in dimensions:
                _LOG.warning("  %s: %sx%s pixels", frame_file, size[0], size[1])
            hdbg.dfatal(
                "Frame dimensions are inconsistent. Expected all frames to have the same size."
            )


# #############################################################################
# Figure saving utilities.
# #############################################################################

FIG_DIR = "/app/lectures_source/figures"


def save_ax(ax: Any, file_name: str) -> None:
    """
    Save matplotlib axes figure to file and print markdown reference.

    :param ax: Matplotlib axes object
    :param file_name: Output filename
    """
    file_name = os.path.join(FIG_DIR, file_name)
    ax.figure.savefig(file_name, dpi=300, bbox_inches="tight")
    # Convert path to relative markdown reference.
    file_name = file_name.replace("/app/", "")
    cmd = f"![]({file_name})"
    _LOG.info(cmd)


def save_fig(axes: Any, file_name: str) -> None:
    """
    Save matplotlib figure from axes array to file and print markdown reference.

    :param axes: Array of matplotlib axes
    :param file_name: Output filename
    """
    file_name = os.path.join(FIG_DIR, file_name)
    fig = axes[0, 0].figure
    fig.savefig(file_name, dpi=300, bbox_inches="tight")
    # Convert path to relative markdown reference.
    file_name = file_name.replace("/app/", "")
    cmd = f"![]({file_name})"
    _LOG.info(cmd)


def save_dot(model: Any, file_name: str) -> None:
    """
    Save PyMC model graph to PNG file and print markdown reference.

    :param model: PyMC model object
    :param file_name: Output filename
    """
    import pymc as pm

    dot = pm.model_to_graphviz(model)
    dot2 = copy.deepcopy(dot)
    file_name = file_name.replace(".png", "")
    file_name = os.path.join(FIG_DIR, file_name)
    # 300 is print quality; try 600 for very sharp images.
    dot2.graph_attr["dpi"] = "300"
    dot2.render(file_name, format="png", cleanup=True)
    # Convert path to relative markdown reference.
    file_name = file_name.replace("/app/", "")
    cmd = f"![]({file_name})"
    _LOG.info(cmd)


def save_df(df: "pd.DataFrame", file_name: str) -> None:
    """
    Save DataFrame as image file and print markdown reference.

    :param df: DataFrame to save
    :param file_name: Output filename
    """
    import dataframe_image as dfi  # type: ignore[import-untyped]

    file_name = os.path.join(FIG_DIR, file_name)
    dfi.export(df, file_name, table_conversion="matplotlib", dpi=300)
    # Convert path to relative markdown reference.
    file_name = file_name.replace("/app/", "")
    cmd = f"![]({file_name})"
    _LOG.info(cmd)


def save_plt(file_name: str) -> None:
    """
    Save current matplotlib figure to file and print markdown reference.

    :param file_name: Output filename
    """
    file_name = os.path.join(FIG_DIR, file_name)
    plt.savefig(file_name, dpi=300, bbox_inches="tight")
    # Convert path to relative markdown reference.
    file_name = file_name.replace("/app/", "")
    cmd = f"![]({file_name})"
    _LOG.info(cmd)
