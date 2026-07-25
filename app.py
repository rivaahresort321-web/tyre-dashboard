import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Tyre Compound Review", layout="wide")
st.title("Rubber Compound Property Review")

st.sidebar.header("1. Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload your Excel template", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # --- 1. DATA CLEANING ENGINE ---
        df_raw = pd.read_excel(uploaded_file, sheet_name='SUMMARY')
        
        comp_row = df_raw.iloc[2]
        property_col_name = df_raw.columns[0]
        
        compound_cols = []
        compound_names = []
        for i in range(2, len(df_raw.columns)):
            val = str(comp_row.iloc[i]).strip()
            if val and val.lower() != 'nan':
                compound_cols.append(df_raw.columns[i])
                compound_names.append(val)

        df_data = df_raw.iloc[3:].copy()
        df_data = df_data[[property_col_name] + compound_cols]
        df_data = df_data.dropna(subset=[property_col_name])
        df_data.columns = ['Property'] + compound_names

        for col in compound_names:
            df_data[col] = pd.to_numeric(df_data[col], errors='coerce')

        df_clean = df_data.dropna(subset=compound_names, how='all').reset_index(drop=True)
        df_clean = df_clean.fillna(0)

        # Make duplicate properties unique
        s = df_clean['Property']
        df_clean['Property'] = s.where(~s.duplicated(), s + ' (' + s.groupby(s).cumcount().astype(str) + ')')
        
        # --- 2. DASHBOARD UI SETUP ---
        all_properties = df_clean['Property'].tolist()
        LOWER_IS_BETTER = ['MH - ML', 'tanD @70°C'] 

        st.sidebar.header("2. Review Mode")
        mode = st.sidebar.radio("Values to Display:", ["Absolute Values", "Indexed against 100"])
        
        reference_compound = None
        if mode == "Indexed against 100":
            reference_compound = st.sidebar.selectbox("Select Reference Compound:", compound_names)

        st.sidebar.header("3. Chart Aesthetics")
        show_labels = st.sidebar.checkbox("Show Data Values on Chart", value=True)
        fill_area = st.sidebar.checkbox("Fill Radar Area", value=True)
        grid_shape = st.sidebar.radio("Grid Shape", ["Polygon", "Circular"])

        # Layout: Properties selection at the top of the main page for better UX
        st.subheader("Select Properties to Visualize")
        default_props = all_properties[:5] if len(all_properties) >= 5 else all_properties
        selected_properties = st.multiselect(
            "Add or remove properties to update the radar instantly:", 
            options=all_properties, 
            default=default_props
        )

        st.divider()

        # --- 3. DYNAMIC PLOTLY ENGINE ---
        if len(selected_properties) > 2:
            df_filtered = df_clean[df_clean['Property'].isin(selected_properties)]
            fig = go.Figure()
            
            for compound in compound_names:
                if mode == "Absolute Values":
                    r_values = df_filtered[compound].tolist()
                else:
                    ref_values = df_filtered[reference_compound].tolist()
                    raw_values = df_filtered[compound].tolist()
                    r_values = []
                    for prop, val, ref in zip(selected_properties, raw_values, ref_values):
                        if pd.isna(val) or pd.isna(ref) or ref == 0:
                            r_values.append(0)
                        elif prop in LOWER_IS_BETTER:
                            r_values.append((ref / val * 100) if val != 0 else 0)
                        else:
                            r_values.append((val / ref * 100))
                            
                # Close the shape loop
                r_values.append(r_values[0])
                theta_values = selected_properties + [selected_properties[0]]
                
                # Format text labels (e.g., 105.2)
                text_labels = [f"{val:.1f}" for val in r_values]
                
                # Draw the trace with advanced styling
                fig.add_trace(go.Scatterpolar(
                    r=r_values,
                    theta=theta_values,
                    fill='toself' if fill_area else 'none',
                    name=compound,
                    mode='lines+markers+text' if show_labels else 'lines+markers',
                    text=text_labels,
                    textposition="top center",
                    textfont=dict(size=12, color="black" if fill_area else None),
                    marker=dict(size=8, symbol='circle'),
                    hoverinfo="text",
                    hovertext=[f"<b>{prop}</b><br>{compound}: {val:.1f}" for prop, val in zip(theta_values, r_values)]
                ))
                
            # Update layout aesthetics
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        showline=True,
                        linewidth=1,
                        gridcolor="lightgrey"
                    ),
                    angularaxis=dict(
                        gridcolor="lightgrey",
                        linewidth=1
                    ),
                    gridshape='linear' if grid_shape == "Polygon" else 'circular',
                    bgcolor="rgba(245, 245, 245, 0.5)" # Subtle background color for contrast
                ),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
                height=700,
                margin=dict(t=80, b=40, l=40, r=40)
            )
            
            # Display chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Display Data Table beneath
            with st.expander("View Cleaned Raw Data Table"):
                st.dataframe(df_filtered, use_container_width=True)
                
        else:
            st.warning("⚠️ Radar charts require at least 3 properties to draw a shape. Please select more from the dropdown above.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload your Excel file on the left menu to generate the dashboard.")
