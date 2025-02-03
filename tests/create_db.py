import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from tqdm import tqdm
import requests


workers = 5
db_name = "test"

def createDB(db_name):
    url = "http://0.0.0.0:6006/v1/memory/create"
    payload = {"db": db_name}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    print(response.text)


def addRecord(db_name, text, metadata):
    url = "http://0.0.0.0:6006/v1/vector/add"
    payload = {
        "db": db_name,
        "text": text,
        "metadata": metadata
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    

def backup(db_name):
    url = "http://0.0.0.0:6006/v1/memory/backup"
    payload = {"db": db_name}
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    print(response.text)


def run(df):
    data = df.to_dict('records')
    createDB(db_name)
    row_count = len(data)
    tbar = tqdm(total=row_count, desc='Adding', leave=True, unit='records')
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(addRecord, db_name, str(row["Prompt"]), row["Metadata"]): row for row in data}
        for future in as_completed(futures):
            tbar.update(n=1)
            tbar.refresh()
    tbar.refresh()
    tbar.close()


if __name__ == "__main__":
    df = pd.read_excel("./tests/input.xlsx", header=0)
    df = df.where(pd.notnull(df), None)
    run(df)
    sys.exit(0)