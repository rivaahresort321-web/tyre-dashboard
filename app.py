import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Set up the web page layout
st.set_page_config(page_title="Tyre Compound Review", layout="wide")
st.title("Rubber Compound Property Review")

# 1. Sidebar for File Upload
st.sidebar.header("1. Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload your Excel template", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Read the Excel file automatically
    df = pd.read_excel(uploaded_file)
    
    # We assume the first column is the list of properties, and the rest are compounds
    property_col = df.columns[0]
    compounds = df.columns[1:].tolist()

    # 2. Two-Page Navigation (Using Sidebar)
    st.sidebar.header("2. Dashboard View")
    view = st.sidebar.radio("Select View:", [
        "Internal Dept Review (All Properties)", 
        "Cross-Functional (Selective)"
    ])
    
    # 3. Chart Settings (Absolute vs Indexed)
    st.sidebar.header("3. Chart Settings")
    mode = st.sidebar.radio("Values to Display:", ["Absolute Values", "Indexed against 100"])
    
    reference_compound = None
    if mode == "Indexed against 100":
        reference_compound = st.sidebar.selectbox("Select Reference Compound:", compounds)
        
    # Determine which properties to show based on the selected view
    if view == "Internal Dept Review (All Properties)":
        selected_properties = st.multiselect(
            "Select Properties to Compare:", 
            df[property_col].tolist(), 
            default=df[property_col].tolist()[:5] # Selects first 5 by default
        )
    else:
        st.info("Cross-Functional Mode: Focus on high-level KPIs.")
        selected_properties = st.multiselect(
            "Select Key KPIs:", 
            df[property_col].tolist(), 
            default=df[property_col].tolist()[:3]
        )

    # Filter the data based on user selection
    df_filtered = df[df[property_col].isin(selected_properties)]
    
    # 4. Draw the Radar Chart
    if len(selected_properties) > 2:
        fig = go.Figure()
        
        for compound in compounds:
            if mode == "Absolute Values":
                r_values = df_filtered[compound].tolist()
            else:
                # Calculate index against 100
                ref_values = df_filtered[reference_compound].tolist()
                raw_values = df_filtered[compound].tolist()
                
                # Formula: (Test / Reference) * 100
                r_values = [(val / ref * 100) if ref != 0 else 0 for val, ref in zip(raw_values, ref_values)]
            
            # Plotly requires the first value to be repeated at the end to close the circle
            r_values.append(r_values[0])
            theta_values = selected_properties + [selected_properties[0]]
            
            # Draw the lines
            fig.add_trace(go.Scatterpolar(
                r=r_values,
                theta=theta_values,
                fill='toself' if compound == reference_compound else 'none',
                name=compound
            ))
            
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)), 
            showlegend=True,
            height=600
        )
        
        # Display the chart and the raw data table
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Raw Data Table")
        st.dataframe(df_filtered)
        
    else:
        st.warning("Radar charts require at least 3 properties to draw a shape. Please select more.")
else:
    st.info("Please upload your Excel file on the left menu to generate the dashboard.")
