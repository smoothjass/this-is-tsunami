import pandas as pd
import requests
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


# get all earthquakes for a year with a magnitude stronger than 4.0
def getEarthquakesForYear(year):
    URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    start = f'{year}-01-01'
    end = f'{year}-12-31'
    PARAMS = {
        "eventtype": "earthquake",
        "format":"geojson",
        'starttime': start,
        'endtime': end,
        'minmagnitude': 4.0,
    }

    response = requests.get(url=URL, params=PARAMS)
    data = response.json()


    # if the year had an earthquake (we went back until 1600, so there have been years without a documented earthquake)
    if data['metadata']['count'] > 0:

        # extract properties and data cleaning
        properties_list = [item['properties'] for item in data["features"]]
        coordinates_list = [item['geometry']['coordinates'] for item in data["features"]]

        properties_df = pd.DataFrame(properties_list)
        coordinates_df = pd.DataFrame(coordinates_list, columns=['longitude', 'latitude', 'altitude'])

        df = pd.concat([properties_df, coordinates_df], axis=1)

        df = df.drop(columns = ["place", "updated", "tz", "url", "sources", "types", "title", "net", "type"])
        df['status'] = df['status'].map({'automatic': 0, 'reviewed': 1})
        df = pd.get_dummies(df, dummy_na=True, columns=['alert'])
        df = pd.get_dummies(df, columns=['magType'])

        return df
    return 0





# connect to mongoDB instance and select correct collection
uri = "mongodb+srv://if21b152:2110257152@cluster-1.z3dutog.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

database = client['TsunamiDB']
collection = database['tsunamidata']


# we deleted all current data to replace them with a clean dataset
# result = collection.delete_many({})



years = set(range(1600, 2024))

# get requests for every year from 1600 to 2023
for year in years:
    df = getEarthquakesForYear(year)
    if df is not 0:

        # insert them into the database
        data_dict = df.to_dict(orient='records')
        result = collection.insert_many(data_dict)


        if result.acknowledged:
            print(f"{year}: Insertion successful. Inserted {len(result.inserted_ids)} documents.")
        else:
            print("Insertion failed.")








