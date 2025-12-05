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
| **Producer Service** | Sends analytics data to Kafka | https://github.com/6gaurav13/AnalyticsProducer |
| **Consumer Service** | Reads from Kafka and stores in DB | https://github.com/6gaurav13/AnalyticsConsumer |
| **Reporting Service** | Aggregates analytics and exposes APIs | https://github.com/6gaurav13/AnalyticsReporter |

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
- Java 17+
- Maven
- Kafka & Zookeeper
- PostgreSQL / MySQL

### (Optional) Run with Docker Compose
*(Add this file later if you want to run all services together)*

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
