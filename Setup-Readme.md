# Paragraph Word Count Backend --- Django + Docker + Celery

This project is a Django REST based backend application that allows
users to register, login, submit paragraphs, and analyze word frequency
across stored paragraphs. Background processing is handled using Celery
with Redis as the message broker and PostgreSQL as the database.

------------------------------------------------------------------------

## Tech Stack

-   Django + Django REST Framework\
-   PostgreSQL (Relational Database)\
-   Redis (Message Broker)\
-   Celery (Task Queue)\
-   Celery Beat (Task Scheduler)\
-   Docker & Docker Compose

------------------------------------------------------------------------

## Prerequisites

Make sure the following are installed on your system.

### 1. Install Docker

Download and install Docker Desktop:

https://www.docker.com/products/docker-desktop/

After installation, verify:

docker --version

------------------------------------------------------------------------

### 2. Install Docker Compose

Docker Compose comes with Docker Desktop.

Verify:

docker compose version

------------------------------------------------------------------------

## Clone Repository

git clone `<your-repo-url>`{=html}\
cd para-word-count

------------------------------------------------------------------------

## Environment Setup

### Step 1 --- Create .env File

Copy example file:

cp .env.example .env

------------------------------------------------------------------------

### Step 2 --- Update .env Values

.env is already present with all the values.\
Give permissions:

chmod +x .env

------------------------------------------------------------------------

## Running The Project

### Step 1 --- Build and Start Containers

docker compose -f docker-compose.yaml up -d

This will start:

-   Django Backend\
-   PostgreSQL Database\
-   Redis Server\
-   Celery Worker\
-   Celery Beat Scheduler

------------------------------------------------------------------------

### Step 2 --- Check Running Containers

docker ps

You should see:

-   django_backend\
-   postgres_db\
-   redis_server\
-   celery_worker\
-   celery_beat

------------------------------------------------------------------------

## Access Application

Open browser:

http://localhost:8000

------------------------------------------------------------------------

## Testing APIs

You can test using:

-   Browser (for UI pages)\
-   Postman\
-   cURL

------------------------------------------------------------------------

## Background Task Processing

### Celery Worker

Handles background tasks like paragraph processing and word
tokenization.

### Celery Beat

Runs scheduled jobs like:

-   Cleaning old paragraphs\
-   Generating daily statistics

------------------------------------------------------------------------

## Database

PostgreSQL runs inside Docker container.

Connection details (internal Docker network):

Host: postgres\
Port: 5432\
DB: app_db\
User: app_user\
Password: app_password

------------------------------------------------------------------------

## Redis

Redis is used for:

-   Celery Message Queue\
-   Task Result Backend

Internal connection:

redis://redis:6379/0

------------------------------------------------------------------------

## Stopping Containers

docker compose -f docker-compose.yaml down

------------------------------------------------------------------------

## Rebuild Containers

docker compose down\
docker compose up --build

------------------------------------------------------------------------

## Common Issues

### Cannot Connect To Redis

Make sure settings use:

redis://redis:6379

Not localhost.

------------------------------------------------------------------------

### Database Connection Error

Make sure .env contains:

DB_HOST=postgres

------------------------------------------------------------------------

### Port Already In Use

Stop existing containers:

docker compose down


