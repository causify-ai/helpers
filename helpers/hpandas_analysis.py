"""
Statistical analysis and ML functions for pandas DataFrames.

Import as:

import helpers.hpandas_analysis as hpananal
"""

import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import sklearn.linear_model
import statsmodels.api
import tqdm.autonotebook as tauton

import helpers.hdbg as hdbg
import helpers.hmatplotlib as hmatloti
import helpers.hpandas as hpandas
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


def _get_num_pcs_to_plot(num_pcs_to_plot: int, max_pcs: int) -> int:
    """
    Get the number of principal components to plot.

    :param num_pcs_to_plot: requested number of PCs to plot, use -1 for all
    :param max_pcs: maximum number of available principal components
    :return: validated number of PCs to plot
    """
    if num_pcs_to_plot == -1:
        num_pcs_to_plot = max_pcs
    hdbg.dassert_lte(0, num_pcs_to_plot)
    hdbg.dassert_lte(num_pcs_to_plot, max_pcs)
    return num_pcs_to_plot


def rolling_corr_over_time(
    df: pd.DataFrame, com: float, nan_mode: str
) -> pd.DataFrame:
    """
    Compute rolling correlation over time.

    :return: corr_df is a multi-index df storing correlation matrices with
        labels
    """
    hpandas.dassert_strictly_increasing_index(df)
    # Handle NaNs based on mode.
    if nan_mode == "drop":
        df = df.dropna(how="any")
    elif nan_mode == "fill_with_zero":
        df = df.fillna(0.0)
    elif nan_mode == "abort":
        num_nans = np.isnan(df).sum().sum()
        if num_nans > 0:
            raise ValueError("df has %d nans\n%s" % (num_nans, df))
    else:
        raise ValueError("Invalid nan_mode='%s'" % nan_mode)
    corr_df = df.ewm(com=com, min_periods=3 * com).corr()
    return corr_df


def _get_eigvals_eigvecs(
    df: pd.DataFrame, dt: datetime.date, sort_eigvals: bool
) -> Tuple[np.array, np.array]:
    """
    Compute eigenvalues and eigenvectors for a correlation matrix at a
    specific date.

    :param df: correlation matrix dataframe with multiindex (date, columns)
    :param dt: date for which to compute eigenvalues/eigenvectors
    :param sort_eigvals: whether to sort eigenvalues in descending order
    :return: tuple of (eigenvalues array, eigenvectors array)
    """
    hdbg.dassert_isinstance(dt, datetime.date)
    df_tmp = df.loc[dt].copy()
    # Compute rolling eigenvalues and eigenvectors.
    # TODO(gp): Count and report inf and nans as warning.
    df_tmp.replace([np.inf, -np.inf], np.nan, inplace=True)
    df_tmp.fillna(0.0, inplace=True)
    eigval, eigvec = np.linalg.eigh(df_tmp)
    # Sort eigenvalues, if needed.
    if not (sorted(eigval) == eigval).all():
        _LOG.debug("eigvals not sorted: %s", eigval)
        if sort_eigvals:
            _LOG.debug(
                "Before sorting:\neigval=\n%s\neigvec=\n%s", eigval, eigvec
            )
            _LOG.debug("eigvals: %s", eigval)
            idx = eigval.argsort()[::-1]
            eigval = eigval[idx]
            eigvec = eigvec[:, idx]
            _LOG.debug(
                "After sorting:\neigval=\n%s\neigvec=\n%s", eigval, eigvec
            )
    #
    if (eigval == 0).all():
        eigvec = np.nan * eigvec
    return eigval, eigvec


def rolling_pca_over_time(
    df: pd.DataFrame, com: float, nan_mode: str, sort_eigvals: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Compute rolling PCAs over time.

    :param sort_eigvals: sort the eigenvalues in descending orders
    :return:
        - eigval_df stores eigenvalues for the different components indexed by
          timestamps
        - eigvec_df stores eigenvectors as multiindex df
    """
    # Compute rolling correlation.
    corr_df = rolling_corr_over_time(df, com, nan_mode)
    # Compute eigvalues and eigenvectors.
    timestamps = corr_df.index.get_level_values(0).unique()
    eigval = np.zeros((timestamps.shape[0], df.shape[1]))
    eigvec = np.zeros((timestamps.shape[0], df.shape[1], df.shape[1]))
    for i, dt in tauton.tqdm(
        enumerate(timestamps),
        total=timestamps.shape[0],
        desc="Computing rolling PCA",
    ):
        eigval[i], eigvec[i] = _get_eigvals_eigvecs(corr_df, dt, sort_eigvals)
    # Package results.
    eigval_df = pd.DataFrame(eigval, index=timestamps)
    hdbg.dassert_eq(eigval_df.shape[0], len(timestamps))
    hpandas.dassert_strictly_increasing_index(eigval_df)
    # Normalize by sum.
    # TODO(gp): Move this up.
    eigval_df = eigval_df.multiply(1 / eigval_df.sum(axis=1), axis="index")
    #
    # pylint ref: github.com/PyCQA/pylint/issues/3139
    eigvec = eigvec.reshape((-1, eigvec.shape[-1]))  # pylint: disable=unsubscriptable-object
    idx = pd.MultiIndex.from_product(
        [timestamps, df.columns], names=["datetime", None]
    )
    eigvec_df = pd.DataFrame(eigvec, index=idx, columns=range(df.shape[1]))  # pylint: disable=unsubscriptable-object
    hdbg.dassert_eq(
        len(eigvec_df.index.get_level_values(0).unique()), len(timestamps)
    )
    return corr_df, eigval_df, eigvec_df


def plot_pca_over_time(
    eigval_df: pd.DataFrame,
    eigvec_df: pd.DataFrame,
    num_pcs_to_plot: int = 0,
    num_cols: int = 2,
) -> None:
    """
    Similar to plot_pca_analysis() but over time.
    """
    # Plot eigenvalues.
    eigval_df.plot(title="Eigenvalues over time", ylim=(0, 1))
    # Plot cumulative variance.
    eigval_df.cumsum(axis=1).plot(
        title="Fraction of variance explained by top PCs over time", ylim=(0, 1)
    )
    # Plot eigenvalues.
    max_pcs = eigvec_df.shape[1]
    num_pcs_to_plot = _get_num_pcs_to_plot(num_pcs_to_plot, max_pcs)
    _LOG.info("num_pcs_to_plot=%s", num_pcs_to_plot)
    if num_pcs_to_plot > 0:
        _, axes = hmatloti.get_multiple_plots(
            num_pcs_to_plot,
            num_cols=num_cols,
            y_scale=4,
            sharex=True,
            sharey=True,
        )
        for i in range(num_pcs_to_plot):
            eigvec_df[i].unstack(1).plot(
                ax=axes[i], ylim=(-1, 1), title="PC%s" % i
            )


def plot_time_distributions(
    dts: List[Union[datetime.datetime, pd.Timestamp]],
    mode: str,
    density: bool = True,
) -> mpl.axes.Axes:
    """
    Compute distribution for an array of timestamps `dts`.

    - mode: see below
    """
    hdbg.dassert_type_in(dts[0], (datetime.datetime, pd.Timestamp))
    hdbg.dassert_in(
        mode,
        (
            "time_of_the_day",
            "weekday",
            "minute_of_the_hour",
            "day_of_the_month",
            "month_of_the_year",
            "year",
        ),
    )
    if mode == "time_of_the_day":
        # Convert in minutes from the beginning of the day.
        data = [dt.time() for dt in dts]
        data = [t.hour * 60 + t.minute for t in data]
        # 1 hour bucket.
        step = 60
        bins = np.arange(0, 24 * 60 + step, step)
        vals = pd.cut(
            data,
            bins=bins,
            include_lowest=True,
            right=False,
            retbins=False,
            labels=False,
        )
        # Count.
        count = pd.Series(vals).value_counts(sort=False)
        # Compute the labels.
        yticks = [
            "%02d:%02d" % (bins[k] / 60, bins[k] % 60) for k in count.index
        ]
    elif mode == "weekday":
        data = [dt.date().weekday() for dt in dts]
        bins = np.arange(0, 7 + 1)
        vals = pd.cut(
            data,
            bins=bins,
            include_lowest=True,
            right=False,
            retbins=False,
            labels=False,
        )
        # Count.
        count = pd.Series(vals).value_counts(sort=False)
        # Compute the labels.
        yticks = "Mon Tue Wed Thu Fri Sat Sun".split()
    elif mode == "minute_of_the_hour":
        vals = [dt.time().minute for dt in dts]
        # Count.
        count = pd.Series(vals).value_counts(sort=False)
        # Compute the labels.
        yticks = list(map(str, list(range(1, 60 + 1))))
    elif mode == "day_of_the_month":
        vals = [dt.date().day for dt in dts]
        # Count.
        count = pd.Series(vals).value_counts(sort=False)
        # Compute the labels.
        yticks = list(map(str, list(range(1, 31 + 1))))
    elif mode == "month_of_the_year":
        vals = [dt.date().month for dt in dts]
        # Count.
        count = pd.Series(vals).value_counts(sort=False)
        # Compute the labels.
        yticks = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    elif mode == "year":
        vals = [dt.date().year for dt in dts]
        # Count.
        count = pd.Series(vals).value_counts(sort=False)
        # Compute the labels.
        yticks = pd.Series(vals).unique().tolist()
    else:
        raise ValueError("Invalid mode='%s'" % mode)
    hdbg.dassert_eq(count.sum(), len(dts))
    #
    if density:
        count /= count.sum()
    label = "num points=%s" % len(dts)
    ax = count.plot(kind="bar", label=label, figsize=(20, 7))
    ax.set_xticklabels(yticks)
    if density:
        ax.set_ylabel("Probability")
    else:
        ax.set_ylabel("Count")
    ax.legend(loc="best")
    return ax


# TODO(gp): It can't accept ax. Remove this limitation.
def jointplot(
    df: pd.DataFrame,
    predicted_var: str,
    predictor_var: str,
    height: Optional[int] = None,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Perform a scatterplot of two columns of a dataframe using
    seaborn.jointplot().

    :param df: dataframe
    :param predicted_var: y-var
    :param predictor_var: x-var
    :param args, kwargs: arguments passed to seaborn.jointplot()
    """
    hdbg.dassert_in(predicted_var, df.columns)
    hdbg.dassert_in(predictor_var, df.columns)
    df = df[[predicted_var, predictor_var]]
    # Remove non-finite values.
    # TODO(gp): Use explore.dropna().
    mask = np.all(np.isfinite(df.values), axis=1)
    df = df[mask]
    # Plot.
    sns.jointplot(
        x=predictor_var, y=predicted_var, data=df, height=height, *args, **kwargs
    )


def _preprocess_regression(
    df: pd.DataFrame,
    intercept: bool,
    predicted_var: str,
    predicted_var_delay: int,
    predictor_vars: Union[str, List[str]],
    predictor_vars_delay: int,
) -> Optional[Tuple[pd.DataFrame, List[str], List[str]]]:
    """
    Preprocess data in dataframe form in order to perform a regression.
    """
    # Sanity check vars.
    hdbg.dassert_type_is(df, pd.DataFrame)
    hdbg.dassert_lte(1, df.shape[0])
    if isinstance(predictor_vars, str):
        predictor_vars = [predictor_vars]
    hdbg.dassert_type_is(predictor_vars, list)
    # hdbg.dassert_type_is(predicted_var, str)
    hdbg.dassert_not_in(predicted_var, predictor_vars)
    if not predictor_vars:
        # No predictors.
        _LOG.warning("No predictor vars: skipping")
        return None
    #
    col_names = [predicted_var] + predictor_vars
    hdbg.dassert_is_subset(col_names, df.columns)
    df = df[col_names].copy()
    num_rows = df.shape[0]
    # Shift.
    if predicted_var_delay != 0:
        df[predicted_var] = df[predicted_var].shift(predicted_var_delay)
        _LOG.warning("Shifting predicted_var=%s", predicted_var_delay)
    if predictor_vars_delay != 0:
        df[predictor_vars] = df[predictor_vars].shift(predictor_vars_delay)
        _LOG.warning("Shifting predictor_vars=%s", predictor_vars_delay)
    # Remove non-finite values.
    # TODO(gp): Use the function.
    df.dropna(how="all", inplace=True)
    num_rows_after_drop_nan_all = df.shape[0]
    if num_rows_after_drop_nan_all != num_rows:
        _LOG.info(
            "Removed %s rows with all nans",
            hprint.perc(num_rows - num_rows_after_drop_nan_all, num_rows),
        )
    #
    df.dropna(how="any", inplace=True)
    num_rows_after_drop_nan_any = df.shape[0]
    if num_rows_after_drop_nan_any != num_rows_after_drop_nan_all:
        _LOG.warning(
            "Removed %s rows with any nans",
            hprint.perc(num_rows - num_rows_after_drop_nan_any, num_rows),
        )
    # Prepare data.
    if intercept:
        if "const" not in df.columns:
            df.insert(0, "const", 1.0)
        predictor_vars = ["const"] + predictor_vars[:]
    param_names = predictor_vars[:]
    hdbg.dassert(np.all(np.isfinite(df[predicted_var].values)))
    hdbg.dassert(
        np.all(np.isfinite(df[predictor_vars].values)),
        msg="predictor_vars=%s" % predictor_vars,
    )
    # Perform regression.
    if df.shape[0] < 1:
        return None
    return df, param_names, predictor_vars


def ols_regress(
    df: pd.DataFrame,
    predicted_var: str,
    predictor_vars: str,
    intercept: bool,
    print_model_stats: bool = True,
    tsplot: bool = False,
    tsplot_figsize: Optional[Any] = None,
    jointplot_: bool = True,
    jointplot_height: Optional[Any] = None,
    predicted_var_delay: int = 0,
    predictor_vars_delay: int = 0,
    max_nrows: float = 1e4,
) -> Optional[Dict[str, Any]]:
    """
    Perform OLS on columns of a dataframe.

    :param df: dataframe
    :param predicted_var: y variable
    :param predictor_vars: x variables
    :param intercept:
    :param print_model_stats: print or return the model stats
    :param tsplot: plot a time-series if possible
    :param tsplot_figsize:
    :param jointplot_: plot a scatter plot
    :param jointplot_height:
    :param predicted_var_delay:
    :param predictor_vars_delay:
    :param max_nrows: do not plot if there are too many rows, since notebook
        can be slow or hang
    :return:
    """
    obj = _preprocess_regression(
        df,
        intercept,
        predicted_var,
        predicted_var_delay,
        predictor_vars,
        predictor_vars_delay,
    )
    if obj is None:
        return None
    df, param_names, predictor_vars = obj
    hdbg.dassert_lte(1, df.shape[0])
    model = statsmodels.api.OLS(
        df[predicted_var], df[predictor_vars], hasconst=intercept
    ).fit()
    regr_res = {
        "param_names": param_names,
        "coeffs": model.params,
        "pvals": model.pvalues,
        # pylint: disable=no-member
        "rsquared": model.rsquared,
        "adj_rsquared": model.rsquared_adj,
        "model": model,
    }
    if print_model_stats:
        # pylint: disable=no-member
        _LOG.info(model.summary().as_text())
    if tsplot or jointplot_:
        if max_nrows is not None and df.shape[0] > max_nrows:
            _LOG.warning(
                "Skipping plots since df has %d > %d rows",
                df.shape[0],
                max_nrows,
            )
        else:
            predictor_vars = [p for p in predictor_vars if p != "const"]
            if len(predictor_vars) == 1:
                if tsplot:
                    # Plot the data over time.
                    if tsplot_figsize is None:
                        tsplot_figsize = hmatloti.FIG_SIZE
                    df[[predicted_var, predictor_vars[0]]].plot(
                        figsize=tsplot_figsize
                    )
                if jointplot_:
                    # Perform scatter plot.
                    if jointplot_height is None:
                        jointplot_height = hmatloti.FIG_SIZE[1]
                    jointplot(
                        df,
                        predicted_var,
                        predictor_vars[0],
                        height=jointplot_height,
                    )
            else:
                _LOG.warning(
                    "Skipping plots since there are too many predictors"
                )
    if print_model_stats:
        return None
    return regr_res


def ols_regress_series(
    srs1: pd.Series,
    srs2: pd.Series,
    intercept: bool,
    srs1_name: Optional[Any] = None,
    srs2_name: Optional[Any] = None,
    convert_to_dates: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Regress two series against each other.

    Wrapper around regress() to regress series against each other.
    """
    # Validate inputs are Series.
    hdbg.dassert_isinstance(srs1, pd.Series)
    hdbg.dassert_isinstance(srs2, pd.Series)
    srs1 = srs1.copy()
    srs2 = srs2.copy()
    #
    if convert_to_dates:
        _LOG.warning("Sampling to date")
        srs1.index = [pd.to_datetime(dt).date() for dt in srs1.index]
        srs2.index = [pd.to_datetime(dt).date() for dt in srs2.index]
    #
    hdbg.dassert_array_has_same_type_element(srs1, srs2, only_first_elem=True)
    # Check common indices.
    common_idx = srs1.index.intersection(srs2.index)
    hdbg.dassert_lte(1, len(common_idx))
    # Merge series into a dataframe.
    if srs1_name is None:
        srs1_name = srs1.name if srs1.name is not None else ""
    if srs2_name is None:
        srs2_name = srs2.name if srs2.name is not None else ""
    if srs1_name == srs2_name:
        srs1_name += "_1"
        srs2_name += "_2"
        _LOG.warning("Series have the same name: adding suffix to distinguish")
    df = pd.concat([srs1, srs2], axis=1, join="outer")
    df.columns = [srs1_name, srs2_name]
    #
    val = ols_regress(df, srs1_name, srs2_name, intercept=intercept, **kwargs)
    val = cast(Dict[str, Any], val)
    return val


def robust_regression(
    df: pd.DataFrame,
    predicted_var: str,
    predictor_vars: str,
    intercept: bool,
    jointplot_: bool = True,
    jointplot_figsize: Optional[Any] = None,
    predicted_var_delay: int = 0,
    predictor_vars_delay: int = 0,
) -> None:
    """
    Perform robust regression using RANSAC algorithm to handle outliers.

    :param df: dataframe with data
    :param predicted_var: dependent variable column name
    :param predictor_vars: independent variable column name(s)
    :param intercept: whether to include intercept in regression
    :param jointplot_: whether to create a scatter plot
    :param jointplot_figsize: size of the joint plot
    :param predicted_var_delay: shift predicted variable by this many periods
    :param predictor_vars_delay: shift predictor variables by this many periods
    """
    obj = _preprocess_regression(
        df,
        intercept,
        predicted_var,
        predicted_var_delay,
        predictor_vars,
        predictor_vars_delay,
    )
    if obj is None:
        return
    # From http://scikit-learn.org/stable/auto_examples/linear_model/
    #   plot_robust_fit.html#sphx-glr-auto-examples-linear-model-plot-robust-fit-py
    # TODO(gp): Add also TheilSenRegressor and HuberRegressor.

    hdbg.dassert_eq(len(predictor_vars), 1)
    y = df[predicted_var]
    X = df[predictor_vars]
    # Fit line using all data.
    lr = sklearn.linear_model.LinearRegression()
    lr.fit(X, y)
    # Robustly fit linear model with RANSAC algorithm.
    ransac = sklearn.linear_model.RANSACRegressor()
    ransac.fit(X, y)
    inlier_mask = ransac.inlier_mask_
    outlier_mask = np.logical_not(inlier_mask)
    # Predict data of estimated models.
    line_X = np.linspace(X.min().values[0], X.max().values[0], num=100)[
        :, np.newaxis
    ]
    line_y = lr.predict(line_X)
    line_y_ransac = ransac.predict(line_X)
    # Compare estimated coefficients
    _LOG.info("Estimated coef for linear regression=%s", lr.coef_)
    _LOG.info("Estimated coef for RANSAC=%s", ransac.estimator_.coef_)
    if jointplot_:
        if jointplot_figsize is None:
            jointplot_figsize = hmatloti.FIG_SIZE
        plt.figure(figsize=jointplot_figsize)
        plt.scatter(
            X[inlier_mask],
            y[inlier_mask],
            color="red",
            marker="o",
            label="Inliers",
        )
        plt.scatter(
            X[outlier_mask],
            y[outlier_mask],
            color="blue",
            marker="o",
            label="Outliers",
        )
        plt.plot(line_X, line_y, color="green", linewidth=2, label="OLS")
        plt.plot(
            line_X, line_y_ransac, color="black", linewidth=3, label="RANSAC"
        )
        plt.legend(loc="best")
        plt.xlabel(", ".join(predictor_vars))
        plt.ylabel(predicted_var)
