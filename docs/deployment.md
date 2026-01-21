# Deployment Guide

## 1. Prerequisites
* **Python:** 3.10 or higher.
* **Neo4j Aura:** A running Cloud Instance (Free tier works).
* **Groq API Key:** For the LLM inference.

## 2. Environment Variables
Create a `.env` file (locally) or add these to your Cloud Dashboard (Railway/Render):

```bash
NEO4J_URI=neo4j+s://<your-instance-id>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-password>
GROQ_API_KEY=<your-groq-key>