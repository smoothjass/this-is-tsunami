import pandas as pd
from multiprocessing import Pool
from multiprocessing import cpu_count
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import time
import math

def getDB():
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

    cursor = collection.find({},{'_id': False})
    df = pd.DataFrame(list(cursor))

    return df
def getClusters():
    clusters = []

    # define Clusters

    for x in range(0,19):
        for y in range(0,19):
            startX = -180 if x == 0 else -180 + x * 20
            startY = -90 if y == 0 else -90 + y * 10
            endX = -180 + (x+1) * 20
            endY = -90 + (y+1) * 10
            clusters.append({"startX":startX, "startY":startY, "endX":endX, "endY":endY})

    clusters = pd.DataFrame.from_records(clusters)
    return clusters

def convertToCorrectDataframe(results):
    correctDF = []
    for r in results:
        x = math.floor(r[0]/19)
        y = r[0] % 19
        quakes = r[1]
        tsunamis = r[2]
        correctDF.append({"x": x, "y": y, "quakes": quakes, "tsunamis": tsunamis})

    correctDF = pd.DataFrame.from_records(correctDF)
    return correctDF

def mapper(data, clusters):
    map = []
    for index, datarows in data.iterrows():
        for i, c in clusters.iterrows():
            if c["endX"] > datarows["longitude"] >= c["startX"] and c["endY"] > datarows["latitude"] >= c["startY"]:
                map.append((i, datarows["tsunami"]))
    return map

def reducer(key_values):
    key, values = key_values
    count_0 = values.count(0)
    count_1 = values.count(1)
    return key, count_0, count_1


def map_reduce(data, clusters, num_processes=4):
    # splitting
    chunk_size = len(data) // num_processes
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

    # Create a pool of worker processes
    with Pool(processes=num_processes) as pool:
        # Map phase: Apply the map function to each chunk in parallel
        mapped_results = pool.starmap(mapper, [(chunk, clusters) for chunk in chunks])

        # Flatten the list of mapped results
        flat_mapped_results = [item for sublist in mapped_results for item in sublist]

        # Group the mapped results by key for the reduce phase
        key_value_pairs = {}
        for key, value in flat_mapped_results:
            if key in key_value_pairs:
                key_value_pairs[key].append(value)
            else:
                key_value_pairs[key] = [value]

        # Reduce phase: Apply the reduce function to each group of key-value pairs in parallel
        reduced_results = pool.map(reducer, key_value_pairs.items())

    return reduced_results


if __name__ == '__main__':

    sTime = time.time()
    df = getDB()
    eTime = time.time()
    print(f"fetched DF in {eTime - sTime} seconds")

    clusters = getClusters()

    pr = cpu_count() - 1
    sTime = time.time()
    results = map_reduce(df, clusters, pr)
    eTime = time.time()
    print(f"map reduce in {eTime - sTime} seconds")

    mrDF = convertToCorrectDataframe(results)
    mrDF = mrDF.sort_values(by=['x', 'y'])
    print(mrDF)
    mrDF.to_csv("mapReduce.csv", index=False)

