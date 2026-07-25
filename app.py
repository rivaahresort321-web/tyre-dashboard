import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# 1. PAGE SETUP
st.set_page_config(page_title="Tyre Dashboard", layout="wide", initial_sidebar_state="auto")
st.title("Rubber Compound Dashboard 3.0")

# 2. SESSION STATE MEMORY
if "df_clean" not in st.session_state:
    st.session_state.df_clean = None
    st.session_state.compound_names = []
    st.session_state.file_name = None
    st.session_state.file_details = {}

# 3. SIDEBAR: FILE MANAGEMENT
st.sidebar.header("📁 File Management")
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

# 4. DASHBOARD RENDER
if st.session_state.df_clean is not None:
    df_clean = st.session_state.df_clean
    compound_names = st.session_state.compound_names
    all_properties = df_clean['Property'].tolist()
    LOWER_IS_BETTER = ['MH - ML', 'tanD @70°C', 'Abrasion Loss', 'Heat Buildup'] 

    # --- FILE DETAILS PANEL ---
    with st.expander(f"📄 Active File: {st.session_state.file_name}", expanded=False):
        st.write(f"**Compounds:** {st.session_state.file_details['Compounds Detected']}")
        st.write(f"**Properties Mapped:** {st.session_state.file_details['Total Properties']}")
        st.info("Upload a new file in the sidebar to replace this data.")

    # --- UI CONTROLS ---
    st.sidebar.header("🎯 Review Baseline")
    reference_compound = st.sidebar.selectbox(
        "Select Reference (Baseline for Delta Heatmap):", 
        compound_names,
        help="This compound will act as the '100' baseline for color calculations."
    )

    st.sidebar.header("⚙️ View Mode")
    mode = st.sidebar.radio("Values to Display:", ["Absolute Values", "Indexed against 100"])

    st.sidebar.header("🎨 Customize Colors")
    with st.sidebar.expander("Pick Compound Colors"):
        compound_colors = {}
        # Default professional hex colors
        default_colors = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b']
        for i, comp in enumerate(compound_names):
            compound_colors[comp] = st.color_picker(f"{comp}", default_colors[i % len(default_colors)])

    st.sidebar.header("📈 Chart Aesthetics")
    show_labels = st.sidebar.checkbox("Show Data Values", value=True)
    fill_area = st.sidebar.checkbox("Fill Radar Area", value=True)
    
    show_target = False
    if mode == "Indexed against 100":
        show_target = st.sidebar.checkbox("Show Target Envelope (±5%)", value=True)

    # Main Area Selector
    st.subheader("Select Properties to Visualize")
    default_props = all_properties[:6] if len(all_properties) >= 6 else all_properties
    selected_properties = st.multiselect(
        "Tap to add/remove properties:", 
        options=all_properties, 
        default=default_props
    )
    st.divider()

    if len(selected_properties) > 2:
        tab1, tab2, tab3 = st.tabs(["📊 Interactive Radar", "🚦 Delta Heatmap", "📋 Raw Data"])
        df_filtered = df_clean[df_clean['Property'].isin(selected_properties)]
        
        # --- CALCULATE BOTH ABSOLUTE AND INDEXED VALUES ---
        display_data = {} # What the user sees
        index_data = {}   # What drives the background logic & colors
        
        for compound in compound_names:
            ref_values = df_filtered[reference_compound].tolist()
            raw_values = df_filtered[compound].tolist()
            
            d_vals = []
            i_vals = []
            
            for i, prop in enumerate(selected_properties):
                val = raw_values[i]
                ref = ref_values[i]
                
                # Calculate index strictly for coloring & radar logic
                if pd.isna(val) or pd.isna(ref) or ref == 0:
                    idx = 0
                elif prop in LOWER_IS_BETTER:
                    idx = (ref / val * 100) if val != 0 else 0
                else:
                    idx = (val / ref * 100)
                
                i_vals.append(idx)
                d_vals.append(val if mode == "Absolute Values" else idx)
                
            display_data[compound] = d_vals
            index_data[compound] = i_vals
        
        # --- TAB 1: RADAR CHART ---
        with tab1:
            st.info("🖱️ **Tip:** You can now **scroll your mouse wheel** to zoom in/out, and click & drag to move the radar.")
            fig = go.Figure()
            
            # Target Envelope (Only when viewing Index mode)
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
                r_plot = display_data[compound] + [display_data[compound][0]] 
                theta_plot = selected_properties + [selected_properties[0]]
                text_labels = [f"{val:.1f}" for val in r_plot]
                
                fig.add_trace(go.Scatterpolar(
                    r=r_plot, theta=theta_plot,
                    fill='toself' if fill_area else 'none',
                    name=compound,
                    mode='lines+markers+text' if show_labels else 'lines+markers',
                    line=dict(color=compound_colors[compound]),
                    marker=dict(size=8, color=compound_colors[compound]),
                    text=text_labels, textposition="top center",
                    textfont=dict(size=11, color="black"),
                    hoverinfo="text",
                    hovertext=[f"<b>{prop}</b><br>{compound}: {val:.1f}" for prop, val in zip(theta_plot, r_plot)]
                ))
                
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, showline=True, gridcolor="lightgrey"),
                    angularaxis=dict(gridcolor="lightgrey"),
                    bgcolor="rgba(245, 245, 245, 0.3)"
                ),
                showlegend=True,
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                height=650, margin=dict(t=50, b=100, l=30, r=30)
            )
            
            # The 'config' line enables the zoom on hover
            st.plotly_chart(fig, use_container_width=True, config={
                'scrollZoom': True, 
                'displayModeBar': True,
                'displaylogo': False
            })

        # --- TAB 2: DELTA HEATMAP ---
        with tab2:
            st.markdown(f"### Performance Matrix vs {reference_compound}")
            st.info("🟩 Improved (>5%) | 🟨 Specs (±5%) | 🟥 Degraded (>5%) — *Colors apply even in Absolute view!*")
            
            df_display = pd.DataFrame(display_data, index=selected_properties)
            df_index = pd.DataFrame(index_data, index=selected_properties)
            
            # Function to color cells based on the hidden Index DataFrame
            def highlight_matrix(display_df, index_df):
                styles = pd.DataFrame('', index=display_df.index, columns=display_df.columns)
                for row in display_df.index:
                    for col in display_df.columns:
                        idx_val = index_df.loc[row, col]
                        if pd.isna(idx_val) or idx_val == 0:
                            styles.loc[row, col] = ''
                        elif idx_val >= 105:
                            styles.loc[row, col] = 'background-color: #d4edda; color: #155724; font-weight: bold;'
                        elif idx_val <= 95:
                            styles.loc[row, col] = 'background-color: #f8d7da; color: #721c24; font-weight: bold;'
                        else:
                            styles.loc[row, col] = 'background-color: #fff3cd; color: #856404;'
                return styles
            
            # Apply styles
            styled_df = df_display.style.format("{:.2f}").apply(lambda x: highlight_matrix(df_display, df_index), axis=None)
            st.dataframe(styled_df, use_container_width=True)

        # --- TAB 3: RAW DATA ---
        with tab3:
            st.markdown("### Absolute Values (Unformatted)")
            st.dataframe(df_filtered.set_index('Property'), use_container_width=True)
            
    else:
        st.warning("⚠️ Radar charts require at least 3 properties to draw a shape. Please select more.")
else:
    st.info("Welcome! Please upload your Excel file on the left menu to generate the dashboard.")
