# How to build standalone Docker image for Pole

To build a standalone Docker image for [Pole](https://github.com/biocypher/pole), please follow these steps:
1. Clone the Pole repository
```
git clone https://github.com/biocypher/pole.git
cd pole
```
2. Attach volumes to container by modifying docker-compose.yml
![Changes in docker-compose.yml](pole-docker-compose-changes.png)
3. Run the deploy stage of docker-compose.yml
```
docker compose up deploy
```
4. Create pole standalone Docker file `pole-standalone.Dockerfile`:
```
# pole-standalone.Dockerfile

FROM neo4j:4.4-enterprise

COPY ./biocypher_neo4j_volume /data

RUN chown -R 7474:7474 /data

EXPOSE 7474
EXPOSE 7687
```
5. Build the Pole standalone image
```
docker build -t pole-standalone:latest -f pole-standalone.Dockerfile .
```

