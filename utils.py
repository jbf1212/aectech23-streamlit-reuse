import pandas as pd
import plotly.express as px

DEFAULT_COLOR_SEQ = px.colors.sequential.Viridis


def is_valid_postal_code(postal_code):
    if len(postal_code) != 5:
        return False
    try:
        int(postal_code)
        return True
    except ValueError:
        return False

# Converting links to html tags
def path_to_image_html(path):
    return '<img src="' + path + '" width="100" >'

def gen_sankey(df,cat_cols=[],primary_field=''):

    n_colors = len(cat_cols)
    color_palette= px.colors.sample_colorscale(DEFAULT_COLOR_SEQ, [n/(n_colors -1) for n in range(n_colors)])

    label_list = []
    color_num_list = []

    for cc in cat_cols:
        label_listTemp =  list(set(df[cc].values))
        color_num_list.append(len(label_listTemp))
        label_list = label_list + label_listTemp

    # remove duplicates from label_list
    label_list = list(dict.fromkeys(label_list))

    # define colors based on number of levels
    color_list = []
    for idx, colornum in enumerate(color_num_list):
        color_list = color_list + [color_palette[idx]]*colornum

    # transform df into a source-target pair
    for i in range(len(cat_cols)-1):
        if i==0:
            sankey_df = df[[cat_cols[i],cat_cols[i+1],primary_field]]
            sankey_df.columns = ['source','target','value']
        else:
            tempDf = df[[cat_cols[i],cat_cols[i+1],primary_field]]
            tempDf.columns = ['source','target','value']
            sankey_df = pd.concat([sankey_df,tempDf])
        sankey_df = sankey_df.groupby(['source','target']).agg({'value':'sum'}).reset_index()

    # add index for source-target pair
    sankey_df['sourceID'] = sankey_df['source'].apply(lambda x: label_list.index(x))
    sankey_df['targetID'] = sankey_df['target'].apply(lambda x: label_list.index(x))

    return sankey_df, label_list, color_list