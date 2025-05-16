FROM confluentinc/cp-kafka-connect:latest

#If you want to run a local build of the connector, uncomment the COPY command and make sure the JAR file is in the directory path
#COPY mongo-kafka-connect-<<INSERT BUILD HERE>>3-all.jar /usr/share/confluent-hub-components
RUN confluent-hub install --no-prompt --verbose mongodb/kafka-connect-mongodb:latest

ENV CONNECT_GROUP_ID="mongo-connect-group"
ENV CONNECT_CONFIG_STORAGE_TOPIC="mongo-connect-configs"
ENV CONNECT_OFFSET_STORAGE_TOPIC="mongo-connect-offsets"
ENV CONNECT_STATUS_STORAGE_TOPIC="mongo-connect-status"
ENV CONNECT_CONFIG_STORAGE_REPLICATION_FACTOR=1
ENV CONNECT_OFFSET_STORAGE_REPLICATION_FACTOR=1
ENV CONNECT_STATUS_STORAGE_REPLICATION_FACTOR=1
ENV CONNECT_KEY_CONVERTER="org.apache.kafka.connect.storage.StringConverter"
ENV CONNECT_VALUE_CONVERTER="org.apache.kafka.connect.json.JsonConverter"
ENV CONNECT_INTERNAL_KEY_CONVERTER="org.apache.kafka.connect.storage.StringConverter"
ENV CONNECT_INTERNAL_VALUE_CONVERTER="org.apache.kafka.connect.json.JsonConverter"
ENV CONNECT_PLUGIN_PATH="/usr/share/java,/usr/share/confluent-hub-components"

ADD connectors /etc/kafka-connect/connectors

WORKDIR /etc/kafka-connect/connectors

CMD ["./register_connectors.sh"]