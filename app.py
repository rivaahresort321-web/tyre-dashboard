import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# ==========================================
# 1. GENERATE MOCK DATA (100 Compounds, 50 Properties)
# ==========================================
np.random.seed(42)
compounds = [f"Compound_{i:03d}" for i in range(1, 101)]

# Create 50 random properties (some correlated, some noise)
data = {f"Prop_{i:02d}": np.random.randn(100) * 10 for i in range(1, 51)}
df = pd.DataFrame(data, index=compounds)

# Add a categorical "Family" column to help with color-coding later
df['Family'] = np.random.choice(['Kinase Inhibitor', 'GPCR Target', 'Ion Channel'], 100)

# Standardize the numerical data (crucial when properties have different scales/units)
numeric_df = df.drop(columns=['Family'])
scaler = StandardScaler()
df_scaled = pd.DataFrame(scaler.fit_transform(numeric_df), columns=numeric_df.columns, index=numeric_df.index)

# ==========================================
# STYLE 1: The Correlation Matrix (Static)
# ==========================================
plt.figure(figsize=(12, 10))
corr = df_scaled.corr()
sns.heatmap(corr, cmap="coolwarm", center=0, square=True, 
            xticklabels=False, yticklabels=False, 
            cbar_kws={"shrink": .8})
plt.title("Style 1: Correlation Matrix of 50 Properties", fontsize=16)
plt.tight_layout()
plt.show()

# ==========================================
# STYLE 2: The Clustered Heatmap (Static)
# ==========================================
clustermap = sns.clustermap(df_scaled, cmap="viridis", figsize=(14, 12),
                            xticklabels=False, yticklabels=False,
                            method='ward', metric='euclidean')
clustermap.fig.suptitle('Style 2: Clustered Heatmap of Compounds vs. Properties', y=1.05, fontsize=16)
plt.show()

# ==========================================
# STYLE 3: Interactive 2D PCA Scatter Plot (Plotly)
# ==========================================
pca_2d = PCA(n_components=2)
pca_2d_results = pca_2d.fit_transform(df_scaled)
df['PCA1'] = pca_2d_results[:, 0]
df['PCA2'] = pca_2d_results[:, 1]

fig_pca_2d = px.scatter(df, x='PCA1', y='PCA2', color='Family', 
                        hover_name=df.index, template="plotly_dark",
                        title="Style 3: Interactive 2D PCA Scatter Plot")
fig_pca_2d.show()

# ==========================================
# STYLE 4: Interactive Parallel Coordinates (Plotly)
# ==========================================
family_mapping = {'Kinase Inhibitor': 1, 'GPCR Target': 2, 'Ion Channel': 3}
df['Family_ID'] = df['Family'].map(family_mapping)
cols_to_plot = [f"Prop_{i:02d}" for i in range(1, 9)]

fig_parallel = px.parallel_coordinates(df, color="Family_ID", dimensions=cols_to_plot,
                                       color_continuous_scale=px.colors.diverging.Tealrose,
                                       title="Style 4: Parallel Coordinates (Drag axes to filter)")
fig_parallel.show()

# ==========================================
# STYLE 5: Violin Plot Distribution Grid (Static)
# ==========================================
df_melted_violin = df.reset_index().melt(id_vars=['index', 'Family'], 
                                         value_vars=['Prop_01', 'Prop_02', 'Prop_03', 'Prop_04'],
                                         var_name='Property', value_name='Value')

plt.figure(figsize=(12, 6))
sns.violinplot(data=df_melted_violin, x='Property', y='Value', hue='Family', split=False, inner="quartile", palette="Set2")
plt.title("Style 5: Property Distribution by Compound Family", fontsize=16)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

# ==========================================
# NEW STYLE 6: Interactive 3D PCA Scatter Plot (Plotly)
# Purpose: Add a third dimension to better visualize complex clusters.
# ==========================================
# We need 3 principal components instead of 2
pca_3d = PCA(n_components=3)
pca_3d_results = pca_3d.fit_transform(df_scaled)
df['PCA1_3D'] = pca_3d_results[:, 0]
df['PCA2_3D'] = pca_3d_results[:, 1]
df['PCA3_3D'] = pca_3d_results[:, 2]

fig_pca_3d = px.scatter_3d(df, x='PCA1_3D', y='PCA2_3D', z='PCA3_3D',
                           color='Family', hover_name=df.index, 
                           template="plotly_dark", opacity=0.8,
                           title="Style 6: Interactive 3D PCA Scatter Plot")
fig_pca_3d.update_traces(marker=dict(size=5)) # Make dots slightly smaller for 3D
fig_pca_3d.show()

# ==========================================
# NEW STYLE 7: Grouped Bar Chart (Plotly)
# Purpose: Compare the *average* values of specific properties across families.
# ==========================================
# Let's take the first 6 properties and find the average for each family
cols_for_bar = [f"Prop_{i:02d}" for i in range(1, 7)]
df_mean_bar = df.groupby('Family')[cols_for_bar].mean().reset_index()

# Melt the dataframe so Plotly can group it easily
df_mean_bar_melted = df_mean_bar.melt(id_vars='Family', var_name='Property', value_name='Average Value')

fig_bar = px.bar(df_mean_bar_melted, x='Property', y='Average Value', color='Family', 
                 barmode='group', template="plotly_white",
                 title="Style 7: Average Property Values by Compound Family")
fig_bar.show()

# ==========================================
# NEW STYLE 8: Radar Chart / Spider Plot (Plotly)
# Purpose: Show the "fingerprint" profile of each family across multiple properties.
# ==========================================
# We'll use 8 properties to give the radar chart a nice shape
cols_for_radar = [f"Prop_{i:02d}" for i in range(1, 9)]
df_mean_radar = df_scaled.groupby(df['Family'])[cols_for_radar].mean().reset_index()

# Melt the data into a long format for the polar chart
df_radar_melted = df_mean_radar.melt(id_vars='Family', var_name='Property', value_name='Standardized Mean')

fig_radar = px.line_polar(df_radar_melted, r='Standardized Mean', theta='Property', color='Family',
                          line_close=True, template="plotly_dark",
                          title="Style 8: Radar Chart Profiling (Standardized Means)")
# Fill the area under the lines to make it look like a classic radar chart
fig_radar.update_traces(fill='toself')
fig_radar.show()
