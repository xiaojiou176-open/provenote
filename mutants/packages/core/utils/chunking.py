"""
Chunking utilities for Notebooklab.

Provides content-type detection and smart text chunking for embedding operations.
Supports HTML, Markdown, and plain text with appropriate splitters for each type.

Key functions:
- detect_content_type(): Detects content type from file extension or content heuristics
- chunk_text(): Splits text into chunks using appropriate splitter for content type

Environment Variables:
    OPEN_NOTEBOOK_CHUNK_SIZE: Maximum chunk size in characters (default: 1200)
    OPEN_NOTEBOOK_CHUNK_OVERLAP: Overlap between chunks in characters (default: 15% of CHUNK_SIZE)
"""

import re
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

from langchain_text_splitters import (
    HTMLHeaderTextSplitter,
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from loguru import logger

from packages.core.settings import read_env
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"]  # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg=None):  # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os  # type: ignore

    mutant_under_test = os.environ["MUTANT_UNDER_TEST"]  # type: ignore
    if mutant_under_test == "fail":  # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException  # type: ignore

        raise MutmutProgrammaticFailException("Failed programmatically")  # type: ignore
    elif mutant_under_test == "stats":  # type: ignore
        from mutmut.__main__ import record_trampoline_hit  # type: ignore

        record_trampoline_hit(orig.__module__ + "." + orig.__name__)  # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs)  # type: ignore
        return result  # type: ignore
    prefix = orig.__module__ + "." + orig.__name__ + "__mutmut_"  # type: ignore
    if not mutant_under_test.startswith(prefix):  # type: ignore
        result = orig(*call_args, **call_kwargs)  # type: ignore
        return result  # type: ignore
    mutant_name = mutant_under_test.rpartition(".")[-1]  # type: ignore
    if self_arg is not None:  # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)  # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)  # type: ignore
    return result  # type: ignore


def _get_chunk_size() -> int:
    args = []  # type: ignore
    kwargs = {}  # type: ignore
    return _mutmut_trampoline(
        x__get_chunk_size__mutmut_orig,
        x__get_chunk_size__mutmut_mutants,
        args,
        kwargs,
        None,
    )


def x__get_chunk_size__mutmut_orig() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_1() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = None
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_2() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env(None)
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_3() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("XXOPEN_NOTEBOOK_CHUNK_SIZEXX")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_4() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("open_notebook_chunk_size")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_5() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = None
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_6() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = int(None)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_7() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size <= 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_8() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 101:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_9() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(None)
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_10() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 101
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_11() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size >= 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_12() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8193:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_13() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(None)
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_14() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(None)
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def x__get_chunk_size__mutmut_15() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(None)
    return 1200


def x__get_chunk_size__mutmut_16() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1201


x__get_chunk_size__mutmut_mutants: ClassVar[MutantDict] = {  # type: ignore
    "x__get_chunk_size__mutmut_1": x__get_chunk_size__mutmut_1,
    "x__get_chunk_size__mutmut_2": x__get_chunk_size__mutmut_2,
    "x__get_chunk_size__mutmut_3": x__get_chunk_size__mutmut_3,
    "x__get_chunk_size__mutmut_4": x__get_chunk_size__mutmut_4,
    "x__get_chunk_size__mutmut_5": x__get_chunk_size__mutmut_5,
    "x__get_chunk_size__mutmut_6": x__get_chunk_size__mutmut_6,
    "x__get_chunk_size__mutmut_7": x__get_chunk_size__mutmut_7,
    "x__get_chunk_size__mutmut_8": x__get_chunk_size__mutmut_8,
    "x__get_chunk_size__mutmut_9": x__get_chunk_size__mutmut_9,
    "x__get_chunk_size__mutmut_10": x__get_chunk_size__mutmut_10,
    "x__get_chunk_size__mutmut_11": x__get_chunk_size__mutmut_11,
    "x__get_chunk_size__mutmut_12": x__get_chunk_size__mutmut_12,
    "x__get_chunk_size__mutmut_13": x__get_chunk_size__mutmut_13,
    "x__get_chunk_size__mutmut_14": x__get_chunk_size__mutmut_14,
    "x__get_chunk_size__mutmut_15": x__get_chunk_size__mutmut_15,
    "x__get_chunk_size__mutmut_16": x__get_chunk_size__mutmut_16,
}
x__get_chunk_size__mutmut_orig.__name__ = "x__get_chunk_size"


def _get_chunk_overlap(chunk_size: int) -> int:
    args = [chunk_size]  # type: ignore
    kwargs = {}  # type: ignore
    return _mutmut_trampoline(
        x__get_chunk_overlap__mutmut_orig,
        x__get_chunk_overlap__mutmut_mutants,
        args,
        kwargs,
        None,
    )


def x__get_chunk_overlap__mutmut_orig(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_1(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = None
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_2(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env(None)
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_3(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("XXOPEN_NOTEBOOK_CHUNK_OVERLAPXX")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_4(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("open_notebook_chunk_overlap")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_5(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = None
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_6(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(None)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_7(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap <= 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_8(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 1:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_9(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(None)
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_10(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 1
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_11(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap > chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_12(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(None)
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_13(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(None)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_14(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size / 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_15(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 1.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_16(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(None)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_17(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size / 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_18(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 1.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_19(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(None)
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_20(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(None)
    return int(chunk_size * 0.15)


def x__get_chunk_overlap__mutmut_21(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(None)


def x__get_chunk_overlap__mutmut_22(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size / 0.15)


def x__get_chunk_overlap__mutmut_23(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 1.15)


x__get_chunk_overlap__mutmut_mutants: ClassVar[MutantDict] = {  # type: ignore
    "x__get_chunk_overlap__mutmut_1": x__get_chunk_overlap__mutmut_1,
    "x__get_chunk_overlap__mutmut_2": x__get_chunk_overlap__mutmut_2,
    "x__get_chunk_overlap__mutmut_3": x__get_chunk_overlap__mutmut_3,
    "x__get_chunk_overlap__mutmut_4": x__get_chunk_overlap__mutmut_4,
    "x__get_chunk_overlap__mutmut_5": x__get_chunk_overlap__mutmut_5,
    "x__get_chunk_overlap__mutmut_6": x__get_chunk_overlap__mutmut_6,
    "x__get_chunk_overlap__mutmut_7": x__get_chunk_overlap__mutmut_7,
    "x__get_chunk_overlap__mutmut_8": x__get_chunk_overlap__mutmut_8,
    "x__get_chunk_overlap__mutmut_9": x__get_chunk_overlap__mutmut_9,
    "x__get_chunk_overlap__mutmut_10": x__get_chunk_overlap__mutmut_10,
    "x__get_chunk_overlap__mutmut_11": x__get_chunk_overlap__mutmut_11,
    "x__get_chunk_overlap__mutmut_12": x__get_chunk_overlap__mutmut_12,
    "x__get_chunk_overlap__mutmut_13": x__get_chunk_overlap__mutmut_13,
    "x__get_chunk_overlap__mutmut_14": x__get_chunk_overlap__mutmut_14,
    "x__get_chunk_overlap__mutmut_15": x__get_chunk_overlap__mutmut_15,
    "x__get_chunk_overlap__mutmut_16": x__get_chunk_overlap__mutmut_16,
    "x__get_chunk_overlap__mutmut_17": x__get_chunk_overlap__mutmut_17,
    "x__get_chunk_overlap__mutmut_18": x__get_chunk_overlap__mutmut_18,
    "x__get_chunk_overlap__mutmut_19": x__get_chunk_overlap__mutmut_19,
    "x__get_chunk_overlap__mutmut_20": x__get_chunk_overlap__mutmut_20,
    "x__get_chunk_overlap__mutmut_21": x__get_chunk_overlap__mutmut_21,
    "x__get_chunk_overlap__mutmut_22": x__get_chunk_overlap__mutmut_22,
    "x__get_chunk_overlap__mutmut_23": x__get_chunk_overlap__mutmut_23,
}
x__get_chunk_overlap__mutmut_orig.__name__ = "x__get_chunk_overlap"


# Constants (computed at import time from environment variables)
CHUNK_SIZE = _get_chunk_size()
CHUNK_OVERLAP = _get_chunk_overlap(CHUNK_SIZE)
HIGH_CONFIDENCE_THRESHOLD = 0.8  # Threshold for heuristics to override extension

logger.debug(
    f"Chunking configuration: CHUNK_SIZE={CHUNK_SIZE}, CHUNK_OVERLAP={CHUNK_OVERLAP}"
)


class ContentType(Enum):
    """Content type for chunking strategy selection."""

    HTML = "html"
    MARKDOWN = "markdown"
    PLAIN = "plain"


# File extension mappings
_EXTENSION_TO_CONTENT_TYPE = {
    # HTML
    ".html": ContentType.HTML,
    ".htm": ContentType.HTML,
    ".xhtml": ContentType.HTML,
    # Markdown
    ".md": ContentType.MARKDOWN,
    ".markdown": ContentType.MARKDOWN,
    ".mdown": ContentType.MARKDOWN,
    ".mkd": ContentType.MARKDOWN,
    # Plain text (explicit)
    ".txt": ContentType.PLAIN,
    ".text": ContentType.PLAIN,
    # Code files (treat as plain)
    ".py": ContentType.PLAIN,
    ".js": ContentType.PLAIN,
    ".ts": ContentType.PLAIN,
    ".java": ContentType.PLAIN,
    ".c": ContentType.PLAIN,
    ".cpp": ContentType.PLAIN,
    ".go": ContentType.PLAIN,
    ".rs": ContentType.PLAIN,
    ".rb": ContentType.PLAIN,
    ".php": ContentType.PLAIN,
    ".sh": ContentType.PLAIN,
    ".bash": ContentType.PLAIN,
    ".zsh": ContentType.PLAIN,
    ".sql": ContentType.PLAIN,
    ".json": ContentType.PLAIN,
    ".yaml": ContentType.PLAIN,
    ".yml": ContentType.PLAIN,
    ".xml": ContentType.PLAIN,
    ".csv": ContentType.PLAIN,
    ".tsv": ContentType.PLAIN,
}


def detect_content_type_from_extension(
    file_path: Optional[str],
) -> Optional[ContentType]:
    args = [file_path]  # type: ignore
    kwargs = {}  # type: ignore
    return _mutmut_trampoline(
        x_detect_content_type_from_extension__mutmut_orig,
        x_detect_content_type_from_extension__mutmut_mutants,
        args,
        kwargs,
        None,
    )


def x_detect_content_type_from_extension__mutmut_orig(
    file_path: Optional[str],
) -> Optional[ContentType]:
    """
    Detect content type from file extension.

    Args:
        file_path: Path to the file (can be full path or just filename)

    Returns:
        ContentType if extension is recognized, None otherwise
    """
    if not file_path:
        return None

    try:
        extension = Path(file_path).suffix.lower()
        return _EXTENSION_TO_CONTENT_TYPE.get(extension)
    except Exception:
        return None


def x_detect_content_type_from_extension__mutmut_1(
    file_path: Optional[str],
) -> Optional[ContentType]:
    """
    Detect content type from file extension.

    Args:
        file_path: Path to the file (can be full path or just filename)

    Returns:
        ContentType if extension is recognized, None otherwise
    """
    if file_path:
        return None

    try:
        extension = Path(file_path).suffix.lower()
        return _EXTENSION_TO_CONTENT_TYPE.get(extension)
    except Exception:
        return None


def x_detect_content_type_from_extension__mutmut_2(
    file_path: Optional[str],
) -> Optional[ContentType]:
    """
    Detect content type from file extension.

    Args:
        file_path: Path to the file (can be full path or just filename)

    Returns:
        ContentType if extension is recognized, None otherwise
    """
    if not file_path:
        return None

    try:
        extension = None
        return _EXTENSION_TO_CONTENT_TYPE.get(extension)
    except Exception:
        return None


def x_detect_content_type_from_extension__mutmut_3(
    file_path: Optional[str],
) -> Optional[ContentType]:
    """
    Detect content type from file extension.

    Args:
        file_path: Path to the file (can be full path or just filename)

    Returns:
        ContentType if extension is recognized, None otherwise
    """
    if not file_path:
        return None

    try:
        extension = Path(file_path).suffix.upper()
        return _EXTENSION_TO_CONTENT_TYPE.get(extension)
    except Exception:
        return None


def x_detect_content_type_from_extension__mutmut_4(
    file_path: Optional[str],
) -> Optional[ContentType]:
    """
    Detect content type from file extension.

    Args:
        file_path: Path to the file (can be full path or just filename)

    Returns:
        ContentType if extension is recognized, None otherwise
    """
    if not file_path:
        return None

    try:
        extension = Path(None).suffix.lower()
        return _EXTENSION_TO_CONTENT_TYPE.get(extension)
    except Exception:
        return None


def x_detect_content_type_from_extension__mutmut_5(
    file_path: Optional[str],
) -> Optional[ContentType]:
    """
    Detect content type from file extension.

    Args:
        file_path: Path to the file (can be full path or just filename)

    Returns:
        ContentType if extension is recognized, None otherwise
    """
    if not file_path:
        return None

    try:
        extension = Path(file_path).suffix.lower()
        return _EXTENSION_TO_CONTENT_TYPE.get(None)
    except Exception:
        return None


x_detect_content_type_from_extension__mutmut_mutants: ClassVar[MutantDict] = {  # type: ignore
    "x_detect_content_type_from_extension__mutmut_1": x_detect_content_type_from_extension__mutmut_1,
    "x_detect_content_type_from_extension__mutmut_2": x_detect_content_type_from_extension__mutmut_2,
    "x_detect_content_type_from_extension__mutmut_3": x_detect_content_type_from_extension__mutmut_3,
    "x_detect_content_type_from_extension__mutmut_4": x_detect_content_type_from_extension__mutmut_4,
    "x_detect_content_type_from_extension__mutmut_5": x_detect_content_type_from_extension__mutmut_5,
}
x_detect_content_type_from_extension__mutmut_orig.__name__ = (
    "x_detect_content_type_from_extension"
)


def detect_content_type_from_heuristics(text: str) -> Tuple[ContentType, float]:
    args = [text]  # type: ignore
    kwargs = {}  # type: ignore
    return _mutmut_trampoline(
        x_detect_content_type_from_heuristics__mutmut_orig,
        x_detect_content_type_from_heuristics__mutmut_mutants,
        args,
        kwargs,
        None,
    )


def x_detect_content_type_from_heuristics__mutmut_orig(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_1(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text and len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_2(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_3(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) <= 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_4(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 11:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_5(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 1.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_6(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = None

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_7(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5001]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_8(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = None
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_9(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(None)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_10(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score > HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_11(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = None

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_12(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(None)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_13(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score or html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_14(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score >= markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_15(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score >= 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_16(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 1.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_17(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score >= 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_18(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 1.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def x_detect_content_type_from_heuristics__mutmut_19(
    text: str,
) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 1.6


x_detect_content_type_from_heuristics__mutmut_mutants: ClassVar[MutantDict] = {  # type: ignore
    "x_detect_content_type_from_heuristics__mutmut_1": x_detect_content_type_from_heuristics__mutmut_1,
    "x_detect_content_type_from_heuristics__mutmut_2": x_detect_content_type_from_heuristics__mutmut_2,
    "x_detect_content_type_from_heuristics__mutmut_3": x_detect_content_type_from_heuristics__mutmut_3,
    "x_detect_content_type_from_heuristics__mutmut_4": x_detect_content_type_from_heuristics__mutmut_4,
    "x_detect_content_type_from_heuristics__mutmut_5": x_detect_content_type_from_heuristics__mutmut_5,
    "x_detect_content_type_from_heuristics__mutmut_6": x_detect_content_type_from_heuristics__mutmut_6,
    "x_detect_content_type_from_heuristics__mutmut_7": x_detect_content_type_from_heuristics__mutmut_7,
    "x_detect_content_type_from_heuristics__mutmut_8": x_detect_content_type_from_heuristics__mutmut_8,
    "x_detect_content_type_from_heuristics__mutmut_9": x_detect_content_type_from_heuristics__mutmut_9,
    "x_detect_content_type_from_heuristics__mutmut_10": x_detect_content_type_from_heuristics__mutmut_10,
    "x_detect_content_type_from_heuristics__mutmut_11": x_detect_content_type_from_heuristics__mutmut_11,
    "x_detect_content_type_from_heuristics__mutmut_12": x_detect_content_type_from_heuristics__mutmut_12,
    "x_detect_content_type_from_heuristics__mutmut_13": x_detect_content_type_from_heuristics__mutmut_13,
    "x_detect_content_type_from_heuristics__mutmut_14": x_detect_content_type_from_heuristics__mutmut_14,
    "x_detect_content_type_from_heuristics__mutmut_15": x_detect_content_type_from_heuristics__mutmut_15,
    "x_detect_content_type_from_heuristics__mutmut_16": x_detect_content_type_from_heuristics__mutmut_16,
    "x_detect_content_type_from_heuristics__mutmut_17": x_detect_content_type_from_heuristics__mutmut_17,
    "x_detect_content_type_from_heuristics__mutmut_18": x_detect_content_type_from_heuristics__mutmut_18,
    "x_detect_content_type_from_heuristics__mutmut_19": x_detect_content_type_from_heuristics__mutmut_19,
}
x_detect_content_type_from_heuristics__mutmut_orig.__name__ = (
    "x_detect_content_type_from_heuristics"
)


def _calculate_html_score(text: str) -> float:
    args = [text]  # type: ignore
    kwargs = {}  # type: ignore
    return _mutmut_trampoline(
        x__calculate_html_score__mutmut_orig,
        x__calculate_html_score__mutmut_mutants,
        args,
        kwargs,
        None,
    )


def x__calculate_html_score__mutmut_orig(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_1(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = None
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_2(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.upper()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_3(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = None

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_4(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("XX<headXX", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_5(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<HEAD", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_6(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "XX<bodyXX", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_7(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<BODY", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_8(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "XX<divXX", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_9(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<DIV", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_10(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "XX<spanXX", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_11(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<SPAN", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_12(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "XX<p>XX", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_13(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<P>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_14(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "XX<tableXX", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_15(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<TABLE", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_16(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "XX<formXX")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_17(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<FORM")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_18(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = None
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_19(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 1.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_20(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "XX<!doctype htmlXX" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_21(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!DOCTYPE HTML" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_22(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" not in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_23(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 1.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_24(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = None
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_25(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 1.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_26(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(None, normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_27(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", None) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_28(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_29(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = (
        0.3
        if re.search(
            r"<html[\s>]",
        )
        else 0.0
    )
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_30(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"XX<html[\s>]XX", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_31(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<HTML[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_32(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 1.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_33(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = None
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_34(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) - int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_35(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(None) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_36(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score >= 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_37(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 1.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_38(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(None)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_39(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score >= 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_40(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 1.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_41(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = None
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_42(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(None)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_43(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag not in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_44(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = None
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_45(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 + strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_46(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 6 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_47(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = None
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_48(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) / 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_49(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(None, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_50(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, None) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_51(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_52(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = (
        min(
            structural_hits,
        )
        * 0.1
    )
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_53(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 1.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_54(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = None
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_55(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 1.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_56(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(None, normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_57(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", None) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_58(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_59(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = (
        0.15
        if re.search(
            r"<h[1-6][\s>]",
        )
        else 0.0
    )
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_60(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"XX<h[1-6][\s>]XX", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_61(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<H[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_62(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 1.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_63(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = None

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_64(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 1.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_65(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(None, text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_66(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", None) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_67(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_68(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = (
        0.1
        if re.search(
            r"</\w+>",
        )
        else 0.0
    )

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_69(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"XX</\w+>XX", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_70(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 1.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_71(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = None
    return min(score, 1.0)


def x__calculate_html_score__mutmut_72(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        - closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_73(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        - header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_74(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        - structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_75(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        - html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def x__calculate_html_score__mutmut_76(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(None, 1.0)


def x__calculate_html_score__mutmut_77(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, None)


def x__calculate_html_score__mutmut_78(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(1.0)


def x__calculate_html_score__mutmut_79(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(
        score,
    )


def x__calculate_html_score__mutmut_80(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 2.0)


x__calculate_html_score__mutmut_mutants: ClassVar[MutantDict] = {  # type: ignore
    "x__calculate_html_score__mutmut_1": x__calculate_html_score__mutmut_1,
    "x__calculate_html_score__mutmut_2": x__calculate_html_score__mutmut_2,
    "x__calculate_html_score__mutmut_3": x__calculate_html_score__mutmut_3,
    "x__calculate_html_score__mutmut_4": x__calculate_html_score__mutmut_4,
    "x__calculate_html_score__mutmut_5": x__calculate_html_score__mutmut_5,
    "x__calculate_html_score__mutmut_6": x__calculate_html_score__mutmut_6,
    "x__calculate_html_score__mutmut_7": x__calculate_html_score__mutmut_7,
    "x__calculate_html_score__mutmut_8": x__calculate_html_score__mutmut_8,
    "x__calculate_html_score__mutmut_9": x__calculate_html_score__mutmut_9,
    "x__calculate_html_score__mutmut_10": x__calculate_html_score__mutmut_10,
    "x__calculate_html_score__mutmut_11": x__calculate_html_score__mutmut_11,
    "x__calculate_html_score__mutmut_12": x__calculate_html_score__mutmut_12,
    "x__calculate_html_score__mutmut_13": x__calculate_html_score__mutmut_13,
    "x__calculate_html_score__mutmut_14": x__calculate_html_score__mutmut_14,
    "x__calculate_html_score__mutmut_15": x__calculate_html_score__mutmut_15,
    "x__calculate_html_score__mutmut_16": x__calculate_html_score__mutmut_16,
    "x__calculate_html_score__mutmut_17": x__calculate_html_score__mutmut_17,
    "x__calculate_html_score__mutmut_18": x__calculate_html_score__mutmut_18,
    "x__calculate_html_score__mutmut_19": x__calculate_html_score__mutmut_19,
    "x__calculate_html_score__mutmut_20": x__calculate_html_score__mutmut_20,
    "x__calculate_html_score__mutmut_21": x__calculate_html_score__mutmut_21,
    "x__calculate_html_score__mutmut_22": x__calculate_html_score__mutmut_22,
    "x__calculate_html_score__mutmut_23": x__calculate_html_score__mutmut_23,
    "x__calculate_html_score__mutmut_24": x__calculate_html_score__mutmut_24,
    "x__calculate_html_score__mutmut_25": x__calculate_html_score__mutmut_25,
    "x__calculate_html_score__mutmut_26": x__calculate_html_score__mutmut_26,
    "x__calculate_html_score__mutmut_27": x__calculate_html_score__mutmut_27,
    "x__calculate_html_score__mutmut_28": x__calculate_html_score__mutmut_28,
    "x__calculate_html_score__mutmut_29": x__calculate_html_score__mutmut_29,
    "x__calculate_html_score__mutmut_30": x__calculate_html_score__mutmut_30,
    "x__calculate_html_score__mutmut_31": x__calculate_html_score__mutmut_31,
    "x__calculate_html_score__mutmut_32": x__calculate_html_score__mutmut_32,
    "x__calculate_html_score__mutmut_33": x__calculate_html_score__mutmut_33,
    "x__calculate_html_score__mutmut_34": x__calculate_html_score__mutmut_34,
    "x__calculate_html_score__mutmut_35": x__calculate_html_score__mutmut_35,
    "x__calculate_html_score__mutmut_36": x__calculate_html_score__mutmut_36,
    "x__calculate_html_score__mutmut_37": x__calculate_html_score__mutmut_37,
    "x__calculate_html_score__mutmut_38": x__calculate_html_score__mutmut_38,
    "x__calculate_html_score__mutmut_39": x__calculate_html_score__mutmut_39,
    "x__calculate_html_score__mutmut_40": x__calculate_html_score__mutmut_40,
    "x__calculate_html_score__mutmut_41": x__calculate_html_score__mutmut_41,
    "x__calculate_html_score__mutmut_42": x__calculate_html_score__mutmut_42,
    "x__calculate_html_score__mutmut_43": x__calculate_html_score__mutmut_43,
    "x__calculate_html_score__mutmut_44": x__calculate_html_score__mutmut_44,
    "x__calculate_html_score__mutmut_45": x__calculate_html_score__mutmut_45,
    "x__calculate_html_score__mutmut_46": x__calculate_html_score__mutmut_46,
    "x__calculate_html_score__mutmut_47": x__calculate_html_score__mutmut_47,
    "x__calculate_html_score__mutmut_48": x__calculate_html_score__mutmut_48,
    "x__calculate_html_score__mutmut_49": x__calculate_html_score__mutmut_49,
    "x__calculate_html_score__mutmut_50": x__calculate_html_score__mutmut_50,
    "x__calculate_html_score__mutmut_51": x__calculate_html_score__mutmut_51,
    "x__calculate_html_score__mutmut_52": x__calculate_html_score__mutmut_52,
    "x__calculate_html_score__mutmut_53": x__calculate_html_score__mutmut_53,
    "x__calculate_html_score__mutmut_54": x__calculate_html_score__mutmut_54,
    "x__calculate_html_score__mutmut_55": x__calculate_html_score__mutmut_55,
    "x__calculate_html_score__mutmut_56": x__calculate_html_score__mutmut_56,
    "x__calculate_html_score__mutmut_57": x__calculate_html_score__mutmut_57,
    "x__calculate_html_score__mutmut_58": x__calculate_html_score__mutmut_58,
    "x__calculate_html_score__mutmut_59": x__calculate_html_score__mutmut_59,
    "x__calculate_html_score__mutmut_60": x__calculate_html_score__mutmut_60,
    "x__calculate_html_score__mutmut_61": x__calculate_html_score__mutmut_61,
    "x__calculate_html_score__mutmut_62": x__calculate_html_score__mutmut_62,
    "x__calculate_html_score__mutmut_63": x__calculate_html_score__mutmut_63,
    "x__calculate_html_score__mutmut_64": x__calculate_html_score__mutmut_64,
    "x__calculate_html_score__mutmut_65": x__calculate_html_score__mutmut_65,
    "x__calculate_html_score__mutmut_66": x__calculate_html_score__mutmut_66,
    "x__calculate_html_score__mutmut_67": x__calculate_html_score__mutmut_67,
    "x__calculate_html_score__mutmut_68": x__calculate_html_score__mutmut_68,
    "x__calculate_html_score__mutmut_69": x__calculate_html_score__mutmut_69,
    "x__calculate_html_score__mutmut_70": x__calculate_html_score__mutmut_70,
    "x__calculate_html_score__mutmut_71": x__calculate_html_score__mutmut_71,
    "x__calculate_html_score__mutmut_72": x__calculate_html_score__mutmut_72,
    "x__calculate_html_score__mutmut_73": x__calculate_html_score__mutmut_73,
    "x__calculate_html_score__mutmut_74": x__calculate_html_score__mutmut_74,
    "x__calculate_html_score__mutmut_75": x__calculate_html_score__mutmut_75,
    "x__calculate_html_score__mutmut_76": x__calculate_html_score__mutmut_76,
    "x__calculate_html_score__mutmut_77": x__calculate_html_score__mutmut_77,
    "x__calculate_html_score__mutmut_78": x__calculate_html_score__mutmut_78,
    "x__calculate_html_score__mutmut_79": x__calculate_html_score__mutmut_79,
    "x__calculate_html_score__mutmut_80": x__calculate_html_score__mutmut_80,
}
x__calculate_html_score__mutmut_orig.__name__ = "x__calculate_html_score"


def _calculate_markdown_score(text: str) -> float:
    args = [text]  # type: ignore
    kwargs = {}  # type: ignore
    return _mutmut_trampoline(
        x__calculate_markdown_score__mutmut_orig,
        x__calculate_markdown_score__mutmut_mutants,
        args,
        kwargs,
        None,
    )


def x__calculate_markdown_score__mutmut_orig(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_1(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = None
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_2(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = None
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_3(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = None
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_4(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches = len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_5(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches -= len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_6(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = None
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_7(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 1.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_8(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches > 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_9(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 4 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_10(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 1.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_11(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches > 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_12(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 2 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_13(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 1.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_14(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = None
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_15(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 1.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_16(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches > 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_17(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 3 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_18(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 1.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_19(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches > 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_20(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 2 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_21(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 1.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_22(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = None
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_23(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 1.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_24(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(None, text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_25(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", None, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_26(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, None) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_27(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_28(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_29(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = (
        0.2
        if re.search(
            r"^```",
            text,
        )
        else 0.0
    )
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_30(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"XX^```XX", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_31(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 1.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_32(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = None
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_33(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 1.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_34(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(None, text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_35(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", None) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_36(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_37(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = (
        0.1
        if re.search(
            r"`[^`]+`",
        )
        else 0.0
    )
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_38(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"XX`[^`]+`XX", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_39(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 1.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_40(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = None
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_41(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 1.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_42(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches > 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_43(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 4 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_44(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 1.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_45(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches > 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_46(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 2 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_47(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 1.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_48(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = None
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_49(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 1.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_50(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(None, text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_51(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", None) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_52(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_53(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = (
        0.1
        if re.search(
            r"\*\*.+?\*\*|__.+?__",
        )
        else 0.0
    )
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_54(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"XX\*\*.+?\*\*|__.+?__XX", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_55(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 1.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_56(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = None

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_57(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 1.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_58(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(None, text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_59(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", None, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_60(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, None) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_61(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_62(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_63(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = (
        0.1
        if re.search(
            r"^>\s+",
            text,
        )
        else 0.0
    )

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_64(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"XX^>\s+XX", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_65(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 1.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_66(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = None
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_67(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        - blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_68(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        - emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_69(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        - list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_70(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        - inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_71(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        - code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_72(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        - link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def x__calculate_markdown_score__mutmut_73(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(None, 1.0)


def x__calculate_markdown_score__mutmut_74(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, None)


def x__calculate_markdown_score__mutmut_75(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(1.0)


def x__calculate_markdown_score__mutmut_76(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(
        score,
    )


def x__calculate_markdown_score__mutmut_77(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[.+?\]\(.+?\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 2.0)


x__calculate_markdown_score__mutmut_mutants: ClassVar[MutantDict] = {  # type: ignore
    "x__calculate_markdown_score__mutmut_1": x__calculate_markdown_score__mutmut_1,
    "x__calculate_markdown_score__mutmut_2": x__calculate_markdown_score__mutmut_2,
    "x__calculate_markdown_score__mutmut_3": x__calculate_markdown_score__mutmut_3,
    "x__calculate_markdown_score__mutmut_4": x__calculate_markdown_score__mutmut_4,
    "x__calculate_markdown_score__mutmut_5": x__calculate_markdown_score__mutmut_5,
    "x__calculate_markdown_score__mutmut_6": x__calculate_markdown_score__mutmut_6,
    "x__calculate_markdown_score__mutmut_7": x__calculate_markdown_score__mutmut_7,
    "x__calculate_markdown_score__mutmut_8": x__calculate_markdown_score__mutmut_8,
    "x__calculate_markdown_score__mutmut_9": x__calculate_markdown_score__mutmut_9,
    "x__calculate_markdown_score__mutmut_10": x__calculate_markdown_score__mutmut_10,
    "x__calculate_markdown_score__mutmut_11": x__calculate_markdown_score__mutmut_11,
    "x__calculate_markdown_score__mutmut_12": x__calculate_markdown_score__mutmut_12,
    "x__calculate_markdown_score__mutmut_13": x__calculate_markdown_score__mutmut_13,
    "x__calculate_markdown_score__mutmut_14": x__calculate_markdown_score__mutmut_14,
    "x__calculate_markdown_score__mutmut_15": x__calculate_markdown_score__mutmut_15,
    "x__calculate_markdown_score__mutmut_16": x__calculate_markdown_score__mutmut_16,
    "x__calculate_markdown_score__mutmut_17": x__calculate_markdown_score__mutmut_17,
    "x__calculate_markdown_score__mutmut_18": x__calculate_markdown_score__mutmut_18,
    "x__calculate_markdown_score__mutmut_19": x__calculate_markdown_score__mutmut_19,
    "x__calculate_markdown_score__mutmut_20": x__calculate_markdown_score__mutmut_20,
    "x__calculate_markdown_score__mutmut_21": x__calculate_markdown_score__mutmut_21,
    "x__calculate_markdown_score__mutmut_22": x__calculate_markdown_score__mutmut_22,
    "x__calculate_markdown_score__mutmut_23": x__calculate_markdown_score__mutmut_23,
    "x__calculate_markdown_score__mutmut_24": x__calculate_markdown_score__mutmut_24,
    "x__calculate_markdown_score__mutmut_25": x__calculate_markdown_score__mutmut_25,
    "x__calculate_markdown_score__mutmut_26": x__calculate_markdown_score__mutmut_26,
    "x__calculate_markdown_score__mutmut_27": x__calculate_markdown_score__mutmut_27,
    "x__calculate_markdown_score__mutmut_28": x__calculate_markdown_score__mutmut_28,
    "x__calculate_markdown_score__mutmut_29": x__calculate_markdown_score__mutmut_29,
    "x__calculate_markdown_score__mutmut_30": x__calculate_markdown_score__mutmut_30,
    "x__calculate_markdown_score__mutmut_31": x__calculate_markdown_score__mutmut_31,
    "x__calculate_markdown_score__mutmut_32": x__calculate_markdown_score__mutmut_32,
    "x__calculate_markdown_score__mutmut_33": x__calculate_markdown_score__mutmut_33,
    "x__calculate_markdown_score__mutmut_34": x__calculate_markdown_score__mutmut_34,
    "x__calculate_markdown_score__mutmut_35": x__calculate_markdown_score__mutmut_35,
    "x__calculate_markdown_score__mutmut_36": x__calculate_markdown_score__mutmut_36,
    "x__calculate_markdown_score__mutmut_37": x__calculate_markdown_score__mutmut_37,
    "x__calculate_markdown_score__mutmut_38": x__calculate_markdown_score__mutmut_38,
    "x__calculate_markdown_score__mutmut_39": x__calculate_markdown_score__mutmut_39,
    "x__calculate_markdown_score__mutmut_40": x__calculate_markdown_score__mutmut_40,
    "x__calculate_markdown_score__mutmut_41": x__calculate_markdown_score__mutmut_41,
    "x__calculate_markdown_score__mutmut_42": x__calculate_markdown_score__mutmut_42,
    "x__calculate_markdown_score__mutmut_43": x__calculate_markdown_score__mutmut_43,
    "x__calculate_markdown_score__mutmut_44": x__calculate_markdown_score__mutmut_44,
    "x__calculate_markdown_score__mutmut_45": x__calculate_markdown_score__mutmut_45,
    "x__calculate_markdown_score__mutmut_46": x__calculate_markdown_score__mutmut_46,
    "x__calculate_markdown_score__mutmut_47": x__calculate_markdown_score__mutmut_47,
    "x__calculate_markdown_score__mutmut_48": x__calculate_markdown_score__mutmut_48,
    "x__calculate_markdown_score__mutmut_49": x__calculate_markdown_score__mutmut_49,
    "x__calculate_markdown_score__mutmut_50": x__calculate_markdown_score__mutmut_50,
    "x__calculate_markdown_score__mutmut_51": x__calculate_markdown_score__mutmut_51,
    "x__calculate_markdown_score__mutmut_52": x__calculate_markdown_score__mutmut_52,
    "x__calculate_markdown_score__mutmut_53": x__calculate_markdown_score__mutmut_53,
    "x__calculate_markdown_score__mutmut_54": x__calculate_markdown_score__mutmut_54,
    "x__calculate_markdown_score__mutmut_55": x__calculate_markdown_score__mutmut_55,
    "x__calculate_markdown_score__mutmut_56": x__calculate_markdown_score__mutmut_56,
    "x__calculate_markdown_score__mutmut_57": x__calculate_markdown_score__mutmut_57,
    "x__calculate_markdown_score__mutmut_58": x__calculate_markdown_score__mutmut_58,
    "x__calculate_markdown_score__mutmut_59": x__calculate_markdown_score__mutmut_59,
    "x__calculate_markdown_score__mutmut_60": x__calculate_markdown_score__mutmut_60,
    "x__calculate_markdown_score__mutmut_61": x__calculate_markdown_score__mutmut_61,
    "x__calculate_markdown_score__mutmut_62": x__calculate_markdown_score__mutmut_62,
    "x__calculate_markdown_score__mutmut_63": x__calculate_markdown_score__mutmut_63,
    "x__calculate_markdown_score__mutmut_64": x__calculate_markdown_score__mutmut_64,
    "x__calculate_markdown_score__mutmut_65": x__calculate_markdown_score__mutmut_65,
    "x__calculate_markdown_score__mutmut_66": x__calculate_markdown_score__mutmut_66,
    "x__calculate_markdown_score__mutmut_67": x__calculate_markdown_score__mutmut_67,
    "x__calculate_markdown_score__mutmut_68": x__calculate_markdown_score__mutmut_68,
    "x__calculate_markdown_score__mutmut_69": x__calculate_markdown_score__mutmut_69,
    "x__calculate_markdown_score__mutmut_70": x__calculate_markdown_score__mutmut_70,
    "x__calculate_markdown_score__mutmut_71": x__calculate_markdown_score__mutmut_71,
    "x__calculate_markdown_score__mutmut_72": x__calculate_markdown_score__mutmut_72,
    "x__calculate_markdown_score__mutmut_73": x__calculate_markdown_score__mutmut_73,
    "x__calculate_markdown_score__mutmut_74": x__calculate_markdown_score__mutmut_74,
    "x__calculate_markdown_score__mutmut_75": x__calculate_markdown_score__mutmut_75,
    "x__calculate_markdown_score__mutmut_76": x__calculate_markdown_score__mutmut_76,
    "x__calculate_markdown_score__mutmut_77": x__calculate_markdown_score__mutmut_77,
}
x__calculate_markdown_score__mutmut_orig.__name__ = "x__calculate_markdown_score"


def detect_content_type(text: str, file_path: Optional[str] = None) -> ContentType:
    args = [text, file_path]  # type: ignore
    kwargs = {}  # type: ignore
    return _mutmut_trampoline(
        x_detect_content_type__mutmut_orig,
        x_detect_content_type__mutmut_mutants,
        args,
        kwargs,
        None,
    )


def x_detect_content_type__mutmut_orig(
    text: str, file_path: Optional[str] = None
) -> ContentType:
    """
    Detect content type using file extension (primary) and heuristics (fallback).

    Strategy:
    1. If file extension is available and recognized, use it as primary
    2. If no extension or generic extension (.txt), use heuristics
    3. Heuristics can override extension only with very high confidence

    Args:
        text: The text content
        file_path: Optional file path for extension-based detection

    Returns:
        Detected ContentType
    """
    # Try extension-based detection first
    extension_type = detect_content_type_from_extension(file_path)

    # Get heuristic-based detection
    heuristic_type, confidence = detect_content_type_from_heuristics(text)

    # If no extension or generic extension, use heuristics
    if extension_type is None:
        logger.debug(
            f"No file extension, using heuristics: {heuristic_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        return heuristic_type

    # If extension suggests plain text but heuristics are very confident, override
    if extension_type == ContentType.PLAIN and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        logger.debug(
            f"Extension suggests plain, but heuristics override with "
            f"{heuristic_type.value} (confidence: {confidence:.2f})"
        )
        return heuristic_type

    # Otherwise trust the extension
    logger.debug(f"Using extension-based content type: {extension_type.value}")
    return extension_type


def x_detect_content_type__mutmut_1(
    text: str, file_path: Optional[str] = None
) -> ContentType:
    """
    Detect content type using file extension (primary) and heuristics (fallback).

    Strategy:
    1. If file extension is available and recognized, use it as primary
    2. If no extension or generic extension (.txt), use heuristics
    3. Heuristics can override extension only with very high confidence

    Args:
        text: The text content
        file_path: Optional file path for extension-based detection

    Returns:
        Detected ContentType
    """
    # Try extension-based detection first
    extension_type = None

    # Get heuristic-based detection
    heuristic_type, confidence = detect_content_type_from_heuristics(text)

    # If no extension or generic extension, use heuristics
    if extension_type is None:
        logger.debug(
            f"No file extension, using heuristics: {heuristic_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        return heuristic_type

    # If extension suggests plain text but heuristics are very confident, override
    if extension_type == ContentType.PLAIN and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        logger.debug(
            f"Extension suggests plain, but heuristics override with "
            f"{heuristic_type.value} (confidence: {confidence:.2f})"
        )
        return heuristic_type

    # Otherwise trust the extension
    logger.debug(f"Using extension-based content type: {extension_type.value}")
    return extension_type


def x_detect_content_type__mutmut_2(
    text: str, file_path: Optional[str] = None
) -> ContentType:
    """
    Detect content type using file extension (primary) and heuristics (fallback).

    Strategy:
    1. If file extension is available and recognized, use it as primary
    2. If no extension or generic extension (.txt), use heuristics
    3. Heuristics can override extension only with very high confidence

    Args:
        text: The text content
        file_path: Optional file path for extension-based detection

    Returns:
        Detected ContentType
    """
    # Try extension-based detection first
    extension_type = detect_content_type_from_extension(None)

    # Get heuristic-based detection
    heuristic_type, confidence = detect_content_type_from_heuristics(text)

    # If no extension or generic extension, use heuristics
    if extension_type is None:
        logger.debug(
            f"No file extension, using heuristics: {heuristic_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        return heuristic_type

    # If extension suggests plain text but heuristics are very confident, override
    if extension_type == ContentType.PLAIN and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        logger.debug(
            f"Extension suggests plain, but heuristics override with "
            f"{heuristic_type.value} (confidence: {confidence:.2f})"
        )
        return heuristic_type

    # Otherwise trust the extension
    logger.debug(f"Using extension-based content type: {extension_type.value}")
    return extension_type


def x_detect_content_type__mutmut_3(
    text: str, file_path: Optional[str] = None
) -> ContentType:
    """
    Detect content type using file extension (primary) and heuristics (fallback).

    Strategy:
    1. If file extension is available and recognized, use it as primary
    2. If no extension or generic extension (.txt), use heuristics
    3. Heuristics can override extension only with very high confidence

    Args:
        text: The text content
        file_path: Optional file path for extension-based detection

    Returns:
        Detected ContentType
    """
    # Try extension-based detection first
    extension_type = detect_content_type_from_extension(file_path)

    # Get heuristic-based detection
    heuristic_type, confidence = None

    # If no extension or generic extension, use heuristics
    if extension_type is None:
        logger.debug(
            f"No file extension, using heuristics: {heuristic_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        return heuristic_type

    # If extension suggests plain text but heuristics are very confident, override
    if extension_type == ContentType.PLAIN and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        logger.debug(
            f"Extension suggests plain, but heuristics override with "
            f"{heuristic_type.value} (confidence: {confidence:.2f})"
        )
        return heuristic_type

    # Otherwise trust the extension
    logger.debug(f"Using extension-based content type: {extension_type.value}")
    return extension_type


def x_detect_content_type__mutmut_4(
    text: str, file_path: Optional[str] = None
) -> ContentType:
    """
    Detect content type using file extension (primary) and heuristics (fallback).

    Strategy:
    1. If file extension is available and recognized, use it as primary
    2. If no extension or generic extension (.txt), use heuristics
    3. Heuristics can override extension only with very high confidence

    Args:
        text: The text content
        file_path: Optional file path for extension-based detection

    Returns:
        Detected ContentType
    """
    # Try extension-based detection first
    extension_type = detect_content_type_from_extension(file_path)

    # Get heuristic-based detection
    heuristic_type, confidence = detect_content_type_from_heuristics(None)

    # If no extension or generic extension, use heuristics
    if extension_type is None:
        logger.debug(
            f"No file extension, using heuristics: {heuristic_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        return heuristic_type

    # If extension suggests plain text but heuristics are very confident, override
    if extension_type == ContentType.PLAIN and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        logger.debug(
            f"Extension suggests plain, but heuristics override with "
            f"{heuristic_type.value} (confidence: {confidence:.2f})"
        )
        return heuristic_type

    # Otherwise trust the extension
    logger.debug(f"Using extension-based content type: {extension_type.value}")
    return extension_type


def x_detect_content_type__mutmut_5(
    text: str, file_path: Optional[str] = None
) -> ContentType:
    """
    Detect content type using file extension (primary) and heuristics (fallback).

    Strategy:
    1. If file extension is available and recognized, use it as primary
    2. If no extension or generic extension (.txt), use heuristics
    3. Heuristics can override extension only with very high confidence

    Args:
        text: The text content
        file_path: Optional file path for extension-based detection

    Returns:
        Detected ContentType
    """
    # Try extension-based detection first
    extension_type = detect_content_type_from_extension(file_path)

    # Get heuristic-based detection
    heuristic_type, confidence = detect_content_type_from_heuristics(text)

    # If no extension or generic extension, use heuristics
    if extension_type is not None:
        logger.debug(
            f"No file extension, using heuristics: {heuristic_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        return heuristic_type

    # If extension suggests plain text but heuristics are very confident, override
    if extension_type == ContentType.PLAIN and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        logger.debug(
            f"Extension suggests plain, but heuristics override with "
            f"{heuristic_type.value} (confidence: {confidence:.2f})"
        )
        return heuristic_type

    # Otherwise trust the extension
    logger.debug(f"Using extension-based content type: {extension_type.value}")
    return extension_type


def x_detect_content_type__mutmut_6(
    text: str, file_path: Optional[str] = None
) -> ContentType:
    """
    Detect content type using file extension (primary) and heuristics (fallback).

    Strategy:
    1. If file extension is available and recognized, use it as primary
    2. If no extension or generic extension (.txt), use heuristics
    3. Heuristics can override extension only with very high confidence

    Args:
        text: The text content
        file_path: Optional file path for extension-based detection

    Returns:
        Detected ContentType
    """
    # Try extension-based detection first
    extension_type = detect_content_type_from_extension(file_path)

    # Get heuristic-based detection
    heuristic_type, confidence = detect_content_type_from_heuristics(text)

    # If no extension or generic extension, use heuristics
    if extension_type is None:
        logger.debug(None)
        return heuristic_type

    # If extension suggests plain text but heuristics are very confident, override
    if extension_type == ContentType.PLAIN and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        logger.debug(
            f"Extension suggests plain, but heuristics override with "
            f"{heuristic_type.value} (confidence: {confidence:.2f})"
        )
        return heuristic_type

    # Otherwise trust the extension
    logger.debug(f"Using extension-based content type: {extension_type.value}")
    return extension_type


def x_detect_content_type__mutmut_7(
    text: str, file_path: Optional[str] = None
) -> ContentType:
    """
    Detect content type using file extension (primary) and heuristics (fallback).

    Strategy:
    1. If file extension is available and recognized, use it as primary
    2. If no extension or generic extension (.txt), use heuristics
    3. Heuristics can override extension only with very high confidence

    Args:
        text: The text content
        file_path: Optional file path for extension-based detection

    Returns:
        Detected ContentType
    """
    # Try extension-based detection first
    extension_type = detect_content_type_from_extension(file_path)

    # Get heuristic-based detection
    heuristic_type, confidence = detect_content_type_from_heuristics(text)

    # If no extension or generic extension, use heuristics
    if extension_type is None:
        logger.debug(
            f"No file extension, using heuristics: {heuristic_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        return heuristic_type

    # If extension suggests plain text but heuristics are very confident, override
    if extension_type == ContentType.PLAIN or confidence >= HIGH_CONFIDENCE_THRESHOLD:
        logger.debug(
            f"Extension suggests plain, but heuristics override with "
            f"{heuristic_type.value} (confidence: {confidence:.2f})"
        )
        return heuristic_type

    # Otherwise trust the extension
    logger.debug(f"Using extension-based content type: {extension_type.value}")
    return extension_type


def x_detect_content_type__mutmut_8(
    text: str, file_path: Optional[str] = None
) -> ContentType:
    """
    Detect content type using file extension (primary) and heuristics (fallback).

    Strategy:
    1. If file extension is available and recognized, use it as primary
    2. If no extension or generic extension (.txt), use heuristics
    3. Heuristics can override extension only with very high confidence

    Args:
        text: The text content
        file_path: Optional file path for extension-based detection

    Returns:
        Detected ContentType
    """
    # Try extension-based detection first
    extension_type = detect_content_type_from_extension(file_path)

    # Get heuristic-based detection
    heuristic_type, confidence = detect_content_type_from_heuristics(text)

    # If no extension or generic extension, use heuristics
    if extension_type is None:
        logger.debug(
            f"No file extension, using heuristics: {heuristic_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        return heuristic_type

    # If extension suggests plain text but heuristics are very confident, override
    if extension_type != ContentType.PLAIN and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        logger.debug(
            f"Extension suggests plain, but heuristics override with "
            f"{heuristic_type.value} (confidence: {confidence:.2f})"
        )
        return heuristic_type

    # Otherwise trust the extension
    logger.debug(f"Using extension-based content type: {extension_type.value}")
    return extension_type


def x_detect_content_type__mutmut_9(
    text: str, file_path: Optional[str] = None
) -> ContentType:
    """
    Detect content type using file extension (primary) and heuristics (fallback).

    Strategy:
    1. If file extension is available and recognized, use it as primary
    2. If no extension or generic extension (.txt), use heuristics
    3. Heuristics can override extension only with very high confidence

    Args:
        text: The text content
        file_path: Optional file path for extension-based detection

    Returns:
        Detected ContentType
    """
    # Try extension-based detection first
    extension_type = detect_content_type_from_extension(file_path)

    # Get heuristic-based detection
    heuristic_type, confidence = detect_content_type_from_heuristics(text)

    # If no extension or generic extension, use heuristics
    if extension_type is None:
        logger.debug(
            f"No file extension, using heuristics: {heuristic_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        return heuristic_type

    # If extension suggests plain text but heuristics are very confident, override
    if extension_type == ContentType.PLAIN and confidence > HIGH_CONFIDENCE_THRESHOLD:
        logger.debug(
            f"Extension suggests plain, but heuristics override with "
            f"{heuristic_type.value} (confidence: {confidence:.2f})"
        )
        return heuristic_type

    # Otherwise trust the extension
    logger.debug(f"Using extension-based content type: {extension_type.value}")
    return extension_type


def x_detect_content_type__mutmut_10(
    text: str, file_path: Optional[str] = None
) -> ContentType:
    """
    Detect content type using file extension (primary) and heuristics (fallback).

    Strategy:
    1. If file extension is available and recognized, use it as primary
    2. If no extension or generic extension (.txt), use heuristics
    3. Heuristics can override extension only with very high confidence

    Args:
        text: The text content
        file_path: Optional file path for extension-based detection

    Returns:
        Detected ContentType
    """
    # Try extension-based detection first
    extension_type = detect_content_type_from_extension(file_path)

    # Get heuristic-based detection
    heuristic_type, confidence = detect_content_type_from_heuristics(text)

    # If no extension or generic extension, use heuristics
    if extension_type is None:
        logger.debug(
            f"No file extension, using heuristics: {heuristic_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        return heuristic_type

    # If extension suggests plain text but heuristics are very confident, override
    if extension_type == ContentType.PLAIN and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        logger.debug(None)
        return heuristic_type

    # Otherwise trust the extension
    logger.debug(f"Using extension-based content type: {extension_type.value}")
    return extension_type


def x_detect_content_type__mutmut_11(
    text: str, file_path: Optional[str] = None
) -> ContentType:
    """
    Detect content type using file extension (primary) and heuristics (fallback).

    Strategy:
    1. If file extension is available and recognized, use it as primary
    2. If no extension or generic extension (.txt), use heuristics
    3. Heuristics can override extension only with very high confidence

    Args:
        text: The text content
        file_path: Optional file path for extension-based detection

    Returns:
        Detected ContentType
    """
    # Try extension-based detection first
    extension_type = detect_content_type_from_extension(file_path)

    # Get heuristic-based detection
    heuristic_type, confidence = detect_content_type_from_heuristics(text)

    # If no extension or generic extension, use heuristics
    if extension_type is None:
        logger.debug(
            f"No file extension, using heuristics: {heuristic_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        return heuristic_type

    # If extension suggests plain text but heuristics are very confident, override
    if extension_type == ContentType.PLAIN and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        logger.debug(
            f"Extension suggests plain, but heuristics override with "
            f"{heuristic_type.value} (confidence: {confidence:.2f})"
        )
        return heuristic_type

    # Otherwise trust the extension
    logger.debug(None)
    return extension_type


x_detect_content_type__mutmut_mutants: ClassVar[MutantDict] = {  # type: ignore
    "x_detect_content_type__mutmut_1": x_detect_content_type__mutmut_1,
    "x_detect_content_type__mutmut_2": x_detect_content_type__mutmut_2,
    "x_detect_content_type__mutmut_3": x_detect_content_type__mutmut_3,
    "x_detect_content_type__mutmut_4": x_detect_content_type__mutmut_4,
    "x_detect_content_type__mutmut_5": x_detect_content_type__mutmut_5,
    "x_detect_content_type__mutmut_6": x_detect_content_type__mutmut_6,
    "x_detect_content_type__mutmut_7": x_detect_content_type__mutmut_7,
    "x_detect_content_type__mutmut_8": x_detect_content_type__mutmut_8,
    "x_detect_content_type__mutmut_9": x_detect_content_type__mutmut_9,
    "x_detect_content_type__mutmut_10": x_detect_content_type__mutmut_10,
    "x_detect_content_type__mutmut_11": x_detect_content_type__mutmut_11,
}
x_detect_content_type__mutmut_orig.__name__ = "x_detect_content_type"


def _get_html_splitter() -> HTMLHeaderTextSplitter:
    args = []  # type: ignore
    kwargs = {}  # type: ignore
    return _mutmut_trampoline(
        x__get_html_splitter__mutmut_orig,
        x__get_html_splitter__mutmut_mutants,
        args,
        kwargs,
        None,
    )


def x__get_html_splitter__mutmut_orig() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_1() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = None
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_2() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("XXh1XX", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_3() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("H1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_4() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "XXHeader 1XX"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_5() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_6() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "HEADER 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_7() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("XXh2XX", "Header 2"),
        ("h3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_8() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("H2", "Header 2"),
        ("h3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_9() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "XXHeader 2XX"),
        ("h3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_10() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "header 2"),
        ("h3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_11() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "HEADER 2"),
        ("h3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_12() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("XXh3XX", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_13() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("H3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_14() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "XXHeader 3XX"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_15() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_16() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "HEADER 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def x__get_html_splitter__mutmut_17() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=None)


x__get_html_splitter__mutmut_mutants: ClassVar[MutantDict] = {  # type: ignore
    "x__get_html_splitter__mutmut_1": x__get_html_splitter__mutmut_1,
    "x__get_html_splitter__mutmut_2": x__get_html_splitter__mutmut_2,
    "x__get_html_splitter__mutmut_3": x__get_html_splitter__mutmut_3,
    "x__get_html_splitter__mutmut_4": x__get_html_splitter__mutmut_4,
    "x__get_html_splitter__mutmut_5": x__get_html_splitter__mutmut_5,
    "x__get_html_splitter__mutmut_6": x__get_html_splitter__mutmut_6,
    "x__get_html_splitter__mutmut_7": x__get_html_splitter__mutmut_7,
    "x__get_html_splitter__mutmut_8": x__get_html_splitter__mutmut_8,
    "x__get_html_splitter__mutmut_9": x__get_html_splitter__mutmut_9,
    "x__get_html_splitter__mutmut_10": x__get_html_splitter__mutmut_10,
    "x__get_html_splitter__mutmut_11": x__get_html_splitter__mutmut_11,
    "x__get_html_splitter__mutmut_12": x__get_html_splitter__mutmut_12,
    "x__get_html_splitter__mutmut_13": x__get_html_splitter__mutmut_13,
    "x__get_html_splitter__mutmut_14": x__get_html_splitter__mutmut_14,
    "x__get_html_splitter__mutmut_15": x__get_html_splitter__mutmut_15,
    "x__get_html_splitter__mutmut_16": x__get_html_splitter__mutmut_16,
    "x__get_html_splitter__mutmut_17": x__get_html_splitter__mutmut_17,
}
x__get_html_splitter__mutmut_orig.__name__ = "x__get_html_splitter"


def _get_markdown_splitter() -> MarkdownHeaderTextSplitter:
    args = []  # type: ignore
    kwargs = {}  # type: ignore
    return _mutmut_trampoline(
        x__get_markdown_splitter__mutmut_orig,
        x__get_markdown_splitter__mutmut_mutants,
        args,
        kwargs,
        None,
    )


def x__get_markdown_splitter__mutmut_orig() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_1() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = None
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_2() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("XX#XX", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_3() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "XXHeader 1XX"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_4() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_5() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "HEADER 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_6() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("XX##XX", "Header 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_7() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "XXHeader 2XX"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_8() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "header 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_9() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "HEADER 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_10() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("XX###XX", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_11() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "XXHeader 3XX"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_12() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_13() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "HEADER 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_14() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=None,
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_15() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=None,
    )


def x__get_markdown_splitter__mutmut_16() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        strip_headers=False,
    )


def x__get_markdown_splitter__mutmut_17() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
    )


def x__get_markdown_splitter__mutmut_18() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=True,
    )


x__get_markdown_splitter__mutmut_mutants: ClassVar[MutantDict] = {  # type: ignore
    "x__get_markdown_splitter__mutmut_1": x__get_markdown_splitter__mutmut_1,
    "x__get_markdown_splitter__mutmut_2": x__get_markdown_splitter__mutmut_2,
    "x__get_markdown_splitter__mutmut_3": x__get_markdown_splitter__mutmut_3,
    "x__get_markdown_splitter__mutmut_4": x__get_markdown_splitter__mutmut_4,
    "x__get_markdown_splitter__mutmut_5": x__get_markdown_splitter__mutmut_5,
    "x__get_markdown_splitter__mutmut_6": x__get_markdown_splitter__mutmut_6,
    "x__get_markdown_splitter__mutmut_7": x__get_markdown_splitter__mutmut_7,
    "x__get_markdown_splitter__mutmut_8": x__get_markdown_splitter__mutmut_8,
    "x__get_markdown_splitter__mutmut_9": x__get_markdown_splitter__mutmut_9,
    "x__get_markdown_splitter__mutmut_10": x__get_markdown_splitter__mutmut_10,
    "x__get_markdown_splitter__mutmut_11": x__get_markdown_splitter__mutmut_11,
    "x__get_markdown_splitter__mutmut_12": x__get_markdown_splitter__mutmut_12,
    "x__get_markdown_splitter__mutmut_13": x__get_markdown_splitter__mutmut_13,
    "x__get_markdown_splitter__mutmut_14": x__get_markdown_splitter__mutmut_14,
    "x__get_markdown_splitter__mutmut_15": x__get_markdown_splitter__mutmut_15,
    "x__get_markdown_splitter__mutmut_16": x__get_markdown_splitter__mutmut_16,
    "x__get_markdown_splitter__mutmut_17": x__get_markdown_splitter__mutmut_17,
    "x__get_markdown_splitter__mutmut_18": x__get_markdown_splitter__mutmut_18,
}
x__get_markdown_splitter__mutmut_orig.__name__ = "x__get_markdown_splitter"


def _get_plain_splitter() -> RecursiveCharacterTextSplitter:
    args = []  # type: ignore
    kwargs = {}  # type: ignore
    return _mutmut_trampoline(
        x__get_plain_splitter__mutmut_orig,
        x__get_plain_splitter__mutmut_mutants,
        args,
        kwargs,
        None,
    )


def x__get_plain_splitter__mutmut_orig() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
    )


def x__get_plain_splitter__mutmut_1() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_size=None,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
    )


def x__get_plain_splitter__mutmut_2() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=None,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
    )


def x__get_plain_splitter__mutmut_3() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=None,
    )


def x__get_plain_splitter__mutmut_4() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
    )


def x__get_plain_splitter__mutmut_5() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
    )


def x__get_plain_splitter__mutmut_6() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )


def x__get_plain_splitter__mutmut_7() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["XX\n\nXX", "\n", ". ", ", ", " ", ""],
    )


def x__get_plain_splitter__mutmut_8() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "XX\nXX", ". ", ", ", " ", ""],
    )


def x__get_plain_splitter__mutmut_9() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "XX. XX", ", ", " ", ""],
    )


def x__get_plain_splitter__mutmut_10() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", "XX, XX", " ", ""],
    )


def x__get_plain_splitter__mutmut_11() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", ", ", "XX XX", ""],
    )


def x__get_plain_splitter__mutmut_12() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", ", ", " ", "XXXX"],
    )


x__get_plain_splitter__mutmut_mutants: ClassVar[MutantDict] = {  # type: ignore
    "x__get_plain_splitter__mutmut_1": x__get_plain_splitter__mutmut_1,
    "x__get_plain_splitter__mutmut_2": x__get_plain_splitter__mutmut_2,
    "x__get_plain_splitter__mutmut_3": x__get_plain_splitter__mutmut_3,
    "x__get_plain_splitter__mutmut_4": x__get_plain_splitter__mutmut_4,
    "x__get_plain_splitter__mutmut_5": x__get_plain_splitter__mutmut_5,
    "x__get_plain_splitter__mutmut_6": x__get_plain_splitter__mutmut_6,
    "x__get_plain_splitter__mutmut_7": x__get_plain_splitter__mutmut_7,
    "x__get_plain_splitter__mutmut_8": x__get_plain_splitter__mutmut_8,
    "x__get_plain_splitter__mutmut_9": x__get_plain_splitter__mutmut_9,
    "x__get_plain_splitter__mutmut_10": x__get_plain_splitter__mutmut_10,
    "x__get_plain_splitter__mutmut_11": x__get_plain_splitter__mutmut_11,
    "x__get_plain_splitter__mutmut_12": x__get_plain_splitter__mutmut_12,
}
x__get_plain_splitter__mutmut_orig.__name__ = "x__get_plain_splitter"


def _apply_secondary_chunking(chunks: List[str]) -> List[str]:
    args = [chunks]  # type: ignore
    kwargs = {}  # type: ignore
    return _mutmut_trampoline(
        x__apply_secondary_chunking__mutmut_orig,
        x__apply_secondary_chunking__mutmut_mutants,
        args,
        kwargs,
        None,
    )


def x__apply_secondary_chunking__mutmut_orig(chunks: List[str]) -> List[str]:
    """
    Apply secondary chunking to ensure no chunk exceeds CHUNK_SIZE.

    Used when primary splitters (HTML/Markdown) produce oversized chunks.
    """
    result = []
    secondary_splitter = _get_plain_splitter()

    for chunk in chunks:
        if len(chunk) > CHUNK_SIZE:
            # Split oversized chunk
            sub_chunks = secondary_splitter.split_text(chunk)
            result.extend(sub_chunks)
        else:
            result.append(chunk)

    return result


def x__apply_secondary_chunking__mutmut_1(chunks: List[str]) -> List[str]:
    """
    Apply secondary chunking to ensure no chunk exceeds CHUNK_SIZE.

    Used when primary splitters (HTML/Markdown) produce oversized chunks.
    """
    result = None
    secondary_splitter = _get_plain_splitter()

    for chunk in chunks:
        if len(chunk) > CHUNK_SIZE:
            # Split oversized chunk
            sub_chunks = secondary_splitter.split_text(chunk)
            result.extend(sub_chunks)
        else:
            result.append(chunk)

    return result


def x__apply_secondary_chunking__mutmut_2(chunks: List[str]) -> List[str]:
    """
    Apply secondary chunking to ensure no chunk exceeds CHUNK_SIZE.

    Used when primary splitters (HTML/Markdown) produce oversized chunks.
    """
    result = []
    secondary_splitter = None

    for chunk in chunks:
        if len(chunk) > CHUNK_SIZE:
            # Split oversized chunk
            sub_chunks = secondary_splitter.split_text(chunk)
            result.extend(sub_chunks)
        else:
            result.append(chunk)

    return result


def x__apply_secondary_chunking__mutmut_3(chunks: List[str]) -> List[str]:
    """
    Apply secondary chunking to ensure no chunk exceeds CHUNK_SIZE.

    Used when primary splitters (HTML/Markdown) produce oversized chunks.
    """
    result = []
    secondary_splitter = _get_plain_splitter()

    for chunk in chunks:
        if len(chunk) >= CHUNK_SIZE:
            # Split oversized chunk
            sub_chunks = secondary_splitter.split_text(chunk)
            result.extend(sub_chunks)
        else:
            result.append(chunk)

    return result


def x__apply_secondary_chunking__mutmut_4(chunks: List[str]) -> List[str]:
    """
    Apply secondary chunking to ensure no chunk exceeds CHUNK_SIZE.

    Used when primary splitters (HTML/Markdown) produce oversized chunks.
    """
    result = []
    secondary_splitter = _get_plain_splitter()

    for chunk in chunks:
        if len(chunk) > CHUNK_SIZE:
            # Split oversized chunk
            sub_chunks = None
            result.extend(sub_chunks)
        else:
            result.append(chunk)

    return result


def x__apply_secondary_chunking__mutmut_5(chunks: List[str]) -> List[str]:
    """
    Apply secondary chunking to ensure no chunk exceeds CHUNK_SIZE.

    Used when primary splitters (HTML/Markdown) produce oversized chunks.
    """
    result = []
    secondary_splitter = _get_plain_splitter()

    for chunk in chunks:
        if len(chunk) > CHUNK_SIZE:
            # Split oversized chunk
            sub_chunks = secondary_splitter.split_text(None)
            result.extend(sub_chunks)
        else:
            result.append(chunk)

    return result


def x__apply_secondary_chunking__mutmut_6(chunks: List[str]) -> List[str]:
    """
    Apply secondary chunking to ensure no chunk exceeds CHUNK_SIZE.

    Used when primary splitters (HTML/Markdown) produce oversized chunks.
    """
    result = []
    secondary_splitter = _get_plain_splitter()

    for chunk in chunks:
        if len(chunk) > CHUNK_SIZE:
            # Split oversized chunk
            sub_chunks = secondary_splitter.split_text(chunk)
            result.extend(None)
        else:
            result.append(chunk)

    return result


def x__apply_secondary_chunking__mutmut_7(chunks: List[str]) -> List[str]:
    """
    Apply secondary chunking to ensure no chunk exceeds CHUNK_SIZE.

    Used when primary splitters (HTML/Markdown) produce oversized chunks.
    """
    result = []
    secondary_splitter = _get_plain_splitter()

    for chunk in chunks:
        if len(chunk) > CHUNK_SIZE:
            # Split oversized chunk
            sub_chunks = secondary_splitter.split_text(chunk)
            result.extend(sub_chunks)
        else:
            result.append(None)

    return result


x__apply_secondary_chunking__mutmut_mutants: ClassVar[MutantDict] = {  # type: ignore
    "x__apply_secondary_chunking__mutmut_1": x__apply_secondary_chunking__mutmut_1,
    "x__apply_secondary_chunking__mutmut_2": x__apply_secondary_chunking__mutmut_2,
    "x__apply_secondary_chunking__mutmut_3": x__apply_secondary_chunking__mutmut_3,
    "x__apply_secondary_chunking__mutmut_4": x__apply_secondary_chunking__mutmut_4,
    "x__apply_secondary_chunking__mutmut_5": x__apply_secondary_chunking__mutmut_5,
    "x__apply_secondary_chunking__mutmut_6": x__apply_secondary_chunking__mutmut_6,
    "x__apply_secondary_chunking__mutmut_7": x__apply_secondary_chunking__mutmut_7,
}
x__apply_secondary_chunking__mutmut_orig.__name__ = "x__apply_secondary_chunking"


def chunk_text(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    args = [text, content_type, file_path]  # type: ignore
    kwargs = {}  # type: ignore
    return _mutmut_trampoline(
        x_chunk_text__mutmut_orig, x_chunk_text__mutmut_mutants, args, kwargs, None
    )


def x_chunk_text__mutmut_orig(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_1(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text and not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_2(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_3(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_4(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) < CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_5(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is not None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_6(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = None

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_7(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(None, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_8(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, None)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_9(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_10(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(
            text,
        )

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_11(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(None)

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_12(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type != ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_13(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = None
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_14(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = None
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_15(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(None)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_16(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = None
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_17(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(None, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_18(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [doc.page_content if hasattr(doc, None) else str(doc) for doc in docs]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_19(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr("page_content") else str(doc) for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_20(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content
            if hasattr(
                doc,
            )
            else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_21(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "XXpage_contentXX") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_22(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "PAGE_CONTENT") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_23(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(None)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_24(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type != ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_25(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = None
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_26(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = None
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_27(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(None)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_28(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = None
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_29(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(None, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_30(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [doc.page_content if hasattr(doc, None) else str(doc) for doc in docs]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_31(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr("page_content") else str(doc) for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_32(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content
            if hasattr(
                doc,
            )
            else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_33(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "XXpage_contentXX") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_34(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "PAGE_CONTENT") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_35(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(None)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_36(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = None
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_37(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = None

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_38(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(None)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_39(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type not in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_40(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = None

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_41(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(None)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_42(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = None

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_43(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c or c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks


def x_chunk_text__mutmut_44(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(None)
    return chunks


x_chunk_text__mutmut_mutants: ClassVar[MutantDict] = {  # type: ignore
    "x_chunk_text__mutmut_1": x_chunk_text__mutmut_1,
    "x_chunk_text__mutmut_2": x_chunk_text__mutmut_2,
    "x_chunk_text__mutmut_3": x_chunk_text__mutmut_3,
    "x_chunk_text__mutmut_4": x_chunk_text__mutmut_4,
    "x_chunk_text__mutmut_5": x_chunk_text__mutmut_5,
    "x_chunk_text__mutmut_6": x_chunk_text__mutmut_6,
    "x_chunk_text__mutmut_7": x_chunk_text__mutmut_7,
    "x_chunk_text__mutmut_8": x_chunk_text__mutmut_8,
    "x_chunk_text__mutmut_9": x_chunk_text__mutmut_9,
    "x_chunk_text__mutmut_10": x_chunk_text__mutmut_10,
    "x_chunk_text__mutmut_11": x_chunk_text__mutmut_11,
    "x_chunk_text__mutmut_12": x_chunk_text__mutmut_12,
    "x_chunk_text__mutmut_13": x_chunk_text__mutmut_13,
    "x_chunk_text__mutmut_14": x_chunk_text__mutmut_14,
    "x_chunk_text__mutmut_15": x_chunk_text__mutmut_15,
    "x_chunk_text__mutmut_16": x_chunk_text__mutmut_16,
    "x_chunk_text__mutmut_17": x_chunk_text__mutmut_17,
    "x_chunk_text__mutmut_18": x_chunk_text__mutmut_18,
    "x_chunk_text__mutmut_19": x_chunk_text__mutmut_19,
    "x_chunk_text__mutmut_20": x_chunk_text__mutmut_20,
    "x_chunk_text__mutmut_21": x_chunk_text__mutmut_21,
    "x_chunk_text__mutmut_22": x_chunk_text__mutmut_22,
    "x_chunk_text__mutmut_23": x_chunk_text__mutmut_23,
    "x_chunk_text__mutmut_24": x_chunk_text__mutmut_24,
    "x_chunk_text__mutmut_25": x_chunk_text__mutmut_25,
    "x_chunk_text__mutmut_26": x_chunk_text__mutmut_26,
    "x_chunk_text__mutmut_27": x_chunk_text__mutmut_27,
    "x_chunk_text__mutmut_28": x_chunk_text__mutmut_28,
    "x_chunk_text__mutmut_29": x_chunk_text__mutmut_29,
    "x_chunk_text__mutmut_30": x_chunk_text__mutmut_30,
    "x_chunk_text__mutmut_31": x_chunk_text__mutmut_31,
    "x_chunk_text__mutmut_32": x_chunk_text__mutmut_32,
    "x_chunk_text__mutmut_33": x_chunk_text__mutmut_33,
    "x_chunk_text__mutmut_34": x_chunk_text__mutmut_34,
    "x_chunk_text__mutmut_35": x_chunk_text__mutmut_35,
    "x_chunk_text__mutmut_36": x_chunk_text__mutmut_36,
    "x_chunk_text__mutmut_37": x_chunk_text__mutmut_37,
    "x_chunk_text__mutmut_38": x_chunk_text__mutmut_38,
    "x_chunk_text__mutmut_39": x_chunk_text__mutmut_39,
    "x_chunk_text__mutmut_40": x_chunk_text__mutmut_40,
    "x_chunk_text__mutmut_41": x_chunk_text__mutmut_41,
    "x_chunk_text__mutmut_42": x_chunk_text__mutmut_42,
    "x_chunk_text__mutmut_43": x_chunk_text__mutmut_43,
    "x_chunk_text__mutmut_44": x_chunk_text__mutmut_44,
}
x_chunk_text__mutmut_orig.__name__ = "x_chunk_text"
