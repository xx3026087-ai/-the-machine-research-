# The Machine (Research Edition)

A stable, self-monitoring distributed system for entity extraction, graph reasoning, and continuous observation with bounded self-improvement.

## Architecture Overview

**7-Node Bootstrap**

```
Node 1: Kafka (Event Stream)
Node 2: PostgreSQL (Structured Storage)
Node 3: Neo4j (Relationship Graph)
Node 4: OpenSearch (Full-Text Memory)
Node 5: Whisper + spaCy (Perception)
Node 6: Ray + LLM (Reasoning)
Node 7: Grafana (Monitoring)
```

**Critical Design Principle**

- Self-modification limited to **prompts, configurations, model retraining only**
- All code changes require **human approval gate**
- Health monitoring prevents cascade failures
- Confidence system surfaces uncertain conclusions

## Phases

1. **Phase 1**: Core infrastructure (Kafka, PostgreSQL, Neo4j)
2. **Phase 2**: Perception layer (OpenSearch, spaCy, Whisper)
3. **Phase 3**: Vector search (Ray, Qdrant)
4. **Phase 4**: Language models (Llama 3, vLLM)
5. **Phase 5**: Reflection engine (self-analysis)
6. **Phase 6**: Task generator (autonomous tasking)
7. **Phase 7**: Performance evaluator (metrics tracking)
8. **Phase 8**: Dashboard (human visualization)
9. **Phase 9**: Human oversight (approval gates)

## Repository Structure

```
the-machine-research/
├── docker/
│   ├── docker-compose.yml
│   ├── nodes/
│   │   ├── kafka/
│   │   ├── postgres/
│   │   ├── neo4j/
│   │   ├── opensearch/
│   │   ├── ray/
│   │   └── grafana/
├── core/
│   ├── health_monitor.py
│   ├── entity_extractor.py
│   ├── graph_manager.py
│   ├── memory_store.py
│   └── event_handler.py
├── loops/
│   ├── main_loop.py
│   ├── self_prompting_loop.py
│   ├── reflection_engine.py
│   ├── task_generator.py
│   └── performance_evaluator.py
├── models/
│   ├── confidence_scorer.py
│   └── entity_classifier.py
├── supervisor/
│   ├── approval_gate.py
│   ├── upgrade_manager.py
│   └── human_interface.py
├── config/
│   ├── services.yaml
│   ├── thresholds.yaml
│   └── prompts.yaml
└── tests/
    ├── test_health_monitor.py
    ├── test_entity_extraction.py
    └── test_graph_integrity.py
```

## Getting Started

See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for phase-by-phase setup.

## Safety Constraints

- ✅ **Allowed**: Prompt tuning, configuration changes, model retraining
- ❌ **Blocked**: Automatic code generation, self-deployment without approval
- 🔍 **Monitored**: All confidence scores < 0.7 flagged for review
- 👤 **Required**: Human approval for any system upgrade
