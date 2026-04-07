import json
from typing import Any, AsyncGenerator, cast

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.runnables import RunnableConfig

from packages.core.ai.models import DefaultModels, Model, model_manager
from packages.core.application.models import (
    AskRequest,
    AskResponse,
    SearchRequest,
    SearchResponse,
)
from packages.core.domain.notebook import text_search, vector_search
from packages.core.exceptions import DatabaseOperationError, InvalidInputError
from packages.core.graphs.ask import graph as ask_graph
from packages.core.observability.logger import logger

router = APIRouter()


async def _require_explicit_embedding_model() -> None:
    """Enforce explicit embedding model configuration for vector/ask flows."""
    defaults = await DefaultModels.get_instance()
    embedding_model_id = defaults.default_embedding_model
    if not embedding_model_id:
        raise HTTPException(
            status_code=400,
            detail="Embedding model is not configured. Please set a default embedding model in the Models section.",
        )
    embedding_model = await Model.get(embedding_model_id)
    if not embedding_model or embedding_model.type != "embedding":
        raise HTTPException(
            status_code=400,
            detail="Default embedding model is invalid. Please configure a valid embedding model in the Models section.",
        )
    if not await model_manager.get_model(embedding_model_id):
        raise HTTPException(
            status_code=400,
            detail="Configured embedding model is unavailable. Please verify provider credentials and model settings.",
        )


def _require_language_model(model: Model | None, role: str, model_id: str) -> Model:
    if not model:
        raise HTTPException(
            status_code=400, detail=f"{role} model {model_id} not found"
        )
    if model.type != "language":
        raise HTTPException(
            status_code=400,
            detail=f"{role} model {model_id} must be a language model",
        )
    return model


async def _resolve_ask_models(ask_request: AskRequest) -> tuple[Model, Model, Model]:
    strategy_model = _require_language_model(
        await Model.get(ask_request.strategy_model),
        "Strategy",
        ask_request.strategy_model,
    )
    answer_model = _require_language_model(
        await Model.get(ask_request.answer_model),
        "Answer",
        ask_request.answer_model,
    )
    final_answer_model = _require_language_model(
        await Model.get(ask_request.final_answer_model),
        "Final answer",
        ask_request.final_answer_model,
    )
    return strategy_model, answer_model, final_answer_model


@router.post("/search", response_model=SearchResponse)
async def search_knowledge_base(search_request: SearchRequest):
    """Search the knowledge base using text or vector search."""
    try:
        if search_request.type == "vector":
            await _require_explicit_embedding_model()

            results = await vector_search(
                keyword=search_request.query,
                results=search_request.limit,
                source=search_request.search_sources,
                note=search_request.search_notes,
                minimum_score=search_request.minimum_score,
            )
        else:
            # Text search
            results = await text_search(
                keyword=search_request.query,
                results=search_request.limit,
                source=search_request.search_sources,
                note=search_request.search_notes,
            )

        return SearchResponse(
            results=results or [],
            total_count=len(results) if results else 0,
            search_type=search_request.type,
        )

    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except DatabaseOperationError as e:
        logger.error("Database error during search error_type={}", type(e).__name__)
        raise HTTPException(status_code=500, detail="Search failed")
    except Exception as e:
        logger.error("Unexpected search error error_type={}", type(e).__name__)
        raise HTTPException(status_code=500, detail="Search failed")


async def stream_ask_response(
    question: str, strategy_model: Model, answer_model: Model, final_answer_model: Model
) -> AsyncGenerator[str, None]:
    """Stream the ask response as Server-Sent Events."""
    try:
        final_answer = None
        ask_config = cast(
            RunnableConfig,
            {
                "configurable": {
                    "strategy_model": strategy_model.id,
                    "answer_model": answer_model.id,
                    "final_answer_model": final_answer_model.id,
                }
            },
        )

        graph = cast(Any, ask_graph)
        async for chunk in graph.astream(
            input={"question": question},
            config=ask_config,
            stream_mode="updates",
        ):
            if "agent" in chunk:
                strategy_data = {
                    "type": "strategy",
                    "reasoning": chunk["agent"]["strategy"].reasoning,
                    "searches": [
                        {"term": search.term, "instructions": search.instructions}
                        for search in chunk["agent"]["strategy"].searches
                    ],
                }
                yield f"data: {json.dumps(strategy_data)}\n\n"

            elif "provide_answer" in chunk:
                for answer in chunk["provide_answer"]["answers"]:
                    answer_data = {"type": "answer", "content": answer}
                    yield f"data: {json.dumps(answer_data)}\n\n"

            elif "write_final_answer" in chunk:
                final_answer = chunk["write_final_answer"]["final_answer"]
                final_data = {"type": "final_answer", "content": final_answer}
                yield f"data: {json.dumps(final_data)}\n\n"

        # Send completion signal
        completion_data = {"type": "complete", "final_answer": final_answer}
        yield f"data: {json.dumps(completion_data)}\n\n"

    except Exception as e:
        logger.error("Ask streaming failed error_type={}", type(e).__name__)
        error_data = {
            "type": "error",
            "message": "Ask request failed. Check provider configuration and server logs.",
        }
        yield f"data: {json.dumps(error_data)}\n\n"


@router.post("/search/ask")
async def ask_knowledge_base(ask_request: AskRequest):
    """Ask the knowledge base a question using AI models."""
    try:
        strategy_model, answer_model, final_answer_model = await _resolve_ask_models(
            ask_request
        )
        await _require_explicit_embedding_model()

        # For streaming response
        return StreamingResponse(
            stream_ask_response(
                ask_request.question, strategy_model, answer_model, final_answer_model
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ask endpoint failed error_type={}", type(e).__name__)
        raise HTTPException(status_code=500, detail="Ask operation failed")


@router.post("/search/ask/simple", response_model=AskResponse)
async def ask_knowledge_base_simple(ask_request: AskRequest):
    """Ask the knowledge base a question and return a simple response (non-streaming)."""
    try:
        strategy_model, answer_model, final_answer_model = await _resolve_ask_models(
            ask_request
        )
        await _require_explicit_embedding_model()

        # Run the ask graph and get final result
        final_answer = None
        ask_config = cast(
            RunnableConfig,
            {
                "configurable": {
                    "strategy_model": strategy_model.id,
                    "answer_model": answer_model.id,
                    "final_answer_model": final_answer_model.id,
                }
            },
        )
        graph = cast(Any, ask_graph)
        async for chunk in graph.astream(
            input={"question": ask_request.question},
            config=ask_config,
            stream_mode="updates",
        ):
            if "write_final_answer" in chunk:
                final_answer = chunk["write_final_answer"]["final_answer"]

        if not final_answer:
            raise HTTPException(status_code=500, detail="No answer generated")

        return AskResponse(answer=final_answer, question=ask_request.question)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ask simple endpoint failed error_type={}", type(e).__name__)
        raise HTTPException(status_code=500, detail="Ask operation failed")
