import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# Page configuration
st.set_page_config(page_title="Compound Analysis Dashboard", layout="wide")
st.title("Compound Property Analysis (50 Dimensions)")

# ==========================================
# 1. GENERATE MOCK DATA 
# ==========================================
np.random.seed(42)
compounds = [f"Compound_{i:03d}" for i in range(1, 101)]
data = {f"Prop_{i:02d}": np.random.randn(100) * 10 for i in range(1, 51)}
df = pd.DataFrame(data, index=compounds)
df['Family'] = np.random.choice(['Kinase Inhibitor', 'GPCR Target', 'Ion Channel'], 100)

numeric_df = df.drop(columns=['Family'])
scaler = StandardScaler()
df_scaled = pd.DataFrame(scaler.fit_transform(numeric_df), columns=numeric_df.columns, index=numeric_df.index)

# ==========================================
# STYLE 1: The Correlation Matrix 
# ==========================================
st.subheader("1. Correlation Matrix of 50 Properties")
st.write("Identifies which of the 50 properties are redundant.")

fig1, ax1 = plt.subplots(figsize=(12, 8))
corr = df_scaled.corr()
sns.heatmap(corr, cmap="coolwarm", center=0, square=True, 
            xticklabels=False, yticklabels=False, cbar_kws={"shrink": .8}, ax=ax1)
st.pyplot(fig1) # <-- Streamlit command for Matplotlib/Seaborn

st.divider()

# ==========================================
# STYLE 2: The Clustered Heatmap 
# ==========================================
st.subheader("2. Clustered Heatmap")
st.write("Groups similar compounds and similar properties together.")

clustermap = sns.clustermap(df_scaled, cmap="viridis", figsize=(12, 10),
                            xticklabels=False, yticklabels=False,
                            method='ward', metric='euclidean')
st.pyplot(clustermap.fig) # <-- Pass the clustermap figure to Streamlit

st.divider()

# ==========================================
# STYLE 3: Interactive PCA Scatter Plot
# ==========================================
st.subheader("3. Interactive PCA Scatter Plot")
st.write("Compresses 50 dimensions into 2D to find clusters. (Hover for details)")

pca = PCA(n_components=2)
pca_results = pca.fit_transform(df_scaled)
df['PCA1'] = pca_results[:, 0]
df['PCA2'] = pca_results[:, 1]

fig_pca = px.scatter(df, x='PCA1', y='PCA2', color='Family', 
                     hover_name=df.index, template="plotly_dark")
st.plotly_chart(fig_pca, use_container_width=True) # <-- Streamlit command for Plotly

st.divider()

# ==========================================
# STYLE 4: Interactive Parallel Coordinates
# ==========================================
st.subheader("4. Parallel Coordinates")
st.write("Drag vertically along the axes to filter compounds by property thresholds.")

family_mapping = {'Kinase Inhibitor': 1, 'GPCR Target': 2, 'Ion Channel': 3}
df['Family_ID'] = df['Family'].map(family_mapping)
cols_to_plot = [f"Prop_{i:02d}" for i in range(1, 9)]

fig_parallel = px.parallel_coordinates(df, color="Family_ID", dimensions=cols_to_plot,
                                       color_continuous_scale=px.colors.diverging.Tealrose)
st.plotly_chart(fig_parallel, use_container_width=True)

st.divider()

# ==========================================
# STYLE 5: Violin Plot Distribution Grid
# ==========================================
st.subheader("5. Property Distribution by Compound Family")

df_melted = df.reset_index().melt(id_vars=['index', 'Family'], 
                                  value_vars=['Prop_01', 'Prop_02', 'Prop_03', 'Prop_04'],
                                  var_name='Property', value_name='Value')

fig5, ax5 = plt.subplots(figsize=(12, 6))
sns.violinplot(data=df_melted, x='Property', y='Value', hue='Family', split=False, inner="quartile", palette="Set2", ax=ax5)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
st.pyplot(fig5)
