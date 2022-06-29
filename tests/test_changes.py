import matplotlib.pyplot as plt
import pandas as pd

from pdpbox.info_plots import actual_plot_interact, actual_plot

from sklearn.ensemble import RandomForestRegressor
from sklearn.datasets import fetch_california_housing

# data = fetch_california_housing()
#
# x = data['data']
# y = data['target']
# feature_names = data['feature_names']
#
# rgr = RandomForestRegressor()
# rgr.fit(x, y)
#
#
# fig, ax, summ = actual_plot_interact(
#     rgr,
#     pd.DataFrame(x, columns=feature_names),
#     features=['HouseAge', 'AveRooms'],
#     feature_names=feature_names, annotate=True, annotate_counts=False)
# plt.show()



