# Embeddings in NLQ Chat Interface

## Current Status: NOT USED in MVP

The NLQ Chat Interface MVP **does not use embeddings**. All natural language understanding is handled by the Featherless.ai LLM (Llama 3.1 8B Instruct).

## Why Not Use Embeddings?

1. **LLM is sufficient**: Llama 3.1 8B already understands natural language perfectly for SQL generation
2. **Simplicity**: No need for embedding generation, storage, or similarity computation in MVP
3. **Performance**: Direct LLM API calls are fast enough (1-3 seconds)
4. **Incremental approach**: Can add embeddings later for specific optimizations

## Existing Embedding Infrastructure

The EduScale application **already has embeddings** for other purposes:

### Configuration

```python
# src/eduscale/core/config.py
EMBEDDING_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DIMENSION: int = 768
```

### Functions

```python
# src/eduscale/tabular/concepts.py
from eduscale.tabular.concepts import embed_texts

# Generate embeddings for texts
embeddings = embed_texts(["text1", "text2"])  # Returns np.ndarray (2, 768)
```

### Current Use Cases

1. **Tabular Ingestion**:
   - Table type classification (ATTENDANCE, ASSESSMENT, etc.)
   - Column mapping to concepts (student_id, test_score, etc.)

2. **Entity Resolution**:
   - Match student/teacher/parent names across files
   - `EntityCache` stores embeddings for all entities
   - `_embedding_match()` finds best match via cosine similarity

3. **Feedback Analysis**:
   - Find relevant entities in text feedback
   - `_embedding_based_matching()` extracts targets from feedback

## Future Use Cases for NLQ (Out of MVP Scope)

### 1. Semantic Query Caching

**Problem**: Users ask similar questions with different wording
- "Show test scores for Region A"
- "What are the test results in Region A?"
- "Display assessment scores from Region A"

**Solution**: Cache queries with embeddings

```python
from eduscale.tabular.concepts import embed_texts
from sklearn.metrics.pairwise import cosine_similarity
import json

# In-memory cache (or Redis)
query_cache = {}  # {query_text: {"sql": "...", "embedding": np.ndarray}}

def get_sql_with_cache(user_query: str) -> dict:
    """Generate SQL or return cached result if similar query exists."""
    
    # Generate embedding for user query
    query_embedding = embed_texts([user_query])[0]
    
    # Check cache for similar queries
    for cached_query, cached_data in query_cache.items():
        similarity = cosine_similarity(
            query_embedding.reshape(1, -1),
            cached_data["embedding"].reshape(1, -1)
        )[0][0]
        
        # If very similar (>0.95), reuse cached SQL
        if similarity > 0.95:
            logger.info(f"Cache hit: {user_query} -> {cached_query} (similarity={similarity:.3f})")
            return {"sql": cached_data["sql"], "explanation": cached_data["explanation"]}
    
    # No cache hit, generate new SQL
    result = generate_sql_from_nl(user_query)
    
    # Store in cache
    query_cache[user_query] = {
        "sql": result["sql"],
        "explanation": result["explanation"],
        "embedding": query_embedding
    }
    
    return result
```

**Benefits**:
- Faster responses for similar queries
- Consistent SQL for similar questions
- Reduce LLM API calls (cost savings)

**Complexity**: Medium (needs cache management, TTL, eviction policy)

### 2. Query Suggestions

**Problem**: Users don't know what questions to ask

**Solution**: Suggest similar questions based on embeddings

```python
from eduscale.tabular.concepts import embed_texts
from sklearn.metrics.pairwise import cosine_similarity

# Precomputed example questions with embeddings
EXAMPLE_QUERIES = [
    {"question": "Compare regions by test scores", "embedding": ...},
    {"question": "Show interventions in Region A", "embedding": ...},
    {"question": "Find observations mentioning teachers", "embedding": ...},
    # ... more examples
]

def suggest_similar_queries(user_query: str, top_k: int = 3) -> list[str]:
    """Suggest similar example queries based on user input."""
    
    # Generate embedding for partial user input
    query_embedding = embed_texts([user_query])[0]
    
    # Compute similarity with all examples
    similarities = []
    for example in EXAMPLE_QUERIES:
        sim = cosine_similarity(
            query_embedding.reshape(1, -1),
            example["embedding"].reshape(1, -1)
        )[0][0]
        similarities.append((example["question"], sim))
    
    # Sort by similarity and return top K
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [q for q, s in similarities[:top_k]]
```

**Benefits**:
- Better user onboarding
- Discover available data
- Faster query formulation

**Complexity**: Low (just add suggestions UI component)

### 3. Entity Extraction from Questions

**Problem**: User mentions specific entities ("Show scores for John Smith in Prague")

**Solution**: Extract entities using embeddings + entity cache

```python
from eduscale.tabular.analysis.entity_resolver import load_entity_cache
from eduscale.tabular.concepts import embed_texts
from sklearn.metrics.pairwise import cosine_similarity

def extract_entities_from_query(user_query: str, region_id: str) -> dict:
    """Extract mentioned entities from user query."""
    
    entity_cache = load_entity_cache(region_id)
    query_embedding = embed_texts([user_query])[0]
    
    extracted = {
        "students": [],
        "teachers": [],
        "schools": [],
    }
    
    # Check for student mentions
    for student_id, student_embedding in entity_cache.student_embeddings.items():
        similarity = cosine_similarity(
            query_embedding.reshape(1, -1),
            student_embedding.reshape(1, -1)
        )[0][0]
        
        if similarity > 0.8:  # High threshold for explicit mentions
            student_name = entity_cache.entity_names[student_id]
            extracted["students"].append({
                "id": student_id,
                "name": student_name,
                "confidence": similarity
            })
    
    # Same for teachers, schools, etc.
    
    return extracted
```

**Benefits**:
- More accurate SQL (can use specific IDs)
- Better understanding of user intent
- Support for complex queries with multiple entities

**Complexity**: High (needs entity cache in NLQ context, careful threshold tuning)

### 4. Query Clustering & Analytics

**Problem**: Understand what users are asking about

**Solution**: Cluster query embeddings to find patterns

```python
from sklearn.cluster import KMeans
import numpy as np

def analyze_query_patterns(queries: list[str], n_clusters: int = 5):
    """Cluster user queries to understand usage patterns."""
    
    # Generate embeddings for all queries
    embeddings = embed_texts(queries)
    
    # Cluster embeddings
    kmeans = KMeans(n_clusters=n_clusters)
    labels = kmeans.fit_predict(embeddings)
    
    # Group queries by cluster
    clusters = {}
    for i, (query, label) in enumerate(zip(queries, labels)):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(query)
    
    # Find representative query for each cluster (closest to centroid)
    for label, centroid in enumerate(kmeans.cluster_centers_):
        cluster_queries = clusters[label]
        cluster_embeddings = embeddings[labels == label]
        
        similarities = cosine_similarity([centroid], cluster_embeddings)[0]
        best_idx = np.argmax(similarities)
        
        print(f"Cluster {label}: {cluster_queries[best_idx]}")
        print(f"  Examples: {cluster_queries[:3]}")
```

**Benefits**:
- Understand user needs
- Improve system prompt based on common patterns
- Identify missing features

**Complexity**: Low (analytics only, no user-facing changes)

## Implementation Priority (If Adding Embeddings)

1. **Semantic Query Caching** (HIGH) - immediate performance benefit, cost savings
2. **Query Suggestions** (MEDIUM) - improves UX, easy to implement
3. **Query Clustering** (LOW) - analytics only, no user impact
4. **Entity Extraction** (LOW) - complex, marginal benefit over LLM-based extraction

## Dependencies

If implementing any embedding-based features:

```python
# Already available in application
from eduscale.tabular.concepts import embed_texts, init_embeddings
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Configuration (already exists)
from eduscale.core.config import settings
# settings.EMBEDDING_MODEL_NAME
# settings.EMBEDDING_DIMENSION
```

No new dependencies needed!

## Performance Considerations

### Embedding Generation

- **Model**: sentence-transformers/paraphrase-multilingual-mpnet-base-v2
- **Size**: 470MB (already loaded in memory for tabular ingestion)
- **Latency**: ~50ms for single query (local, on CPU)
- **Batch latency**: ~200ms for 10 queries

### Similarity Computation

- **Cosine similarity**: O(d) where d=768 dimensions
- **Single comparison**: ~1μs (negligible)
- **Cache search** (1000 entries): ~1ms (acceptable)

### Conclusion

Embeddings add **minimal overhead** (~50ms) if model is already loaded. Main complexity is cache management, not performance.

## Recommendation

**For MVP**: Skip embeddings, use Featherless.ai LLM only (simpler, faster to implement)

**For production**: Add semantic query caching after MVP launch (easy win, saves API costs)

**For advanced features**: Consider entity extraction and query suggestions in Phase 2

## References

- Current embedding usage: `src/eduscale/tabular/concepts.py`
- Entity resolution: `src/eduscale/tabular/analysis/entity_resolver.py`
- Feedback analysis: `src/eduscale/tabular/analysis/feedback_analyzer.py`
- Configuration: `src/eduscale/core/config.py`

