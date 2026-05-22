"""
Import as:

import helpers.hnotebook as hnotebo
"""

import logging


def config_notebook(sns_set: bool = True) -> None:
    """
    Configure the notebook for plotting.
    """
    import helpers.hmodule as hmodule

    # Matplotlib.
    module = "matplotlib"
    if hmodule.has_module(module):
        # Matplotlib.
        import matplotlib.pyplot as plt

        # plt.rcParams
        plt.rcParams["figure.figsize"] = (20, 5)
        plt.rcParams["legend.fontsize"] = 14
        plt.rcParams["font.size"] = 14
        plt.rcParams["image.cmap"] = "rainbow"
        if False:
            # Tweak the size of the plots to make it more readable when embedded in
            # documents or presentations.
            # font = {'family' : 'normal',
            #         #'weight' : 'bold',
            #         'size'   : 32}
            # matplotlib.rc('font', **font)
            scale = 3
            small_size = 8 * scale
            medium_size = 10 * scale
            bigger_size = 12 * scale
            # Default text sizes.
            plt.rc("font", size=small_size)
            # Fontsize of the axes title.
            plt.rc("axes", titlesize=small_size)
            # Fontsize of the x and y labels.
            plt.rc("axes", labelsize=medium_size)
            # Fontsize of the tick labels.
            plt.rc("xtick", labelsize=small_size)
            # Fontsize of the tick labels.
            plt.rc("ytick", labelsize=small_size)
            # Legend fontsize.
            plt.rc("legend", fontsize=small_size)
            # Fontsize of the figure title.
            plt.rc("figure", titlesize=bigger_size)
    else:
        print(f"No module '{module}'")
    # Seaborn.
    module = "seaborn"
    if hmodule.has_module(module):
        import seaborn as sns

        if sns_set:
            sns.set()
    else:
        print(f"No module '{module}'")
    # Pandas.
    module = "pandas"
    if hmodule.has_module(module):
        import pandas as pd

        pd.set_option("display.max_rows", 500)
        pd.set_option("display.max_columns", 500)
        pd.set_option("display.width", 1000)
    else:
        print(f"No module '{module}'")
    # Warnings.
    import helpers.hwarnings as hwarnin

    # Force the linter to keep this import.
    _ = hwarnin


# #############################################################################

# Notebook util libraries can use the following idiom to control the logging so
# that it works well both in a notebook and in code.

# In the notebook add:
# ```
# import helpers.htutorial as htutorial
# import <tutorial>_utils as utils

# # Configure the logger for this tutorial.
# _LOG = logging.getLogger(__name__)
# utils.init_logger(_LOG)
# ```

# Define `init_logger()` in the paired `*_utils.py` file:
# ```
# import helpers.hnotebook as hnotebo
#
# def init_logger(notebook_log: logging.Logger) -> None:
#     hnotebo.config_notebook()
#     hdbg.init_logger(verbosity=logging.INFO, use_exec_path=False)
#     # Init notebook logging.
#     hnotebo.set_logger_to_print(notebook_log)
#     # Init module logging.
#     <package>_logger: logging.Logger = logging.getLogger("<package>")
#     hnotebo.set_logger_to_print(<package>_logger)
# ```


def _info_print(msg: str, *args, **kwargs) -> None:
    """
    Print a message with optional formatting arguments.
    """
    if args:
        msg = msg % args
    print(msg)


def set_logger_to_print(log) -> None:
    """
    Replace `log.info` method with a `print` function.

    :param log: logger object to modify
    """
    log.info = _info_print


def set_all_loggers_to_print() -> None:
    """
    Replace all loggers' info method with a print function.
    """
    for name in logging.root.manager.loggerDict:
        logger = logging.getLogger(name)
        # print("Setting logger %s to print" % name)
        set_logger_to_print(logger)
