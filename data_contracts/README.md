# Data Contracts Specification

## Overview

This directory contains JSON Schema exports and documentation for all canonical data contracts used in TAKTKRONE-I. These schemas define the structure, validation rules, and documentation for all data flowing through the system.

## Core Principles

1. **Versioning**: All schemas are versioned using semantic versioning
2. **Provenance**: Every record includes source and ingestion metadata
3. **Timestamps**: All temporal data uses ISO 8601 with timezone
4. **Operators**: Standardized operator codes (e.g., "mta_nyct", "mbta")
5. **Validation**: Pydantic models enforce constraints at runtime
6. **Documentation**: Every field has clear descriptions and examples

## Schema Categories

### 1. Network Topology Schemas
- `stop.schema.json` - Transit stop/station entity
- `route.schema.json` - Transit route/line entity
- `trip.schema.json` - Scheduled trip pattern
- `shape.schema.json` - Geographic route alignment
- `transfer.schema.json` - Transfer/connection between stops

### 2. Realtime Operational Schemas
- `realtime_event.schema.json` - Generic realtime event
- `trip_update.schema.json` - GTFS-RT trip update
- `vehicle_position.schema.json` - GTFS-RT vehicle location
- `service_alert.schema.json` - GTFS-RT service alert
- `network_snapshot.schema.json` - Point-in-time network state

### 3. Disruption & Incident Schemas
- `incident_record.schema.json` - Disruption event metadata
- `disruption_bulletin.schema.json` - Official service bulletin
- `planned_work.schema.json` - Scheduled maintenance event
- `station_closure.schema.json` - Station accessibility change

### 4. Synthetic Training Data Schemas
- `occ_dialogue_sample.schema.json` - Instruction tuning example
- `synthetic_scenario.schema.json` - Generated operational scenario
- `action_recommendation.schema.json` - Model output format
- `after_action_review.schema.json` - Post-incident analysis

### 5. Retrieval & Knowledge Schemas
- `retrieval_document.schema.json` - RAG document format
- `operational_procedure.schema.json` - Procedure/playbook
- `glossary_term.schema.json` - Domain terminology
- `constraint.schema.json` - Operational constraint definition

## Common Fields

All schemas include these base fields:

```json
{
  "id": "string (UUID or stable identifier)",
  "schema_version": "string (semver, e.g., '1.0.0')",
  "timestamp": "string (ISO 8601 with timezone)",
  "operator": "string (operator code)",
  "source": "string (data source identifier)",
  "provenance": {
    "ingestion_time": "string (ISO 8601)",
    "ingestion_method": "string (e.g., 'gtfs_rt_adapter')",
    "raw_source_url": "string (optional)",
    "version": "string (source data version)"
  }
}
```

## Usage

### Python (Pydantic)

```python
from occlm.schemas import RealtimeEvent, NetworkSnapshot

event = RealtimeEvent(
    id="evt_001",
    timestamp="2026-03-27T17:30:00Z",
    operator="mta_nyct",
    event_type="trip_update",
    data={...}
)

# Validation happens automatically
event.validate()  # Raises ValidationError if invalid

# Export to JSON
event.model_dump_json()
```

### Validation

```bash
# Validate data files against schemas
occlm validate \
    --schema data_contracts/realtime_event.schema.json \
    --data data/raw/mta/events.jsonl

# Batch validation
occlm validate \
    --schema-dir data_contracts/ \
    --data-dir data/normalized/ \
    --recursive
```

## Schema Versioning

Schemas follow semantic versioning:

- **MAJOR**: Breaking changes (field removal, type changes)
- **MINOR**: Backward-compatible additions (new optional fields)
- **PATCH**: Documentation updates, constraint clarifications

Example evolution:
```
realtime_event.v1.0.0.schema.json  (initial)
realtime_event.v1.1.0.schema.json  (added confidence field)
realtime_event.v2.0.0.schema.json  (changed timestamp format)
```

Current schemas default to latest stable version.

## Extending Schemas

To add new schemas:

1. Define Pydantic model in `occlm/schemas/`
2. Add validation rules and examples
3. Export to JSON Schema: `occlm export-schemas`
4. Document in this README
5. Update version in schema metadata

## Schema Files

| File | Description | Version | Status |
|------|-------------|---------|--------|
| `realtime_event.schema.json` | Generic realtime event | 1.0.0 | Stable |
| `network_snapshot.schema.json` | Point-in-time network state | 1.0.0 | Stable |
| `incident_record.schema.json` | Disruption event | 1.0.0 | Stable |
| `occ_dialogue_sample.schema.json` | Training example | 1.0.0 | Stable |
| `action_recommendation.schema.json` | Model output | 1.0.0 | Stable |
| `synthetic_scenario.schema.json` | Generated scenario | 1.0.0 | Stable |
| `retrieval_document.schema.json` | RAG document | 1.0.0 | Stable |

See individual `.schema.json` files for complete specifications.

---

**Last Updated**: 2026-03-27
**Schema Version**: 1.0.0
