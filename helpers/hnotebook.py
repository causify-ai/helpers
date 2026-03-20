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
        print("No module '{module}'")
    # Seaborn.
    module = "seaborn"
    if hmodule.has_module(module):
        import seaborn as sns

        if sns_set:
            sns.set()
    else:
        print("No module '{module}'")
    # Pandas.
    module = "pandas"
    if hmodule.has_module(module):
        import pandas as pd

        pd.set_option("display.max_rows", 500)
        pd.set_option("display.max_columns", 500)
        pd.set_option("display.width", 1000)
    else:
        print("No module '{module}'")
    # Warnings.
    import helpers.hwarnings as hwarnin

    # Force the linter to keep this import.
    _ = hwarnin
