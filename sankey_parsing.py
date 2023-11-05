from collections import defaultdict
import ast

# (0.5%)if percentage of material is less than this, group it as 'other
PERCENT_THRESHOLD = 0.005

#COLORS
STEEL_COLOR_N = "rgba(0,113,139,0.9)"
CONCRETE_COLOR_N = "rgba(70,174,160, 0.9)"
OTHER_COLOR_N = "rgba(183,230,165,0.9)"
STEEL_COLOR_L = "rgba(40,139,161,0.5)"
CONCRETE_COLOR_L = "rgba(106,189,178, 0.5)"
OTHER_COLOR_L = "rgba(207,240,194,0.5)"

#COLOR DICTIONARIES
COLOR_DICT_N = {"Concrete": CONCRETE_COLOR_N, "Steel": STEEL_COLOR_N, "Other": OTHER_COLOR_N} #NODES
COLOR_DICT_L = {"Concrete": CONCRETE_COLOR_L, "Steel": STEEL_COLOR_L, "Other": OTHER_COLOR_L} #LINKS

def generate_master_elem_list(mq_dataframe):
    master_elem_list = []

    for index, row in mq_dataframe.iterrows():
        mat_dict = {}

        mat_dict["Volume"] = row["volume_val"]

        #vol_kgm3 = row["volume_val"] * 0.0283168  # converts cubic ft to cubic meters
        mat_mass = row["weight_val"] *  0.45359237  # converts lbs to kg
        mat_dict["Mass"] = mat_mass
        mat_dict["gwp"] = row['gwp_val']

        mat_name = row["MaterialFormName"]
        mat_dict["Material Name"] = mat_name

        mat_class = row["Product.Type"].split(".")[-1]
        mat_dict["Material Class"] = mat_class

        elem_class = row["ElementClass"]

        link_pairs = [(mat_class, elem_class), (elem_class, mat_name)]
        mat_dict["Links"] = link_pairs

        master_elem_list.append(mat_dict)

    return master_elem_list

def generate_unique_links(master_elem_list):
    all_links = []

    for el in master_elem_list:
        link_pairs = el['Links']

        if el['Material Class'] != "Concrete" and el['Material Class'] != "Steel":
            m_class = "Other"
        else:
            m_class = el['Material Class'] #will be used to hold colors

        for link in link_pairs:
            all_links.append((link, m_class)) #adds tuple of link and material class (for color

    unique_links = list(set(all_links))  # gets list of unique tuples of links

    return unique_links

def sort_by_prop(master_elem_list, prop_string, link_dict):
    project_total_quant = 0
    for elem in master_elem_list:
        quant = elem[prop_string]

        for l in elem["Links"]:
            mclass_str = elem['Material Class']
            if mclass_str != "Concrete" and mclass_str != "Steel":
                m_class = "Other"
            else:
                m_class = mclass_str

            link_str = str(l) + "|" + m_class
            link_dict[link_str] += quant

        project_total_quant += quant


    return link_dict, project_total_quant


def remove_insignif(link_dict, project_total_quant, threshold=PERCENT_THRESHOLD):
    if project_total_quant == 0:
        return link_dict
    # remove insignificant links
    for key in list(link_dict):
        percent_val = link_dict[key] / project_total_quant
        if percent_val < PERCENT_THRESHOLD:
            del link_dict[key]

    return link_dict


def make_nodes(link_dict):
    all_used_nodes = []
    node_color_dict = {}

    for ld, v in link_dict.items():
        ld_list = ld.split("|")
        orig_tup = ast.literal_eval(ld_list[0])

        node_mat_class = ld_list[1]

        for nd in orig_tup:
            all_used_nodes.append(nd)
            node_color_dict[nd+'|'+node_mat_class] = v

    unique_nodes = list(set(all_used_nodes))

    node_dict = {}
    label_list = []
    color_list = []

    node_lookup = {}
    for i, node in enumerate(unique_nodes):
        label_list.append(node)

        #figure out dominant color based on attached links
        all_relevant_items = {k:v for k,v in node_color_dict.items() if node in k}
        keymax = max(zip(all_relevant_items.values(), all_relevant_items.keys()))[1]
        node_mat_class = keymax.split("|")[1]
        color_list.append(COLOR_DICT_N[node_mat_class])

        # dictionary to allow for more efficient lookup of node in following steps
        node_lookup[node] = i

    node_dict["label"] = label_list
    node_dict["color"] = color_list

    return node_dict, node_lookup


def make_links(link_dict, node_lookup):
    link_dict_out = {}
    source_list = []
    target_list = []
    value_list = []
    color_list=[]

    for ld, v in link_dict.items():
        ld_list = ld.split("|")
        orig_tup = ast.literal_eval(ld_list[0])
        source_str, target_str = orig_tup[0], orig_tup[1]
        source_node, target_node = node_lookup[source_str], node_lookup[target_str]

        color_list.append(COLOR_DICT_L[ld_list[1]])

        source_list.append(source_node)
        target_list.append(target_node)
        value_list.append(v)

    link_dict_out['source'] = source_list
    link_dict_out['target'] = target_list
    link_dict_out['value'] = value_list
    link_dict_out['color'] = color_list

    return link_dict_out

def calc_color_scale(nodes_dict):
    pass

def process_df_to_sankey(mq_dataframe, prop_string):
    master_elem_list = generate_master_elem_list(mq_dataframe)
    unique_links = generate_unique_links(master_elem_list)

    # link_dict = {str(k): 0 for k in unique_links}  # dictionary to store quantities
    link_dict = {str(k[0])+ "|" + k[1] : 0 for k in unique_links}  # dictionary to store quantities

    link_dict, project_total_quant = sort_by_prop(master_elem_list, prop_string, link_dict)
    link_dict = remove_insignif(link_dict, project_total_quant)
    # st.write(link_dict)
    # st.stop()

    nodes_dict_out, nodes_lookup = make_nodes(link_dict)
    links_dict_out = make_links(link_dict, nodes_lookup)
    # st.write(links_dict_out)
    # st.write(nodes_dict_out)
    # st.write(nodes_lookup)
    # st.stop()

    sankey_dict = {"nodes": nodes_dict_out, "links": links_dict_out}

    return sankey_dict

def process_sankey_dict(link_dict):
    nodes_dict_out, nodes_lookup = make_nodes(link_dict)
    links_dict_out = make_links(link_dict, nodes_lookup)

    sankey_dict = {"nodes": nodes_dict_out, "links": links_dict_out}

    return sankey_dict


def get_sankey(data,field_list,primary_val):
    sankey_data = {
    'label':[],
    'source': [],
    'target' : [],
    'value' : []
    }
    counter = 0
    while (counter < len(field_list) - 1):
        for parent in data[field_list[counter]].unique():
            sankey_data['label'].append(parent)
            for sub in data[data[field_list[counter]] == parent][field_list[counter+1]].unique():
                sankey_data['source'].append(sankey_data['label'].index(parent))
                sankey_data['label'].append(sub)
                sankey_data['target'].append(sankey_data['label'].index(sub))
                sankey_data['value'].append(data[data[field_list[counter+1]] == sub][primary_val].sum())

        counter +=1
    return sankey_data
