
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

from .info_plot_utils import (_target_plot, _info_plot_interact, _actual_plot, _prepare_info_plot_interact_data,
                              _prepare_info_plot_interact_summary, _prepare_info_plot_data,
                              _check_info_plot_interact_params, _check_info_plot_params)
from .utils import _make_list, _check_model, _check_target, _check_classes


def target_plot(df, feature, feature_name, target, num_grid_points=10, grid_type='percentile',
                percentile_range=None, grid_range=None, cust_grid_points=None, show_percentile=False,
                show_outliers=False, endpoint=True, figsize=None, ncols=2, plot_params=None):
    """
    Plot average target value across different feature values (feature grids)

    Parameters
    ----------
    df: pandas DataFrame
        data set to investigate on, should contain at least
        the feature to investigate as well as the target
    feature: string or list
        feature or feature list to investigate,
        for one-hot encoding features, feature list is required
    feature_name: string
        name of the feature, not necessary a column name
    target: string or list
        column name or column name list for target value
        for multi-class problem, a list of one-hot encoding target column
    num_grid_points: integer, optional, default=10
        number of grid points for numeric feature
    grid_type: string, optional, default='percentile'
        'percentile' or 'equal'
        type of grid points for numeric feature
    percentile_range: tuple or None, optional, default=None
        percentile range to investigate
        for numeric feature when grid_type='percentile'
    grid_range: tuple or None, optional, default=None
        value range to investigate
        for numeric feature when grid_type='equal'
    cust_grid_points: Series, 1d-array, list or None, optional, default=None
        customized list of grid points
        for numeric feature
    show_percentile: bool, optional, default=False
        whether to display the percentile buckets
        for numeric feature when grid_type='percentile'
    show_outliers: bool, optional, default=False
        whether to display the out of range buckets
        for numeric feature when percentile_range or grid_range is not None
    endpoint: bool, optional, default=True
        If True, stop is the last grid point
        Otherwise, it is not included
    figsize: tuple or None, optional, default=None
        size of the figure, (width, height)
    ncols: integer, optional, default=2
        number subplot columns, used when it is multi-class problem
    plot_params: dict or None, optional, default=None
        parameters for the plot

    Returns
    -------
    fig: matplotlib Figure
    axes: a dictionary of matplotlib Axes
        Returns the Axes objects for further tweaking
    summary_df: pandas DataFrame
        Graph data in data frame format

    Examples
    --------

    Quick start with target_plot

    .. highlight:: python
    .. code-block:: python

        from pdpbox import info_plots, get_dataset

        test_titanic = get_dataset.titanic()
        titanic_data = test_titanic['data']
        titanic_target = test_titanic['target']
        fig, axes, summary_df = info_plots.target_plot(
            df=titanic_data, feature='Sex', feature_name='Sex', target=titanic_target)


    With One-hot encoding features

    .. highlight:: python
    .. code-block:: python

        fig, axes, summary_df = info_plots.target_plot(
            df=titanic_data, feature=['Embarked_C', 'Embarked_Q', 'Embarked_S'],
            feature_name='Embarked', target=titanic_target)


    With numeric features

    .. highlight:: python
    .. code-block:: python

        fig, axes, summary_df = info_plots.target_plot(
            df=titanic_data, feature='Fare', feature_name='Fare',
            target=titanic_target, show_percentile=True)


    With multi-class

    .. highlight:: python
    .. code-block:: python

        from pdpbox import info_plots, get_dataset

        test_otto = get_dataset.otto()
        otto_data = test_otto['data']
        otto_target = test_otto['target']
        fig, axes, summary_df = info_plots.target_plot(
            df=otto_data, feature='feat_67', feature_name='feat_67',
            target=['target_0', 'target_2', 'target_5', 'target_8'])

    """

    # check inputs
    _ = _check_target(target=target, df=df)
    feature_type, show_outliers = _check_info_plot_params(
        df=df, feature=feature, grid_type=grid_type, percentile_range=percentile_range, grid_range=grid_range,
        cust_grid_points=cust_grid_points, show_outliers=show_outliers)

    # create feature grids and bar counts
    target = _make_list(target)
    useful_features = _make_list(feature) + target

    # map feature values to grid point buckets (x)
    data = df[useful_features]
    data_x, bar_data, summary_df, info_cols, display_columns, percentile_columns = _prepare_info_plot_data(
        feature=feature, feature_type=feature_type, data=data, num_grid_points=num_grid_points,
        grid_type=grid_type, percentile_range=percentile_range, grid_range=grid_range,
        cust_grid_points=cust_grid_points, show_percentile=show_percentile, show_outliers=show_outliers,
        endpoint=endpoint)

    # prepare data for target lines
    # each target line contains 'x' and mean target value
    target_lines = []
    for target_idx in range(len(target)):
        target_line = data_x.groupby('x', as_index=False).agg(
            {target[target_idx]: 'mean'}).sort_values('x', ascending=True)
        target_lines.append(target_line)
        summary_df = summary_df.merge(target_line, on='x', how='outer')
    summary_df = summary_df[info_cols + ['count'] + target]

    # inner call target plot
    fig, axes = _target_plot(
        feature_name=feature_name, display_columns=display_columns, percentile_columns=percentile_columns,
        target=target, bar_data=bar_data, target_lines=target_lines, figsize=figsize, ncols=ncols,
        plot_params=plot_params)

    return fig, axes, summary_df


def q1(x):
    return x.quantile(0.25)


def q2(x):
    return x.quantile(0.5)


def q3(x):
    return x.quantile(0.75)


def actual_plot(model, X, feature, feature_name, num_grid_points=10, grid_type='percentile',
                percentile_range=None,
                grid_range=None, cust_grid_points=None, show_percentile=False,
                show_outliers=False, endpoint=True,
                which_classes=None, predict_kwds={}, ncols=2, figsize=None, plot_params=None):
    """Plot prediction distribution across different feature values (feature grid)

    Parameters
    ----------

    model: a fitted sklearn model
    X: pandas DataFrame
        data set on which the model is trained
    feature: string or list
        feature or feature list to investigate
        for one-hot encoding features, feature list is required
    feature_name: string
        name of the feature, not necessary a column name
    num_grid_points: integer, optional, default=10
        number of grid points for numeric feature
    grid_type: string, optional, default='percentile'
        'percentile' or 'equal',
        type of grid points for numeric feature
    percentile_range: tuple or None, optional, default=None
        percentile range to investigate,
        for numeric feature when grid_type='percentile'
    grid_range: tuple or None, optional, default=None
        value range to investigate,
        for numeric feature when grid_type='equal'
    cust_grid_points: Series, 1d-array, list or None, optional, default=None
        customized list of grid points for numeric feature
    show_percentile: bool, optional, default=False
        whether to display the percentile buckets,
        for numeric feature when grid_type='percentile'
    show_outliers: bool, optional, default=False
        whether to display the out of range buckets
        for numeric feature when percentile_range or grid_range is not None
    endpoint: bool, optional
        If True, stop is the last grid point, default=True
        Otherwise, it is not included
    which_classes: list, optional, default=None
        which classes to plot, only use when it is a multi-class problem
    predict_kwds: dict, default={}
        keywords to be passed to the model's predict function
    figsize: tuple or None, optional, default=None
        size of the figure, (width, height)
    ncols: integer, optional, default=2
        number subplot columns, used when it is multi-class problem
    plot_params: dict or None, optional, default=None
        parameters for the plot

    Returns
    -------
    fig: matplotlib Figure
    axes: a dictionary of matplotlib Axes
        Returns the Axes objects for further tweaking
    summary_df: pandas DataFrame
        Graph data in data frame format

    Examples
    --------

    Quick start with actual_plot

    .. highlight:: python
    .. code-block:: python

        from pdpbox import info_plots, get_dataset

        test_titanic = get_dataset.titanic()
        titanic_data = test_titanic['data']
        titanic_features = test_titanic['features']
        titanic_target = test_titanic['target']
        titanic_model = test_titanic['xgb_model']
        fig, axes, summary_df = info_plots.actual_plot(
            model=titanic_model, X=titanic_data[titanic_features],
            feature='Sex', feature_name='Sex')


    With One-hot encoding features

    .. highlight:: python
    .. code-block:: python

        fig, axes, summary_df = info_plots.actual_plot(
            model=titanic_model, X=titanic_data[titanic_features],
            feature=['Embarked_C', 'Embarked_Q', 'Embarked_S'], feature_name='Embarked')


    With numeric features

    .. highlight:: python
    .. code-block:: python

        fig, axes, summary_df = info_plots.actual_plot(
            model=titanic_model, X=titanic_data[titanic_features],
            feature='Fare', feature_name='Fare')


    With multi-class

    .. highlight:: python
    .. code-block:: python

        from pdpbox import info_plots, get_dataset

        test_otto = get_dataset.otto()
        otto_data = test_otto['data']
        otto_model = test_otto['rf_model']
        otto_features = test_otto['features']
        otto_target = test_otto['target']

        fig, axes, summary_df = info_plots.actual_plot(
            model=otto_model, X=otto_data[otto_features],
            feature='feat_67', feature_name='feat_67', which_classes=[1, 2, 3])

    """

    # check inputs
    n_classes, predict = _check_model(model=model)
    feature_type, show_outliers = _check_info_plot_params(
        df=X, feature=feature, grid_type=grid_type, percentile_range=percentile_range, grid_range=grid_range,
        cust_grid_points=cust_grid_points, show_outliers=show_outliers)

    # make predictions
    # info_df only contains feature value and actual predictions
    prediction = predict(X, **predict_kwds)
    info_df = X[_make_list(feature)]
    actual_prediction_columns = ['actual_prediction']
    if n_classes == 0:
        info_df['actual_prediction'] = prediction
    elif n_classes == 2:
        info_df['actual_prediction'] = prediction[:, 1]
    else:
        plot_classes = range(n_classes)
        if which_classes is not None:
            _check_classes(classes_list=which_classes, n_classes=n_classes)
            plot_classes = sorted(which_classes)

        actual_prediction_columns = []
        for class_idx in plot_classes:
            info_df['actual_prediction_%d' % class_idx] = prediction[:, class_idx]
            actual_prediction_columns.append('actual_prediction_%d' % class_idx)

    info_df_x, bar_data, summary_df, info_cols, display_columns, percentile_columns = _prepare_info_plot_data(
        feature=feature, feature_type=feature_type, data=info_df, num_grid_points=num_grid_points,
        grid_type=grid_type, percentile_range=percentile_range, grid_range=grid_range,
        cust_grid_points=cust_grid_points, show_percentile=show_percentile,
        show_outliers=show_outliers, endpoint=endpoint)

    # prepare data for box lines
    # each box line contains 'x' and actual prediction q1, q2, q3
    box_lines = []
    actual_prediction_columns_qs = []
    for idx in range(len(actual_prediction_columns)):
        box_line = info_df_x.groupby('x', as_index=False).agg(
            {actual_prediction_columns[idx]: [q1, q2, q3]}).sort_values('x', ascending=True)
        box_line.columns = ['_'.join(col) if col[1] != '' else col[0] for col in box_line.columns]
        box_lines.append(box_line)
        actual_prediction_columns_qs += [actual_prediction_columns[idx] + '_%s' % q for q in ['q1', 'q2', 'q3']]
        summary_df = summary_df.merge(box_line, on='x', how='outer').fillna(0)
    summary_df = summary_df[info_cols + ['count'] + actual_prediction_columns_qs]

    fig, axes = _actual_plot(plot_data=info_df_x, bar_data=bar_data, box_lines=box_lines,
                             actual_prediction_columns=actual_prediction_columns, feature_name=feature_name,
                             display_columns=display_columns, percentile_columns=percentile_columns, figsize=figsize,
                             ncols=ncols, plot_params=plot_params)
    return fig, axes, summary_df


def target_plot_interact(df, features, feature_names, target, num_grid_points=None, grid_types=None,
                         percentile_ranges=None, grid_ranges=None, cust_grid_points=None, show_percentile=False,
                         show_outliers=False, endpoint=True, figsize=None, ncols=2, annotate=False, plot_params=None):
    """Plot average target value across different feature value combinations (feature grid combinations)

    Parameters
    ----------

    df: pandas DataFrame
        data set to investigate on, should contain at least
        the feature to investigate as well as the target
    features: list
        two features to investigate
    feature_names: list
        feature names
    target: string or list
        column name or column name list for target value
        for multi-class problem, a list of one-hot encoding target column
    num_grid_points: list, optional, default=None
        number of grid points for each feature
    grid_types: list, optional, default=None
        type of grid points for each feature
    percentile_ranges: list of tuple, optional, default=None
        percentile range to investigate for each feature
    grid_ranges: list of tuple, optional, default=None
        value range to investigate for each feature
    cust_grid_points: list of (Series, 1d-array, list), optional, default=None
        customized list of grid points for each feature
    show_percentile: bool, optional, default=False
        whether to display the percentile buckets for both feature
    show_outliers: bool, optional, default=False
        whether to display the out of range buckets for both features
    endpoint: bool, optional
        If True, stop is the last grid point, default=True
        Otherwise, it is not included
    figsize: tuple or None, optional, default=None
        size of the figure, (width, height)
    ncols: integer, optional, default=2
        number subplot columns, used when it is multi-class problem
    annotate: bool, default=False
        whether to annotate the points
    plot_params: dict or None, optional, default=None
        parameters for the plot

    Notes
    -----

    - Parameters are consistent with the ones for function target_plot
    - But for this function, you need to specify parameter value for both features in list format
    - For example:
        - percentile_ranges = [(0, 90), (5, 95)] means
        - percentile_range = (0, 90) for feature 1
        - percentile_range = (5, 95) for feature 2

    Returns
    -------
    fig: matplotlib Figure
    axes: a dictionary of matplotlib Axes
        Returns the Axes objects for further tweaking
    summary_df: pandas DataFrame
        Graph data in data frame format

    Examples
    --------

    Quick start with target_plot_interact

    .. highlight:: python
    .. code-block:: python

        from pdpbox import info_plots, get_dataset

        test_titanic = get_dataset.titanic()
        titanic_data = test_titanic['data']
        titanic_target = test_titanic['target']

        fig, axes, summary_df = info_plots.target_plot_interact(
            df=titanic_data, features=['Sex', ['Embarked_C', 'Embarked_Q', 'Embarked_S']],
            feature_names=['Sex', 'Embarked'], target=titanic_target)

    """

    # check inputs
    _ = _check_target(target=target, df=df)
    check_results = _check_info_plot_interact_params(
        num_grid_points=num_grid_points, grid_types=grid_types, percentile_ranges=percentile_ranges,
        grid_ranges=grid_ranges, cust_grid_points=cust_grid_points, show_outliers=show_outliers,
        plot_params=plot_params, features=features, df=df)

    num_grid_points = check_results['num_grid_points']
    grid_types = check_results['grid_types']
    percentile_ranges = check_results['percentile_ranges']
    grid_ranges = check_results['grid_ranges']
    cust_grid_points = check_results['cust_grid_points']
    show_outliers = check_results['show_outliers']
    plot_params = check_results['plot_params']
    feature_types = check_results['feature_types']

    # create feature grids and bar counts
    target = _make_list(target)
    useful_features = _make_list(features[0]) + _make_list(features[1]) + target

    # prepare data for bar plot
    data = df[useful_features].copy()

    # prepare data for target interact plot
    agg_dict = {}
    for t in target:
        agg_dict[t] = 'mean'
    agg_dict['fake_count'] = 'count'

    data_x, target_plot_data, prepared_results = _prepare_info_plot_interact_data(
        data_input=data, features=features, feature_types=feature_types, num_grid_points=num_grid_points,
        grid_types=grid_types, percentile_ranges=percentile_ranges, grid_ranges=grid_ranges,
        cust_grid_points=cust_grid_points, show_percentile=show_percentile,
        show_outliers=show_outliers, endpoint=endpoint, agg_dict=agg_dict)

    # prepare summary data frame
    summary_df, info_cols, display_columns, percentile_columns = _prepare_info_plot_interact_summary(
        data_x=data_x, plot_data=target_plot_data, prepared_results=prepared_results, feature_types=feature_types)
    summary_df = summary_df[info_cols + ['count'] + target]

    title = plot_params.get('title', 'Target plot for feature "%s"' % ' & '.join(feature_names))
    subtitle = plot_params.get('subtitle', 'Average target value through different feature value combinations.')

    # inner call target plot interact
    fig, axes = _info_plot_interact(
        feature_names=feature_names, display_columns=display_columns, percentile_columns=percentile_columns,
        ys=target, plot_data=target_plot_data, title=title, subtitle=subtitle, figsize=figsize,
        ncols=ncols, annotate=annotate, plot_params=plot_params)

    return fig, axes, summary_df


def actual_plot_interact(model, X, features, feature_names,
                         num_grid_points=None,
                         grid_types=None,
                         percentile_ranges=None,
                         grid_ranges=None,
                         cust_grid_points=None,
                         show_percentile=False,
                         show_outliers=False,
                         endpoint=True,
                         which_classes=None,
                         predict_kwds={},
                         ncols=2,
                         figsize=None,
                         annotate=False,
                         plot_params=None,
                         annotate_counts=True,
                         plot_type="circles",
                         annotate_colors=("black", "white"),
                         annotate_color_threshold=None,
                         annotate_fmt=None,
                         annotate_fontsize=7
                         ):
    """Plot prediction distribution across different feature value combinations (feature grid combinations)

    Parameters
    ----------

    model: a fitted sklearn model
    X: pandas DataFrame
        data set to investigate on, should contain at least
        the feature to investigate as well as the target
    features: list
        two features to investigate
    feature_names: list
        feature names
    num_grid_points: list, optional, default=None
        number of grid points for each feature
    grid_types: list, optional, default=None
        type of grid points for each feature
    percentile_ranges: list of tuple, optional, default=None
        percentile range to investigate for each feature
    grid_ranges: list of tuple, optional, default=None
        value range to investigate for each feature
    cust_grid_points: list of (Series, 1d-array, list), optional, default=None
        customized list of grid points for each feature
    show_percentile: bool, optional, default=False
        whether to display the percentile buckets for both feature
    show_outliers: bool, optional, default=False
        whether to display the out of range buckets for both features
    endpoint: bool, optional
        If True, stop is the last grid point, default=True
        Otherwise, it is not included
    which_classes: list, optional, default=None
        which classes to plot, only use when it is a multi-class problem
    predict_kwds: dict, default={}
        keywords to be passed to the model's predict function
    figsize: tuple or None, optional, default=None
        size of the figure, (width, height)
    ncols: integer, optional, default=2
        number subplot columns, used when it is multi-class problem
    annotate: bool, default=False
        whether to annotate the points
    annotate_counts : bool, default=False
        whether to annotate counts or not.
    plot_type : str, optional (default="circles")
        either ``circles`` or ``hetmap``
    annotate_colors : tuple
        pair of colors
    annotate_color_threshold : float
    annotate_fmt : str
        format for annotation
    annotate_fontsize : int
    plot_params: dict or None, optional, default=None
        parameters for the plot

    Returns
    -------
    fig: matplotlib Figure
    axes: a dictionary of matplotlib Axes
        Returns the Axes objects for further tweaking
    summary_df: pandas DataFrame
        Graph data in data frame format

    Notes
    -----

    - Parameters are consistent with the ones for function actual_plot
    - But for this function, you need to specify parameter value for both features in list format
    - For example:
        - percentile_ranges = [(0, 90), (5, 95)] means
        - percentile_range = (0, 90) for feature 1
        - percentile_range = (5, 95) for feature 2

    Examples
    --------

    Quick start with actual_plot_interact

    .. highlight:: python
    .. code-block:: python

        from pdpbox import info_plots, get_dataset

        test_titanic = get_dataset.titanic()
        titanic_data = test_titanic['data']
        titanic_features = test_titanic['features']
        titanic_target = test_titanic['target']
        titanic_model = test_titanic['xgb_model']

        fig, axes, summary_df = info_plots.actual_plot_interact(
            model=titanic_model, X=titanic_data[titanic_features],
            features=['Fare', ['Embarked_C', 'Embarked_Q', 'Embarked_S']],
            feature_names=['Fare', 'Embarked'])

    """

    # check model
    n_classes, predict = _check_model(model=model)
    check_results = _check_info_plot_interact_params(
        num_grid_points=num_grid_points, grid_types=grid_types, percentile_ranges=percentile_ranges,
        grid_ranges=grid_ranges, cust_grid_points=cust_grid_points, show_outliers=show_outliers,
        plot_params=plot_params, features=features, df=X)

    num_grid_points = check_results['num_grid_points']
    grid_types = check_results['grid_types']
    percentile_ranges = check_results['percentile_ranges']
    grid_ranges = check_results['grid_ranges']
    cust_grid_points = check_results['cust_grid_points']
    show_outliers = check_results['show_outliers']
    plot_params = check_results['plot_params']
    feature_types = check_results['feature_types']

    # prediction
    prediction = predict(X, **predict_kwds)

    info_df = X[_make_list(features[0]) + _make_list(features[1])]
    actual_prediction_columns = ['actual_prediction']
    if n_classes == 0:
        info_df['actual_prediction'] = prediction
    elif n_classes == 2:
        info_df['actual_prediction'] = prediction[:, 1]
    else:
        plot_classes = range(n_classes)
        if which_classes is not None:
            plot_classes = sorted(which_classes)

        actual_prediction_columns = []
        for class_idx in plot_classes:
            info_df['actual_prediction_%d' % class_idx] = prediction[:, class_idx]
            actual_prediction_columns.append('actual_prediction_%d' % class_idx)

    agg_dict = {}
    actual_prediction_columns_qs = []
    for idx in range(len(actual_prediction_columns)):
        agg_dict[actual_prediction_columns[idx]] = [q1, q2, q3]
        actual_prediction_columns_qs += [actual_prediction_columns[idx] + '_%s' % q for q in ['q1', 'q2', 'q3']]
    agg_dict['fake_count'] = 'count'

    data_x, actual_plot_data, prepared_results = _prepare_info_plot_interact_data(
        data_input=info_df, features=features, feature_types=feature_types, num_grid_points=num_grid_points,
        grid_types=grid_types, percentile_ranges=percentile_ranges, grid_ranges=grid_ranges,
        cust_grid_points=cust_grid_points, show_percentile=show_percentile,
        show_outliers=show_outliers, endpoint=endpoint, agg_dict=agg_dict)

    actual_plot_data.columns = ['_'.join(col) if col[1] != '' else col[0] for col in actual_plot_data.columns]
    actual_plot_data = actual_plot_data.rename(columns={'fake_count_count': 'fake_count'})

    # prepare summary data frame
    summary_df, info_cols, display_columns, percentile_columns = _prepare_info_plot_interact_summary(
        data_x=data_x, plot_data=actual_plot_data, prepared_results=prepared_results, feature_types=feature_types)
    summary_df = summary_df[info_cols + ['count'] + actual_prediction_columns_qs]

    title = plot_params.get('title', 'Actual predictions plot for %s' % ' & '.join(feature_names))
    subtitle = plot_params.get('subtitle',
                               'Medium value of actual prediction through different feature value combinations.')

    if plot_type== "circles":
        fig, axes = _info_plot_interact(
            feature_names=feature_names, display_columns=display_columns,
            percentile_columns=percentile_columns, ys=[col + '_q2' for col in actual_prediction_columns],
            plot_data=actual_plot_data, title=title, subtitle=subtitle, figsize=figsize,
            ncols=ncols, annotate=annotate, plot_params=plot_params, is_target_plot=False,
            annotate_counts=annotate_counts)
    else:
        vals = []
        for i in np.unique(summary_df['x1']):
            row = summary_df['actual_prediction_q2'].loc[summary_df['x1'] == i]
            for j in np.unique(summary_df['x2'])[::-1]:
                vals.append(row.iloc[j])

        counts = []
        for i in np.unique(summary_df['x1']):
            row = summary_df['count'].loc[summary_df['x1'] == i]
            for j in np.unique(summary_df['x2'])[::-1]:
                counts.append(row.iloc[j])

        xticklabels = summary_df.loc[summary_df['x1'] == 0]['display_column_2'].values[::-1]

        #if yticklabels is None:
        yticklabels = summary_df.loc[summary_df['x2'] == 0]['display_column_1'].values

        x = np.array(vals).reshape(len(yticklabels), len(xticklabels))
        df = pd.DataFrame(x, columns=xticklabels, index=yticklabels)

        counts = np.array(counts).reshape(len(yticklabels), len(xticklabels))
        counts = pd.DataFrame(counts, columns=xticklabels, index=yticklabels, dtype=int)

        fig, axes = plt.subplots(figsize=figsize)
        im, cbar = heatmap(
            df,
            row_labels=df.index,
            col_labels=df.columns,
            ax=axes,
            cmap="YlGn",
            cbarlabel="Median Prediction"
        )
        axes.set_ylabel(features[0])
        axes.set_xlabel(features[1])
        if annotate:
            texts = annotate_heatmap(
                im,
                valfmt=annotate_fmt or "{x:.1f}",
                fontsize=annotate_fontsize,
                textcolors=annotate_colors,
                threshold=annotate_color_threshold,
            )
        elif annotate_counts:
            texts = annotate_heatmap(
                im, counts.values,
                valfmt=annotate_fmt or "{x}",
                fontsize=annotate_fontsize,
                textcolors=annotate_colors,
                threshold=annotate_color_threshold)

    return fig, axes, summary_df


def heatmap(data, row_labels, col_labels, ax=None,
            cbar_kw={}, cbarlabel="",
            xlabel_on_top=True,
            **kwargs):
    """
    Create a heatmap from a numpy array and two lists of labels.
    Parameters
    ----------
    data
        A 2D numpy array of shape (M, N).
    row_labels
        A list or array of length M with the labels for the rows.
    col_labels
        A list or array of length N with the labels for the columns.
    ax
        A `matplotlib.axes.Axes` instance to which the heatmap is plotted.  If
        not provided, use current axes or create a new one.  Optional.
    cbar_kw
        A dictionary with arguments to `matplotlib.Figure.colorbar`.  Optional.
    cbarlabel
        The label for the colorbar.  Optional.
    **kwargs
        All other arguments are forwarded to `imshow`.
    """

    if not ax:
        ax = plt.gca()

    # Plot the heatmap
    im = ax.imshow(data, **kwargs)

    # Create colorbar
    # cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)
    # cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom")
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.2)
    fig: plt.Figure = plt.gcf()
    cbar = fig.colorbar(im, orientation="vertical", pad=0.2, cax=cax)
    cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom")

    # Show all ticks and label them with the respective list entries.
    ax.set_xticks(np.arange(data.shape[1]))
    ax.set_xticklabels(col_labels)
    ax.set_yticks(np.arange(data.shape[0]))
    ax.set_yticklabels(row_labels)


    if xlabel_on_top:
        # Let the horizontal axes labeling appear on top.
        ax.tick_params(top=True, bottom=False,
                       labeltop=True, labelbottom=False)
    #else:


    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=-30, ha="right",
             rotation_mode="anchor")

    # Turn spines off and create white grid.
    # in older versions ax.spines is dict and in newer versions it is list
    if isinstance(ax.spines, dict):
        for v in ax.spines.values():
            v.set_visible(False)
    else:
        ax.spines[:].set_visible(False)

    if xlabel_on_top:
        ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
    else:
        ax.set_xticks(np.arange(data.shape[1] - 1) + .5, minor=True)

    ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=3)
    ax.tick_params(which="minor", bottom=False, left=False)

    return im, cbar


def annotate_heatmap(im, data=None, valfmt="{x:.2f}",
                     textcolors=("black", "white"),
                     threshold=None, **textkw):
    """
    A function to annotate a heatmap.
    Parameters
    ----------
    im
        The AxesImage to be labeled.
    data
        Data used to annotate.  If None, the image's data is used.  Optional.
    valfmt
        The format of the annotations inside the heatmap.  This should either
        use the string format method, e.g. "$ {x:.2f}", or be a
        `matplotlib.ticker.Formatter`.  Optional.
    textcolors
        A pair of colors.  The first is used for values below a threshold,
        the second for those above.  Optional.
    threshold
        Value in data units according to which the colors from textcolors are
        applied.  If None (the default) uses the middle of the colormap as
        separation.  Optional.
    **kwargs
        All other arguments are forwarded to each call to `text` used to create
        the text labels.
    """

    if not isinstance(data, (list, np.ndarray)):
        data = im.get_array()

    # Normalize the threshold to the images color range.
    if threshold is not None:
        threshold = im.norm(threshold)
    else:
        threshold = im.norm(data.max())/2.

    # Set default alignment to center, but allow it to be
    # overwritten by textkw.
    kw = dict(horizontalalignment="center",
              verticalalignment="center")
    kw.update(textkw)

    # Get the formatter in case a string is supplied
    if isinstance(valfmt, str):
        valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

    # Loop over the data and create a `Text` for each "pixel".
    # Change the text's color depending on the data.
    texts = []
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            kw.update(color=textcolors[int(im.norm(data[i, j]) > threshold)])
            text = im.axes.text(j, i, valfmt(data[i, j], None), **kw)
            texts.append(text)

    return texts