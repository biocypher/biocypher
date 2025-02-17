# Standalone Docker Image

In order to build a standalone Docker image for a BioCypher KG, you only need
small modifications to the Docker image of the template. We will render the data
that ususally is stored in the `biocypher_neo4j_volume` to our local disk by
exchanging `biocypher_neo4j_volume` with a local directory,
`./biocypher_neo4j_volume`. Then, we use a Dockerfile to build an image that
contains the final database. This image can be used to deploy the database
anywhere, without the need to run the BioCypher code. This process is
demonstrated in the
[drug-interactions](https://github.com/biocypher/drug-interactions) example
repository.

1. Clone the example repository

```
git clone https://github.com/biocypher/drug-interactions.git
cd drug-interactions
```

2. Attach volumes to disk by modifying the docker-compose.yml. In the example
repository, we have created a dedicated compose file for the standalone image.
You can see the differences between the standard and standalone compose files
[here](https://github.com/biocypher/drug-interactions/commit/f03360c526d2ef042d2a6a4a5e2beb27608d1d76).
IMPORTANT: only run the standalone compose file once, as the data in the
`./biocypher_neo4j_volume` directory is persistent and interferes with
subsequent runs. If you want to run it again, you need to delete the
`./biocypher_neo4j_volume` directory.

3. Run the standalone compose file. This will create the
`./biocypher_neo4j_volume` directory and store the data in it. You can stop
the container after the database has been created.

```
docker compose -f docker-compose-local-disk.yml up -d
docker compose -f docker-compose-local-disk.yml down
```

4. Create standalone `Dockerfile` (example
[here](https://github.com/biocypher/drug-interactions/blob/main/Dockerfile)):

```
# Dockerfile
FROM neo4j:4.4-enterprise
COPY ./biocypher_neo4j_volume /data
RUN chown -R 7474:7474 /data
EXPOSE 7474
EXPOSE 7687
```

5. Build the standalone image.

```
docker build -t drug-interactions:latest .
```

This image can be deployed anywhere, without the need to run the BioCypher code.
For example, you can add it to a Docker Compose file (example
[here](https://github.com/biocypher/biochatter-next/blob/main/biochatter-next/docker-compose.yml)):

```
# docker-compose.yml
version: '3.9'
services:
  [other services ...]

  biocypher:
    container_name: biocypher
    image: biocypher/drug-interactions:latest
    environment:
      NEO4J_dbms_security_auth__enabled: "false"
      NEO4J_dbms_databases_default__to__read__only: "false"
      NEO4J_ACCEPT_LICENSE_AGREEMENT: "yes"
    ports:
      - "0.0.0.0:7474:7474"
      - "0.0.0.0:7687:7687"
```
