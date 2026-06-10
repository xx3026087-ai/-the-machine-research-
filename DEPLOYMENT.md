# The Machine (Research Edition) - Deployment Guide

## Prerequisites

- Docker and Docker Compose (version 20.10+)
- Python 3.10+
- At least 16GB RAM available
- GPU recommended (CUDA 11.8+ for LLM inference)

## Phase 1: Core Infrastructure

### 1.1 Initialize Environment

```bash
# Clone repository
git clone https://github.com/xx3026087-ai/-the-machine-research-.git
cd -the-machine-research-

# Create environment file
cp .env.example .env

# Set secure passwords
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "NEO4J_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "OPENSEARCH_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "GRAFANA_PASSWORD=$(openssl rand -base64 32)" >> .env
```

### 1.2 Start Core Services

```bash
# Start only Kafka, PostgreSQL, Neo4j
docker-compose up -d kafka postgres neo4j

# Wait for services to be healthy
docker-compose ps

# Verify connectivity
docker exec kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092
docker exec postgres psql -U machine -d machine_db -c "SELECT 1"
docker exec neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 1"
```

## Phase 2: Perception Layer

### 2.1 Start OpenSearch

```bash
docker-compose up -d opensearch

# Wait for health check
sleep 30

# Verify cluster health
curl -k -u admin:${OPENSEARCH_PASSWORD} https://localhost:9200/_cluster/health
```

### 2.2 Build Perception Module

```bash
# Build Whisper + spaCy container
docker-compose build perception

# Start perception service
docker-compose up -d perception

# Test perception endpoint
curl -X POST http://localhost:8001/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "John works at Apple in San Francisco"}'
```

## Phase 3: Vector Search

### 3.1 Start Ray Cluster

```bash
docker-compose up -d ray-head

# Wait for Ray to initialize
sleep 10

# Check Ray dashboard
open http://localhost:8265
```

## Phase 4: Language Models

### 4.1 Build LLM Server

```bash
# Download model weights (example: Mistral-7B)
python -c "from huggingface_hub import snapshot_download; snapshot_download('mistralai/Mistral-7B-v0.1', cache_dir='./models')"

# Build vLLM container
docker-compose build llm-server

# Start LLM service
docker-compose up -d llm-server

# Wait for model loading (2-5 minutes)
sleep 120

# Test LLM endpoint
curl -X POST http://localhost:8002/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral-7b", "prompt": "What is the capital of France?"}'
```

## Phase 5: Reflection Engine

### 5.1 Deploy Reflection Service

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start reflection engine
python -m loops.reflection_engine \
  --config config/thresholds.yaml \
  --log-level INFO
```

## Phase 6: Task Generator

### 6.1 Deploy Task Generation

```bash
# Start task generator
python -m loops.task_generator \
  --config config/thresholds.yaml \
  --log-level INFO
```

## Phase 7: Performance Evaluator

### 7.1 Deploy Metrics Collection

```bash
# Start performance evaluator
python -m loops.performance_evaluator \
  --config config/thresholds.yaml \
  --grafana-url http://localhost:3000 \
  --log-level INFO
```

## Phase 8: Dashboard

### 8.1 Start Grafana

```bash
docker-compose up -d grafana

# Access Grafana
open http://localhost:3000

# Add data sources:
# - PostgreSQL: postgres:5432
# - OpenSearch: http://opensearch:9200

# Import dashboards from config/grafana/dashboards/
```

## Phase 9: Human Oversight

### 9.1 Deploy Approval Interface

```bash
# Start approval gateway
python -m supervisor.approval_gate \
  --config config/thresholds.yaml \
  --port 8003

# Access approval interface
open http://localhost:8003/approve
```

## Full Stack Deployment

### Deploy Everything

```bash
# Start all services
docker-compose up -d

# Start Python services
docker-compose exec machine-core bash -c "
  python -m loops.self_prompting_loop &
  python -m loops.reflection_engine &
  python -m loops.task_generator &
  python -m loops.performance_evaluator &
  python -m supervisor.approval_gate
"
```

### Monitor System

```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs -f machine-core

# Health check
curl http://localhost:8000/health
```

## Testing

### Unit Tests

```bash
pytest tests/ -v --cov=core --cov=loops --cov=supervisor
```

### Integration Tests

```bash
python tests/integration/test_end_to_end.py
```

### Load Testing

```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Troubleshooting

### Service Health Issues

```bash
# Restart health monitoring
docker-compose restart machine-core

# View health monitor logs
docker logs machine-core | grep "health_monitor"
```

### Low Confidence Flags

```bash
# Query flagged items
python -c "from core.memory_store import MemoryStore; m = MemoryStore(); print(m.get_review_flags())"
```

### Approval Bottlenecks

```bash
# Check pending approvals
curl http://localhost:8003/approval/pending

# Get approval statistics
curl http://localhost:8003/approval/stats
```

## Production Hardening

1. **Enable authentication** across all services
2. **Set resource limits** in docker-compose
3. **Configure persistent volumes** with proper backups
4. **Enable TLS/SSL** for service communication
5. **Set up centralized logging** (ELK, Loki)
6. **Configure alerting** for threshold violations
7. **Implement rate limiting** on public endpoints
8. **Enable audit logging** for all changes
