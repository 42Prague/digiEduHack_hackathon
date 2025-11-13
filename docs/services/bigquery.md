# BigQuery (EU)

## Responsibilities

BigQuery is the final data warehouse for structured analytical data:

1. **Data loading**
   - Receiving data from Tabular service
   - Loading to staging tables for validation
   - MERGE operations to final tables (dim_*, fact_*, observations)
   - Batch loading optimization

2. **Data storage**
   - Storing dimensional data (dim_* tables)
   - Storing fact data (fact_* tables)
   - Storing observation data (observations table)
   - Partitioning by date/region for query performance
   - Clustering for access patterns

3. **Query performance**
   - Columnar storage for analytical queries
   - Automatic caching of query results
   - Query optimization and execution
   - Reporting bytes_processed and cache_hit metrics

4. **Data locality and compliance**
   - EU region for GDPR compliance
   - Data encryption at rest and in transit
   - Access control and audit logging

## Motivation

**Why BigQuery (EU) is needed:**

1. **Analytical data warehouse**
   - Optimized for OLAP queries, not OLTP
   - Supports complex aggregations and analytics
   - SQL interface for business intelligence tools
   - Scalable to petabytes without performance degradation

2. **Serverless and fully managed**
   - No infrastructure to provision or manage
   - Automatic scaling based on query load
   - Pay only for data stored and queries executed
   - High availability built-in

3. **Structured data model**
   - Enforces schema for data quality
   - Supports star schema (dimensions + facts)
   - Enables relational queries and joins
   - Type safety and validation

4. **Integration with analytics tools**
   - Standard SQL for familiar querying
   - Native connectors for BI tools (Looker, Tableau, etc.)
   - API access for custom applications
   - Export to ML models and data science tools

5. **Performance optimization features**
   - Partitioning by date/region reduces query cost
   - Clustering improves query performance
   - Materialized views for pre-aggregated data
   - BI Engine for sub-second dashboard queries

6. **Data governance**
   - Column-level security
   - Row-level security policies
   - Audit logs for compliance
   - Data lineage tracking
   - EU region ensures data sovereignty
