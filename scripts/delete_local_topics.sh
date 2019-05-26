#!/usr/bin/env bash

kafka-topics --bootstrap-server localhost:9092 --delete --topic raw_logs
kafka-topics --bootstrap-server localhost:9092 --delete --topic parsed_logs
kafka-topics --bootstrap-server localhost:9092 --delete --topic log_keys
