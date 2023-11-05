import streamlit as st
import requests
import pandas as pd

API_KEY = st.secrets["1BUILD_API_KEY"]
BASE_URL = 'https://gateway-external.1build.com/'

def add_cost_data(df, zip_code):
    #val_cost, val_uom, val_image = lookup_cost(df['name'], zip_code, 'materialRateUsdCents')
    df[['cost', 'uom', 'image_url']] = df.apply(lambda row: pd.Series(lookup_cost(row['name'], zip_code, 'calculatedUnitRateUsdCents')), axis=1)

    #df['cost'] = df.apply(lambda row: lookup_cost(row['name'], zip_code, 'materialRateUsdCents'), axis=1)
    return df

def map_cost_units(df):
    #NOTE the following assumptions are VERY rough and may not always work!
    conversion_lookup = {
        'Concrete': 0.02469130864, # Assumes an 8" slab converting from ft^2 to yd^3
        'Steel': 1.0, # Assumes a 1 ft thick flange is what's being mapped
        'Glass': 0.004, #assumes units are in indivudal glass doors
        'Wood Flooring': 1.0, #Assumes SF is unit
        "Carpet": 1.0, #Assumes SF is unit
        "Acoustic Ceiling Tiles": 1.0, #Assumes SF is unit
        "Drywall": 1.0, #Assumes SF is unit
    }
    reuse_lookup = {
        'Concrete': 0.02469130864, # Assumes an 8" slab converting from ft^2 to yd^3
        'Steel': 1.0, # Assumes a 1 ft thick flange is what's being mapped
        'Glass': 0.004, #assumes units are in indivudal glass doors
        'Wood Flooring': 1.0, #Assumes SF is unit
        "Carpet": 1.0, #Assumes SF is unit
        "Acoustic Ceiling Tiles": 1.0, #Assumes SF is unit
        "Drywall": 1.0, #Assumes SF is unit
    }

    df['quant_in_unit'] = df['name'].map(conversion_lookup) * df['area']

    return df


def lookup_cost(name, postal_code, key_param):
    headers = {
        "1build-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    query = """
    query sources($input: SourceSearchInput!) {
        sources(input: $input) {
            nodes {
                id
                name
                uom
                calculatedUnitRateUsdCents
                imagesUrls
            }
        }
    }
    """

    variables = {
        "input": {
            #"sourceType": "MATERIAL",
            "zipcode": postal_code,
            "searchTerm": name,
            "page": {
                "limit": 1
            }
        }
    }

    data = {
        "query": query,
        "variables": variables
    }
    response = requests.post(BASE_URL, headers=headers, json=data)

    json_response = response.json()

    val_primary= json_response['data']['sources']['nodes'][0][key_param]
    val_uom = json_response['data']['sources']['nodes'][0]['uom']
    val_image = json_response['data']['sources']['nodes'][0]['imagesUrls'][0]

    return val_primary, val_uom, val_image