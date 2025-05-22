import requests
import json

START_YEAR = 2015
END_YEAR = 2025
BLS_API_URL = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'

headers = {"Content-type": "application/json"}

def get_bls_data(seriesid):
    """ Fetches average pricing data from the BLS API for the given series IDs. """
    prices = []

    data = json.dumps({
        "seriesid": seriesid,
        "startyear": str(START_YEAR),
        "endyear": str(END_YEAR)
    })

    p = requests.post(BLS_API_URL, data = data, headers = headers)
    json_data = json.loads(p.text)
    for series in json_data['Results']['series']:
        value = None
        for item in series['data']:
            value = item['value']
            break

        if value is not None:
            prices.append(float(value))

    return prices