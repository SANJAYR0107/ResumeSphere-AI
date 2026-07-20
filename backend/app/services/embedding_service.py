"""
embedding_service.py  —  Phase 3 Sentence Embedding Service

Purpose
-------
Generate dense vector representations (embeddings) of resume text using a
pretrained sentence-transformer model.  These embeddings power semantic
search, resume ranking, and similarity scoring in Phase 4+.

Model
-----
``sentence-transformers/all-MiniLM-L6-v2``
  - Embedding dimension : 384
  - Max input tokens    : 256 (longer text is automatically truncated)
  - Size on disk        : ~90 MB
  - Inference time      : ~20–50 ms on CPU for typical resume text

Singleton strategy
------------------
The ``SentenceTransformer`` model is heavy to initialise (~1–2 s).  Loading
it on every request is unacceptable.  This module uses a lazy singleton:

  • ``load_model()``   — called once during FastAPI startup (lifespan).
  • ``get_embedding()`` — assumes the model is already loaded; raises if not.

This guarantees zero model-load overhead on the request path.

API surface
-----------
  load_model()       → None              (call once at startup)
  get_embedding(str) → EmbeddingResult   (call per request)
  is_loaded()        → bool              (health-check helper)

Inputs
------
text : str
    Preprocessed resume text.  Typically 500–5000 characters.

Outputs
-------
EmbeddingResult (TypedDict)
  ``dimension``      (int)         — vector dimensionality (384)
  ``model_name``     (str)         — HuggingFace model identifier
  ``text_length``    (int)         — character length of the encoded text

Note: The raw embedding vector is NOT included in the TypedDict.
The vector is stored internally and available via ``get_raw_vector()``
for Phase 4 similarity computation.  It is never serialised into API
responses to avoid 384-float JSON payloads on every call.

Exceptions
----------
RuntimeError
    Raised by ``get_embedding()`` if ``load_model()`` has not been called.
RuntimeError
    Raised by ``load_model()`` if the HuggingFace model cannot be downloaded
    or loaded (e.g. no internet, corrupted cache).

Complexity
----------
load_model   : O(model_size) — one-time cost
get_embedding: O(T) where T = number of tokens in the input text
"""

import logging
from typing import TYPE_CHECKING, Optional, TypedDict

import numpy as np

from backend.app.config import EMBEDDING_MODEL_NAME

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Types
# ---------------------------------------------------------------------------

class EmbeddingResult(TypedDict):
    """Metadata about a generated sentence embedding.

    The raw vector is intentionally excluded from this TypedDict.
    Retrieve it via :func:`get_raw_vector` when needed for similarity
    computation.
    """
    dimension: int
    model_name: str
    text_length: int


# ---------------------------------------------------------------------------
# Singleton state
# ---------------------------------------------------------------------------

_model: Optional["SentenceTransformer"] = None          # SentenceTransformer instance (set by load_model)
_last_vector: Optional[np.ndarray] = None  # Most recently generated vector


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_model() -> None:
    """Load the sentence-transformer model into memory.

    This function must be called **once** during application startup
    (e.g. inside the FastAPI ``lifespan`` context manager).  Calling it
    multiple times is safe — it is idempotent.

    Raises
    ------
    RuntimeError
        If the model cannot be loaded from HuggingFace Hub or local cache.
    """
    global _model  # noqa: PLW0603

    if _model is not None:
        logger.info(
            "EmbeddingService: model '%s' already loaded — skipping",
            EMBEDDING_MODEL_NAME,
        )
        return

    try:
        from sentence_transformers import SentenceTransformer  # lazy import
        logger.info(
            "EmbeddingService: loading model '%s' …", EMBEDDING_MODEL_NAME
        )
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        _model = model
        dim: int = 0  # will be overwritten; default silences Pylance "possibly unbound"
        try:
            dim = int(model.get_embedding_dimension() or 0)  # type: ignore
        except AttributeError:
            dim = int(model.get_sentence_embedding_dimension() or 0)  # type: ignore
        logger.info(
            "EmbeddingService: model loaded — dimension=%d", dim
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load embedding model '{EMBEDDING_MODEL_NAME}': {exc}"
        ) from exc


def get_embedding(text: str) -> EmbeddingResult:
    """Generate a sentence embedding for the given text.

    Parameters
    ----------
    text : str
        Preprocessed resume text.  Empty strings are handled gracefully
        (returns a zero vector of the correct dimension).

    Returns
    -------
    EmbeddingResult
        Metadata about the generated embedding.  The raw vector is stored
        internally and retrievable via :func:`get_raw_vector`.

    Raises
    ------
    RuntimeError
        If ``load_model()`` has not been called before this function.
    """
    global _last_vector  # noqa: PLW0603

    model = _model
    if model is None:
        raise RuntimeError(
            "EmbeddingService: model is not loaded. "
            "Call load_model() during application startup."
        )

    dim: int = 0  # default; overwritten below — silences Pylance "possibly unbound"
    try:
        dim = int(model.get_embedding_dimension() or 0)  # type: ignore
    except AttributeError:
        dim = int(model.get_sentence_embedding_dimension() or 0)  # type: ignore

    if not text or not text.strip():
        logger.warning("EmbeddingService: received empty text — returning zero vector")
        _last_vector = np.zeros(dim, dtype=np.float32)
        return EmbeddingResult(
            dimension=dim,
            model_name=EMBEDDING_MODEL_NAME,
            text_length=0,
        )

    # Encode returns a numpy array of shape (dim,) for a single string
    vector: np.ndarray = model.encode(  # type: ignore
        text,
        convert_to_numpy=True,
        show_progress_bar=False,
        normalize_embeddings=True,   # unit-norm vectors → cosine = dot product
    )

    _last_vector = vector

    logger.debug(
        "EmbeddingService: generated embedding dim=%d for %d chars",
        len(vector),
        len(text),
    )

    return EmbeddingResult(
        dimension=len(vector),
        model_name=EMBEDDING_MODEL_NAME,
        text_length=len(text),
    )


def get_raw_vector() -> Optional[np.ndarray]:
    """Return the most recently generated embedding vector.

    This is intended for Phase 4 similarity computation (cosine similarity,
    nearest-neighbour search, etc.) and should NOT be serialised into API
    responses.

    Returns
    -------
    numpy.ndarray or None
        Shape ``(384,)`` float32 array, or ``None`` if no embedding has been
        generated in this process lifetime.
    """
    return _last_vector


def is_loaded() -> bool:
    """Return True if the model has been successfully loaded.

    Useful for health-check endpoints.

    Returns
    -------
    bool
    """
    return _model is not None


def get_model_dimension() -> int:
    """Return the embedding dimension of the loaded model.

    Returns
    -------
    int
        384 for all-MiniLM-L6-v2.

    Raises
    ------
    RuntimeError
        If the model is not yet loaded.
    """
    model = _model
    if model is None:
        raise RuntimeError("EmbeddingService: model not loaded.")
    try:
        return int(model.get_embedding_dimension() or 0)  # type: ignore
    except AttributeError:
        return int(model.get_sentence_embedding_dimension() or 0)  # type: ignore
