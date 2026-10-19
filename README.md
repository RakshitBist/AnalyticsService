# AnalyticsService

# Analytics Microservices Architecture (Event-Driven System)

This project is a complete event-driven analytics pipeline built using **Java Spring Boot**, **Kafka**, **JWT Authentication**, and **Microservices Architecture**.  
It includes authentication, data ingestion, stream processing, and reporting services.

---

## 🚀 Architecture Overview

The system consists of four independent microservices:

1. **Registration Service**
   - Generates JWT + Refresh Tokens with versioning
   - Allows token invalidation by bumping the version
   - Provides authentication & authorization layer

2. **Producer Service**
   - Receives analytics events from the app
   - Publishes events into **Kafka Topics**
   - Acts as the entry point for analytics data

3. **Consumer Service**
   - Listens to Kafka topics in real-time
   - Processes events and stores them in the database
   - Ensures reliable ingestion using distributed messaging

4. **Reporting Service**
   - Aggregates analytics data from the database
   - Provides API endpoints for dashboards/reports
   - Supports filters, date ranges, and summaries

---

## 🏗️ High-Level Flow


This architecture ensures **scalability, fault tolerance, and real-time analytics**.

---

## 📌 Microservice Repositories

| Service | Purpose | GitHub Link |
|--------|---------|-------------|
| **Registration Service** | JWT + Refresh Token with versioning | https://github.com/6gaurav13/AnalyticsRegistration |
| **Producer Service** | Sends analytics data to Kafka | https://github.com/RakshitBist/AnalyticsProducer |
| **Consumer Service** | Reads from Kafka and stores in DB | https://github.com/RakshitBist/AnalyticsConsumer |
| **Reporting Service** | Aggregates analytics and exposes APIs | https://github.com/RakshitBist/AnalyticsReporter |

---

## 🛠️ Tech Stack

### **Backend**
- Java 17+
- Spring Boot
- Spring Security (JWT)
- Spring Kafka
- Spring Data JPA
- Lombok
- MapStruct (optional)

### **Infrastructure**
- Kafka & Zookeeper
- PostgreSQL / MySQL
- Docker (optional)

---

## 📦 Running the System

### Prerequisites
- macOS with **Java 17+** and **Docker Desktop**
- Python 3 and Git (both come with the Xcode command line tools)

Maven, Kafka, PostgreSQL and Redis do not need installing: each service ships a Maven wrapper (`mvnw`) and the rest run in Docker.

### Start everything with one command
```bash
git clone https://github.com/RakshitBist/AnalyticsService
cd AnalyticsService
./start.sh
```

`start.sh` will:
1. open Docker Desktop if it isn't running
2. start Kafka (port **9094**), PostgreSQL (5432) and Redis (6379) from `docker-compose.yml`
3. register the demo app `app1` in Redis (the Registration service's job)
4. download or update the Producer, Consumer and Reporter into `services/` and start them (logs in `logs/`)
5. start the dashboard and open **http://localhost:8090**

The first run takes a few minutes while Maven downloads libraries. Later runs take about 30 seconds.

Stop everything with `./stop.sh`. Your data is kept for the next start.

### Dashboard
`dashboard.py` is a small web page, written using only the Python standard library, that:
- shows which of the six parts are running
- sends events through the Producer and animates them along the pipeline
- shows the Reporter's live counts (events by type and by device)
- can simulate traffic, and can test that one app can't read another app's report

It signs its own demo JWT for `app1`, so no token setup is needed.

### Ports
| Part | Port |
|---|---|
| Producer | 8082 |
| Consumer | 8083 |
| Reporter | 8084 |
| Dashboard | 8090 |
| Kafka | 9094 |
| PostgreSQL | 5432 |
| Redis | 6379 |

---

## 📊 Features

### ✔️ Authentication & Token Versioning  
- JWT access token  
- Refresh token  
- Versioning system to invalidate tokens easily  
- Secure role-based access  

### ✔️ Event-Driven Analytics  
- Kafka for asynchronous communication  
- High throughput ingestion  
- Scalable consumer processing  

### ✔️ Reporting & Aggregation  
- Query optimized analytics tables  
- Daily/weekly/monthly summaries  
- Real-time dashboard support  

---

## 📚 Future Improvements
- Add API Gateway
- Externalized configuration service
- Zipkin distributed tracing
- Circuit breaker (Resilience4J)
- Kubernetes deployment

---

## 👨‍💻 Developer

**Gaurav**  
Java Backend Developer  
Newgen Software  
