import operator
from pathlib import Path
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlparse

from content_core import extract_content
from content_core.common import ProcessSourceState
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from typing_extensions import Annotated, NotRequired, TypedDict

from packages.core.ai.models import Model, ModelManager
from packages.core.domain.content_settings import ContentSettings
from packages.core.domain.notebook import Asset, Source
from packages.core.domain.transformation import Transformation
from packages.core.graphs.transformation import graph as transform_graph
from packages.core.observability.logger import logger


class SourceState(TypedDict):
    content_state: ProcessSourceState
    apply_transformations: List[Transformation]
    source_id: str
    notebook_ids: List[str]
    source: NotRequired[Source]
    transformation: NotRequired[Annotated[list, operator.add]]
    gemini_telemetry: NotRequired[Annotated[list, operator.add]]
    embed: bool


class TransformationState(TypedDict):
    source: Source
    transformation: Transformation


async def content_process(state: SourceState) -> dict:
    content_settings = ContentSettings(
        default_content_processing_engine_doc="auto",
        default_content_processing_engine_url="auto",
        default_embedding_option="ask",
        auto_delete_files="yes",
        youtube_preferred_languages=[
            "en",
            "pt",
            "es",
            "de",
            "nl",
            "en-GB",
            "fr",
            "hi",
            "ja",
        ],
    )
    content_state: Dict[str, Any] = state["content_state"]  # type: ignore[assignment]

    content_state["url_engine"] = (
        content_settings.default_content_processing_engine_url or "auto"
    )
    content_state["document_engine"] = (
        content_settings.default_content_processing_engine_doc or "auto"
    )
    content_state["output_format"] = "markdown"

    # Add speech-to-text model configuration from Default Models
    try:
        model_manager = ModelManager()
        defaults = await model_manager.get_defaults()
        if defaults.default_speech_to_text_model:
            stt_model = await Model.get(defaults.default_speech_to_text_model)
            if stt_model:
                content_state["audio_provider"] = stt_model.provider
                content_state["audio_model"] = stt_model.name
                logger.debug(
                    f"Using speech-to-text model: {stt_model.provider}/{stt_model.name}"
                )
    except Exception as e:
        logger.warning(f"Failed to retrieve speech-to-text model configuration: {e}")
        # Continue without custom audio model (content-core will use its default)

    processed_state = await extract_content(content_state)

    if not processed_state.content or not processed_state.content.strip():
        url = processed_state.url or ""
        parsed_url = urlparse(url)
        hostname = (parsed_url.hostname or "").rstrip(".").lower()
        if hostname in {"youtube.com", "youtu.be"} or hostname.endswith(
            (".youtube.com", ".youtu.be")
        ):
            raise ValueError(
                "Could not extract content from this YouTube video. "
                "No transcript or subtitles are available. "
                "Try configuring a Speech-to-Text model in Settings "
                "to transcribe the audio instead."
            )
        raise ValueError(
            "Could not extract any text content from this source. "
            "The content may be empty, inaccessible, or in an unsupported format."
        )

    return {"content_state": processed_state}


async def save_source(state: SourceState) -> dict:
    content_state = state["content_state"]

    # Get existing source using the provided source_id
    source = await Source.get(state["source_id"])
    if not source:
        raise ValueError(f"Source with ID {state['source_id']} not found")

    # Update the source with processed content
    source.asset = Asset(url=content_state.url, file_path=content_state.file_path)
    source.full_text = content_state.content

    # Preserve existing title if none provided in processed content
    if content_state.title:
        source.title = content_state.title

    await source.save()

    # NOTE: Notebook associations are created by the API immediately for UI responsiveness
    # No need to create them here to avoid duplicate edges

    if state["embed"]:
        if source.full_text and source.full_text.strip():
            logger.debug("Embedding content for vector search")
            await source.vectorize()
        else:
            logger.warning(
                f"Source {source.id} has no text content to embed, skipping vectorization"
            )

    return {"source": source}


def trigger_transformations(state: SourceState, config: RunnableConfig) -> List[Send]:
    if len(state["apply_transformations"]) == 0:
        return []

    to_apply = state["apply_transformations"]
    logger.debug(f"Applying transformations {to_apply}")

    return [
        Send(
            "transform_content",
            {
                "source": state["source"],
                "transformation": t,
            },
        )
        for t in to_apply
    ]


def _derive_media_resolution_hint(source: Source) -> str:
    asset = getattr(source, "asset", None)
    file_path = getattr(asset, "file_path", None) if asset else None
    url = getattr(asset, "url", None) if asset else None
    candidate = str(file_path or url or "").lower()
    suffix = Path(candidate).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic"}:
        return "high"
    if suffix in {".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav", ".m4a"}:
        return "medium"
    return "low"


async def transform_content(
    state: TransformationState, config: RunnableConfig
) -> Optional[dict]:
    source = state["source"]
    content = source.full_text
    if not content:
        return None
    transformation: Transformation = state["transformation"]

    logger.debug(f"Applying transformation {transformation.name}")
    media_resolution = _derive_media_resolution_hint(source)
    graph = cast(Any, transform_graph)
    result = await graph.ainvoke(
        {
            "input_text": content,
            "transformation": transformation,
            "input_parts": [
                {
                    "type": "text",
                    "text": content,
                    "metadata": {"media_resolution": media_resolution},
                }
            ],
        },
        config=config,
    )
    await source.add_insight(transformation.title, result["output"])
    output = {
        "transformation": [
            {
                "output": result["output"],
                "transformation_name": transformation.name,
            }
        ]
    }
    telemetry = result.get("gemini_telemetry")
    if telemetry:
        output["gemini_telemetry"] = [telemetry]
    return output


# Create and compile the workflow
workflow = StateGraph(SourceState)

# Add nodes
workflow.add_node("content_process", content_process)
workflow.add_node("save_source", save_source)
workflow.add_node("transform_content", transform_content)
# Define the graph edges
workflow.add_edge(START, "content_process")
workflow.add_edge("content_process", "save_source")
workflow.add_conditional_edges(
    "save_source", trigger_transformations, ["transform_content"]
)
workflow.add_edge("transform_content", END)

# Compile the graph
source_graph = workflow.compile()
