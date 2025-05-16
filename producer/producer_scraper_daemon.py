from confluent_kafka import Producer
import requests
import xmltodict

import datetime
import logging
import json
import os
import time

# Configure logging
log_file_path = './nytimes_scraper.log'
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(log_file_path)]
                    )


def delivery_callback(err, msg):
    if err:
        logging.error('Message delivery failed: {}'.format(err))
        # print('ERROR: Message failed delivery: {}'.format(err))
    else:
        logging.info("Produced event to topic {topic}: key = {key:12} value = {value:12}".format(
            topic=msg.topic(),
            key=(msg.key().decode('utf-8') if msg.key() else 'None'),
            value=msg.value().decode('utf-8', errors='replace')
        ))
        # print("Produced event to topic {topic}: key = {key:12} value = {value:12}".format(
        #     topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))

def fetch_data(news_type):
    """
    Fetch data from nytimes rss 
    """
    if news_type == "world_nyt":
        url = 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml'
    elif news_type == "biz_nyt":
        url = 'https://rss.nytimes.com/services/xml/rss/nyt/Business.xml'
    response = requests.get(url)
    if response.status_code == 200:
        return response
    else:
        print(f'Failed to fetch data. Status code: {response.status_code}')
        return None

def parse_data(response):
    """
    Parse the response and retain selected keys 
    """
    soup = xmltodict.parse(response.content)
    selected_keys = ['title', 'link', 'description', 'dc:creator','pubDate']
    data = [{key:item.get(key, '') for key in selected_keys} for item in soup['rss']['channel']['item']]

    return data 

def load_max_publish_time():

    try:
        with open('./global_publish_time.json', 'r') as f:
            max_publish_time_global = datetime.datetime.fromisoformat(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        # some default value set tot the start of the year
        max_publish_time_global = datetime.datetime.fromisoformat("2025-01-01T00:00:00")
    
    return max_publish_time_global

def main():
    # Kafka Configuration 
    # this config only work when running on the host 
    # bootstrap_servers = 'localhost:9091'
    # producer_conf = {
    #     'bootstrap.servers': bootstrap_servers
    #     }
    producer_conf = {'bootstrap.servers': 'kafka:19091'}

    producer = Producer(producer_conf)
    news_type = os.getenv('NEWS_TYPE')
    topic = news_type
    
    # Wait until Kafka is reachable
    MAX_RETRIES = 30
    retries = 0
    while retries < MAX_RETRIES:
        try:
            # Try fetching metadata from Kafka
            producer.list_topics(timeout=5)
            logging.info("Kafka is ready!")
            break
        except Exception as e:
            logging.info(f"Kafka not ready ({retries}/{MAX_RETRIES}): {e}. Retrying in 5 seconds...")
            time.sleep(5)
    else:
        logging.error("Kafka connection failed after max retries.")
        raise RuntimeError("Kafka unavailable.")

    # Load Producer
    while True:

        try: 
            # Request and parse dataset 
            data = fetch_data(news_type)
            if data is None:
                time.sleep(300)
                continue

            data = parse_data(data)

            # Load the max_publish_time
            max_publish_time_global = load_max_publish_time()
            max_publish_time_update = max_publish_time_global

            for msg in data:

                publish_time = msg['pubDate']
                publish_time = datetime.datetime.strptime(publish_time, "%a, %d %b %Y %H:%M:%S %z").replace(tzinfo=None)

                # only write to Kafka when the publish time is later than the global publish time 
                if publish_time > max_publish_time_global and len(msg['title']) > 2 :

                    logging.info(f"New article: {msg['title']} (Published at {publish_time})")

                    producer.produce(
                    topic=topic,
                    key=None,
                    value=json.dumps(msg).encode('utf-8'),
                    callback=delivery_callback)
                    # print(msg)

                    max_publish_time_update = max(publish_time, max_publish_time_update)
        
            # Update global publish time file only if updated
            if max_publish_time_update > max_publish_time_global:
                with open('./global_publish_time.json', 'w') as f:
                    json.dump(max_publish_time_update.isoformat(), f)
            
            producer.flush()

        except Exception as e:
            print(f"[ERROR] {e}")
        
        time.sleep(300)

if __name__ == '__main__':
    main()