# Data Schema & Ontology

TITAN uses a property graph model to represent the supply chain ecosystem.

## 1. Node Labels (Entities)

### `Factory`
* **Role:** Production origin.
* **Properties:**
    * `id`: Unique Identifier (e.g., FACTORY_001)
    * `name`: Display Name
    * `country`: ISO Country Name
    * `city`: Location City
    * `lat`, `lon`: Geospatial coordinates
    * `product_type`: Primary output category (e.g., P1, P2)
    * `capacity`: Monthly production capacity (int)

### `Port`
* **Role:** Transit hub.
* **Properties:** `id`, `name`, `type` (Container/Bulk/Mixed), `lat`, `lon`, `capacity`.

### `Warehouse`
* **Role:** Storage and distribution center.
* **Properties:** `id`, `name`, `warehouse_type` (Cross-dock/Storage), `lat`, `lon`.

### `Product`
* **Role:** The SKU being moved.
* **Properties:**
    * `id`: SKU ID (e.g., P1)
    * `name`: Descriptive Name (e.g., "Semiconductors")
    * `weight_kg`: Unit weight
    * `price`: Unit cost

### `Disaster` (Dynamic Node)
* **Role:** Temporary event impacting the graph.
* **Properties:** `id`, `type` (Earthquake/Flood), `severity`, `lat`, `lon`, `radius_km`.

---

## 2. Relationships (Edges)

### `[:SUPPLIES_TO]`
* **Direction:** `Factory` -> `Port` -> `Warehouse`
* **Properties:**
    * `distance_km`: Haversine distance between nodes.
    * `frequency`: Shipment cadence (Daily/Weekly).
    * `transport_mode`: Air/Sea/Land.

### `[:STOCKS]`
* **Direction:** `Warehouse` -> `Product`
* **Properties:**
    * `quantity`: Current inventory level.
    * `last_updated`: Timestamp.

### `[:AFFECTS]` (Computed dynamically)
* **Direction:** `Disaster` -> `Factory/Port/Warehouse`
* **Properties:**
    * `impact_score`: 0.0 - 1.0 severity.
    * `status`: 'Disrupted' or 'Offline'.

---

## 3. Vector Embeddings Structure (ChromaDB)
* **Document:** Raw text of product manuals or news.
* **Metadata:**
    * `category`: "ProductSpec" or "RiskAlert"
    * `related_node_id`: Links back to a Neo4j Node ID (The bridge between Graph and Vector).