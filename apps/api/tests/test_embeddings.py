from knowledge.embeddings import _hash_embedding, vector_literal


def test_hash_embedding_dimension() -> None:
    vector = _hash_embedding("relay knowledge", 32)
    assert len(vector) == 32
    assert abs(sum(value * value for value in vector) - 1.0) < 1e-6


def test_vector_literal_format() -> None:
    literal = vector_literal([0.1, -0.2])
    assert literal.startswith("[")
    assert "0.10000000" in literal
