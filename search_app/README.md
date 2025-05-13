# Elasticsearch Search Application

A dockerized application that provides a web interface for searching Elasticsearch data with filtering capabilities.

## Overview

This project consists of:
- An Elasticsearch server
- A search web application is accessible at http://127.0.0.1:5000/

The search application provides an interface to search and filter data from Elasticsearch.

## Prerequisites

- Docker and Docker Compose

## Setup Instructions

### 1. Configure Environment Variables

Create a `.env` file in the project directory with the following content:

```
ELASTIC_URL="http://elasticsearch:9200"
ELASTIC_USER="YOURUSERNAME"
ELASTIC_PASSWORD="YOURPASSWORD"
```

Replace `YOURUSERNAME` and `YOURPASSWORD` with credentials of your choice.

### 2. Build and Start the Application

Build the Docker containers:
```bash
docker compose build
```

Start the application:
```bash
docker compose up
```

To run in detached mode (background):
```bash
docker compose up -d
```

## Accessing the Application

Once the containers are running, access the search web interface at:

```
http://127.0.0.1:5000/
```

## Search Features

The search application provides the following capabilities:

### Search Categories
- **Description**: Search within description fields
- **SemanticID**: Search for specific semantic identifiers
- **idShort**: Search by short identifiers
- **Identifier**: Search by full identifiers
- **Specific Values of SubmodelElements**: Search for values within submodel elements and returns the referable object
- **Search for specific Values**: Enables free search where you can specify both the field and value

### Additional Options
- **Result Size**: Configure how many results should be returned (may return fewer if limited matches are found)
- **Filtering**: Optional filtering by specifying a field (category) and value

## Important Notes

- **The Elasticsearch server is initially empty and must be manually populated with data.**
- Both services (Elasticsearch and the search app) must be running for the application to work properly.
- Elasticsearch does not use ssl by default to make syncing with neo4j possible.
- 

## Stopping the Application

To stop the application:

```bash
docker compose down
```

## Troubleshooting

- If you encounter connection issues, ensure both services are running and the Elasticsearch service has fully started before attempting to use the search app.

    Start first Elasticsearch and wait for it to be fully up before starting the search app
    ```bash
  docker compose up elasticsearch
  ```
  ```bash
  docker compose up search-app
  ```
- Verify your `.env` file has the correct format with no spaces around the equal signs
- Check Docker logs for any error messages:
  ```bash
  docker compose logs
  ```