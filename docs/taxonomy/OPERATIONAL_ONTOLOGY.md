# TAKTKRONE-I Operational Ontology

**Version:** 1.0.0
**Last Updated:** 2026-03-27

---

## Overview

This document defines the formal operational ontology for TAKTKRONE-I. The ontology establishes a shared vocabulary and conceptual model for metro operations control center reasoning, ensuring consistent interpretation across data sources, models, and operators.

---

## Core Entity Categories

### 1. Network Topology Entities

#### Line
**Definition:** A transit route with a unique identifier, typically named or numbered.

**Properties:**
- `line_id`: Unique identifier (e.g., "1", "Red", "Victoria")
- `line_name`: Human-readable name
- `operator`: Operating agency
- `mode`: Rail type (subway, light rail, commuter rail)
- `terminals`: List of terminal stations
- `branches`: Optional route variants
- `typical_headway`: Normal service frequency
- `peak_hours`: Peak service periods

**Examples:** NYC Subway Line 1, MBTA Red Line, London Victoria Line

#### Station
**Definition:** A fixed location where passengers board and alight.

**Properties:**
- `station_id`: Unique identifier
- `station_name`: Official name
- `coordinates`: Latitude, longitude
- `lines_served`: Lines stopping at this station
- `transfer_available`: Whether transfers exist
- `accessibility`: ADA/accessibility status
- `platform_count`: Number of platforms
- `typical_dwell_seconds`: Average dwell time

**Related Entities:** Platform, Transfer Point

#### Platform
**Definition:** A specific boarding area within a station for a particular direction.

**Properties:**
- `platform_id`: Unique identifier
- `station_id`: Parent station
- `direction`: Northbound, southbound, etc.
- `track_number`: Associated track
- `capacity`: Approximate passenger capacity

#### Terminal
**Definition:** An endpoint station where trains typically reverse direction.

**Properties:**
- `terminal_id`: Identifier
- `station_id`: Associated station
- `lines`: Lines terminating here
- `turnback_facilities`: Crossovers, loops, sidings
- `turnback_time_minutes`: Typical turnaround time
- `capacity`: Maximum trains that can turn simultaneously

#### Crossover
**Definition:** Track infrastructure allowing trains to change tracks.

**Properties:**
- `crossover_id`: Identifier
- `location`: Between which stations
- `crossover_type`: Universal, scissors, trailing
- `usage_restrictions`: Operational limitations
- `typical_crossing_time_seconds`: Time to execute

#### Track Segment
**Definition:** A section of track between two stations or junctions.

**Properties:**
- `segment_id`: Identifier
- `start_location`: Station or junction
- `end_location`: Station or junction
- `length_meters`: Physical length
- `typical_travel_time_seconds`: Normal transit time
- `max_speed_kph`: Speed limit
- `signaling_system`: Signal control type

---

### 2. Operational Service Entities

#### Trip
**Definition:** A single scheduled journey from origin to destination.

**Properties:**
- `trip_id`: Unique identifier
- `route_id`: Associated route
- `direction_id`: Direction of travel
- `scheduled_start_time`: Planned departure
- `scheduled_end_time`: Planned arrival
- `stops`: Ordered list of stops
- `block_id`: Operating block assignment
- `service_date`: Date of operation

#### Train Run
**Definition:** A physical train executing one or more trips.

**Properties:**
- `run_id`: Identifier
- `vehicle_id`: Physical vehicle
- `operator_id`: Train operator (if tracked)
- `current_trip_id`: Active trip
- `current_location`: Real-time position
- `current_delay_seconds`: Current delay
- `status`: Operating, delayed, out of service

#### Block
**Definition:** A sequence of trips assigned to a single vehicle.

**Properties:**
- `block_id`: Identifier
- `trips`: Ordered list of trip IDs
- `vehicle_id`: Assigned vehicle
- `start_terminal`: First trip origin
- `end_terminal`: Last trip destination

#### Headway
**Definition:** Time interval between consecutive trains on the same line.

**Properties:**
- `measured_at_station`: Reference station
- `line_id`: Line being measured
- `direction`: Direction of travel
- `actual_headway_seconds`: Measured interval
- `scheduled_headway_seconds`: Planned interval
- `deviation_seconds`: Difference from plan
- `timestamp`: Measurement time

#### Dwell Time
**Definition:** Duration a train remains at a station.

**Properties:**
- `station_id`: Station location
- `trip_id`: Associated trip
- `actual_dwell_seconds`: Measured dwell
- `scheduled_dwell_seconds`: Planned dwell
- `door_open_time`: When doors opened
- `door_close_time`: When doors closed
- `passenger_boardings`: Passengers boarding
- `passenger_alightings`: Passengers alighting

---

### 3. Disruption & Incident Entities

#### Disruption Event
**Definition:** An unplanned deviation from normal operations.

**Properties:**
- `disruption_id`: Unique identifier
- `disruption_type`: Classification (see disruption taxonomy)
- `severity`: Low, medium, high, critical
- `status`: Active, monitoring, resolved
- `start_time`: When disruption began
- `end_time`: When disruption ended (if resolved)
- `affected_lines`: Impacted lines
- `affected_stations`: Impacted stations
- `root_cause`: Determined cause (if known)

**Disruption Taxonomy:**
- Signal failure
- Track obstruction
- Vehicle breakdown
- Power outage
- Police activity
- Medical emergency
- Weather impact
- Infrastructure degradation
- Crew unavailability
- Overcrowding

#### Delay
**Definition:** A measurable deviation from scheduled timing.

**Properties:**
- `delay_id`: Identifier
- `trip_id`: Affected trip
- `delay_seconds`: Magnitude of delay
- `delay_location`: Where delay occurred
- `delay_cause`: Known or suspected cause
- `propagated_from`: Original delay source (if cascaded)

#### Bunching Event
**Definition:** Multiple trains operating closer together than scheduled headways.

**Properties:**
- `bunching_id`: Identifier
- `line_id`: Affected line
- `trains_involved`: List of trip/vehicle IDs
- `minimum_headway_seconds`: Smallest gap in bunch
- `normal_headway_seconds`: Expected headway
- `location`: Where bunching observed
- `estimated_cause`: Suspected root cause

---

### 4. Operational Action Entities

#### Holding Action
**Definition:** Intentionally delaying a train at a station.

**Properties:**
- `action_id`: Identifier
- `trip_id`: Train being held
- `station_id`: Hold location
- `hold_duration_seconds`: Planned hold time
- `rationale`: Reason for holding
- `expected_outcome`: Intended effect

#### Short Turn Action
**Definition:** Reversing a train before its scheduled terminal.

**Properties:**
- `action_id`: Identifier
- `trip_id`: Affected trip
- `original_terminal`: Planned terminus
- `short_turn_station`: Actual turn location
- `affected_stops`: Skipped stops
- `rationale`: Reason for short turn
- `passengers_affected_estimate`: Impact assessment

#### Express Operation
**Definition:** Skipping stops to recover schedule.

**Properties:**
- `action_id`: Identifier
- `trip_id`: Trip running express
- `skipped_stops`: List of bypassed stations
- `reason`: Recovery, crowding, etc.
- `time_saved_seconds`: Expected time gain

#### Turnback Operation
**Definition:** Reversing train direction using crossover or terminal.

**Properties:**
- `action_id`: Identifier
- `trip_id`: Train performing turnback
- `turnback_location`: Station or crossover
- `turnback_type`: Terminal, mid-line, emergency
- `execution_time_seconds`: Time to complete
- `outcome`: Success, delay, failure

#### Dispatch Order
**Definition:** An operational command issued by OCC.

**Properties:**
- `order_id`: Identifier
- `order_type`: Hold, express, short turn, etc.
- `issued_by`: Dispatcher/system ID
- `issued_at`: Timestamp
- `target_train`: Train receiving order
- `acknowledged`: Whether operator confirmed
- `executed`: Whether completed

---

### 5. Constraint & Resource Entities

#### Infrastructure Constraint
**Definition:** A limitation imposed by physical infrastructure.

**Properties:**
- `constraint_id`: Identifier
- `constraint_type`: Track capacity, power availability, etc.
- `affected_locations`: Where constraint applies
- `severity`: Impact level
- `duration`: Temporary or permanent
- `workaround_available`: Whether mitigations exist

**Examples:**
- Single tracking due to maintenance
- Platform length limiting train length
- Power supply capacity limiting frequency

#### Rolling Stock Constraint
**Definition:** A limitation related to available vehicles.

**Properties:**
- `constraint_id`: Identifier
- `available_vehicles`: Current fleet size
- `required_vehicles`: Needed for schedule
- `shortfall`: Deficit
- `vehicle_type`: Specific vehicle requirements
- `reason`: Maintenance, breakdown, etc.

#### Crew Constraint
**Definition:** A limitation related to available operators (if tracked).

**Properties:**
- `constraint_id`: Identifier
- `available_operators`: Current staffing
- `required_operators`: Needed for schedule
- `affected_lines`: Impact
- `resolution_time`: Expected availability

---

### 6. Performance & Impact Entities

#### Passenger Impact
**Definition:** The effect of disruptions on riders.

**Properties:**
- `impact_id`: Identifier
- `disruption_id`: Causing disruption
- `estimated_passengers_affected`: Passenger count
- `average_additional_delay_minutes`: Per-passenger delay
- `missed_connections`: Transfer failures
- `crowding_level`: Platform/vehicle crowding

#### Service Degradation
**Definition:** Reduction in normal service level.

**Properties:**
- `degradation_id`: Identifier
- `affected_lines`: Lines operating below normal
- `degradation_type`: Frequency, speed, reliability
- `magnitude`: Percentage reduction
- `start_time`: When degradation began
- `expected_duration`: Anticipated length

#### Recovery Window
**Definition:** The expected timeframe to restore normal service.

**Properties:**
- `recovery_id`: Identifier
- `disruption_id`: Associated disruption
- `estimated_recovery_time`: Expected restoration
- `confidence`: Confidence in estimate
- `recovery_strategy`: Planned approach
- `interim_service_plan`: Temporary operations

---

### 7. Uncertainty & Confidence Entities

#### Uncertainty Estimate
**Definition:** Quantified uncertainty in analysis or prediction.

**Properties:**
- `estimate_id`: Identifier
- `entity_type`: What is uncertain (delay, cause, etc.)
- `point_estimate`: Most likely value
- `confidence_interval`: Range of likely values
- `confidence_level`: Statistical confidence
- `uncertainty_sources`: Contributors to uncertainty

#### Confidence Score
**Definition:** Model or system confidence in an output.

**Properties:**
- `confidence_value`: 0.0 to 1.0
- `computation_method`: How confidence was calculated
- `calibrated`: Whether confidence is calibrated
- `interpretation`: What confidence means

---

### 8. Knowledge & Procedure Entities

#### Operational Procedure
**Definition:** A documented operational practice.

**Properties:**
- `procedure_id`: Identifier
- `procedure_name`: Title
- `category`: Disruption response, daily ops, etc.
- `steps`: Ordered procedure steps
- `applicability`: When procedure applies
- `authority_level`: Who can authorize

#### Glossary Term
**Definition:** Domain-specific terminology definition.

**Properties:**
- `term`: The term being defined
- `definition`: Clear definition
- `synonyms`: Alternative names
- `operator_specific`: Whether term varies by operator
- `examples`: Usage examples

---

## Relationships

### Topology Relationships

- **Station** `located_on` **Line**
- **Platform** `part_of` **Station**
- **Crossover** `connects` **Track Segment**
- **Terminal** `at_end_of` **Line**

### Operational Relationships

- **Trip** `operates_on` **Line**
- **Trip** `stops_at` **Station**
- **Train Run** `executes` **Trip**
- **Delay** `affects` **Trip**
- **Bunching** `involves` **Multiple Trips**

### Causal Relationships

- **Disruption** `causes` **Delay**
- **Delay** `propagates_to` **Downstream Trips**
- **Action** `intended_to_resolve` **Disruption**
- **Action** `has_outcome` **Result**

### Constraint Relationships

- **Infrastructure Constraint** `limits` **Operations**
- **Rolling Stock Constraint** `restricts` **Service Level**
- **Passenger Impact** `results_from` **Disruption**

---

## Operational Reasoning Patterns

### Pattern 1: Delay Diagnosis

```
Observed: Trip delay at Station X
Question: What is the root cause?

Reasoning Chain:
1. Check upstream conditions (prior stations, prior trips)
2. Check infrastructure status (signals, tracks)
3. Check vehicle status (if available)
4. Check external factors (weather, incidents)
5. Assess propagation (did delay cascade from earlier?)
6. Estimate confidence in diagnosis
```

### Pattern 2: Headway Regulation

```
Observed: Bunching on Line Y
Question: How to restore headways?

Reasoning Chain:
1. Identify bunch composition (how many trains, gaps)
2. Assess current positions and speeds
3. Evaluate hold vs. express options
4. Consider passenger load distribution
5. Estimate time to headway restoration
6. Recommend action with rationale
```

### Pattern 3: Recovery Planning

```
Observed: Major disruption on Line Z
Question: What recovery strategy should be used?

Reasoning Chain:
1. Assess severity and expected duration
2. Identify affected infrastructure
3. Check availability of crossovers/terminals
4. Consider short turn vs. single tracking options
5. Estimate passenger impact of each option
6. Recommend prioritized actions
```

---

## Ontology Usage Guidelines

### For Model Training

- Ensure synthetic scenarios use ontology terms consistently
- Label entities explicitly in training data
- Include entity relationships in context
- Model outputs should reference ontology entities

### For Evaluation

- Verify model outputs conform to ontology
- Check relationship consistency (e.g., station actually on line)
- Validate action feasibility given constraints
- Test entity recognition accuracy

### For Retrieval

- Index knowledge base by ontology entities
- Enable entity-based retrieval queries
- Support relationship-based search
- Maintain entity resolution across sources

---

## Extension Guidelines

To extend this ontology:

1. Identify new entity or relationship need
2. Define precisely with properties
3. Document examples and usage
4. Update schemas to reflect changes
5. Version the ontology

---

**Ontology Version:** 1.0.0
**Schema Version:** 1.0.0
**Maintained by:** metroLM Contributors
