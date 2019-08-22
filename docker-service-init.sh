#!/bin/bash
docker swarm leave --force
docker swarm init
docker network create -d overlay api_uvarc_network
docker service create --name=postfix --env ALLOWED_SENDER_DOMAINS=virginia.edu --network=api_uvarc_network -p 25:25 --replicas 2 boky/postfix