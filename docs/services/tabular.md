# Tabular

## Responsibilities

Tabular transforms unstructured text into structured tabular data for analytics:

1. **Text structure analysis**
   - Retrieving text files from Cloud Storage by text_uri
   - Determining structure: tabular data, JSON, CSV, free-form text
   - Extracting entities and relationships

2. **Schema inference**
   - Automatic detection of fields and their types
   - Using embeddings for semantic understanding
   - Mapping to predefined concepts and ontologies

3. **Format standardization**
   - Converting to unified tabular structure
   - Normalizing data types
   - Forming dimensions and facts

4. **Validation and storage**
   - Validating types, ranges, identifiers
   - Generating audit report with warnings
   - Direct loading to BigQuery:
     - Load to staging tables
     - MERGE to final tables (dim_*, fact_*, observations)
     - Using partitioning and clustering

5. **Status relay**
   - Returning INGESTED status with issues/warnings
   - Information about bytes_processed and cache_hit from BigQuery

## Motivation

**Why a separate Tabular service is needed:**

1. **Semantic analysis**
   - Transformer does "text → text", while Tabular does "text → structure"
   - Requires ML models for content understanding
   - Embeddings and NLP require separate infrastructure

2. **Separation of extraction from structuring**
   - Transformer extracts "raw" text
   - Tabular understands **meaning** and **structure** of text
   - Different levels of abstraction and processing

3. **Domain-specific logic**
   - Knowledge of business entities (dim_*, fact_*, observations)
   - Mapping to domain concepts
   - Can evolve independently from Transformer

4. **Direct storage integration**
   - Optimization of BigQuery loading (batch, MERGE)
   - Managing partitions and clusters
   - No intermediate layer needed through MIME Decoder

5. **Data Quality**
   - Centralized validation of all data before storage
   - Single point for audit trail
   - Quality control independent from data source

6. **Scaling analytical workload**
   - Schema inference is computationally expensive
   - May require significant resources for embeddings
   - Independent scaling from other services
