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
# Purpose: Find out which of the 50 properties are redundant.
# ==========================================
plt.figure(figsize=(12, 10))
corr = df_scaled.corr()
# Use a diverging color map (coolwarm) to show positive/negative correlations
sns.heatmap(corr, cmap="coolwarm", center=0, square=True, 
            xticklabels=False, yticklabels=False, 
            cbar_kws={"shrink": .8})
plt.title("Style 1: Correlation Matrix of 50 Properties", fontsize=16)
plt.tight_layout()
plt.show()

# ==========================================
# STYLE 2: The Clustered Heatmap (Static)
# Purpose: Group similar compounds and similar properties together.
# ==========================================
# We use seaborn's clustermap which adds dendrograms automatically
clustermap = sns.clustermap(df_scaled, cmap="viridis", figsize=(14, 12),
                            xticklabels=False, yticklabels=False,
                            method='ward', metric='euclidean')
clustermap.fig.suptitle('Style 2: Clustered Heatmap of Compounds vs. Properties', y=1.05, fontsize=16)
plt.show()

# ==========================================
# STYLE 3: Interactive PCA Scatter Plot (Plotly)
# Purpose: Compress 50 dimensions into 2D to see "clusters" of compounds.
# ==========================================
# Run PCA to reduce 50 properties down to 2 principal components
pca = PCA(n_components=2)
pca_results = pca.fit_transform(df_scaled)
df['PCA1'] = pca_results[:, 0]
df['PCA2'] = pca_results[:, 1]

fig_pca = px.scatter(df, x='PCA1', y='PCA2', color='Family', 
                     hover_name=df.index, template="plotly_dark",
                     title="Style 3: Interactive PCA Scatter Plot (Hover for details)")
fig_pca.show()

# ==========================================
# STYLE 4: Interactive Parallel Coordinates (Plotly)
# Purpose: Visually filter compounds based on specific property thresholds.
# ==========================================
# Map the categorical 'Family' to numbers for the color scale
family_mapping = {'Kinase Inhibitor': 1, 'GPCR Target': 2, 'Ion Channel': 3}
df['Family_ID'] = df['Family'].map(family_mapping)

# We'll plot just the first 8 properties so it isn't visually overwhelming
cols_to_plot = [f"Prop_{i:02d}" for i in range(1, 9)]

fig_parallel = px.parallel_coordinates(df, color="Family_ID", dimensions=cols_to_plot,
                                       color_continuous_scale=px.colors.diverging.Tealrose,
                                       title="Style 4: Parallel Coordinates (Drag axes to filter)")
fig_parallel.show()

# ==========================================
# STYLE 5: Violin Plot Distribution Grid (Static)
# Purpose: Compare the spread of specific properties across compound families.
# ==========================================
# Melt the dataframe to make it compatible with Seaborn's faceted plots
df_melted = df.reset_index().melt(id_vars=['index', 'Family'], 
                                  value_vars=['Prop_01', 'Prop_02', 'Prop_03', 'Prop_04'],
                                  var_name='Property', value_name='Value')

plt.figure(figsize=(12, 6))
sns.violinplot(data=df_melted, x='Property', y='Value', hue='Family', split=False, inner="quartile", palette="Set2")
plt.title("Style 5: Property Distribution by Compound Family", fontsize=16)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()
