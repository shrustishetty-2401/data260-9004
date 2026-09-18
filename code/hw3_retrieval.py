import csv
import json
import math
import time
from pathlib import Path
from statistics import mean
from typing import Any

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import (
    SemanticSplitterNodeParser,
    SentenceWindowNodeParser,
    TokenTextSplitter,
)
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


REPO_ROOT = Path(__file__).resolve().parents[1]

CORPUS_DIR = REPO_ROOT / "reports/hw03/corpus"
QUESTIONS_PATH = REPO_ROOT / "reports/hw03/questions.yaml"
OUTPUT_DIR = REPO_ROOT / "reports/hw03/raw/retrieval"

TOP_K = 3
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_questions() -> list[dict[str, Any]]:
    questions = []
    current = None

    for line in QUESTIONS_PATH.read_text(
        encoding="utf-8"
    ).splitlines():
        stripped = line.strip()

        if stripped.startswith("- id:"):
            if current is not None:
                questions.append(current)

            current = {
                "id": stripped.split(":", 1)[1].strip()
            }

        elif current is not None and stripped.startswith(
            "question:"
        ):
            current["question"] = (
                stripped.split(":", 1)[1]
                .strip()
                .strip('"')
            )

        elif current is not None and stripped.startswith(
            "expected_answer:"
        ):
            current["expected_answer"] = (
                stripped.split(":", 1)[1]
                .strip()
                .strip('"')
            )

        elif current is not None and stripped.startswith(
            "- corpus/"
        ):
            current.setdefault(
                "source_files",
                [],
            ).append(stripped[2:].strip())

    if current is not None:
        questions.append(current)

    return questions


def load_documents() -> list[Document]:
    documents = []

    cisa_path = CORPUS_DIR / "cisa_kev.json"
    cisa_text = cisa_path.read_text(
        encoding="utf-8"
    )

    documents.append(
        Document(
            text=cisa_text,
            metadata={
                "source_file": "corpus/cisa_kev.json"
            },
        )
    )

    owasp_path = CORPUS_DIR / "owasp_top10.md"
    owasp_text = owasp_path.read_text(
        encoding="utf-8"
    )

    documents.append(
        Document(
            text=owasp_text,
            metadata={
                "source_file": "corpus/owasp_top10.md"
            },
        )
    )

    return documents


def cosine_similarity(
    first_vector: list[float],
    second_vector: list[float],
) -> float:
    if not first_vector or not second_vector:
        return 0.0

    numerator = sum(
        first_value * second_value
        for first_value, second_value in zip(
            first_vector,
            second_vector,
        )
    )

    first_length = math.sqrt(
        sum(value * value for value in first_vector)
    )

    second_length = math.sqrt(
        sum(value * value for value in second_vector)
    )

    if first_length == 0 or second_length == 0:
        return 0.0

    return numerator / (
        first_length * second_length
    )


def preview(text: str, length: int = 240) -> str:
    cleaned = " ".join(text.split())

    if len(cleaned) <= length:
        return cleaned

    return cleaned[:length] + "..."


def build_parsers(
    embed_model: HuggingFaceEmbedding,
) -> dict[str, Any]:
    return {
        "token": TokenTextSplitter(
            chunk_size=256,
            chunk_overlap=40,
        ),
        "semantic": SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=95,
            embed_model=embed_model,
        ),
        "sentence_window": SentenceWindowNodeParser.from_defaults(
            window_size=3,
            window_metadata_key="window",
            original_text_metadata_key="original_text",
        ),
    }


def extract_node_text(node: Any) -> str:
    return node.get_content()


def get_source_file(node: Any) -> str:
    metadata = getattr(node, "metadata", {}) or {}

    return metadata.get(
        "source_file",
        metadata.get("file_name", "unknown"),
    )


def save_results(
    technique_name: str,
    results: list[dict[str, Any]],
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = OUTPUT_DIR / f"{technique_name}.json"
    csv_path = OUTPUT_DIR / f"{technique_name}.csv"
    jsonl_path = OUTPUT_DIR / f"{technique_name}.jsonl"

    json_path.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    if results:
        csv_rows = []

        for result in results:
            row = {
                "technique": result["technique"],
                "question_id": result["question_id"],
                "question": result["question"],
                "latency_ms": result["latency_ms"],
                "query_embedding_dimension": result[
                    "query_embedding_dimension"
                ],
                "retrieved_chunks": json.dumps(
                    result["retrieved_chunks"]
                ),
            }

            csv_rows.append(row)

        with csv_path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=csv_rows[0].keys(),
            )
            writer.writeheader()
            writer.writerows(csv_rows)

    with jsonl_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for result in results:
            file.write(
                json.dumps(result) + "\n"
            )


def calculate_metrics(
    technique_name: str,
    results: list[dict[str, Any]],
    chunk_count: int,
    chunk_lengths: list[int],
) -> dict[str, Any]:
    top1_scores = []
    all_scores = []
    recall_values = []
    latencies = []

    for result in results:
        retrieved_chunks = result[
            "retrieved_chunks"
        ]

        if retrieved_chunks:
            top1_scores.append(
                retrieved_chunks[0][
                    "explicit_cosine_similarity"
                ]
            )

        all_scores.extend(
            chunk["explicit_cosine_similarity"]
            for chunk in retrieved_chunks
        )

        expected_sources = set(
            result["expected_source_files"]
        )

        retrieved_sources = {
            chunk["source_file"]
            for chunk in retrieved_chunks
        }

        if expected_sources:
            recall_values.append(
                int(
                    bool(
                        expected_sources
                        & retrieved_sources
                    )
                )
            )

        latencies.append(result["latency_ms"])

    return {
        "technique": technique_name,
        "chunks": chunk_count,
        "questions": len(results),
        "average_chunk_length": round(
            mean(chunk_lengths),
            2,
        ) if chunk_lengths else 0,
        "top1_cosine": round(
            mean(top1_scores),
            6,
        ) if top1_scores else 0,
        "mean_at_k_cosine": round(
            mean(all_scores),
            6,
        ) if all_scores else 0,
        "recall_at_k": round(
            mean(recall_values),
            4,
        ) if recall_values else 0,
        "mean_latency_ms": round(
            mean(latencies),
            2,
        ) if latencies else 0,
    }


def run_technique(
    technique_name: str,
    parser: Any,
    documents: list[Document],
    questions: list[dict[str, Any]],
    embed_model: HuggingFaceEmbedding,
) -> dict[str, Any]:
    print(
        f"\nRunning technique: "
        f"{technique_name}"
    )

    nodes = parser.get_nodes_from_documents(
        documents
    )

    chunk_lengths = []
    node_embeddings = {}

    for node in nodes:
        chunk_text = extract_node_text(node)

        chunk_lengths.append(
            len(chunk_text)
        )

        node_id = getattr(
            node,
            "node_id",
            str(id(node)),
        )

        node_embeddings[node_id] = (
            embed_model.get_text_embedding(
                chunk_text
            )
        )

    print(
        f"Chunks created: {len(nodes)}"
    )

    index = VectorStoreIndex(
        nodes,
        embed_model=embed_model,
        vector_store=SimpleVectorStore(),
    )

    retriever = index.as_retriever(
        similarity_top_k=TOP_K
    )

    technique_results = []

    for question in questions:
        started = time.perf_counter()

        query_text = question["question"]

        query_embedding = (
            embed_model.get_text_embedding(
                query_text
            )
        )

        retrieved_nodes = retriever.retrieve(
            query_text
        )

        latency_ms = round(
            (
                time.perf_counter()
                - started
            )
            * 1000,
            2,
        )

        retrieved_chunks = []

        for rank, result in enumerate(
            retrieved_nodes,
            start=1,
        ):
            node = result.node
            chunk_text = extract_node_text(node)

            node_id = getattr(
                node,
                "node_id",
                str(id(node)),
            )

            chunk_embedding = node_embeddings.get(
                node_id,
                [],
            )

            explicit_score = cosine_similarity(
                query_embedding,
                chunk_embedding,
            )

            retrieved_chunks.append(
                {
                    "rank": rank,
                    "stored_score": result.score,
                    "explicit_cosine_similarity": round(
                        explicit_score,
                        6,
                    ),
                    "source_file": get_source_file(
                        node
                    ),
                    "chunk_length": len(
                        chunk_text
                    ),
                    "chunk_preview": preview(
                        chunk_text
                    ),
                    "vector_dimension": len(
                        chunk_embedding
                    ),
                    "vector_shape": [
                        len(chunk_embedding)
                    ] if chunk_embedding else [],
                    "node_id": node_id,
                }
            )

        result_record = {
            "technique": technique_name,
            "question_id": question["id"],
            "question": query_text,
            "expected_answer": question.get(
                "expected_answer",
                "",
            ),
            "expected_source_files": question.get(
                "source_files",
                [],
            ),
            "top_k": TOP_K,
            "query_embedding_dimension": len(
                query_embedding
            ),
            "query_embedding_first_8": (
                query_embedding[:8]
            ),
            "retrieved_chunks": retrieved_chunks,
            "latency_ms": latency_ms,
        }

        technique_results.append(
            result_record
        )

        if retrieved_chunks:
            top1_score = retrieved_chunks[0][
                "explicit_cosine_similarity"
            ]
        else:
            top1_score = "N/A"

        print(
            f"{question['id']}: "
            f"top1 cosine={top1_score}"
        )

    save_results(
        technique_name,
        technique_results,
    )

    return calculate_metrics(
        technique_name,
        technique_results,
        len(nodes),
        chunk_lengths,
    )


def main() -> None:
    print("Loading embedding model...")

    embed_model = HuggingFaceEmbedding(
        model_name=MODEL_NAME
    )

    print("Loading documents...")

    documents = load_documents()
    questions = load_questions()
    parsers = build_parsers(
        embed_model
    )

    print(
        f"Documents loaded: "
        f"{len(documents)}"
    )

    print(
        f"Questions loaded: "
        f"{len(questions)}"
    )

    metrics = []

    for technique_name, parser in parsers.items():
        technique_metrics = run_technique(
            technique_name=technique_name,
            parser=parser,
            documents=documents,
            questions=questions,
            embed_model=embed_model,
        )

        metrics.append(
            technique_metrics
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    metrics_path = OUTPUT_DIR / "metrics.json"

    metrics_path.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )

    print(
        "\nFinished successfully."
    )

    print(
        f"Results saved in: "
        f"{OUTPUT_DIR}"
    )

    print(
        f"Metrics saved in: "
        f"{metrics_path}"
    )


if __name__ == "__main__":
    main()