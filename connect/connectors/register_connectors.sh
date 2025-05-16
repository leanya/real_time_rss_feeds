#!/bin/sh

# Start Kafka Connect in the background
/etc/confluent/docker/run &

# Wait until Kafka Connect REST API is ready
echo -e "Waiting for Kafka Connect to start listening on localhost"
while [ $(curl -s -o /dev/null -w %{http_code} http://localhost:8083/connectors) -ne 200 ] ; do 
 echo "$(date) Kafka Connect not ready yet..."
  sleep 10 
done

echo -e $(date) "Kafka Connect is ready! Listener HTTP state: " $(curl -s -o /dev/null -w %{http_code} http://localhost:8083/connectors)

# Register the connector for mongo_sink
curl -s -X "POST" "http://localhost:8083/connectors" -H "Content-Type: application/json" -d @mongo_sink.json

sleep infinity
