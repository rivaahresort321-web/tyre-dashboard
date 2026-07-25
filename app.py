import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Tyre Compound Review", layout="wide")
st.title("Rubber Compound Property Review")

st.sidebar.header("1. Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload your Excel template", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # 1. Read the specific SUMMARY sheet
        df_raw = pd.read_excel(uploaded_file, sheet_name='SUMMARY')
        
        # 2. Clean the Data (Bypass blanks, subheaders, and find compound names)
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

        # FIX FOR STREAMLIT ERROR: Make duplicate properties unique
        s = df_clean['Property']
        df_clean['Property'] = s.where(~s.duplicated(), s + ' (' + s.groupby(s).cumcount().astype(str) + ')')
        
        # --- Dashboard UI Setup ---
        all_properties = df_clean['Property'].tolist()
        
        # Properties where lower is better
        LOWER_IS_BETTER = ['MH - ML', 'tanD @70°C'] 

        st.sidebar.header("2. Dashboard View")
        view = st.sidebar.radio("Select View:", ["Internal Dept Review", "Cross-Functional"])
        
        st.sidebar.header("3. Chart Settings")
        mode = st.sidebar.radio("Values to Display:", ["Absolute Values", "Indexed against 100"])
        
        reference_compound = None
        if mode == "Indexed against 100":
            reference_compound = st.sidebar.selectbox("Select Reference Compound:", compound_names)

        # Multiselect logic using the cleaned, unique properties
        default_props = all_properties[:5] if len(all_properties) >= 5 else all_properties
        selected_properties = st.multiselect(
            "Select Properties to Compare:", 
            options=all_properties, 
            default=default_props
        )

        # 4. Draw the Radar Chart
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
                            
                r_values.append(r_values[0])
                theta_values = selected_properties + [selected_properties[0]]
                
                fig.add_trace(go.Scatterpolar(
                    r=r_values,
                    theta=theta_values,
                    fill='toself' if compound == reference_compound else 'none',
                    name=compound
                ))
                
            fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True, height=600)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Cleaned Raw Data")
            st.dataframe(df_filtered)
        else:
            st.warning("Radar charts require at least 3 properties to draw a shape. Please select more from the dropdown.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload your Excel file on the left menu to generate the dashboard.")
