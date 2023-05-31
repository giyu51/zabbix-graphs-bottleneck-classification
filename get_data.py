import requests
import json
from datetime import datetime
import time
import os
import csv

# Load data configuration from the JSON file
with open("./zabbix_conf.json", 'r') as conf_file:
    conf_file = json.load(conf_file)
    data_conf = conf_file['Data Collection']
COMPANY_DOMAIN_NAME = data_conf['COMPANY_DOMAIN_NAME']
USERNAME = data_conf['USERNAME']
PASSWORD = data_conf['PASSWORD']
IMAGE_DIRECTORY = data_conf['IMAGE_DIRECTORY']
REQUESTS_PER_HOUR = data_conf['REQUESTS_PER_HOUR']

# Check if the specified IMAGE_DIRECTORY exists, create it if not
current_folder_items = os.listdir(".")
if not current_folder_items.__contains__(IMAGE_DIRECTORY.replace("/", "").replace(".", "")):
    print(f'-----IMAGE_DIRECTORY {IMAGE_DIRECTORY} is created')
    os.mkdir(IMAGE_DIRECTORY)
print(f'-----IMAGE_DIRECTORY is set to {IMAGE_DIRECTORY}')

# Set request configurations
url = f'https://{COMPANY_DOMAIN_NAME}/api_jsonrpc.php'
headers = {'content-type': 'application/json-rpc'}

item_dict = {}

# Read item names and IDs from the CSV file and create a dictionary
with open('graphs.csv', 'r') as file:
    reader = csv.reader(file)
    for eachLine in reader:
        if len(eachLine) == 0:  # if the line is empty, ignore that line.
            continue
        if_name = eachLine[0]
        if_id = eachLine[1]
        item_dict.update({if_name: if_id})

# In this script item_dict has almost no use, but in the future if you want to modify the code,
# it could act as a link between interfaces' names and their items' IDs
item_ids = item_dict.values()


# Function to get the current time
def current_time():
    return str(datetime.now().strftime('%d.%m.%y'))


# Function to authenticate the user and get the session token
def authenticate_user():
    auth_payload = {
        'jsonrpc': '2.0',
        'method': 'user.login',
        'params': {
            'user': USERNAME,
            'password': PASSWORD
        },
        'id': 1
    }

    response = requests.post(url, data=json.dumps(auth_payload), headers=headers)
    result = json.loads(response.text)
    session_token = result['result']
    print("Successfully Logged In")
    return session_token


# Function to download images for the specified item IDs
def download_images(session_token, item_ids):
    file_counter = len(os.listdir(IMAGE_DIRECTORY)) + 1
    image_headers = {
        'Cookie': 'zbx_sessionid=' + session_token,
        'Referer': f'https://{COMPANY_DOMAIN_NAME}/charts.php?ddreset=1',
    }

    for item_id in item_ids:
        image_url = f"https://{COMPANY_DOMAIN_NAME}/chart.php?from=now-24h&to=now&itemids[0]={item_id}&type=0&profileIdx=web.item.graph.filter&profileIdx2=263949&legend=0&width=1334&widget_view=1"

        try:
            response = requests.get(image_url, headers=image_headers)
        except:
            # Retry request
            time.sleep(60)
            response = requests.get(image_url, headers=image_headers)
        else:
            with open('{0}/{1}_{2}.jpg'.format(IMAGE_DIRECTORY, current_time(), file_counter), 'wb') as f:
                f.write(response.content)
            print(f'Image #{file_counter} saved successfully')

        file_counter += 1


# Function to logout the user
def logout_user(session_token):
    logout_payload = {
        'jsonrpc': '2.0',
        'method': 'user.logout',
        'params': [],
        'id': 2,
        'auth': session_token
    }

    requests.post(url, data=json.dumps(logout_payload), headers=headers)
    print("Successfully Logged Out")


# Main function to execute the data collection process
def main():
    while True:
        print("__________________________")
        session_token = authenticate_user()
        download_images(session_token, item_ids)
        logout_user(session_token)

        time.sleep(3600 / REQUESTS_PER_HOUR)


if __name__ == "__main__":
    main()
