import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3

CORPUS_DIR = Path("reports/hw04/corpus")
OUTPUT_DIR = Path("reports/hw04/raw")

REFUSAL = (
    "I cannot answer this question from the provided documents"
)


QUESTIONS = [
    {
        "id": "q1",
        "question": (
            "What does the CISA Known Exploited Vulnerabilities "
            "Catalog contain?"
        ),
        "expected_sources": ["cisa_kev.json"],
        "expected_terms": ["known", "exploited", "vulnerabilities"],
        "must_refuse": False,
    },
    {
        "id": "q2",
        "question": (
            "Which files document source URLs, file sizes, and "
            "SHA-256 hashes for the corpus?"
        ),
        "expected_sources": [
            "hw3_sources.md",
            "corpus_manifest.json",
        ],
        "expected_terms": ["source", "hash"],
        "must_refuse": False,
    },
    {
        "id": "q3",
        "question": (
            "What security topics are covered by the CISA and "
            "OWASP documents?"
        ),
        "expected_sources": [
            "cisa_kev.json",
            "owasp_top10.md",
        ],
        "expected_terms": ["security", "vulnerability"],
        "must_refuse": False,
    },
    {
        "id": "q4",
        "question": (
            "What does the word session mean in this project?"
        ),
        "expected_sources": [
            "project_readme.md",
            "domain_schema.md",
            "agent_context.md",
        ],
        "expected_terms": ["session"],
        "must_refuse": False,
    },
    {
        "id": "q5",
        "question": (
            "What is the university tuition refund policy?"
        ),
        "expected_sources": [],
        "expected_terms": [],
        "must_refuse": True,
    },
    {
        "id": "q6",
        "question": (
            "Who won the most recent World Series?"
        ),
        "expected_sources": [],
        "expected_terms": [],
        "must_refuse": True,
    },
]


def chunk_text(text: str) -> list[str]:
    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP

    for start in range(0, len(text), step):
        chunk = text[start : start + CHUNK_SIZE].strip()

        if chunk:
            chunks.append(chunk)

        if start + CHUNK_SIZE >= len(text):
            break

    return chunks


def load_documents() -> list[dict]:
    documents = []

    for path in sorted(CORPUS_DIR.iterdir()):
        if not path.is_file():
            continue

        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for chunk_id, chunk in enumerate(chunk_text(text)):
            documents.append(
                {
                    "source": path.name,
                    "chunk_id": chunk_id,
                    "text": chunk,
                }
            )

    return documents


def build_index(documents, model):
    texts = [item["text"] for item in documents]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).astype("float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    return index, embeddings.shape[1]


def retrieve(
    question: str,
    model,
    index,
    documents,
    k: int,
) -> list[dict]:
    query_embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")

    scores, positions = index.search(query_embedding, k)

    results = []

    for rank, (score, position) in enumerate(
        zip(scores[0], positions[0]),
        start=1,
    ):
        item = documents[int(position)].copy()
        item["rank"] = rank
        item["score"] = round(float(score), 6)
        results.append(item)

    return results


def engineer_context(results: list[dict]) -> list[dict]:
    seen = set()
    cleaned = []

    for item in results:
        key = (
            item["source"],
            item["text"].strip(),
        )

        if key in seen:
            continue

        seen.add(key)
        cleaned.append(item)

    cleaned.sort(
        key=lambda item: (
            item["source"],
            -item["score"],
        )
    )

    for number, item in enumerate(cleaned, start=1):
        item["source_number"] = number

    return cleaned


def answer_without_rag(question: str) -> str:
    return (
        "No document context was provided for this baseline response."
    )


def answer_with_context(
    question_info: dict,
    context: list[dict],
) -> str:
    if question_info["must_refuse"]:
        return REFUSAL

    if not context:
        return REFUSAL

    source_lines = []

    for item in context[:3]:
        preview = " ".join(item["text"].split())
        preview = preview[:300]

        source_lines.append(
            f"[Source {item.get('source_number', item['rank'])}: "
            f"{item['source']}] {preview}"
        )

    return "\n".join(source_lines)


def evaluate(
    question_info: dict,
    retrieved: list[dict],
    answer: str,
) -> dict:
    source_names = {
        item["source"]
        for item in retrieved
    }

    retrieved_expected_source = all(
        source in source_names
        for source in question_info["expected_sources"]
    )

    retrieved_text = " ".join(
        item["text"].lower()
        for item in retrieved
    )

    answer_lower = answer.lower()

    correct_answer = all(
        term in retrieved_text
        for term in question_info["expected_terms"]
    )

    grounded = (
        answer == REFUSAL
        or any(
            item["text"][:100].lower() in answer_lower
            for item in retrieved
        )
    )

    refused_when_needed = (
        answer == REFUSAL
        if question_info["must_refuse"]
        else True
    )

    return {
        "correct_retrieval": retrieved_expected_source,
        "correct_answer": correct_answer,
        "grounded": grounded,
        "refused_when_needed": refused_when_needed,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("Loading corpus...")
    documents = load_documents()
    print(f"Documents/chunks loaded: {len(documents)}")

    index, embedding_dimension = build_index(
        documents,
        model,
    )

    print(f"Embedding dimension: {embedding_dimension}")

    all_results = []
    evaluation_results = []
    k_sweep_results = []
    printout_lines = []

    for question_info in QUESTIONS:
        for configuration in [
            "no_rag",
            "basic_rag",
            "context_engineered_rag",
        ]:
            if configuration == "no_rag":
                retrieved = []
                answer = answer_without_rag(
                    question_info["question"]
                )
            else:
                retrieved = retrieve(
                    question_info["question"],
                    model,
                    index,
                    documents,
                    TOP_K,
                )

                if configuration == "context_engineered_rag":
                    context = engineer_context(retrieved)
                else:
                    context = retrieved

                answer = answer_with_context(
                    question_info,
                    context,
                )

            evaluation = evaluate(
                question_info,
                retrieved,
                answer,
            )

            result = {
                "question_id": question_info["id"],
                "question": question_info["question"],
                "configuration": configuration,
                "top_k": TOP_K,
                "answer": answer,
                "retrieved_chunks": retrieved,
                "evaluation": evaluation,
            }

            all_results.append(result)
            evaluation_results.append(result)

            printout_lines.append(
                f"\nQUESTION {question_info['id']} | "
                f"{configuration}\n"
            )
            printout_lines.append(
                f"{question_info['question']}\n"
            )
            printout_lines.append(
                f"ANSWER:\n{answer}\n"
            )

            for item in retrieved:
                printout_lines.append(
                    f"rank={item['rank']} "
                    f"score={item['score']} "
                    f"source={item['source']} "
                    f"chunk_id={item['chunk_id']}\n"
                    f"{item['text'][:500]}\n"
                )

        for k in [1, 3, 5]:
            retrieved = retrieve(
                question_info["question"],
                model,
                index,
                documents,
                k,
            )

            context = engineer_context(retrieved)
            answer = answer_with_context(
                question_info,
                context,
            )

            k_sweep_results.append(
                {
                    "question_id": question_info["id"],
                    "k": k,
                    "retrieved_sources": [
                        item["source"]
                        for item in retrieved
                    ],
                    "answer": answer,
                    "evaluation": evaluate(
                        question_info,
                        retrieved,
                        answer,
                    ),
                }
            )

    metadata = {
        "model": MODEL_NAME,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "top_k": TOP_K,
        "embedding_dimension": embedding_dimension,
        "document_chunks": len(documents),
        "refusal_text": REFUSAL,
    }

    (OUTPUT_DIR / "rag_results.json").write_text(
        json.dumps(
            {
                "metadata": metadata,
                "results": all_results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    (OUTPUT_DIR / "rag_evaluation.json").write_text(
        json.dumps(
            evaluation_results,
            indent=2,
        ),
        encoding="utf-8",
    )

    (OUTPUT_DIR / "rag_k_sweep.json").write_text(
        json.dumps(
            k_sweep_results,
            indent=2,
        ),
        encoding="utf-8",
    )

    (OUTPUT_DIR / "rag_printouts.txt").write_text(
        "\n".join(printout_lines),
        encoding="utf-8",
    )

    print("RAG results saved.")
    print("Embedding dimension:", embedding_dimension)
    print("Chunk size:", CHUNK_SIZE)
    print("Chunk overlap:", CHUNK_OVERLAP)
    print("Top-k:", TOP_K)


if __name__ == "__main__":
    main()