from flask import Flask, render_template_string
from pymongo import MongoClient

def update_data_type(collection, collection_name):
  # Iterate and update
  try:
    result = collection.update_many(
       { "$expr": { "$eq": [ { "$type": "$pubDate" }, "string" ] } },
       [  # List = aggregation pipeline form
        {
           "$set": {"pubDate": { "$toDate": "$pubDate" }}
        }
      ])
    print(f"{collection_name}: Matched {result.matched_count}, Modified {result.modified_count}")
    
  except Exception as e:
     print(f"Error updating collection '{collection_name}': {e}")

def update_data_type_if_needed(collection, collection_name):
    # update the data type when there are new entries in the database 
    if collection.count_documents({ "$expr": { "$eq": [ { "$type": "$pubDate" }, "string" ] } }) > 0:
        update_data_type(collection, collection_name)

app = Flask(__name__)
# Connecting to the mongodb 
# When connecting from the host machine/laptop
# client = MongoClient('mongodb://user:pass@localhost:27017/default_db?authSource=admin')
# When connecting from inside another Docker container 
client = MongoClient('mongodb://user:pass@mongodb:27017/default_db?authSource=admin')
db = client['mongo']
world_collection = db['nyc_world']
biz_collection = db['nyc_biz']
update_data_type_if_needed(world_collection, 'nyc_world')
update_data_type_if_needed(biz_collection, 'nyc_biz')


@app.route('/')
def get_posts():
  
  recent_posts_world = world_collection.find().sort({"pubDate": -1 }).limit(5)
  recent_posts_world = list(recent_posts_world) 

  recent_posts_biz = biz_collection.find().sort({"pubDate": -1 }).limit(5)
  recent_posts_biz = list(recent_posts_biz) 

  INDEX_TEMPLATE = """
  {# This comment will not be rendered #}
  <h1>Latest World News</h1>
  {% for post in recent_posts_world %}
    <h2>{{ post['title'] }}</h2>
    <span>{{ post['description'] }}</span><br>
    <span>{{ post['pubDate'] }}</span><hr/>
  {% endfor %}

  <h1>Latest Business News</h1>
  {% for post in recent_posts_biz %}
    <h2>{{ post['title'] }}</h2>
    <span>{{ post['description'] }}</span><br>
    <span>{{ post['pubDate'] }}</span><hr/>
  {% endfor %}
  """
  return render_template_string(INDEX_TEMPLATE, 
                                recent_posts_world=recent_posts_world,
                                recent_posts_biz=recent_posts_biz)

if __name__ == '__main__':
    # By default, a Flask app will run on port 5000
    app.run(host = '0.0.0.0', port=5000)