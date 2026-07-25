import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# 1. PAGE SETUP (Mobile Optimized)
st.set_page_config(page_title="Tyre Dashboard", layout="wide", initial_sidebar_state="auto")
st.title("Rubber Compound Dashboard 2.0")

# 2. SESSION STATE MEMORY (Remembers the last file)
if "df_clean" not in st.session_state:
    st.session_state.df_clean = None
    st.session_state.compound_names = []
    st.session_state.file_name = None
    st.session_state.file_details = {}

# 3. SIDEBAR: FILE MANAGEMENT
st.sidebar.header("📁 File Management")

# Upload New File
uploaded_file = st.sidebar.file_uploader("Upload New Excel Template", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Read Data
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

        # Make duplicates unique
        s = df_clean['Property']
        df_clean['Property'] = s.where(~s.duplicated(), s + ' (' + s.groupby(s).cumcount().astype(str) + ')')
        
        # Save to Memory
        st.session_state.df_clean = df_clean
        st.session_state.compound_names = compound_names
        st.session_state.file_name = uploaded_file.name
        st.session_state.file_details = {
            "Total Properties": len(df_clean),
            "Compounds Detected": ", ".join(compound_names)
        }
        
    except Exception as e:
        st.sidebar.error(f"Error processing file: {e}")

# 4. DASHBOARD RENDER (Uses Memory)
if st.session_state.df_clean is not None:
    df_clean = st.session_state.df_clean
    compound_names = st.session_state.compound_names
    all_properties = df_clean['Property'].tolist()
    LOWER_IS_BETTER = ['MH - ML', 'tanD @70°C', 'Abrasion Loss', 'Heat Buildup'] 

    # --- FILE DETAILS PANEL ---
    with st.expander(f"📄 Active File: {st.session_state.file_name}", expanded=False):
        st.write(f"**Compounds Loaded:** {st.session_state.file_details['Compounds Detected']}")
        st.write(f"**Total Properties Mapped:** {st.session_state.file_details['Total Properties']}")
        st.info("To replace this data, upload a new file in the sidebar menu.")

    # --- UI CONTROLS ---
    st.sidebar.header("⚙️ Review Mode")
    mode = st.sidebar.radio("Values to Display:", ["Indexed against 100", "Absolute Values"])
    
    reference_compound = None
    if mode == "Indexed against 100":
        reference_compound = st.sidebar.selectbox("Select Reference Compound:", compound_names)

    st.sidebar.header("🎨 Chart Aesthetics")
    show_labels = st.sidebar.checkbox("Show Data Values", value=True)
    fill_area = st.sidebar.checkbox("Fill Radar Area", value=True)
    show_target = st.sidebar.checkbox("Show Target Envelope (±5%)", value=True)

    # Mobile-friendly multi-select
    st.subheader("Select Properties to Visualize")
    default_props = all_properties[:6] if len(all_properties) >= 6 else all_properties
    selected_properties = st.multiselect(
        "Tap to add/remove properties:", 
        options=all_properties, 
        default=default_props
    )

    st.divider()

    if len(selected_properties) > 2:
        tab1, tab2, tab3 = st.tabs(["📊 Radar Analysis", "🚦 Delta Heatmap", "📋 Raw Data"])
        df_filtered = df_clean[df_clean['Property'].isin(selected_properties)]
        
        # --- CALCULATE VALUES ---
        index_data = {}
        for compound in compound_names:
            ref_values = df_filtered[reference_compound].tolist() if mode == "Indexed against 100" else None
            raw_values = df_filtered[compound].tolist()
            r_values = []
            
            for i, prop in enumerate(selected_properties):
                val = raw_values[i]
                if mode == "Absolute Values":
                    r_values.append(val)
                else:
                    ref = ref_values[i]
                    if pd.isna(val) or pd.isna(ref) or ref == 0:
                        r_values.append(0)
                    elif prop in LOWER_IS_BETTER:
                        r_values.append((ref / val * 100) if val != 0 else 0)
                    else:
                        r_values.append((val / ref * 100))
            index_data[compound] = r_values
        
        # --- TAB 1: RADAR CHART ---
        with tab1:
            fig = go.Figure()
            
            if mode == "Indexed against 100" and show_target:
                theta_closed = selected_properties + [selected_properties[0]]
                fig.add_trace(go.Scatterpolar(
                    r=[105]*len(theta_closed), theta=theta_closed,
                    mode='lines', line_color='rgba(0,0,0,0)', showlegend=False, hoverinfo='skip'
                ))
                fig.add_trace(go.Scatterpolar(
                    r=[95]*len(theta_closed), theta=theta_closed,
                    mode='lines', fill='tonext', fillcolor='rgba(46, 204, 113, 0.2)', 
                    line_color='rgba(46, 204, 113, 0.5)', line_width=1,
                    name='Target (±5%)', hoverinfo='skip'
                ))

            for compound in compound_names:
                r_plot = index_data[compound] + [index_data[compound][0]] 
                theta_plot = selected_properties + [selected_properties[0]]
                text_labels = [f"{val:.1f}" for val in r_plot]
                
                fig.add_trace(go.Scatterpolar(
                    r=r_plot, theta=theta_plot,
                    fill='toself' if fill_area else 'none',
                    name=compound,
                    mode='lines+markers+text' if show_labels else 'lines+markers',
                    text=text_labels, textposition="top center",
                    textfont=dict(size=11, color="black"),
                    marker=dict(size=8), hoverinfo="text",
                    hovertext=[f"<b>{prop}</b><br>{compound}: {val:.1f}" for prop, val in zip(theta_plot, r_plot)]
                ))
                
            # MOBILE OPTIMIZED LAYOUT: Legend moved to the bottom, margins reduced
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, showline=True, gridcolor="lightgrey"),
                    angularaxis=dict(gridcolor="lightgrey"),
                    bgcolor="rgba(245, 245, 245, 0.3)"
                ),
                showlegend=True,
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                height=650, 
                margin=dict(t=50, b=100, l=30, r=30)
            )
            st.plotly_chart(fig, use_container_width=True)

        # --- TAB 2: DELTA HEATMAP ---
        with tab2:
            st.markdown("### Performance Index Matrix")
            if mode == "Indexed against 100":
                st.info("🟩 Improved (>105) | 🟨 Specs (95-105) | 🟥 Degraded (<95)")
                df_heatmap = pd.DataFrame(index_data, index=selected_properties)
                
                def highlight_performance(val):
                    if pd.isna(val) or val == 0: return ''
                    if val >= 105: return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                    elif val <= 95: return 'background-color: #f8d7da; color: #721c24; font-weight: bold;'
                    return 'background-color: #fff3cd; color: #856404;'
                
                styled_df = df_heatmap.style.format("{:.1f}").applymap(highlight_performance)
                st.dataframe(styled_df, use_container_width=True)
            else:
                st.warning("Switch to 'Indexed against 100' mode in the sidebar to view the color-coded delta heatmap.")

        # --- TAB 3: RAW DATA ---
        with tab3:
            st.markdown("### Absolute Values (Cleaned)")
            st.dataframe(df_filtered.set_index('Property'), use_container_width=True)
            
    else:
        st.warning("⚠️ Radar charts require at least 3 properties to draw a shape. Please select more.")
else:
    st.info("Welcome! Please upload your Excel file on the left menu (or tap the '>' icon on mobile) to generate the dashboard.")
