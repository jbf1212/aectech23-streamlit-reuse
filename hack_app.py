import streamlit as st
import json
import pandas as pd
from PIL import Image
import plotly.graph_objects as go
import plotly.express as px

import cost_parsing as cp
import utils as ut


DEFAULT_COLOR_SEQ = px.colors.sequential.Viridis

######################################
# Set session states
######################################
if 'data_uploaded' not in st.session_state:
    st.session_state.data_uploaded = False
    st.session_state.costdata = None
    st.session_state.dummy_data = None
    st.session_state.dummy_bool = True

######################################
# App title and description
######################################
col1, col2, col3, col4, col5 = st.columns(5)
image2 = Image.open("./images/wasted_logo.png")
col3.image(image2, width=250)

######################################
# Have user enter data
######################################
with st.sidebar:
    image1 = Image.open("./images/AECtech-Logo-Raised.png")
    st.image(image1, width=150)
    st.markdown(
    "**A tool for finding new use for end of service buildings**"
    )

with st.sidebar.form(key="Form1"):
    postal_code = st.text_input("Enter a 5-digit postal code")
    uploaded_file = st.file_uploader("Upload JSON", type="json", key="uploaded_file")

    if st.session_state.uploaded_file is not None:
        file_bytes = st.session_state.uploaded_file.getvalue()
        uploaded_data = json.loads(file_bytes)

        if uploaded_data is not None:
            st.session_state.data_uploaded = True
            st.session_state.dummy_bool = False

    use_dummy = st.checkbox("Use Dummy Data", value=st.session_state.dummy_bool , key="use_dummy")

    submitted = st.form_submit_button(label="Apply Region")


######################################
# Load JSON data
######################################

if submitted and st.session_state.dummy_data is None:
    if st.session_state.data_uploaded == False:
        st.session_state.data_uploaded = True

    if st.session_state.use_dummy:
        # Load JSON file
        with open('dummy_data_incoming.json') as f:
            matdata = json.load(f)
    else:
        matdata = uploaded_data

    # Convert to DataFrame
    st.session_state.dummy_data = pd.DataFrame(matdata)

    # Check if postal code is valid
    if not ut.is_valid_postal_code(postal_code):
        st.warning(
            "Invalid postal code. Please enter a 5-digit postal code."
        )
        st.stop()

######################################
# Make request for cost data
######################################
if submitted and st.session_state.dummy_data is not None:
    with st.spinner("Looking up pricing data..."):
        st.session_state.costdata = cp.add_cost_data(st.session_state.dummy_data, postal_code)

    with st.container():
        st.session_state.costdata['cost'] = st.session_state.costdata['cost'] / 100 #convert cents to dollars
        st.session_state.costdata = cp.map_cost_units(st.session_state.costdata)
        st.session_state.costdata['total_cost'] = st.session_state.costdata['cost'] * st.session_state.costdata['quant_in_unit']

        #Set configs for columns
        col_configs = {
                        "image_url": st.column_config.ImageColumn("Image", width="medium"),
                        "name": st.column_config.TextColumn("Material Name", disabled=True),
                        "area": st.column_config.NumberColumn("Measured Area", help="Total area of material", format="%d ft²"),
                        "uom": st.column_config.TextColumn("Unit of Measure", help="Unit of Measure for cost", disabled=True),
                        "cost": st.column_config.NumberColumn("Material Cost per Unit", help="Cost in USD", format="%.2f"),
                        "quant_in_unit": st.column_config.NumberColumn("Quantity per Unit", help="Quantity of material per unit", format="%.2f"),
                        "total_cost": st.column_config.NumberColumn("Total Cost", help="Total cost of material", format="%.2f"),
                        }

        col_order=["image_url", "name", "area", "cost", "uom", "quant_in_unit", "total_cost"]

        #Data viewer
        st.session_state.costdata = st.data_editor(data=st.session_state.costdata, key="ecom_data_editor", hide_index=True, column_order=col_order, column_config=col_configs)
        edited_mat_df = st.session_state.costdata #shorthand

        st.divider()

        #Bar Charts
        bc_labels = edited_mat_df['name'].tolist()
        bc_values = edited_mat_df['total_cost'].tolist()

        bar_fig1 = go.Figure()
        bar_fig1.add_trace(go.Bar(name="Material Values", x=bc_labels, y=bc_values, marker_color='#B4E2BA'))
        bar_fig1.update_layout(title_text="Material Values", yaxis_title="Material Value")

        st.plotly_chart(bar_fig1, use_container_width=True, theme="streamlit")

######################################
# Create and Display Sankeys
######################################
if st.session_state.costdata is not None:
    st.session_state.costdata['structural_type'] = st.session_state.costdata['structural'].apply(lambda x: 'Structural' if x else 'Non-Structural')
    quant_sankey_data, label_list, color_list = ut.gen_sankey(st.session_state.costdata,
                                 ['name', 'structural_type', 'primary_reuse', 'deconstruction_feasibility'],
                                 'total_cost')

    #n_colors=len(label_list)
    #color_list = px.colors.sample_colorscale(DEFAULT_COLOR_SEQ, [n/(n_colors -1) for n in range(n_colors1)])

    with st.container():
        fig1 = go.Figure(data=[go.Sankey(
                            node = dict(
                            pad = 15,
                            thickness = 20,
                            line = dict(color = "black", width = 0.5),
                            # label = quant_sankey_data['label'],
                            label = label_list,
                            color = color_list
                            ),
                            link = dict(
                            source = quant_sankey_data['sourceID'],
                            target = quant_sankey_data['targetID'],
                            value = quant_sankey_data['value']
                            ))])

        fig1.update_layout(title_text="Value Sankey Diagram",
                            font_size=14,
                            margin=dict(l=30, r=30, t=40, b=40)
                            )

        st.plotly_chart(fig1, use_container_width=True, theme="streamlit")
