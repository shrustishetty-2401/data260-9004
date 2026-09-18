# HW3 Retrieval Metrics

## Configuration

- Student ID: 9004
- Domain ID: 4
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Top-k: 3
- Questions: 5
- Corpus files: CISA KEV JSON and OWASP Top 10 Markdown

## Results

| Technique | Chunks | Average chunk length | Top-1 cosine | Mean@k cosine | Recall@k | Mean latency |
|---|---:|---:|---:|---:|---:|---:|
| Token | 3329 | 611.01 | 0.589578 | 0.583063 | 0.40 | 70.45 ms |
| Semantic | 229 | 7620.62 | 0.596274 | 0.559302 | 0.40 | 16.56 ms |
| Sentence window | 4522 | 385.92 | 0.625112 | 0.598668 | 0.40 | 86.51 ms |

## Interpretation

The sentence-window technique produced the strongest retrieval similarity. It had the highest top-1 cosine score and the highest mean cosine score across the top three retrieved chunks.

The semantic technique was the fastest because it created fewer chunks. However, its chunks were much larger, with an average length of more than 7,600 characters.

The token technique provided a middle ground between speed and chunk size.

Recall@k was 0.40 for all three techniques. This means that the expected source was retrieved for two of the five questions.

## Query Embeddings

For every question, the program recorded:

- Query embedding dimension
- First eight query embedding values
- Retrieved chunk scores
- Explicit cosine similarity
- Source file
- Chunk length
- Chunk preview
- Vector dimension and shape
- Query latency

## Conclusion

For this corpus, sentence-window retrieval was the strongest based on cosine similarity. Semantic splitting was fastest, but its chunks were very large. Token splitting provided a balanced alternative.