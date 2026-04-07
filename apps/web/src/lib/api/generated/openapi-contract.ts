// AUTO-GENERATED: DO NOT EDIT DIRECTLY.
// Source: contracts/api/openapi.yaml

export const openApiContractSha256Bytes = [
  251, 123, 135, 199, 88, 199, 251, 167, 73, 244, 12, 1, 44, 108, 151, 160, 59, 96, 160, 94, 140,
  190, 21, 194, 118, 57, 202, 121, 41, 184, 209, 254,
] as const;
export const openApiContractSha256 = Array.from(openApiContractSha256Bytes, (byte) =>
  byte.toString(16).padStart(2, "0"),
).join("");
export const openApiOperationIds = JSON.parse(
  String.raw`
[
  "add_source_to_notebook_api_notebooks__notebook_id__sources__source_id__post",
  "append_research_thread_entry_api_research_threads__thread_id__entries_post",
  "ask_knowledge_base_api_search_ask_post",
  "ask_knowledge_base_simple_api_search_ask_simple_post",
  "auto_assign_defaults_api_models_auto_assign_post",
  "build_context_api_chat_context_post",
  "cancel_command_job_api_commands_jobs__job_id__delete",
  "check_source_file_api_sources__source_id__download_head",
  "confirm_computer_use_action_api_computer_use_sessions__session_id__confirm_post",
  "create_auditable_run_api_sources__source_id__auditable_runs_post",
  "create_auditable_runs_batch_api_auditable_runs_batch_post",
  "create_computer_use_session_api_computer_use_sessions_post",
  "create_credential_api_credentials_post",
  "create_draft_api_notebooks__notebook_id__drafts_post",
  "create_draft_from_thread_api_research_threads__thread_id__drafts_post",
  "create_episode_profile_api_episode_profiles_post",
  "create_model_api_models_post",
  "create_note_api_notes_post",
  "create_notebook_api_notebooks_post",
  "create_research_thread_api_notebooks__notebook_id__research_threads_post",
  "create_session_api_chat_sessions_post",
  "create_source_api_sources_post",
  "create_source_chat_session_api_sources__source_id__chat_sessions_post",
  "create_source_insight_api_sources__source_id__insights_post",
  "create_source_json_api_sources_json_post",
  "create_speaker_profile_api_speaker_profiles_post",
  "create_transformation_api_transformations_post",
  "debug_registry_api_commands_registry_debug_get",
  "delete_credential_api_credentials__credential_id__delete",
  "delete_episode_profile_api_episode_profiles__profile_id__delete",
  "delete_insight_api_insights__insight_id__delete",
  "delete_model_api_models__model_id__delete",
  "delete_note_api_notes__note_id__delete",
  "delete_notebook_api_notebooks__notebook_id__delete",
  "delete_podcast_episode_api_podcasts_episodes__episode_id__delete",
  "delete_session_api_chat_sessions__session_id__delete",
  "delete_source_api_sources__source_id__delete",
  "delete_source_chat_session_api_sources__source_id__chat_sessions__session_id__delete",
  "delete_speaker_profile_api_speaker_profiles__profile_id__delete",
  "delete_transformation_api_transformations__transformation_id__delete",
  "discover_models_api_models_discover__provider__get",
  "discover_models_for_credential_api_credentials__credential_id__discover_post",
  "download_source_file_api_sources__source_id__download_get",
  "duplicate_episode_profile_api_episode_profiles__profile_id__duplicate_post",
  "duplicate_speaker_profile_api_speaker_profiles__profile_id__duplicate_post",
  "embed_content_api_embed_post",
  "execute_chat_api_chat_execute_post",
  "execute_command_api_commands_jobs_post",
  "execute_transformation_api_transformations_execute_post",
  "generate_podcast_api_podcasts_generate_post",
  "get_auditable_run_api_auditable_runs__run_id__get",
  "get_auditable_run_markdown_api_auditable_runs__run_id__markdown_get",
  "get_auth_status_api_auth_status_get",
  "get_command_job_status_api_commands_jobs__job_id__get",
  "get_computer_use_session_api_computer_use_sessions__session_id__get",
  "get_config_api_config_get",
  "get_credential_api_credentials__credential_id__get",
  "get_default_models_api_models_defaults_get",
  "get_default_prompt_api_transformations_default_prompt_get",
  "get_draft_api_drafts__draft_id__get",
  "get_draft_bundle_api_drafts__draft_id__bundle_get",
  "get_draft_markdown_api_drafts__draft_id__markdown_get",
  "get_episode_profile_api_episode_profiles__profile_name__get",
  "get_insight_api_insights__insight_id__get",
  "get_model_count_api_models_count__provider__get",
  "get_models_api_models_get",
  "get_models_by_provider_api_models_by_provider__provider__get",
  "get_note_api_notes__note_id__get",
  "get_notebook_api_notebooks__notebook_id__get",
  "get_notebook_context_api_notebooks__notebook_id__context_post",
  "get_notebook_delete_preview_api_notebooks__notebook_id__delete_preview_get",
  "get_notebooks_api_notebooks_get",
  "get_notes_api_notes_get",
  "get_podcast_episode_api_podcasts_episodes__episode_id__get",
  "get_podcast_job_status_api_podcasts_jobs__job_id__get",
  "get_policy_api_providers_policy_get",
  "get_policy_bootstrap_diagnostics_api_providers_policy_bootstrap_diagnostics_get",
  "get_provider_availability_api_models_providers_get",
  "get_rebuild_status_api_embeddings_rebuild__command_id__status_get",
  "get_research_thread_api_research_threads__thread_id__get",
  "get_session_api_chat_sessions__session_id__get",
  "get_sessions_api_chat_sessions_get",
  "get_settings_api_settings_get",
  "get_source_api_sources__source_id__get",
  "get_source_chat_session_api_sources__source_id__chat_sessions__session_id__get",
  "get_source_chat_sessions_api_sources__source_id__chat_sessions_get",
  "get_source_insights_api_sources__source_id__insights_get",
  "get_source_processing_report_api_sources__source_id__processing_report_get",
  "get_source_status_api_sources__source_id__status_get",
  "get_sources_api_sources_get",
  "get_speaker_profile_api_speaker_profiles__profile_name__get",
  "get_status_api_credentials_status_get",
  "get_transformation_api_transformations__transformation_id__get",
  "get_transformations_api_transformations_get",
  "get_ui_test_report_api_ui_tests__run_id__report_get",
  "get_ui_test_run_api_ui_tests__run_id__get",
  "health_health_get",
  "list_auditable_runs_by_source_api_sources__source_id__auditable_runs_get",
  "list_command_jobs_api_commands_jobs_get",
  "list_credentials_api_credentials_get",
  "list_credentials_by_provider_api_credentials_by_provider__provider__get",
  "list_dead_letter_jobs_api_commands_dead_letter_get",
  "list_episode_profiles_api_episode_profiles_get",
  "list_notebook_drafts_api_notebooks__notebook_id__drafts_get",
  "list_podcast_episodes_api_podcasts_episodes_get",
  "list_research_threads_api_notebooks__notebook_id__research_threads_get",
  "list_speaker_profiles_api_speaker_profiles_get",
  "register_models_for_credential_api_credentials__credential_id__register_models_post",
  "remove_source_from_notebook_api_notebooks__notebook_id__sources__source_id__delete",
  "repair_auditable_claim_api_auditable_runs__run_id__repair_claim_post",
  "repair_auditable_section_api_auditable_runs__run_id__repair_section_post",
  "reprocess_source_api_sources__source_id__reprocess_post",
  "requeue_dead_letter_job_api_commands_dead_letter__entry_id__requeue_post",
  "rerun_draft_api_drafts__draft_id__rerun_post",
  "retry_podcast_episode_api_podcasts_episodes__episode_id__retry_post",
  "retry_source_processing_api_sources__source_id__retry_post",
  "root__get",
  "run_ui_test_api_ui_tests_run_post",
  "save_insight_as_note_api_insights__insight_id__save_as_note_post",
  "search_knowledge_base_api_search_post",
  "send_message_to_source_chat_api_sources__source_id__chat_sessions__session_id__messages_post",
  "start_rebuild_api_embeddings_rebuild_post",
  "stream_podcast_episode_audio_api_podcasts_episodes__episode_id__audio_get",
  "sync_all_models_api_models_sync_post",
  "sync_models_api_models_sync__provider__post",
  "test_credential_api_credentials__credential_id__test_post",
  "test_model_api_models__model_id__test_post",
  "update_credential_api_credentials__credential_id__put",
  "update_default_models_api_models_defaults_put",
  "update_default_prompt_api_transformations_default_prompt_put",
  "update_episode_profile_api_episode_profiles__profile_id__put",
  "update_note_api_notes__note_id__put",
  "update_notebook_api_notebooks__notebook_id__put",
  "update_policy_api_providers_policy_put",
  "update_session_api_chat_sessions__session_id__put",
  "update_settings_api_settings_put",
  "update_source_api_sources__source_id__put",
  "update_source_chat_session_api_sources__source_id__chat_sessions__session_id__put",
  "update_speaker_profile_api_speaker_profiles__profile_id__put",
  "update_transformation_api_transformations__transformation_id__put",
  "verify_draft_api_drafts__draft_id__verify_post"
]
`,
) as readonly string[];
export const openApiSchema = JSON.parse(
  String.raw`
{
  "components": {
    "schemas": {
      "AllProvidersSyncResponse": {
        "description": "Response model for syncing all providers.",
        "properties": {
          "results": {
            "additionalProperties": {
              "$ref": "#/components/schemas/ProviderSyncResponse"
            },
            "title": "Results",
            "type": "object"
          },
          "total_discovered": {
            "title": "Total Discovered",
            "type": "integer"
          },
          "total_new": {
            "title": "Total New",
            "type": "integer"
          }
        },
        "required": [
          "results",
          "total_discovered",
          "total_new"
        ],
        "title": "AllProvidersSyncResponse",
        "type": "object"
      },
      "ApiKeyStatusResponse": {
        "description": "Response showing which providers are configured and their source.",
        "properties": {
          "configured": {
            "additionalProperties": {
              "type": "boolean"
            },
            "description": "Map of provider name to whether it is configured",
            "title": "Configured",
            "type": "object"
          },
          "encryption_configured": {
            "description": "Whether OPEN_NOTEBOOK_ENCRYPTION_KEY is set (required to store keys in database)",
            "title": "Encryption Configured",
            "type": "boolean"
          },
          "legacy_env_detected": {
            "additionalProperties": {
              "type": "boolean"
            },
            "description": "Map of provider name to whether legacy provider ENV variables are present",
            "title": "Legacy Env Detected",
            "type": "object"
          },
          "policy_active_provider": {
            "additionalProperties": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ]
            },
            "description": "Currently active provider per modality according to policy chain",
            "propertyNames": {
              "enum": [
                "language",
                "embedding",
                "speech_to_text",
                "text_to_speech"
              ]
            },
            "title": "Policy Active Provider",
            "type": "object"
          },
          "policy_blockers": {
            "additionalProperties": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ]
            },
            "description": "Blocking reason per modality when policy is not effective",
            "propertyNames": {
              "enum": [
                "language",
                "embedding",
                "speech_to_text",
                "text_to_speech"
              ]
            },
            "title": "Policy Blockers",
            "type": "object"
          },
          "policy_effective": {
            "additionalProperties": {
              "type": "boolean"
            },
            "description": "Whether each modality has at least one configured provider in policy chain",
            "propertyNames": {
              "enum": [
                "language",
                "embedding",
                "speech_to_text",
                "text_to_speech"
              ]
            },
            "title": "Policy Effective",
            "type": "object"
          },
          "provider_capabilities": {
            "additionalProperties": {
              "additionalProperties": {
                "additionalProperties": {
                  "type": "string"
                },
                "type": "object"
              },
              "type": "object"
            },
            "description": "Provider capability matrix by modality. Each modality contains {status: supported|preview|unsupported, detail: string}.",
            "title": "Provider Capabilities",
            "type": "object"
          },
          "source": {
            "additionalProperties": {
              "enum": [
                "environment",
                "none"
              ],
              "type": "string"
            },
            "description": "Map of provider name to configuration source (environment or none)",
            "title": "Source",
            "type": "object"
          }
        },
        "required": [
          "configured",
          "source",
          "legacy_env_detected",
          "encryption_configured"
        ],
        "title": "ApiKeyStatusResponse",
        "type": "object"
      },
      "AskRequest": {
        "properties": {
          "answer_model": {
            "description": "Model ID for individual answers",
            "title": "Answer Model",
            "type": "string"
          },
          "final_answer_model": {
            "description": "Model ID for final answer",
            "title": "Final Answer Model",
            "type": "string"
          },
          "question": {
            "description": "Question to ask the knowledge base",
            "title": "Question",
            "type": "string"
          },
          "strategy_model": {
            "description": "Model ID for query strategy",
            "title": "Strategy Model",
            "type": "string"
          }
        },
        "required": [
          "question",
          "strategy_model",
          "answer_model",
          "final_answer_model"
        ],
        "title": "AskRequest",
        "type": "object"
      },
      "AskResponse": {
        "properties": {
          "answer": {
            "description": "Final answer from the knowledge base",
            "title": "Answer",
            "type": "string"
          },
          "question": {
            "description": "Original question",
            "title": "Question",
            "type": "string"
          }
        },
        "required": [
          "answer",
          "question"
        ],
        "title": "AskResponse",
        "type": "object"
      },
      "AssetModel": {
        "properties": {
          "file_path": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "File Path"
          },
          "url": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Url"
          }
        },
        "title": "AssetModel",
        "type": "object"
      },
      "AuditableBatchRequest": {
        "properties": {
          "language": {
            "default": "zh-CN",
            "description": "Target language",
            "title": "Language",
            "type": "string"
          },
          "model_id": {
            "default": "gemini-2.5-flash",
            "description": "Model name for auditable run",
            "title": "Model Id",
            "type": "string"
          },
          "near_dedup_threshold": {
            "default": 0.97,
            "description": "Near-duplicate threshold",
            "maximum": 1.0,
            "minimum": 0.0,
            "title": "Near Dedup Threshold",
            "type": "number"
          },
          "source_ids": {
            "description": "Source ID list",
            "items": {
              "type": "string"
            },
            "minItems": 1,
            "title": "Source Ids",
            "type": "array"
          }
        },
        "required": [
          "source_ids"
        ],
        "title": "AuditableBatchRequest",
        "type": "object"
      },
      "AuditableBatchResponse": {
        "properties": {
          "run_ids": {
            "items": {
              "type": "string"
            },
            "title": "Run Ids",
            "type": "array"
          }
        },
        "required": [
          "run_ids"
        ],
        "title": "AuditableBatchResponse",
        "type": "object"
      },
      "AuditableMetrics": {
        "properties": {
          "coverage_rate": {
            "title": "Coverage Rate",
            "type": "number"
          },
          "dedup_group_count": {
            "title": "Dedup Group Count",
            "type": "integer"
          },
          "duplicate_count": {
            "title": "Duplicate Count",
            "type": "integer"
          },
          "missing_count": {
            "title": "Missing Count",
            "type": "integer"
          },
          "uncited_claims_count": {
            "title": "Uncited Claims Count",
            "type": "integer"
          },
          "unclassified_count": {
            "title": "Unclassified Count",
            "type": "integer"
          },
          "unknown_pid_count": {
            "title": "Unknown Pid Count",
            "type": "integer"
          }
        },
        "required": [
          "coverage_rate",
          "missing_count",
          "duplicate_count",
          "uncited_claims_count",
          "dedup_group_count",
          "unknown_pid_count",
          "unclassified_count"
        ],
        "title": "AuditableMetrics",
        "type": "object"
      },
      "AuditableRepairRequest": {
        "properties": {
          "model_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional model override for targeted repair",
            "title": "Model Id"
          },
          "target_index": {
            "description": "Claim or section index to repair",
            "minimum": 0.0,
            "title": "Target Index",
            "type": "integer"
          }
        },
        "required": [
          "target_index"
        ],
        "title": "AuditableRepairRequest",
        "type": "object"
      },
      "AuditableRunCreateRequest": {
        "properties": {
          "language": {
            "default": "zh-CN",
            "description": "Target language",
            "title": "Language",
            "type": "string"
          },
          "model_id": {
            "default": "gemini-2.5-flash",
            "description": "Model name for auditable run",
            "title": "Model Id",
            "type": "string"
          },
          "near_dedup_threshold": {
            "default": 0.97,
            "description": "Near-duplicate threshold",
            "maximum": 1.0,
            "minimum": 0.0,
            "title": "Near Dedup Threshold",
            "type": "number"
          }
        },
        "title": "AuditableRunCreateRequest",
        "type": "object"
      },
      "AuditableRunResponse": {
        "properties": {
          "claims": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Claims",
            "type": "array"
          },
          "coverage_json": {
            "additionalProperties": true,
            "title": "Coverage Json",
            "type": "object"
          },
          "created": {
            "title": "Created",
            "type": "string"
          },
          "dedup_entries": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Dedup Entries",
            "type": "array"
          },
          "dedup_json": {
            "additionalProperties": true,
            "title": "Dedup Json",
            "type": "object"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "language": {
            "title": "Language",
            "type": "string"
          },
          "metrics": {
            "$ref": "#/components/schemas/AuditableMetrics"
          },
          "model_id": {
            "title": "Model Id",
            "type": "string"
          },
          "near_dedup_threshold": {
            "title": "Near Dedup Threshold",
            "type": "number"
          },
          "result_markdown": {
            "title": "Result Markdown",
            "type": "string"
          },
          "sections": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Sections",
            "type": "array"
          },
          "source_id": {
            "title": "Source Id",
            "type": "string"
          },
          "source_paragraphs": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Source Paragraphs",
            "type": "array"
          },
          "status": {
            "enum": [
              "queued",
              "running",
              "completed",
              "failed"
            ],
            "title": "Status",
            "type": "string"
          },
          "updated": {
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "source_id",
          "status",
          "model_id",
          "language",
          "near_dedup_threshold",
          "metrics",
          "coverage_json",
          "dedup_json",
          "result_markdown",
          "created",
          "updated"
        ],
        "title": "AuditableRunResponse",
        "type": "object"
      },
      "AutoAssignResult": {
        "description": "Response model for auto-assign operation.",
        "properties": {
          "assigned": {
            "additionalProperties": {
              "type": "string"
            },
            "title": "Assigned",
            "type": "object"
          },
          "missing": {
            "items": {
              "type": "string"
            },
            "title": "Missing",
            "type": "array"
          },
          "skipped": {
            "items": {
              "type": "string"
            },
            "title": "Skipped",
            "type": "array"
          }
        },
        "required": [
          "assigned",
          "skipped",
          "missing"
        ],
        "title": "AutoAssignResult",
        "type": "object"
      },
      "Body_create_source_api_sources_post": {
        "properties": {
          "async_processing": {
            "default": "false",
            "title": "Async Processing",
            "type": "string"
          },
          "content": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Content"
          },
          "delete_source": {
            "default": "false",
            "title": "Delete Source",
            "type": "string"
          },
          "embed": {
            "default": "false",
            "title": "Embed",
            "type": "string"
          },
          "file": {
            "anyOf": [
              {
                "contentMediaType": "application/octet-stream",
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "File"
          },
          "notebook_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Notebook Id"
          },
          "notebooks": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Notebooks"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Title"
          },
          "transformations": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Transformations"
          },
          "type": {
            "title": "Type",
            "type": "string"
          },
          "url": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Url"
          }
        },
        "required": [
          "type"
        ],
        "title": "Body_create_source_api_sources_post",
        "type": "object"
      },
      "BuildContextRequest": {
        "properties": {
          "context_config": {
            "additionalProperties": true,
            "description": "Context configuration",
            "title": "Context Config",
            "type": "object"
          },
          "notebook_id": {
            "description": "Notebook ID",
            "title": "Notebook Id",
            "type": "string"
          }
        },
        "required": [
          "notebook_id",
          "context_config"
        ],
        "title": "BuildContextRequest",
        "type": "object"
      },
      "BuildContextResponse": {
        "properties": {
          "char_count": {
            "description": "Character count",
            "title": "Char Count",
            "type": "integer"
          },
          "context": {
            "additionalProperties": true,
            "description": "Built context data",
            "title": "Context",
            "type": "object"
          },
          "token_count": {
            "description": "Estimated token count",
            "title": "Token Count",
            "type": "integer"
          }
        },
        "required": [
          "context",
          "token_count",
          "char_count"
        ],
        "title": "BuildContextResponse",
        "type": "object"
      },
      "ChatMessage": {
        "properties": {
          "content": {
            "description": "Message content",
            "title": "Content",
            "type": "string"
          },
          "id": {
            "description": "Message ID",
            "title": "Id",
            "type": "string"
          },
          "timestamp": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Message timestamp",
            "title": "Timestamp"
          },
          "type": {
            "description": "Message type (human|ai)",
            "title": "Type",
            "type": "string"
          }
        },
        "required": [
          "id",
          "type",
          "content"
        ],
        "title": "ChatMessage",
        "type": "object"
      },
      "ChatSessionResponse": {
        "properties": {
          "created": {
            "description": "Creation timestamp",
            "title": "Created",
            "type": "string"
          },
          "id": {
            "description": "Session ID",
            "title": "Id",
            "type": "string"
          },
          "message_count": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "description": "Number of messages in session",
            "title": "Message Count"
          },
          "model_override": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Model override for this session",
            "title": "Model Override"
          },
          "notebook_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Notebook ID",
            "title": "Notebook Id"
          },
          "title": {
            "description": "Session title",
            "title": "Title",
            "type": "string"
          },
          "updated": {
            "description": "Last update timestamp",
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "title",
          "created",
          "updated"
        ],
        "title": "ChatSessionResponse",
        "type": "object"
      },
      "ChatSessionWithMessagesResponse": {
        "properties": {
          "created": {
            "description": "Creation timestamp",
            "title": "Created",
            "type": "string"
          },
          "id": {
            "description": "Session ID",
            "title": "Id",
            "type": "string"
          },
          "message_count": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "description": "Number of messages in session",
            "title": "Message Count"
          },
          "messages": {
            "description": "Session messages",
            "items": {
              "$ref": "#/components/schemas/ChatMessage"
            },
            "title": "Messages",
            "type": "array"
          },
          "model_override": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Model override for this session",
            "title": "Model Override"
          },
          "notebook_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Notebook ID",
            "title": "Notebook Id"
          },
          "title": {
            "description": "Session title",
            "title": "Title",
            "type": "string"
          },
          "updated": {
            "description": "Last update timestamp",
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "title",
          "created",
          "updated"
        ],
        "title": "ChatSessionWithMessagesResponse",
        "type": "object"
      },
      "CommandCancelResponse": {
        "properties": {
          "cancelled": {
            "title": "Cancelled",
            "type": "boolean"
          },
          "job_id": {
            "title": "Job Id",
            "type": "string"
          },
          "message": {
            "title": "Message",
            "type": "string"
          },
          "status": {
            "title": "Status",
            "type": "string"
          }
        },
        "required": [
          "job_id",
          "cancelled",
          "status",
          "message"
        ],
        "title": "CommandCancelResponse",
        "type": "object"
      },
      "CommandExecutionRequest": {
        "properties": {
          "app": {
            "description": "Application name (e.g., 'open_notebook')",
            "title": "App",
            "type": "string"
          },
          "command": {
            "description": "Command function name (e.g., 'process_text')",
            "title": "Command",
            "type": "string"
          },
          "idempotency_key": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Idempotency key to guarantee at-most-once submission semantics",
            "title": "Idempotency Key"
          },
          "input": {
            "additionalProperties": true,
            "description": "Arguments to pass to the command",
            "title": "Input",
            "type": "object"
          }
        },
        "required": [
          "command",
          "app",
          "input"
        ],
        "title": "CommandExecutionRequest",
        "type": "object"
      },
      "CommandJobResponse": {
        "properties": {
          "job_id": {
            "title": "Job Id",
            "type": "string"
          },
          "message": {
            "title": "Message",
            "type": "string"
          },
          "status": {
            "title": "Status",
            "type": "string"
          }
        },
        "required": [
          "job_id",
          "status",
          "message"
        ],
        "title": "CommandJobResponse",
        "type": "object"
      },
      "CommandJobStatusResponse": {
        "properties": {
          "created": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Created"
          },
          "error_message": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Error Message"
          },
          "job_id": {
            "title": "Job Id",
            "type": "string"
          },
          "progress": {
            "anyOf": [
              {
                "additionalProperties": true,
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Progress"
          },
          "result": {
            "anyOf": [
              {
                "additionalProperties": true,
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Result"
          },
          "status": {
            "title": "Status",
            "type": "string"
          },
          "updated": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Updated"
          }
        },
        "required": [
          "job_id",
          "status"
        ],
        "title": "CommandJobStatusResponse",
        "type": "object"
      },
      "ComputerUseConfirmRequest": {
        "properties": {
          "action_idempotency_key": {
            "description": "Idempotency key for the action being confirmed",
            "title": "Action Idempotency Key",
            "type": "string"
          },
          "confirmation_token": {
            "description": "Single-use confirmation token",
            "title": "Confirmation Token",
            "type": "string"
          }
        },
        "required": [
          "confirmation_token",
          "action_idempotency_key"
        ],
        "title": "ComputerUseConfirmRequest",
        "type": "object"
      },
      "ComputerUseConfirmResponse": {
        "properties": {
          "approved": {
            "description": "Whether confirmation was accepted",
            "title": "Approved",
            "type": "boolean"
          },
          "message": {
            "description": "Confirmation result message",
            "title": "Message",
            "type": "string"
          },
          "session_id": {
            "description": "Computer-use session ID",
            "title": "Session Id",
            "type": "string"
          },
          "status": {
            "description": "Session status after confirmation",
            "title": "Status",
            "type": "string"
          }
        },
        "required": [
          "session_id",
          "status",
          "approved",
          "message"
        ],
        "title": "ComputerUseConfirmResponse",
        "type": "object"
      },
      "ComputerUseSessionCreateRequest": {
        "properties": {
          "dry_run": {
            "default": true,
            "description": "When true, do not execute real browser actions and keep session simulated",
            "title": "Dry Run",
            "type": "boolean"
          },
          "objective": {
            "description": "High-level objective for computer use",
            "title": "Objective",
            "type": "string"
          },
          "require_confirmation": {
            "default": true,
            "description": "Whether high-risk actions require explicit confirmation",
            "title": "Require Confirmation",
            "type": "boolean"
          }
        },
        "required": [
          "objective"
        ],
        "title": "ComputerUseSessionCreateRequest",
        "type": "object"
      },
      "ComputerUseSessionResponse": {
        "properties": {
          "confirmation_required": {
            "default": false,
            "description": "Whether an action currently requires confirmation",
            "title": "Confirmation Required",
            "type": "boolean"
          },
          "created": {
            "description": "Creation timestamp",
            "title": "Created",
            "type": "string"
          },
          "dry_run": {
            "description": "Whether this is a dry-run session",
            "title": "Dry Run",
            "type": "boolean"
          },
          "objective": {
            "description": "Session objective",
            "title": "Objective",
            "type": "string"
          },
          "pending_action_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Pending action ID waiting for confirmation",
            "title": "Pending Action Id"
          },
          "require_confirmation": {
            "description": "Whether confirmation gate is enabled",
            "title": "Require Confirmation",
            "type": "boolean"
          },
          "session_id": {
            "description": "Computer-use session ID",
            "title": "Session Id",
            "type": "string"
          },
          "status": {
            "description": "Session status",
            "title": "Status",
            "type": "string"
          },
          "updated": {
            "description": "Last update timestamp",
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "session_id",
          "status",
          "objective",
          "require_confirmation",
          "dry_run",
          "created",
          "updated"
        ],
        "title": "ComputerUseSessionResponse",
        "type": "object"
      },
      "ContextConfig": {
        "properties": {
          "notes": {
            "additionalProperties": {
              "type": "string"
            },
            "description": "Note inclusion config {note_id: level}",
            "title": "Notes",
            "type": "object"
          },
          "sources": {
            "additionalProperties": {
              "type": "string"
            },
            "description": "Source inclusion config {source_id: level}",
            "title": "Sources",
            "type": "object"
          }
        },
        "title": "ContextConfig",
        "type": "object"
      },
      "ContextIndicator": {
        "properties": {
          "insights": {
            "description": "Insight IDs used in context",
            "items": {
              "type": "string"
            },
            "title": "Insights",
            "type": "array"
          },
          "notes": {
            "description": "Note IDs used in context",
            "items": {
              "type": "string"
            },
            "title": "Notes",
            "type": "array"
          },
          "sources": {
            "description": "Source IDs used in context",
            "items": {
              "type": "string"
            },
            "title": "Sources",
            "type": "array"
          }
        },
        "title": "ContextIndicator",
        "type": "object"
      },
      "ContextRequest": {
        "properties": {
          "context_config": {
            "anyOf": [
              {
                "$ref": "#/components/schemas/ContextConfig"
              },
              {
                "type": "null"
              }
            ],
            "description": "Context configuration"
          },
          "notebook_id": {
            "description": "Notebook ID to get context for",
            "title": "Notebook Id",
            "type": "string"
          }
        },
        "required": [
          "notebook_id"
        ],
        "title": "ContextRequest",
        "type": "object"
      },
      "ContextResponse": {
        "properties": {
          "notebook_id": {
            "title": "Notebook Id",
            "type": "string"
          },
          "notes": {
            "description": "Note context data",
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Notes",
            "type": "array"
          },
          "sources": {
            "description": "Source context data",
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Sources",
            "type": "array"
          },
          "total_tokens": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "description": "Estimated token count",
            "title": "Total Tokens"
          }
        },
        "required": [
          "notebook_id",
          "sources",
          "notes"
        ],
        "title": "ContextResponse",
        "type": "object"
      },
      "CreateCredentialRequest": {
        "description": "Request to create a new credential.",
        "properties": {
          "api_key": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "API key (stored encrypted)",
            "title": "Api Key"
          },
          "api_version": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "API version (Azure)",
            "title": "Api Version"
          },
          "base_url": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Base URL",
            "title": "Base Url"
          },
          "credentials_path": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Credentials file path (Vertex)",
            "title": "Credentials Path"
          },
          "endpoint": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Endpoint URL (Azure)",
            "title": "Endpoint"
          },
          "endpoint_embedding": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Embedding endpoint",
            "title": "Endpoint Embedding"
          },
          "endpoint_llm": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "LLM endpoint",
            "title": "Endpoint Llm"
          },
          "endpoint_stt": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "STT endpoint",
            "title": "Endpoint Stt"
          },
          "endpoint_tts": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "TTS endpoint",
            "title": "Endpoint Tts"
          },
          "location": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Location (Vertex)",
            "title": "Location"
          },
          "modalities": {
            "description": "Supported modalities (language, embedding, text_to_speech, speech_to_text)",
            "items": {
              "type": "string"
            },
            "title": "Modalities",
            "type": "array"
          },
          "name": {
            "description": "Credential name",
            "title": "Name",
            "type": "string"
          },
          "project": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Project ID (Vertex)",
            "title": "Project"
          },
          "provider": {
            "description": "Provider name (Gemini-only runtime supports 'google')",
            "title": "Provider",
            "type": "string"
          }
        },
        "required": [
          "name",
          "provider"
        ],
        "title": "CreateCredentialRequest",
        "type": "object"
      },
      "CreateSessionRequest": {
        "properties": {
          "model_override": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional model override for this session",
            "title": "Model Override"
          },
          "notebook_id": {
            "description": "Notebook ID to create session for",
            "title": "Notebook Id",
            "type": "string"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional session title",
            "title": "Title"
          }
        },
        "required": [
          "notebook_id"
        ],
        "title": "CreateSessionRequest",
        "type": "object"
      },
      "CreateSourceChatSessionRequest": {
        "properties": {
          "model_override": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional model override for this session",
            "title": "Model Override"
          },
          "source_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional source ID (must match path source_id when provided)",
            "title": "Source Id"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional session title",
            "title": "Title"
          }
        },
        "title": "CreateSourceChatSessionRequest",
        "type": "object"
      },
      "CreateSourceInsightRequest": {
        "properties": {
          "model_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Model ID (uses default if not provided)",
            "title": "Model Id"
          },
          "transformation_id": {
            "description": "ID of transformation to apply",
            "title": "Transformation Id",
            "type": "string"
          }
        },
        "required": [
          "transformation_id"
        ],
        "title": "CreateSourceInsightRequest",
        "type": "object"
      },
      "CredentialDeleteResponse": {
        "description": "Response for credential deletion.",
        "properties": {
          "deleted_models": {
            "default": 0,
            "title": "Deleted Models",
            "type": "integer"
          },
          "message": {
            "title": "Message",
            "type": "string"
          }
        },
        "required": [
          "message"
        ],
        "title": "CredentialDeleteResponse",
        "type": "object"
      },
      "CredentialResponse": {
        "description": "Response for a credential (never includes api_key).",
        "properties": {
          "api_version": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Api Version"
          },
          "base_url": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Base Url"
          },
          "created": {
            "title": "Created",
            "type": "string"
          },
          "credentials_path": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Credentials Path"
          },
          "endpoint": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Endpoint"
          },
          "endpoint_embedding": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Endpoint Embedding"
          },
          "endpoint_llm": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Endpoint Llm"
          },
          "endpoint_stt": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Endpoint Stt"
          },
          "endpoint_tts": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Endpoint Tts"
          },
          "has_api_key": {
            "default": false,
            "title": "Has Api Key",
            "type": "boolean"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "location": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Location"
          },
          "modalities": {
            "items": {
              "type": "string"
            },
            "title": "Modalities",
            "type": "array"
          },
          "model_count": {
            "default": 0,
            "title": "Model Count",
            "type": "integer"
          },
          "name": {
            "title": "Name",
            "type": "string"
          },
          "project": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Project"
          },
          "provider": {
            "title": "Provider",
            "type": "string"
          },
          "updated": {
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "provider",
          "modalities",
          "created",
          "updated"
        ],
        "title": "CredentialResponse",
        "type": "object"
      },
      "DeadLetterRequeueResponse": {
        "properties": {
          "command_id": {
            "title": "Command Id",
            "type": "string"
          },
          "entry_id": {
            "title": "Entry Id",
            "type": "string"
          },
          "message": {
            "title": "Message",
            "type": "string"
          }
        },
        "required": [
          "entry_id",
          "command_id",
          "message"
        ],
        "title": "DeadLetterRequeueResponse",
        "type": "object"
      },
      "DefaultModelsResponse": {
        "properties": {
          "default_chat_model": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Default Chat Model"
          },
          "default_embedding_model": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Default Embedding Model"
          },
          "default_speech_to_text_model": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Default Speech To Text Model"
          },
          "default_text_to_speech_model": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Default Text To Speech Model"
          },
          "default_tools_model": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Default Tools Model"
          },
          "default_transformation_model": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Default Transformation Model"
          },
          "large_context_model": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Large Context Model"
          }
        },
        "title": "DefaultModelsResponse",
        "type": "object"
      },
      "DefaultPromptResponse": {
        "properties": {
          "transformation_instructions": {
            "description": "Default transformation instructions",
            "title": "Transformation Instructions",
            "type": "string"
          }
        },
        "required": [
          "transformation_instructions"
        ],
        "title": "DefaultPromptResponse",
        "type": "object"
      },
      "DefaultPromptUpdate": {
        "properties": {
          "transformation_instructions": {
            "description": "Default transformation instructions",
            "title": "Transformation Instructions",
            "type": "string"
          }
        },
        "required": [
          "transformation_instructions"
        ],
        "title": "DefaultPromptUpdate",
        "type": "object"
      },
      "DiscoverModelsResponse": {
        "description": "Response from model discovery.",
        "properties": {
          "credential_id": {
            "title": "Credential Id",
            "type": "string"
          },
          "discovered": {
            "items": {
              "$ref": "#/components/schemas/DiscoveredModelResponse"
            },
            "title": "Discovered",
            "type": "array"
          },
          "provider": {
            "title": "Provider",
            "type": "string"
          }
        },
        "required": [
          "credential_id",
          "provider",
          "discovered"
        ],
        "title": "DiscoverModelsResponse",
        "type": "object"
      },
      "DiscoveredModelResponse": {
        "description": "A model discovered from a provider.",
        "properties": {
          "description": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Description"
          },
          "model_type": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Model Type"
          },
          "name": {
            "title": "Name",
            "type": "string"
          },
          "provider": {
            "title": "Provider",
            "type": "string"
          }
        },
        "required": [
          "name",
          "provider"
        ],
        "title": "DiscoveredModelResponse",
        "type": "object"
      },
      "DraftCreateRequest": {
        "properties": {
          "language": {
            "default": "zh-CN",
            "description": "Target language",
            "title": "Language",
            "type": "string"
          },
          "model_id": {
            "default": "gemini-2.5-flash",
            "description": "Model name for notebook draft generation",
            "title": "Model Id",
            "type": "string"
          },
          "near_dedup_threshold": {
            "default": 0.97,
            "description": "Near-duplicate threshold",
            "maximum": 1.0,
            "minimum": 0.0,
            "title": "Near Dedup Threshold",
            "type": "number"
          },
          "note_ids": {
            "description": "Optional note IDs reserved for future draft enrichment",
            "items": {
              "type": "string"
            },
            "title": "Note Ids",
            "type": "array"
          },
          "source_ids": {
            "description": "Source IDs to include in the draft",
            "items": {
              "type": "string"
            },
            "minItems": 1,
            "title": "Source Ids",
            "type": "array"
          },
          "thread_ids": {
            "description": "Optional research thread IDs reserved for future draft enrichment",
            "items": {
              "type": "string"
            },
            "title": "Thread Ids",
            "type": "array"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional draft title",
            "title": "Title"
          }
        },
        "required": [
          "source_ids"
        ],
        "title": "DraftCreateRequest",
        "type": "object"
      },
      "DraftRerunRequest": {
        "properties": {
          "language": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional replacement language",
            "title": "Language"
          },
          "model_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional replacement model ID",
            "title": "Model Id"
          },
          "near_dedup_threshold": {
            "anyOf": [
              {
                "maximum": 1.0,
                "minimum": 0.0,
                "type": "number"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional replacement dedup threshold",
            "title": "Near Dedup Threshold"
          },
          "note_ids": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional replacement note IDs",
            "title": "Note Ids"
          },
          "source_ids": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional replacement source IDs",
            "title": "Source Ids"
          },
          "thread_ids": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional replacement thread IDs",
            "title": "Thread Ids"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional replacement title",
            "title": "Title"
          }
        },
        "title": "DraftRerunRequest",
        "type": "object"
      },
      "DraftResponse": {
        "properties": {
          "claims": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Claims",
            "type": "array"
          },
          "coverage_json": {
            "additionalProperties": true,
            "title": "Coverage Json",
            "type": "object"
          },
          "created": {
            "title": "Created",
            "type": "string"
          },
          "dedup_entries": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Dedup Entries",
            "type": "array"
          },
          "dedup_json": {
            "additionalProperties": true,
            "title": "Dedup Json",
            "type": "object"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "language": {
            "title": "Language",
            "type": "string"
          },
          "metrics": {
            "$ref": "#/components/schemas/AuditableMetrics"
          },
          "model_id": {
            "title": "Model Id",
            "type": "string"
          },
          "near_dedup_threshold": {
            "title": "Near Dedup Threshold",
            "type": "number"
          },
          "note_ids": {
            "items": {
              "type": "string"
            },
            "title": "Note Ids",
            "type": "array"
          },
          "notebook_id": {
            "title": "Notebook Id",
            "type": "string"
          },
          "parent_draft_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Parent draft ID when this draft is a rerun revision",
            "title": "Parent Draft Id"
          },
          "result_markdown": {
            "title": "Result Markdown",
            "type": "string"
          },
          "sections": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Sections",
            "type": "array"
          },
          "source_ids": {
            "items": {
              "type": "string"
            },
            "title": "Source Ids",
            "type": "array"
          },
          "source_paragraphs": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Source Paragraphs",
            "type": "array"
          },
          "status": {
            "enum": [
              "queued",
              "running",
              "completed",
              "failed",
              "verified"
            ],
            "title": "Status",
            "type": "string"
          },
          "thread_ids": {
            "items": {
              "type": "string"
            },
            "title": "Thread Ids",
            "type": "array"
          },
          "title": {
            "title": "Title",
            "type": "string"
          },
          "updated": {
            "title": "Updated",
            "type": "string"
          },
          "verified_brief_snapshot": {
            "anyOf": [
              {
                "additionalProperties": true,
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Verified Brief Snapshot"
          },
          "version": {
            "description": "Draft version number",
            "title": "Version",
            "type": "integer"
          }
        },
        "required": [
          "id",
          "notebook_id",
          "title",
          "status",
          "model_id",
          "language",
          "near_dedup_threshold",
          "version",
          "metrics",
          "coverage_json",
          "dedup_json",
          "result_markdown",
          "created",
          "updated"
        ],
        "title": "DraftResponse",
        "type": "object"
      },
      "EmbedRequest": {
        "properties": {
          "async_processing": {
            "default": false,
            "description": "Process asynchronously in background",
            "title": "Async Processing",
            "type": "boolean"
          },
          "item_id": {
            "description": "ID of the item to embed",
            "title": "Item Id",
            "type": "string"
          },
          "item_type": {
            "description": "Type of item (source, note)",
            "title": "Item Type",
            "type": "string"
          }
        },
        "required": [
          "item_id",
          "item_type"
        ],
        "title": "EmbedRequest",
        "type": "object"
      },
      "EmbedResponse": {
        "properties": {
          "command_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Command ID for async processing",
            "title": "Command Id"
          },
          "item_id": {
            "description": "ID of the item that was embedded",
            "title": "Item Id",
            "type": "string"
          },
          "item_type": {
            "description": "Type of item that was embedded",
            "title": "Item Type",
            "type": "string"
          },
          "message": {
            "description": "Result message",
            "title": "Message",
            "type": "string"
          },
          "success": {
            "description": "Whether embedding was successful",
            "title": "Success",
            "type": "boolean"
          }
        },
        "required": [
          "success",
          "message",
          "item_id",
          "item_type"
        ],
        "title": "EmbedResponse",
        "type": "object"
      },
      "EpisodeProfileCreate": {
        "properties": {
          "default_briefing": {
            "description": "Default briefing template",
            "title": "Default Briefing",
            "type": "string"
          },
          "description": {
            "default": "",
            "description": "Profile description",
            "title": "Description",
            "type": "string"
          },
          "name": {
            "description": "Unique profile name",
            "title": "Name",
            "type": "string"
          },
          "num_segments": {
            "default": 5,
            "description": "Number of podcast segments",
            "title": "Num Segments",
            "type": "integer"
          },
          "outline_model": {
            "description": "AI model for outline generation",
            "title": "Outline Model",
            "type": "string"
          },
          "outline_provider": {
            "description": "AI provider for outline generation",
            "title": "Outline Provider",
            "type": "string"
          },
          "speaker_config": {
            "description": "Reference to speaker profile name",
            "title": "Speaker Config",
            "type": "string"
          },
          "transcript_model": {
            "description": "AI model for transcript generation",
            "title": "Transcript Model",
            "type": "string"
          },
          "transcript_provider": {
            "description": "AI provider for transcript generation",
            "title": "Transcript Provider",
            "type": "string"
          }
        },
        "required": [
          "name",
          "speaker_config",
          "outline_provider",
          "outline_model",
          "transcript_provider",
          "transcript_model",
          "default_briefing"
        ],
        "title": "EpisodeProfileCreate",
        "type": "object"
      },
      "EpisodeProfileResponse": {
        "properties": {
          "default_briefing": {
            "title": "Default Briefing",
            "type": "string"
          },
          "description": {
            "title": "Description",
            "type": "string"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "name": {
            "title": "Name",
            "type": "string"
          },
          "num_segments": {
            "title": "Num Segments",
            "type": "integer"
          },
          "outline_model": {
            "title": "Outline Model",
            "type": "string"
          },
          "outline_provider": {
            "title": "Outline Provider",
            "type": "string"
          },
          "speaker_config": {
            "title": "Speaker Config",
            "type": "string"
          },
          "transcript_model": {
            "title": "Transcript Model",
            "type": "string"
          },
          "transcript_provider": {
            "title": "Transcript Provider",
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "description",
          "speaker_config",
          "outline_provider",
          "outline_model",
          "transcript_provider",
          "transcript_model",
          "default_briefing",
          "num_segments"
        ],
        "title": "EpisodeProfileResponse",
        "type": "object"
      },
      "ErrorResponse": {
        "properties": {
          "error": {
            "title": "Error",
            "type": "string"
          },
          "message": {
            "title": "Message",
            "type": "string"
          }
        },
        "required": [
          "error",
          "message"
        ],
        "title": "ErrorResponse",
        "type": "object"
      },
      "ExecuteChatRequest": {
        "properties": {
          "context": {
            "additionalProperties": true,
            "description": "Chat context with sources and notes",
            "title": "Context",
            "type": "object"
          },
          "message": {
            "description": "User message content",
            "title": "Message",
            "type": "string"
          },
          "model_override": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional model override for this message",
            "title": "Model Override"
          },
          "session_id": {
            "description": "Chat session ID",
            "title": "Session Id",
            "type": "string"
          }
        },
        "required": [
          "session_id",
          "message",
          "context"
        ],
        "title": "ExecuteChatRequest",
        "type": "object"
      },
      "ExecuteChatResponse": {
        "properties": {
          "messages": {
            "description": "Updated message list",
            "items": {
              "$ref": "#/components/schemas/ChatMessage"
            },
            "title": "Messages",
            "type": "array"
          },
          "session_id": {
            "description": "Session ID",
            "title": "Session Id",
            "type": "string"
          }
        },
        "required": [
          "session_id",
          "messages"
        ],
        "title": "ExecuteChatResponse",
        "type": "object"
      },
      "HTTPValidationError": {
        "properties": {
          "detail": {
            "items": {
              "$ref": "#/components/schemas/ValidationError"
            },
            "title": "Detail",
            "type": "array"
          }
        },
        "title": "HTTPValidationError",
        "type": "object"
      },
      "InsightCreationResponse": {
        "description": "Response for async insight creation.",
        "properties": {
          "command_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Command Id"
          },
          "message": {
            "default": "Insight generation started",
            "title": "Message",
            "type": "string"
          },
          "source_id": {
            "title": "Source Id",
            "type": "string"
          },
          "status": {
            "const": "pending",
            "default": "pending",
            "title": "Status",
            "type": "string"
          },
          "transformation_id": {
            "title": "Transformation Id",
            "type": "string"
          }
        },
        "required": [
          "source_id",
          "transformation_id"
        ],
        "title": "InsightCreationResponse",
        "type": "object"
      },
      "ModelCreate": {
        "properties": {
          "credential": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Credential ID to link this model to",
            "title": "Credential"
          },
          "name": {
            "description": "Model name (Gemini model ID)",
            "title": "Name",
            "type": "string"
          },
          "provider": {
            "description": "Provider name (Gemini-only runtime uses 'google')",
            "title": "Provider",
            "type": "string"
          },
          "type": {
            "description": "Model type (language, embedding, text_to_speech, speech_to_text)",
            "title": "Type",
            "type": "string"
          }
        },
        "required": [
          "name",
          "provider",
          "type"
        ],
        "title": "ModelCreate",
        "type": "object"
      },
      "ModelResponse": {
        "properties": {
          "created": {
            "title": "Created",
            "type": "string"
          },
          "credential": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Credential"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "name": {
            "title": "Name",
            "type": "string"
          },
          "provider": {
            "title": "Provider",
            "type": "string"
          },
          "type": {
            "title": "Type",
            "type": "string"
          },
          "updated": {
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "provider",
          "type",
          "created",
          "updated"
        ],
        "title": "ModelResponse",
        "type": "object"
      },
      "ModelTestResponse": {
        "description": "Response model for individual model test.",
        "properties": {
          "details": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Details"
          },
          "message": {
            "title": "Message",
            "type": "string"
          },
          "success": {
            "title": "Success",
            "type": "boolean"
          }
        },
        "required": [
          "success",
          "message"
        ],
        "title": "ModelTestResponse",
        "type": "object"
      },
      "NoteCreate": {
        "properties": {
          "content": {
            "description": "Note content",
            "title": "Content",
            "type": "string"
          },
          "note_type": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "default": "human",
            "description": "Type of note (human, ai)",
            "title": "Note Type"
          },
          "notebook_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Notebook ID to add the note to",
            "title": "Notebook Id"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Note title",
            "title": "Title"
          }
        },
        "required": [
          "content"
        ],
        "title": "NoteCreate",
        "type": "object"
      },
      "NoteResponse": {
        "properties": {
          "command_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Command Id"
          },
          "content": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Content"
          },
          "created": {
            "title": "Created",
            "type": "string"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "note_type": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Note Type"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Title"
          },
          "updated": {
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "title",
          "content",
          "note_type",
          "created",
          "updated"
        ],
        "title": "NoteResponse",
        "type": "object"
      },
      "NoteUpdate": {
        "properties": {
          "content": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Note content",
            "title": "Content"
          },
          "note_type": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Type of note (human, ai)",
            "title": "Note Type"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Note title",
            "title": "Title"
          }
        },
        "title": "NoteUpdate",
        "type": "object"
      },
      "NotebookCreate": {
        "properties": {
          "description": {
            "default": "",
            "description": "Description of the notebook",
            "title": "Description",
            "type": "string"
          },
          "name": {
            "description": "Name of the notebook",
            "title": "Name",
            "type": "string"
          }
        },
        "required": [
          "name"
        ],
        "title": "NotebookCreate",
        "type": "object"
      },
      "NotebookDeletePreview": {
        "properties": {
          "exclusive_source_count": {
            "description": "Number of sources only in this notebook",
            "title": "Exclusive Source Count",
            "type": "integer"
          },
          "note_count": {
            "description": "Number of notes that will be deleted",
            "title": "Note Count",
            "type": "integer"
          },
          "notebook_id": {
            "description": "ID of the notebook",
            "title": "Notebook Id",
            "type": "string"
          },
          "notebook_name": {
            "description": "Name of the notebook",
            "title": "Notebook Name",
            "type": "string"
          },
          "shared_source_count": {
            "description": "Number of sources shared with other notebooks",
            "title": "Shared Source Count",
            "type": "integer"
          }
        },
        "required": [
          "notebook_id",
          "notebook_name",
          "note_count",
          "exclusive_source_count",
          "shared_source_count"
        ],
        "title": "NotebookDeletePreview",
        "type": "object"
      },
      "NotebookDeleteResponse": {
        "properties": {
          "deleted_notes": {
            "description": "Number of notes deleted",
            "title": "Deleted Notes",
            "type": "integer"
          },
          "deleted_sources": {
            "description": "Number of exclusive sources deleted",
            "title": "Deleted Sources",
            "type": "integer"
          },
          "message": {
            "description": "Success message",
            "title": "Message",
            "type": "string"
          },
          "unlinked_sources": {
            "description": "Number of sources unlinked from notebook",
            "title": "Unlinked Sources",
            "type": "integer"
          }
        },
        "required": [
          "message",
          "deleted_notes",
          "deleted_sources",
          "unlinked_sources"
        ],
        "title": "NotebookDeleteResponse",
        "type": "object"
      },
      "NotebookResponse": {
        "properties": {
          "archived": {
            "title": "Archived",
            "type": "boolean"
          },
          "created": {
            "title": "Created",
            "type": "string"
          },
          "description": {
            "title": "Description",
            "type": "string"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "name": {
            "title": "Name",
            "type": "string"
          },
          "note_count": {
            "title": "Note Count",
            "type": "integer"
          },
          "source_count": {
            "title": "Source Count",
            "type": "integer"
          },
          "updated": {
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "description",
          "archived",
          "created",
          "updated",
          "source_count",
          "note_count"
        ],
        "title": "NotebookResponse",
        "type": "object"
      },
      "NotebookUpdate": {
        "properties": {
          "archived": {
            "anyOf": [
              {
                "type": "boolean"
              },
              {
                "type": "null"
              }
            ],
            "description": "Whether the notebook is archived",
            "title": "Archived"
          },
          "description": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Description of the notebook",
            "title": "Description"
          },
          "name": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Name of the notebook",
            "title": "Name"
          }
        },
        "title": "NotebookUpdate",
        "type": "object"
      },
      "PodcastEpisodeResponse": {
        "properties": {
          "audio_file": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Audio File"
          },
          "audio_url": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Audio Url"
          },
          "briefing": {
            "title": "Briefing",
            "type": "string"
          },
          "created": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Created"
          },
          "episode_profile": {
            "additionalProperties": true,
            "title": "Episode Profile",
            "type": "object"
          },
          "error_message": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Error Message"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "job_status": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Job Status"
          },
          "name": {
            "title": "Name",
            "type": "string"
          },
          "outline": {
            "anyOf": [
              {
                "additionalProperties": true,
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Outline"
          },
          "speaker_profile": {
            "additionalProperties": true,
            "title": "Speaker Profile",
            "type": "object"
          },
          "transcript": {
            "anyOf": [
              {
                "additionalProperties": true,
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Transcript"
          }
        },
        "required": [
          "id",
          "name",
          "episode_profile",
          "speaker_profile",
          "briefing"
        ],
        "title": "PodcastEpisodeResponse",
        "type": "object"
      },
      "PodcastGenerationRequest": {
        "description": "Request model for podcast generation",
        "properties": {
          "briefing_suffix": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Briefing Suffix"
          },
          "content": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Content"
          },
          "draft_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Draft Id"
          },
          "episode_name": {
            "title": "Episode Name",
            "type": "string"
          },
          "episode_profile": {
            "title": "Episode Profile",
            "type": "string"
          },
          "notebook_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Notebook Id"
          },
          "speaker_profile": {
            "title": "Speaker Profile",
            "type": "string"
          }
        },
        "required": [
          "episode_profile",
          "speaker_profile",
          "episode_name"
        ],
        "title": "PodcastGenerationRequest",
        "type": "object"
      },
      "PodcastGenerationResponse": {
        "description": "Response model for podcast generation",
        "properties": {
          "episode_name": {
            "title": "Episode Name",
            "type": "string"
          },
          "episode_profile": {
            "title": "Episode Profile",
            "type": "string"
          },
          "job_id": {
            "title": "Job Id",
            "type": "string"
          },
          "message": {
            "title": "Message",
            "type": "string"
          },
          "status": {
            "title": "Status",
            "type": "string"
          }
        },
        "required": [
          "job_id",
          "status",
          "message",
          "episode_profile",
          "episode_name"
        ],
        "title": "PodcastGenerationResponse",
        "type": "object"
      },
      "ProviderAvailabilityResponse": {
        "properties": {
          "available": {
            "description": "List of available providers",
            "items": {
              "type": "string"
            },
            "title": "Available",
            "type": "array"
          },
          "supported_types": {
            "additionalProperties": {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            "description": "Provider to supported model types mapping",
            "title": "Supported Types",
            "type": "object"
          },
          "unavailable": {
            "description": "List of unavailable providers",
            "items": {
              "type": "string"
            },
            "title": "Unavailable",
            "type": "array"
          }
        },
        "required": [
          "available",
          "unavailable",
          "supported_types"
        ],
        "title": "ProviderAvailabilityResponse",
        "type": "object"
      },
      "ProviderDiscoveredModelResponse": {
        "description": "Response model for a provider discovery result.",
        "properties": {
          "description": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Description"
          },
          "model_type": {
            "title": "Model Type",
            "type": "string"
          },
          "name": {
            "title": "Name",
            "type": "string"
          },
          "provider": {
            "title": "Provider",
            "type": "string"
          }
        },
        "required": [
          "name",
          "provider",
          "model_type"
        ],
        "title": "ProviderDiscoveredModelResponse",
        "type": "object"
      },
      "ProviderModelCountResponse": {
        "description": "Response model for provider model counts.",
        "properties": {
          "counts": {
            "additionalProperties": {
              "type": "integer"
            },
            "title": "Counts",
            "type": "object"
          },
          "provider": {
            "title": "Provider",
            "type": "string"
          },
          "total": {
            "title": "Total",
            "type": "integer"
          }
        },
        "required": [
          "provider",
          "counts",
          "total"
        ],
        "title": "ProviderModelCountResponse",
        "type": "object"
      },
      "ProviderPolicyResponse": {
        "description": "Provider fallback policy for each modality.",
        "properties": {
          "embedding": {
            "description": "Provider order for embedding models",
            "items": {
              "type": "string"
            },
            "title": "Embedding",
            "type": "array"
          },
          "language": {
            "description": "Provider order for language models",
            "items": {
              "type": "string"
            },
            "title": "Language",
            "type": "array"
          },
          "speech_to_text": {
            "description": "Provider order for speech-to-text models",
            "items": {
              "type": "string"
            },
            "title": "Speech To Text",
            "type": "array"
          },
          "text_to_speech": {
            "description": "Provider order for text-to-speech models",
            "items": {
              "type": "string"
            },
            "title": "Text To Speech",
            "type": "array"
          }
        },
        "required": [
          "language",
          "embedding",
          "speech_to_text",
          "text_to_speech"
        ],
        "title": "ProviderPolicyResponse",
        "type": "object"
      },
      "ProviderPolicyUpdateRequest": {
        "description": "Partial update request for provider fallback policy.",
        "properties": {
          "embedding": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Embedding"
          },
          "language": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Language"
          },
          "speech_to_text": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Speech To Text"
          },
          "text_to_speech": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Text To Speech"
          }
        },
        "title": "ProviderPolicyUpdateRequest",
        "type": "object"
      },
      "ProviderSyncResponse": {
        "description": "Response model for provider sync operation.",
        "properties": {
          "discovered": {
            "title": "Discovered",
            "type": "integer"
          },
          "existing": {
            "title": "Existing",
            "type": "integer"
          },
          "new": {
            "title": "New",
            "type": "integer"
          },
          "provider": {
            "title": "Provider",
            "type": "string"
          }
        },
        "required": [
          "provider",
          "discovered",
          "new",
          "existing"
        ],
        "title": "ProviderSyncResponse",
        "type": "object"
      },
      "RebuildProgress": {
        "properties": {
          "percentage": {
            "description": "Progress percentage",
            "title": "Percentage",
            "type": "number"
          },
          "processed": {
            "description": "Number of items processed",
            "title": "Processed",
            "type": "integer"
          },
          "total": {
            "description": "Total items to process",
            "title": "Total",
            "type": "integer"
          }
        },
        "required": [
          "processed",
          "total",
          "percentage"
        ],
        "title": "RebuildProgress",
        "type": "object"
      },
      "RebuildRequest": {
        "properties": {
          "include_insights": {
            "default": true,
            "description": "Include insights in rebuild",
            "title": "Include Insights",
            "type": "boolean"
          },
          "include_notes": {
            "default": true,
            "description": "Include notes in rebuild",
            "title": "Include Notes",
            "type": "boolean"
          },
          "include_sources": {
            "default": true,
            "description": "Include sources in rebuild",
            "title": "Include Sources",
            "type": "boolean"
          },
          "mode": {
            "description": "Rebuild mode: 'existing' only re-embeds items with embeddings, 'all' embeds everything",
            "enum": [
              "existing",
              "all"
            ],
            "title": "Mode",
            "type": "string"
          }
        },
        "required": [
          "mode"
        ],
        "title": "RebuildRequest",
        "type": "object"
      },
      "RebuildResponse": {
        "properties": {
          "command_id": {
            "description": "Command ID to track progress",
            "title": "Command Id",
            "type": "string"
          },
          "message": {
            "description": "Status message",
            "title": "Message",
            "type": "string"
          },
          "total_items": {
            "description": "Estimated number of items to process",
            "title": "Total Items",
            "type": "integer"
          }
        },
        "required": [
          "command_id",
          "total_items",
          "message"
        ],
        "title": "RebuildResponse",
        "type": "object"
      },
      "RebuildStats": {
        "properties": {
          "failed": {
            "default": 0,
            "description": "Failed items",
            "title": "Failed",
            "type": "integer"
          },
          "insights": {
            "default": 0,
            "description": "Insights processed",
            "title": "Insights",
            "type": "integer"
          },
          "notes": {
            "default": 0,
            "description": "Notes processed",
            "title": "Notes",
            "type": "integer"
          },
          "sources": {
            "default": 0,
            "description": "Sources processed",
            "title": "Sources",
            "type": "integer"
          }
        },
        "title": "RebuildStats",
        "type": "object"
      },
      "RebuildStatusResponse": {
        "properties": {
          "command_id": {
            "description": "Command ID",
            "title": "Command Id",
            "type": "string"
          },
          "completed_at": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Completed At"
          },
          "error_message": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Error Message"
          },
          "progress": {
            "anyOf": [
              {
                "$ref": "#/components/schemas/RebuildProgress"
              },
              {
                "type": "null"
              }
            ]
          },
          "started_at": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Started At"
          },
          "stats": {
            "anyOf": [
              {
                "$ref": "#/components/schemas/RebuildStats"
              },
              {
                "type": "null"
              }
            ]
          },
          "status": {
            "description": "Status: queued, running, completed, failed",
            "title": "Status",
            "type": "string"
          }
        },
        "required": [
          "command_id",
          "status"
        ],
        "title": "RebuildStatusResponse",
        "type": "object"
      },
      "RegisterModelData": {
        "description": "A model to register with user-specified type.",
        "properties": {
          "model_type": {
            "title": "Model Type",
            "type": "string"
          },
          "name": {
            "title": "Name",
            "type": "string"
          },
          "provider": {
            "title": "Provider",
            "type": "string"
          }
        },
        "required": [
          "name",
          "provider",
          "model_type"
        ],
        "title": "RegisterModelData",
        "type": "object"
      },
      "RegisterModelsRequest": {
        "description": "Request to register discovered models.",
        "properties": {
          "models": {
            "items": {
              "$ref": "#/components/schemas/RegisterModelData"
            },
            "title": "Models",
            "type": "array"
          }
        },
        "required": [
          "models"
        ],
        "title": "RegisterModelsRequest",
        "type": "object"
      },
      "RegisterModelsResponse": {
        "description": "Response from model registration.",
        "properties": {
          "created": {
            "title": "Created",
            "type": "integer"
          },
          "existing": {
            "title": "Existing",
            "type": "integer"
          }
        },
        "required": [
          "created",
          "existing"
        ],
        "title": "RegisterModelsResponse",
        "type": "object"
      },
      "ResearchThreadCreateRequest": {
        "properties": {
          "answer": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Saved answer text",
            "title": "Answer"
          },
          "insight_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Origin source insight ID for insight-seeded threads",
            "title": "Insight Id"
          },
          "insight_type": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Origin insight type for insight-seeded threads",
            "title": "Insight Type"
          },
          "note_ids": {
            "description": "Attached note IDs",
            "items": {
              "type": "string"
            },
            "title": "Note Ids",
            "type": "array"
          },
          "question": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Question or query text",
            "title": "Question"
          },
          "search_results": {
            "description": "Saved search result snapshots",
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Search Results",
            "type": "array"
          },
          "seed_kind": {
            "description": "Canonical seed type for the thread",
            "enum": [
              "search",
              "ask",
              "notebook_chat",
              "insight"
            ],
            "title": "Seed Kind",
            "type": "string"
          },
          "source_ids": {
            "description": "Attached source IDs",
            "items": {
              "type": "string"
            },
            "title": "Source Ids",
            "type": "array"
          },
          "title": {
            "description": "Research thread title",
            "title": "Title",
            "type": "string"
          }
        },
        "required": [
          "title",
          "seed_kind"
        ],
        "title": "ResearchThreadCreateRequest",
        "type": "object"
      },
      "ResearchThreadEntryRequest": {
        "properties": {
          "content": {
            "description": "Entry content",
            "title": "Content",
            "type": "string"
          },
          "entry_type": {
            "description": "Entry type",
            "enum": [
              "search_result",
              "answer_snapshot",
              "note_snapshot",
              "insight_snapshot"
            ],
            "title": "Entry Type",
            "type": "string"
          },
          "metadata": {
            "additionalProperties": true,
            "description": "Entry metadata",
            "title": "Metadata",
            "type": "object"
          },
          "note_ids": {
            "description": "Related note IDs",
            "items": {
              "type": "string"
            },
            "title": "Note Ids",
            "type": "array"
          },
          "source_ids": {
            "description": "Related source IDs",
            "items": {
              "type": "string"
            },
            "title": "Source Ids",
            "type": "array"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Entry title",
            "title": "Title"
          }
        },
        "required": [
          "entry_type",
          "content"
        ],
        "title": "ResearchThreadEntryRequest",
        "type": "object"
      },
      "ResearchThreadResponse": {
        "properties": {
          "created": {
            "title": "Created",
            "type": "string"
          },
          "entries": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Entries",
            "type": "array"
          },
          "entry_count": {
            "default": 0,
            "title": "Entry Count",
            "type": "integer"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "note_ids": {
            "items": {
              "type": "string"
            },
            "title": "Note Ids",
            "type": "array"
          },
          "notebook_id": {
            "title": "Notebook Id",
            "type": "string"
          },
          "seed_kind": {
            "enum": [
              "search",
              "ask",
              "notebook_chat",
              "insight"
            ],
            "title": "Seed Kind",
            "type": "string"
          },
          "source_ids": {
            "items": {
              "type": "string"
            },
            "title": "Source Ids",
            "type": "array"
          },
          "title": {
            "title": "Title",
            "type": "string"
          },
          "updated": {
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "notebook_id",
          "title",
          "seed_kind",
          "created",
          "updated"
        ],
        "title": "ResearchThreadResponse",
        "type": "object"
      },
      "SaveAsNoteRequest": {
        "properties": {
          "notebook_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Notebook ID to add note to",
            "title": "Notebook Id"
          }
        },
        "title": "SaveAsNoteRequest",
        "type": "object"
      },
      "SearchRequest": {
        "properties": {
          "limit": {
            "default": 100,
            "description": "Maximum number of results",
            "maximum": 1000.0,
            "title": "Limit",
            "type": "integer"
          },
          "minimum_score": {
            "default": 0.2,
            "description": "Minimum score for vector search",
            "maximum": 1.0,
            "minimum": 0.0,
            "title": "Minimum Score",
            "type": "number"
          },
          "query": {
            "description": "Search query",
            "title": "Query",
            "type": "string"
          },
          "search_notes": {
            "default": true,
            "description": "Include notes in search",
            "title": "Search Notes",
            "type": "boolean"
          },
          "search_sources": {
            "default": true,
            "description": "Include sources in search",
            "title": "Search Sources",
            "type": "boolean"
          },
          "type": {
            "default": "text",
            "description": "Search type",
            "enum": [
              "text",
              "vector"
            ],
            "title": "Type",
            "type": "string"
          }
        },
        "required": [
          "query"
        ],
        "title": "SearchRequest",
        "type": "object"
      },
      "SearchResponse": {
        "properties": {
          "results": {
            "description": "Search results",
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Results",
            "type": "array"
          },
          "search_type": {
            "description": "Type of search performed",
            "title": "Search Type",
            "type": "string"
          },
          "total_count": {
            "description": "Total number of results",
            "title": "Total Count",
            "type": "integer"
          }
        },
        "required": [
          "results",
          "total_count",
          "search_type"
        ],
        "title": "SearchResponse",
        "type": "object"
      },
      "SendMessageRequest": {
        "properties": {
          "message": {
            "description": "User message content",
            "title": "Message",
            "type": "string"
          },
          "model_override": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional model override for this message",
            "title": "Model Override"
          }
        },
        "required": [
          "message"
        ],
        "title": "SendMessageRequest",
        "type": "object"
      },
      "SettingsResponse": {
        "properties": {
          "auto_delete_files": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Auto Delete Files"
          },
          "default_content_processing_engine_doc": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Default Content Processing Engine Doc"
          },
          "default_content_processing_engine_url": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Default Content Processing Engine Url"
          },
          "default_embedding_option": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Default Embedding Option"
          },
          "youtube_preferred_languages": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Youtube Preferred Languages"
          }
        },
        "title": "SettingsResponse",
        "type": "object"
      },
      "SettingsUpdate": {
        "properties": {
          "auto_delete_files": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Auto Delete Files"
          },
          "default_content_processing_engine_doc": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Default Content Processing Engine Doc"
          },
          "default_content_processing_engine_url": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Default Content Processing Engine Url"
          },
          "default_embedding_option": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Default Embedding Option"
          },
          "youtube_preferred_languages": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Youtube Preferred Languages"
          }
        },
        "title": "SettingsUpdate",
        "type": "object"
      },
      "SourceChatSessionResponse": {
        "properties": {
          "created": {
            "description": "Creation timestamp",
            "title": "Created",
            "type": "string"
          },
          "id": {
            "description": "Session ID",
            "title": "Id",
            "type": "string"
          },
          "message_count": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "description": "Number of messages in session",
            "title": "Message Count"
          },
          "model_override": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Model override for this session",
            "title": "Model Override"
          },
          "source_id": {
            "description": "Source ID",
            "title": "Source Id",
            "type": "string"
          },
          "title": {
            "description": "Session title",
            "title": "Title",
            "type": "string"
          },
          "updated": {
            "description": "Last update timestamp",
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "title",
          "source_id",
          "created",
          "updated"
        ],
        "title": "SourceChatSessionResponse",
        "type": "object"
      },
      "SourceChatSessionWithMessagesResponse": {
        "properties": {
          "context_indicators": {
            "anyOf": [
              {
                "$ref": "#/components/schemas/ContextIndicator"
              },
              {
                "type": "null"
              }
            ],
            "description": "Context indicators from last response"
          },
          "created": {
            "description": "Creation timestamp",
            "title": "Created",
            "type": "string"
          },
          "id": {
            "description": "Session ID",
            "title": "Id",
            "type": "string"
          },
          "message_count": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "description": "Number of messages in session",
            "title": "Message Count"
          },
          "messages": {
            "description": "Session messages",
            "items": {
              "$ref": "#/components/schemas/ChatMessage"
            },
            "title": "Messages",
            "type": "array"
          },
          "model_override": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Model override for this session",
            "title": "Model Override"
          },
          "source_id": {
            "description": "Source ID",
            "title": "Source Id",
            "type": "string"
          },
          "title": {
            "description": "Session title",
            "title": "Title",
            "type": "string"
          },
          "updated": {
            "description": "Last update timestamp",
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "title",
          "source_id",
          "created",
          "updated"
        ],
        "title": "SourceChatSessionWithMessagesResponse",
        "type": "object"
      },
      "SourceCreate": {
        "properties": {
          "async_processing": {
            "default": false,
            "description": "Whether to process source asynchronously",
            "title": "Async Processing",
            "type": "boolean"
          },
          "content": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Text content for text type",
            "title": "Content"
          },
          "delete_source": {
            "default": false,
            "description": "Whether to delete uploaded file after processing",
            "title": "Delete Source",
            "type": "boolean"
          },
          "embed": {
            "default": false,
            "description": "Whether to embed content for vector search",
            "title": "Embed",
            "type": "boolean"
          },
          "file_path": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "File path for upload type",
            "title": "File Path"
          },
          "notebook_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Notebook ID to add the source to (deprecated, use notebooks)",
            "title": "Notebook Id"
          },
          "notebooks": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "description": "List of notebook IDs to add the source to",
            "title": "Notebooks"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Source title",
            "title": "Title"
          },
          "transformations": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "description": "Transformation IDs to apply",
            "title": "Transformations"
          },
          "type": {
            "description": "Source type: link, upload, or text",
            "title": "Type",
            "type": "string"
          },
          "url": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "URL for link type",
            "title": "Url"
          }
        },
        "required": [
          "type"
        ],
        "title": "SourceCreate",
        "type": "object"
      },
      "SourceInsightResponse": {
        "properties": {
          "content": {
            "title": "Content",
            "type": "string"
          },
          "created": {
            "title": "Created",
            "type": "string"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "insight_type": {
            "title": "Insight Type",
            "type": "string"
          },
          "source_id": {
            "title": "Source Id",
            "type": "string"
          },
          "updated": {
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "source_id",
          "insight_type",
          "content",
          "created",
          "updated"
        ],
        "title": "SourceInsightResponse",
        "type": "object"
      },
      "SourceListResponse": {
        "properties": {
          "asset": {
            "anyOf": [
              {
                "$ref": "#/components/schemas/AssetModel"
              },
              {
                "type": "null"
              }
            ]
          },
          "command_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Command Id"
          },
          "created": {
            "title": "Created",
            "type": "string"
          },
          "embedded": {
            "title": "Embedded",
            "type": "boolean"
          },
          "embedded_chunks": {
            "title": "Embedded Chunks",
            "type": "integer"
          },
          "file_available": {
            "anyOf": [
              {
                "type": "boolean"
              },
              {
                "type": "null"
              }
            ],
            "title": "File Available"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "insights_count": {
            "title": "Insights Count",
            "type": "integer"
          },
          "processing_info": {
            "anyOf": [
              {
                "additionalProperties": true,
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Processing Info"
          },
          "status": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Status"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Title"
          },
          "topics": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Topics"
          },
          "updated": {
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "title",
          "topics",
          "asset",
          "embedded",
          "embedded_chunks",
          "insights_count",
          "created",
          "updated"
        ],
        "title": "SourceListResponse",
        "type": "object"
      },
      "SourceProcessingReportResponse": {
        "properties": {
          "command_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Last processing command ID",
            "title": "Command Id"
          },
          "embedded": {
            "description": "Whether embeddings exist",
            "title": "Embedded",
            "type": "boolean"
          },
          "embedded_chunks": {
            "description": "Number of embedded chunks",
            "title": "Embedded Chunks",
            "type": "integer"
          },
          "extracted_length": {
            "description": "Extracted text length in characters",
            "title": "Extracted Length",
            "type": "integer"
          },
          "file_available": {
            "anyOf": [
              {
                "type": "boolean"
              },
              {
                "type": "null"
              }
            ],
            "description": "Whether the original uploaded file is still available",
            "title": "File Available"
          },
          "has_file": {
            "description": "Whether this source has a file payload",
            "title": "Has File",
            "type": "boolean"
          },
          "insights_count": {
            "description": "Insight count for this source",
            "title": "Insights Count",
            "type": "integer"
          },
          "paragraph_count": {
            "description": "Extracted paragraph count",
            "title": "Paragraph Count",
            "type": "integer"
          },
          "processing_engine": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Detected processing engine if available",
            "title": "Processing Engine"
          },
          "processing_info": {
            "anyOf": [
              {
                "additionalProperties": true,
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "description": "Detailed backend processing metadata",
            "title": "Processing Info"
          },
          "processing_message": {
            "description": "Human-readable processing summary",
            "title": "Processing Message",
            "type": "string"
          },
          "processing_status": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Current processing status",
            "title": "Processing Status"
          },
          "source_id": {
            "description": "Source ID",
            "title": "Source Id",
            "type": "string"
          },
          "source_type": {
            "description": "Source type",
            "title": "Source Type",
            "type": "string"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Source title",
            "title": "Title"
          }
        },
        "required": [
          "source_id",
          "source_type",
          "processing_message",
          "extracted_length",
          "paragraph_count",
          "embedded",
          "embedded_chunks",
          "insights_count",
          "has_file"
        ],
        "title": "SourceProcessingReportResponse",
        "type": "object"
      },
      "SourceResponse": {
        "properties": {
          "asset": {
            "anyOf": [
              {
                "$ref": "#/components/schemas/AssetModel"
              },
              {
                "type": "null"
              }
            ]
          },
          "command_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Command Id"
          },
          "created": {
            "title": "Created",
            "type": "string"
          },
          "embedded": {
            "title": "Embedded",
            "type": "boolean"
          },
          "embedded_chunks": {
            "title": "Embedded Chunks",
            "type": "integer"
          },
          "file_available": {
            "anyOf": [
              {
                "type": "boolean"
              },
              {
                "type": "null"
              }
            ],
            "title": "File Available"
          },
          "full_text": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Full Text"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "notebooks": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Notebooks"
          },
          "processing_info": {
            "anyOf": [
              {
                "additionalProperties": true,
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Processing Info"
          },
          "status": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Status"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Title"
          },
          "topics": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Topics"
          },
          "updated": {
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "title",
          "topics",
          "asset",
          "full_text",
          "embedded",
          "embedded_chunks",
          "created",
          "updated"
        ],
        "title": "SourceResponse",
        "type": "object"
      },
      "SourceStatusResponse": {
        "properties": {
          "command_id": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Command ID if available",
            "title": "Command Id"
          },
          "message": {
            "description": "Descriptive message about the status",
            "title": "Message",
            "type": "string"
          },
          "processing_info": {
            "anyOf": [
              {
                "additionalProperties": true,
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "description": "Detailed processing information",
            "title": "Processing Info"
          },
          "status": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Processing status",
            "title": "Status"
          }
        },
        "required": [
          "message"
        ],
        "title": "SourceStatusResponse",
        "type": "object"
      },
      "SourceUpdate": {
        "properties": {
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Source title",
            "title": "Title"
          },
          "topics": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "description": "Source topics",
            "title": "Topics"
          }
        },
        "title": "SourceUpdate",
        "type": "object"
      },
      "SpeakerProfileCreate": {
        "properties": {
          "description": {
            "default": "",
            "description": "Profile description",
            "title": "Description",
            "type": "string"
          },
          "name": {
            "description": "Unique profile name",
            "title": "Name",
            "type": "string"
          },
          "speakers": {
            "description": "Array of speaker configurations",
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Speakers",
            "type": "array"
          },
          "tts_model": {
            "description": "TTS model name",
            "title": "Tts Model",
            "type": "string"
          },
          "tts_provider": {
            "description": "TTS provider",
            "title": "Tts Provider",
            "type": "string"
          }
        },
        "required": [
          "name",
          "tts_provider",
          "tts_model",
          "speakers"
        ],
        "title": "SpeakerProfileCreate",
        "type": "object"
      },
      "SpeakerProfileResponse": {
        "properties": {
          "description": {
            "title": "Description",
            "type": "string"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "name": {
            "title": "Name",
            "type": "string"
          },
          "speakers": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "title": "Speakers",
            "type": "array"
          },
          "tts_model": {
            "title": "Tts Model",
            "type": "string"
          },
          "tts_provider": {
            "title": "Tts Provider",
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "description",
          "tts_provider",
          "tts_model",
          "speakers"
        ],
        "title": "SpeakerProfileResponse",
        "type": "object"
      },
      "SuccessResponse": {
        "properties": {
          "message": {
            "description": "Success message",
            "title": "Message",
            "type": "string"
          },
          "success": {
            "default": true,
            "description": "Operation success status",
            "title": "Success",
            "type": "boolean"
          }
        },
        "required": [
          "message"
        ],
        "title": "SuccessResponse",
        "type": "object"
      },
      "TransformationCreate": {
        "properties": {
          "apply_default": {
            "default": false,
            "description": "Whether to apply this transformation by default",
            "title": "Apply Default",
            "type": "boolean"
          },
          "description": {
            "description": "Description of what this transformation does",
            "title": "Description",
            "type": "string"
          },
          "name": {
            "description": "Transformation name",
            "title": "Name",
            "type": "string"
          },
          "prompt": {
            "description": "The transformation prompt",
            "title": "Prompt",
            "type": "string"
          },
          "title": {
            "description": "Display title for the transformation",
            "title": "Title",
            "type": "string"
          }
        },
        "required": [
          "name",
          "title",
          "description",
          "prompt"
        ],
        "title": "TransformationCreate",
        "type": "object"
      },
      "TransformationExecuteRequest": {
        "properties": {
          "input_text": {
            "description": "Text to transform",
            "title": "Input Text",
            "type": "string"
          },
          "model_id": {
            "description": "Model ID to use for the transformation",
            "title": "Model Id",
            "type": "string"
          },
          "transformation_id": {
            "description": "ID of the transformation to execute",
            "title": "Transformation Id",
            "type": "string"
          }
        },
        "required": [
          "transformation_id",
          "input_text",
          "model_id"
        ],
        "title": "TransformationExecuteRequest",
        "type": "object"
      },
      "TransformationExecuteResponse": {
        "properties": {
          "model_id": {
            "description": "Model ID used",
            "title": "Model Id",
            "type": "string"
          },
          "output": {
            "description": "Transformed text",
            "title": "Output",
            "type": "string"
          },
          "transformation_id": {
            "description": "ID of the transformation used",
            "title": "Transformation Id",
            "type": "string"
          }
        },
        "required": [
          "output",
          "transformation_id",
          "model_id"
        ],
        "title": "TransformationExecuteResponse",
        "type": "object"
      },
      "TransformationResponse": {
        "properties": {
          "apply_default": {
            "title": "Apply Default",
            "type": "boolean"
          },
          "created": {
            "title": "Created",
            "type": "string"
          },
          "description": {
            "title": "Description",
            "type": "string"
          },
          "id": {
            "title": "Id",
            "type": "string"
          },
          "name": {
            "title": "Name",
            "type": "string"
          },
          "prompt": {
            "title": "Prompt",
            "type": "string"
          },
          "title": {
            "title": "Title",
            "type": "string"
          },
          "updated": {
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "name",
          "title",
          "description",
          "prompt",
          "apply_default",
          "created",
          "updated"
        ],
        "title": "TransformationResponse",
        "type": "object"
      },
      "TransformationUpdate": {
        "properties": {
          "apply_default": {
            "anyOf": [
              {
                "type": "boolean"
              },
              {
                "type": "null"
              }
            ],
            "description": "Whether to apply this transformation by default",
            "title": "Apply Default"
          },
          "description": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Description of what this transformation does",
            "title": "Description"
          },
          "name": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Transformation name",
            "title": "Name"
          },
          "prompt": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "The transformation prompt",
            "title": "Prompt"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Display title for the transformation",
            "title": "Title"
          }
        },
        "title": "TransformationUpdate",
        "type": "object"
      },
      "UITestReportResponse": {
        "properties": {
          "command": {
            "description": "Command used to execute Playwright",
            "items": {
              "type": "string"
            },
            "title": "Command",
            "type": "array"
          },
          "created": {
            "description": "Run creation timestamp",
            "title": "Created",
            "type": "string"
          },
          "dry_run": {
            "description": "Whether this run was started in dry-run mode",
            "title": "Dry Run",
            "type": "boolean"
          },
          "duration_seconds": {
            "anyOf": [
              {
                "type": "number"
              },
              {
                "type": "null"
              }
            ],
            "description": "Execution duration in seconds",
            "title": "Duration Seconds"
          },
          "finished_at": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Execution finish timestamp",
            "title": "Finished At"
          },
          "id": {
            "description": "Run ID",
            "title": "Id",
            "type": "string"
          },
          "return_code": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "description": "Subprocess exit code once execution has finished",
            "title": "Return Code"
          },
          "started_at": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Execution start timestamp",
            "title": "Started At"
          },
          "status": {
            "description": "Status: queued, running, completed, failed",
            "title": "Status",
            "type": "string"
          },
          "stderr": {
            "description": "Captured subprocess stderr",
            "title": "Stderr",
            "type": "string"
          },
          "stdout": {
            "description": "Captured subprocess stdout",
            "title": "Stdout",
            "type": "string"
          },
          "updated": {
            "description": "Last status update timestamp",
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "status",
          "dry_run",
          "command",
          "created",
          "updated",
          "stdout",
          "stderr"
        ],
        "title": "UITestReportResponse",
        "type": "object"
      },
      "UITestRunRequest": {
        "properties": {
          "dry_run": {
            "default": false,
            "description": "When true, skip actual Playwright execution and return a mocked success result",
            "title": "Dry Run",
            "type": "boolean"
          },
          "project": {
            "default": "chromium",
            "description": "Playwright project name",
            "enum": [
              "chromium",
              "firefox",
              "webkit"
            ],
            "title": "Project",
            "type": "string"
          },
          "spec": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Optional Playwright spec path under e2e/ (apps/web/e2e/ also accepted)",
            "title": "Spec"
          },
          "timeout_seconds": {
            "default": 600,
            "description": "Maximum time allowed for the Playwright subprocess",
            "maximum": 7200.0,
            "minimum": 1.0,
            "title": "Timeout Seconds",
            "type": "integer"
          }
        },
        "title": "UITestRunRequest",
        "type": "object"
      },
      "UITestRunResponse": {
        "properties": {
          "command": {
            "description": "Command used to execute Playwright",
            "items": {
              "type": "string"
            },
            "title": "Command",
            "type": "array"
          },
          "created": {
            "description": "Run creation timestamp",
            "title": "Created",
            "type": "string"
          },
          "dry_run": {
            "description": "Whether this run was started in dry-run mode",
            "title": "Dry Run",
            "type": "boolean"
          },
          "id": {
            "description": "Run ID",
            "title": "Id",
            "type": "string"
          },
          "return_code": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "description": "Subprocess exit code once execution has finished",
            "title": "Return Code"
          },
          "status": {
            "description": "Status: queued, running, completed, failed",
            "title": "Status",
            "type": "string"
          },
          "updated": {
            "description": "Last status update timestamp",
            "title": "Updated",
            "type": "string"
          }
        },
        "required": [
          "id",
          "status",
          "dry_run",
          "command",
          "created",
          "updated"
        ],
        "title": "UITestRunResponse",
        "type": "object"
      },
      "UpdateCredentialRequest": {
        "description": "Request to update an existing credential.",
        "properties": {
          "api_key": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "API key (stored encrypted)",
            "title": "Api Key"
          },
          "api_version": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "API version",
            "title": "Api Version"
          },
          "base_url": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Base URL",
            "title": "Base Url"
          },
          "credentials_path": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Credentials path",
            "title": "Credentials Path"
          },
          "endpoint": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Endpoint URL",
            "title": "Endpoint"
          },
          "endpoint_embedding": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Embedding endpoint",
            "title": "Endpoint Embedding"
          },
          "endpoint_llm": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "LLM endpoint",
            "title": "Endpoint Llm"
          },
          "endpoint_stt": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "STT endpoint",
            "title": "Endpoint Stt"
          },
          "endpoint_tts": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "TTS endpoint",
            "title": "Endpoint Tts"
          },
          "location": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Location",
            "title": "Location"
          },
          "modalities": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "description": "Supported modalities",
            "title": "Modalities"
          },
          "name": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Credential name",
            "title": "Name"
          },
          "project": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Project ID",
            "title": "Project"
          }
        },
        "title": "UpdateCredentialRequest",
        "type": "object"
      },
      "UpdateSessionRequest": {
        "properties": {
          "model_override": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Model override for this session",
            "title": "Model Override"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "New session title",
            "title": "Title"
          }
        },
        "title": "UpdateSessionRequest",
        "type": "object"
      },
      "UpdateSourceChatSessionRequest": {
        "properties": {
          "model_override": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "Model override for this session",
            "title": "Model Override"
          },
          "title": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "description": "New session title",
            "title": "Title"
          }
        },
        "title": "UpdateSourceChatSessionRequest",
        "type": "object"
      },
      "ValidationError": {
        "properties": {
          "ctx": {
            "title": "Context",
            "type": "object"
          },
          "input": {
            "title": "Input"
          },
          "loc": {
            "items": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "integer"
                }
              ]
            },
            "title": "Location",
            "type": "array"
          },
          "msg": {
            "title": "Message",
            "type": "string"
          },
          "type": {
            "title": "Error Type",
            "type": "string"
          }
        },
        "required": [
          "loc",
          "msg",
          "type"
        ],
        "title": "ValidationError",
        "type": "object"
      }
    }
  },
  "info": {
    "description": "API for Provenote, a source-grounded and auditable research workbench.",
    "title": "Provenote API",
    "version": "0.1.0"
  },
  "openapi": "3.1.0",
  "paths": {
    "/": {
      "get": {
        "operationId": "root__get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Root"
      }
    },
    "/api/auditable-runs/batch": {
      "post": {
        "operationId": "create_auditable_runs_batch_api_auditable_runs_batch_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AuditableBatchRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/AuditableBatchResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Auditable Runs Batch",
        "tags": [
          "auditable-runs"
        ]
      }
    },
    "/api/auditable-runs/{run_id}": {
      "get": {
        "operationId": "get_auditable_run_api_auditable_runs__run_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "run_id",
            "required": true,
            "schema": {
              "title": "Run Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/AuditableRunResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Auditable Run",
        "tags": [
          "auditable-runs"
        ]
      }
    },
    "/api/auditable-runs/{run_id}/markdown": {
      "get": {
        "operationId": "get_auditable_run_markdown_api_auditable_runs__run_id__markdown_get",
        "parameters": [
          {
            "in": "path",
            "name": "run_id",
            "required": true,
            "schema": {
              "title": "Run Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Auditable Run Markdown",
        "tags": [
          "auditable-runs"
        ]
      }
    },
    "/api/auditable-runs/{run_id}/repair-claim": {
      "post": {
        "operationId": "repair_auditable_claim_api_auditable_runs__run_id__repair_claim_post",
        "parameters": [
          {
            "in": "path",
            "name": "run_id",
            "required": true,
            "schema": {
              "title": "Run Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AuditableRepairRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/AuditableRunResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Repair Auditable Claim",
        "tags": [
          "auditable-runs"
        ]
      }
    },
    "/api/auditable-runs/{run_id}/repair-section": {
      "post": {
        "operationId": "repair_auditable_section_api_auditable_runs__run_id__repair_section_post",
        "parameters": [
          {
            "in": "path",
            "name": "run_id",
            "required": true,
            "schema": {
              "title": "Run Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AuditableRepairRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/AuditableRunResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Repair Auditable Section",
        "tags": [
          "auditable-runs"
        ]
      }
    },
    "/api/auth/status": {
      "get": {
        "description": "Check if authentication is enabled.\nReturns whether a password is required to access the API.\nSupports Docker secrets via OPEN_NOTEBOOK_PASSWORD_FILE.",
        "operationId": "get_auth_status_api_auth_status_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Get Auth Status",
        "tags": [
          "auth",
          "auth"
        ]
      }
    },
    "/api/chat/context": {
      "post": {
        "description": "Build context for a notebook based on context configuration.",
        "operationId": "build_context_api_chat_context_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/BuildContextRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/BuildContextResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Build Context",
        "tags": [
          "chat"
        ]
      }
    },
    "/api/chat/execute": {
      "post": {
        "description": "Execute a chat request and get AI response.",
        "operationId": "execute_chat_api_chat_execute_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ExecuteChatRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ExecuteChatResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Execute Chat",
        "tags": [
          "chat"
        ]
      }
    },
    "/api/chat/sessions": {
      "get": {
        "description": "Get all chat sessions for a notebook.",
        "operationId": "get_sessions_api_chat_sessions_get",
        "parameters": [
          {
            "description": "Notebook ID",
            "in": "query",
            "name": "notebook_id",
            "required": true,
            "schema": {
              "description": "Notebook ID",
              "title": "Notebook Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/ChatSessionResponse"
                  },
                  "title": "Response Get Sessions Api Chat Sessions Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Sessions",
        "tags": [
          "chat"
        ]
      },
      "post": {
        "description": "Create a new chat session.",
        "operationId": "create_session_api_chat_sessions_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/CreateSessionRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ChatSessionResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Session",
        "tags": [
          "chat"
        ]
      }
    },
    "/api/chat/sessions/{session_id}": {
      "delete": {
        "description": "Delete a chat session.",
        "operationId": "delete_session_api_chat_sessions__session_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "session_id",
            "required": true,
            "schema": {
              "title": "Session Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SuccessResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Delete Session",
        "tags": [
          "chat"
        ]
      },
      "get": {
        "description": "Get a specific session with its messages.",
        "operationId": "get_session_api_chat_sessions__session_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "session_id",
            "required": true,
            "schema": {
              "title": "Session Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ChatSessionWithMessagesResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Session",
        "tags": [
          "chat"
        ]
      },
      "put": {
        "description": "Update session title.",
        "operationId": "update_session_api_chat_sessions__session_id__put",
        "parameters": [
          {
            "in": "path",
            "name": "session_id",
            "required": true,
            "schema": {
              "title": "Session Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/UpdateSessionRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ChatSessionResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Update Session",
        "tags": [
          "chat"
        ]
      }
    },
    "/api/commands/dead-letter": {
      "get": {
        "description": "List dead-letter command entries.",
        "operationId": "list_dead_letter_jobs_api_commands_dead_letter_get",
        "parameters": [
          {
            "description": "Maximum number of dead-letter entries",
            "in": "query",
            "name": "limit",
            "required": false,
            "schema": {
              "default": 50,
              "description": "Maximum number of dead-letter entries",
              "title": "Limit",
              "type": "integer"
            }
          },
          {
            "description": "Pagination offset",
            "in": "query",
            "name": "offset",
            "required": false,
            "schema": {
              "default": 0,
              "description": "Pagination offset",
              "title": "Offset",
              "type": "integer"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "additionalProperties": true,
                    "type": "object"
                  },
                  "title": "Response List Dead Letter Jobs Api Commands Dead Letter Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "List Dead Letter Jobs",
        "tags": [
          "commands"
        ]
      }
    },
    "/api/commands/dead-letter/{entry_id}/requeue": {
      "post": {
        "description": "Requeue a dead-letter command entry.",
        "operationId": "requeue_dead_letter_job_api_commands_dead_letter__entry_id__requeue_post",
        "parameters": [
          {
            "in": "path",
            "name": "entry_id",
            "required": true,
            "schema": {
              "title": "Entry Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/DeadLetterRequeueResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Requeue Dead Letter Job",
        "tags": [
          "commands"
        ]
      }
    },
    "/api/commands/jobs": {
      "get": {
        "description": "List command jobs with optional filtering",
        "operationId": "list_command_jobs_api_commands_jobs_get",
        "parameters": [
          {
            "description": "Filter by app name",
            "in": "query",
            "name": "app_filter",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "description": "Filter by app name",
              "title": "App Filter"
            }
          },
          {
            "description": "Filter by command name",
            "in": "query",
            "name": "command_filter",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "description": "Filter by command name",
              "title": "Command Filter"
            }
          },
          {
            "description": "Filter by status",
            "in": "query",
            "name": "status_filter",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "description": "Filter by status",
              "title": "Status Filter"
            }
          },
          {
            "description": "Maximum number of jobs to return",
            "in": "query",
            "name": "limit",
            "required": false,
            "schema": {
              "default": 50,
              "description": "Maximum number of jobs to return",
              "title": "Limit",
              "type": "integer"
            }
          },
          {
            "description": "Pagination offset",
            "in": "query",
            "name": "offset",
            "required": false,
            "schema": {
              "default": 0,
              "description": "Pagination offset",
              "title": "Offset",
              "type": "integer"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "additionalProperties": true,
                    "type": "object"
                  },
                  "title": "Response List Command Jobs Api Commands Jobs Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "List Command Jobs",
        "tags": [
          "commands"
        ]
      },
      "post": {
        "description": "Submit a command for background processing.\nReturns immediately with job ID for status tracking.\n\nExample request:\n{\n    \"command\": \"process_text\",\n    \"app\": \"open_notebook\",\n    \"input\": {\n        \"text\": \"Hello world\",\n        \"operation\": \"uppercase\"\n    }\n}",
        "operationId": "execute_command_api_commands_jobs_post",
        "parameters": [
          {
            "in": "header",
            "name": "Idempotency-Key",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Idempotency-Key"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/CommandExecutionRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/CommandJobResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Execute Command",
        "tags": [
          "commands"
        ]
      }
    },
    "/api/commands/jobs/{job_id}": {
      "delete": {
        "description": "Cancel a running command job",
        "operationId": "cancel_command_job_api_commands_jobs__job_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "job_id",
            "required": true,
            "schema": {
              "title": "Job Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/CommandCancelResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Cancel Command Job",
        "tags": [
          "commands"
        ]
      },
      "get": {
        "description": "Get the status of a specific command job",
        "operationId": "get_command_job_status_api_commands_jobs__job_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "job_id",
            "required": true,
            "schema": {
              "title": "Job Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/CommandJobStatusResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Command Job Status",
        "tags": [
          "commands"
        ]
      }
    },
    "/api/commands/registry/debug": {
      "get": {
        "description": "Debug endpoint to see what commands are registered",
        "operationId": "debug_registry_api_commands_registry_debug_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Debug Registry",
        "tags": [
          "commands"
        ]
      }
    },
    "/api/computer-use/sessions": {
      "post": {
        "operationId": "create_computer_use_session_api_computer_use_sessions_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ComputerUseSessionCreateRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ComputerUseSessionResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Computer Use Session",
        "tags": [
          "computer-use"
        ]
      }
    },
    "/api/computer-use/sessions/{session_id}": {
      "get": {
        "operationId": "get_computer_use_session_api_computer_use_sessions__session_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "session_id",
            "required": true,
            "schema": {
              "title": "Session Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ComputerUseSessionResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Computer Use Session",
        "tags": [
          "computer-use"
        ]
      }
    },
    "/api/computer-use/sessions/{session_id}/confirm": {
      "post": {
        "operationId": "confirm_computer_use_action_api_computer_use_sessions__session_id__confirm_post",
        "parameters": [
          {
            "in": "path",
            "name": "session_id",
            "required": true,
            "schema": {
              "title": "Session Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ComputerUseConfirmRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ComputerUseConfirmResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Confirm Computer Use Action",
        "tags": [
          "computer-use"
        ]
      }
    },
    "/api/config": {
      "get": {
        "description": "Get frontend configuration.\n\nReturns version information and health status.\nNote: The frontend determines the API URL via its own runtime-config endpoint,\nso this endpoint no longer returns apiUrl.\n\nAlso checks for version updates from GitHub (with caching and error handling).",
        "operationId": "get_config_api_config_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Get Config",
        "tags": [
          "config"
        ]
      }
    },
    "/api/credentials": {
      "get": {
        "description": "List all credentials, optionally filtered by provider.",
        "operationId": "list_credentials_api_credentials_get",
        "parameters": [
          {
            "description": "Filter by provider",
            "in": "query",
            "name": "provider",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "description": "Filter by provider",
              "title": "Provider"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/CredentialResponse"
                  },
                  "title": "Response List Credentials Api Credentials Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "List Credentials",
        "tags": [
          "credentials",
          "credentials"
        ]
      },
      "post": {
        "description": "Create a new credential.",
        "operationId": "create_credential_api_credentials_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/CreateCredentialRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "201": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/CredentialResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Credential",
        "tags": [
          "credentials",
          "credentials"
        ]
      }
    },
    "/api/credentials/by-provider/{provider}": {
      "get": {
        "description": "List all credentials for a specific provider.",
        "operationId": "list_credentials_by_provider_api_credentials_by_provider__provider__get",
        "parameters": [
          {
            "in": "path",
            "name": "provider",
            "required": true,
            "schema": {
              "title": "Provider",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/CredentialResponse"
                  },
                  "title": "Response List Credentials By Provider Api Credentials By Provider  Provider  Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "List Credentials By Provider",
        "tags": [
          "credentials",
          "credentials"
        ]
      }
    },
    "/api/credentials/status": {
      "get": {
        "description": "Get configuration status: encryption key status, and per-provider\nconfigured/source information.",
        "operationId": "get_status_api_credentials_status_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ApiKeyStatusResponse"
                }
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Get Status",
        "tags": [
          "credentials",
          "credentials"
        ]
      }
    },
    "/api/credentials/{credential_id}": {
      "delete": {
        "description": "Delete a credential.\n\nIf the credential has linked models:\n- Pass delete_models=true to delete them\n- Pass migrate_to=<credential_id> to reassign them\n- Without either, returns 409 with linked model info",
        "operationId": "delete_credential_api_credentials__credential_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "credential_id",
            "required": true,
            "schema": {
              "title": "Credential Id",
              "type": "string"
            }
          },
          {
            "description": "Also delete linked models",
            "in": "query",
            "name": "delete_models",
            "required": false,
            "schema": {
              "default": false,
              "description": "Also delete linked models",
              "title": "Delete Models",
              "type": "boolean"
            }
          },
          {
            "description": "Migrate linked models to this credential ID",
            "in": "query",
            "name": "migrate_to",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "description": "Migrate linked models to this credential ID",
              "title": "Migrate To"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/CredentialDeleteResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Delete Credential",
        "tags": [
          "credentials",
          "credentials"
        ]
      },
      "get": {
        "description": "Get a specific credential by ID. Never returns api_key.",
        "operationId": "get_credential_api_credentials__credential_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "credential_id",
            "required": true,
            "schema": {
              "title": "Credential Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/CredentialResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Credential",
        "tags": [
          "credentials",
          "credentials"
        ]
      },
      "put": {
        "description": "Update an existing credential.",
        "operationId": "update_credential_api_credentials__credential_id__put",
        "parameters": [
          {
            "in": "path",
            "name": "credential_id",
            "required": true,
            "schema": {
              "title": "Credential Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/UpdateCredentialRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/CredentialResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Update Credential",
        "tags": [
          "credentials",
          "credentials"
        ]
      }
    },
    "/api/credentials/{credential_id}/discover": {
      "post": {
        "description": "Discover available models using this credential's API key.",
        "operationId": "discover_models_for_credential_api_credentials__credential_id__discover_post",
        "parameters": [
          {
            "in": "path",
            "name": "credential_id",
            "required": true,
            "schema": {
              "title": "Credential Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/DiscoverModelsResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Discover Models For Credential",
        "tags": [
          "credentials",
          "credentials"
        ]
      }
    },
    "/api/credentials/{credential_id}/register-models": {
      "post": {
        "description": "Register discovered models and link them to this credential.",
        "operationId": "register_models_for_credential_api_credentials__credential_id__register_models_post",
        "parameters": [
          {
            "in": "path",
            "name": "credential_id",
            "required": true,
            "schema": {
              "title": "Credential Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/RegisterModelsRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/RegisterModelsResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Register Models For Credential",
        "tags": [
          "credentials",
          "credentials"
        ]
      }
    },
    "/api/credentials/{credential_id}/test": {
      "post": {
        "description": "Test connection using this credential's configuration.",
        "operationId": "test_credential_api_credentials__credential_id__test_post",
        "parameters": [
          {
            "in": "path",
            "name": "credential_id",
            "required": true,
            "schema": {
              "title": "Credential Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Test Credential",
        "tags": [
          "credentials",
          "credentials"
        ]
      }
    },
    "/api/drafts/{draft_id}": {
      "get": {
        "operationId": "get_draft_api_drafts__draft_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "draft_id",
            "required": true,
            "schema": {
              "title": "Draft Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/DraftResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "400": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Invalid draft request"
          },
          "404": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Draft or notebook not found"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          },
          "500": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Unexpected draft error"
          }
        },
        "summary": "Get Draft",
        "tags": [
          "drafts"
        ]
      }
    },
    "/api/drafts/{draft_id}/bundle": {
      "get": {
        "operationId": "get_draft_bundle_api_drafts__draft_id__bundle_get",
        "parameters": [
          {
            "in": "path",
            "name": "draft_id",
            "required": true,
            "schema": {
              "title": "Draft Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/zip": {
                "schema": {
                  "type": "string"
                }
              }
            },
            "description": "Draft export bundle"
          },
          "400": {
            "content": {
              "application/zip": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Invalid draft request"
          },
          "404": {
            "content": {
              "application/zip": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Draft or notebook not found"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          },
          "500": {
            "content": {
              "application/zip": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Unexpected draft error"
          }
        },
        "summary": "Get Draft Bundle",
        "tags": [
          "drafts"
        ]
      }
    },
    "/api/drafts/{draft_id}/markdown": {
      "get": {
        "operationId": "get_draft_markdown_api_drafts__draft_id__markdown_get",
        "parameters": [
          {
            "in": "path",
            "name": "draft_id",
            "required": true,
            "schema": {
              "title": "Draft Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "text/markdown": {},
              "text/markdown; charset=utf-8": {
                "schema": {
                  "type": "string"
                }
              }
            },
            "description": "Draft markdown download"
          },
          "400": {
            "content": {
              "text/markdown; charset=utf-8": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Invalid draft request"
          },
          "404": {
            "content": {
              "text/markdown; charset=utf-8": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Draft or notebook not found"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          },
          "500": {
            "content": {
              "text/markdown; charset=utf-8": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Unexpected draft error"
          }
        },
        "summary": "Get Draft Markdown",
        "tags": [
          "drafts"
        ]
      }
    },
    "/api/drafts/{draft_id}/rerun": {
      "post": {
        "operationId": "rerun_draft_api_drafts__draft_id__rerun_post",
        "parameters": [
          {
            "in": "path",
            "name": "draft_id",
            "required": true,
            "schema": {
              "title": "Draft Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/DraftRerunRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/DraftResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "400": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Invalid draft request"
          },
          "404": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Draft or notebook not found"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          },
          "500": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Unexpected draft error"
          }
        },
        "summary": "Rerun Draft",
        "tags": [
          "drafts"
        ]
      }
    },
    "/api/drafts/{draft_id}/verify": {
      "post": {
        "operationId": "verify_draft_api_drafts__draft_id__verify_post",
        "parameters": [
          {
            "in": "path",
            "name": "draft_id",
            "required": true,
            "schema": {
              "title": "Draft Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/DraftResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "400": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Invalid draft request"
          },
          "404": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Draft or notebook not found"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          },
          "500": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Unexpected draft error"
          }
        },
        "summary": "Verify Draft",
        "tags": [
          "drafts"
        ]
      }
    },
    "/api/embed": {
      "post": {
        "description": "Embed content for vector search.",
        "operationId": "embed_content_api_embed_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/EmbedRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/EmbedResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Embed Content",
        "tags": [
          "embedding"
        ]
      }
    },
    "/api/embeddings/rebuild": {
      "post": {
        "description": "Start a background job to rebuild embeddings.\n\n- **mode**: \"existing\" (re-embed items with embeddings) or \"all\" (embed everything)\n- **include_sources**: Include sources in rebuild (default: true)\n- **include_notes**: Include notes in rebuild (default: true)\n- **include_insights**: Include insights in rebuild (default: true)\n\nReturns command ID to track progress and estimated item count.",
        "operationId": "start_rebuild_api_embeddings_rebuild_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/RebuildRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/RebuildResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Start Rebuild",
        "tags": [
          "embeddings"
        ]
      }
    },
    "/api/embeddings/rebuild/{command_id}/status": {
      "get": {
        "description": "Get the status of a rebuild operation.\n\nReturns:\n- **status**: queued, running, completed, failed\n- **progress**: processed count, total count, percentage\n- **stats**: breakdown by type (sources, notes, insights, failed)\n- **timestamps**: started_at, completed_at",
        "operationId": "get_rebuild_status_api_embeddings_rebuild__command_id__status_get",
        "parameters": [
          {
            "in": "path",
            "name": "command_id",
            "required": true,
            "schema": {
              "title": "Command Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/RebuildStatusResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Rebuild Status",
        "tags": [
          "embeddings"
        ]
      }
    },
    "/api/episode-profiles": {
      "get": {
        "description": "List all available episode profiles",
        "operationId": "list_episode_profiles_api_episode_profiles_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/EpisodeProfileResponse"
                  },
                  "title": "Response List Episode Profiles Api Episode Profiles Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "List Episode Profiles",
        "tags": [
          "episode-profiles"
        ]
      },
      "post": {
        "description": "Create a new episode profile",
        "operationId": "create_episode_profile_api_episode_profiles_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/EpisodeProfileCreate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/EpisodeProfileResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Episode Profile",
        "tags": [
          "episode-profiles"
        ]
      }
    },
    "/api/episode-profiles/{profile_id}": {
      "delete": {
        "description": "Delete an episode profile",
        "operationId": "delete_episode_profile_api_episode_profiles__profile_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "profile_id",
            "required": true,
            "schema": {
              "title": "Profile Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Delete Episode Profile",
        "tags": [
          "episode-profiles"
        ]
      },
      "put": {
        "description": "Update an existing episode profile",
        "operationId": "update_episode_profile_api_episode_profiles__profile_id__put",
        "parameters": [
          {
            "in": "path",
            "name": "profile_id",
            "required": true,
            "schema": {
              "title": "Profile Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/EpisodeProfileCreate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/EpisodeProfileResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Update Episode Profile",
        "tags": [
          "episode-profiles"
        ]
      }
    },
    "/api/episode-profiles/{profile_id}/duplicate": {
      "post": {
        "description": "Duplicate an episode profile",
        "operationId": "duplicate_episode_profile_api_episode_profiles__profile_id__duplicate_post",
        "parameters": [
          {
            "in": "path",
            "name": "profile_id",
            "required": true,
            "schema": {
              "title": "Profile Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/EpisodeProfileResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Duplicate Episode Profile",
        "tags": [
          "episode-profiles"
        ]
      }
    },
    "/api/episode-profiles/{profile_name}": {
      "get": {
        "description": "Get a specific episode profile by name",
        "operationId": "get_episode_profile_api_episode_profiles__profile_name__get",
        "parameters": [
          {
            "in": "path",
            "name": "profile_name",
            "required": true,
            "schema": {
              "title": "Profile Name",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/EpisodeProfileResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Episode Profile",
        "tags": [
          "episode-profiles"
        ]
      }
    },
    "/api/insights/{insight_id}": {
      "delete": {
        "description": "Delete a specific insight.",
        "operationId": "delete_insight_api_insights__insight_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "insight_id",
            "required": true,
            "schema": {
              "title": "Insight Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Delete Insight",
        "tags": [
          "insights"
        ]
      },
      "get": {
        "description": "Get a specific insight by ID.",
        "operationId": "get_insight_api_insights__insight_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "insight_id",
            "required": true,
            "schema": {
              "title": "Insight Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SourceInsightResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Insight",
        "tags": [
          "insights"
        ]
      }
    },
    "/api/insights/{insight_id}/save-as-note": {
      "post": {
        "description": "Convert an insight to a note.",
        "operationId": "save_insight_as_note_api_insights__insight_id__save_as_note_post",
        "parameters": [
          {
            "in": "path",
            "name": "insight_id",
            "required": true,
            "schema": {
              "title": "Insight Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/SaveAsNoteRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/NoteResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Save Insight As Note",
        "tags": [
          "insights"
        ]
      }
    },
    "/api/models": {
      "get": {
        "description": "Get all configured models with optional type filtering.",
        "operationId": "get_models_api_models_get",
        "parameters": [
          {
            "description": "Filter by model type",
            "in": "query",
            "name": "type",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "description": "Filter by model type",
              "title": "Type"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/ModelResponse"
                  },
                  "title": "Response Get Models Api Models Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Models",
        "tags": [
          "models"
        ]
      },
      "post": {
        "description": "Create a new model configuration.",
        "operationId": "create_model_api_models_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ModelCreate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ModelResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Model",
        "tags": [
          "models"
        ]
      }
    },
    "/api/models/auto-assign": {
      "post": {
        "description": "Auto-assign default models based on Gemini slot policy.\n\nReturns:\n    - assigned: Dict of slot names to assigned model IDs\n    - skipped: List of slots that already have models assigned\n    - missing: List of slots with no available models",
        "operationId": "auto_assign_defaults_api_models_auto_assign_post",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/AutoAssignResult"
                }
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Auto Assign Defaults",
        "tags": [
          "models"
        ]
      }
    },
    "/api/models/by-provider/{provider}": {
      "get": {
        "description": "Get all registered models for a specific provider.\n\nReturns models from the database that belong to the specified provider.",
        "operationId": "get_models_by_provider_api_models_by_provider__provider__get",
        "parameters": [
          {
            "in": "path",
            "name": "provider",
            "required": true,
            "schema": {
              "title": "Provider",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/ModelResponse"
                  },
                  "title": "Response Get Models By Provider Api Models By Provider  Provider  Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Models By Provider",
        "tags": [
          "models"
        ]
      }
    },
    "/api/models/count/{provider}": {
      "get": {
        "description": "Get count of registered models for a provider, grouped by type.\n\nReturns counts for each model type (language, embedding,\nspeech_to_text, text_to_speech) as well as total count.",
        "operationId": "get_model_count_api_models_count__provider__get",
        "parameters": [
          {
            "in": "path",
            "name": "provider",
            "required": true,
            "schema": {
              "title": "Provider",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ProviderModelCountResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Model Count",
        "tags": [
          "models"
        ]
      }
    },
    "/api/models/defaults": {
      "get": {
        "description": "Get default model assignments.",
        "operationId": "get_default_models_api_models_defaults_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/DefaultModelsResponse"
                }
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Get Default Models",
        "tags": [
          "models"
        ]
      },
      "put": {
        "description": "Update default model assignments.",
        "operationId": "update_default_models_api_models_defaults_put",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/DefaultModelsResponse"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/DefaultModelsResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Update Default Models",
        "tags": [
          "models"
        ]
      }
    },
    "/api/models/discover/{provider}": {
      "get": {
        "description": "Discover available models from a provider without registering them.\n\nThis endpoint queries the provider's API to list available models\nbut does not save them to the database. Use the sync endpoint\nto both discover and register models.",
        "operationId": "discover_models_api_models_discover__provider__get",
        "parameters": [
          {
            "in": "path",
            "name": "provider",
            "required": true,
            "schema": {
              "title": "Provider",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/ProviderDiscoveredModelResponse"
                  },
                  "title": "Response Discover Models Api Models Discover  Provider  Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Discover Models",
        "tags": [
          "models"
        ]
      }
    },
    "/api/models/providers": {
      "get": {
        "description": "Get provider availability based on database credentials only.",
        "operationId": "get_provider_availability_api_models_providers_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ProviderAvailabilityResponse"
                }
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Get Provider Availability",
        "tags": [
          "models"
        ]
      }
    },
    "/api/models/sync": {
      "post": {
        "description": "Sync models for all configured providers.\n\nDiscovers and registers models from all providers that have\nvalid API keys configured. This is useful for initial setup\nor periodic refresh of available models.",
        "operationId": "sync_all_models_api_models_sync_post",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/AllProvidersSyncResponse"
                }
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Sync All Models",
        "tags": [
          "models"
        ]
      }
    },
    "/api/models/sync/{provider}": {
      "post": {
        "description": "Sync models for a specific provider.\n\nDiscovers available models from the provider's API and registers\nany new models in the database. Existing models are skipped.\n\nReturns counts of discovered, new, and existing models.",
        "operationId": "sync_models_api_models_sync__provider__post",
        "parameters": [
          {
            "in": "path",
            "name": "provider",
            "required": true,
            "schema": {
              "title": "Provider",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ProviderSyncResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Sync Models",
        "tags": [
          "models"
        ]
      }
    },
    "/api/models/{model_id}": {
      "delete": {
        "description": "Delete a model configuration.",
        "operationId": "delete_model_api_models__model_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "model_id",
            "required": true,
            "schema": {
              "title": "Model Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Delete Model",
        "tags": [
          "models"
        ]
      }
    },
    "/api/models/{model_id}/test": {
      "post": {
        "description": "Test if a specific model is correctly configured and functional.",
        "operationId": "test_model_api_models__model_id__test_post",
        "parameters": [
          {
            "in": "path",
            "name": "model_id",
            "required": true,
            "schema": {
              "title": "Model Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ModelTestResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Test Model",
        "tags": [
          "models"
        ]
      }
    },
    "/api/notebooks": {
      "get": {
        "description": "Get all notebooks with optional filtering and ordering.",
        "operationId": "get_notebooks_api_notebooks_get",
        "parameters": [
          {
            "description": "Filter by archived status",
            "in": "query",
            "name": "archived",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "boolean"
                },
                {
                  "type": "null"
                }
              ],
              "description": "Filter by archived status",
              "title": "Archived"
            }
          },
          {
            "description": "Order by field and direction",
            "in": "query",
            "name": "order_by",
            "required": false,
            "schema": {
              "default": "updated desc",
              "description": "Order by field and direction",
              "title": "Order By",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/NotebookResponse"
                  },
                  "title": "Response Get Notebooks Api Notebooks Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Notebooks",
        "tags": [
          "notebooks"
        ]
      },
      "post": {
        "description": "Create a new notebook.",
        "operationId": "create_notebook_api_notebooks_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/NotebookCreate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/NotebookResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Notebook",
        "tags": [
          "notebooks"
        ]
      }
    },
    "/api/notebooks/{notebook_id}": {
      "delete": {
        "description": "Delete a notebook with cascade deletion.\n\nAlways deletes all notes associated with the notebook.\nIf delete_exclusive_sources is True, also deletes sources that belong only\nto this notebook (not linked to any other notebooks).",
        "operationId": "delete_notebook_api_notebooks__notebook_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "notebook_id",
            "required": true,
            "schema": {
              "title": "Notebook Id",
              "type": "string"
            }
          },
          {
            "description": "Whether to delete sources that belong only to this notebook",
            "in": "query",
            "name": "delete_exclusive_sources",
            "required": false,
            "schema": {
              "default": false,
              "description": "Whether to delete sources that belong only to this notebook",
              "title": "Delete Exclusive Sources",
              "type": "boolean"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/NotebookDeleteResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Delete Notebook",
        "tags": [
          "notebooks"
        ]
      },
      "get": {
        "description": "Get a specific notebook by ID.",
        "operationId": "get_notebook_api_notebooks__notebook_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "notebook_id",
            "required": true,
            "schema": {
              "title": "Notebook Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/NotebookResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Notebook",
        "tags": [
          "notebooks"
        ]
      },
      "put": {
        "description": "Update a notebook.",
        "operationId": "update_notebook_api_notebooks__notebook_id__put",
        "parameters": [
          {
            "in": "path",
            "name": "notebook_id",
            "required": true,
            "schema": {
              "title": "Notebook Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/NotebookUpdate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/NotebookResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Update Notebook",
        "tags": [
          "notebooks"
        ]
      }
    },
    "/api/notebooks/{notebook_id}/context": {
      "post": {
        "description": "Get context for a notebook based on configuration.",
        "operationId": "get_notebook_context_api_notebooks__notebook_id__context_post",
        "parameters": [
          {
            "in": "path",
            "name": "notebook_id",
            "required": true,
            "schema": {
              "title": "Notebook Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ContextRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ContextResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Notebook Context",
        "tags": [
          "context"
        ]
      }
    },
    "/api/notebooks/{notebook_id}/delete-preview": {
      "get": {
        "description": "Get a preview of what will be deleted when this notebook is deleted.",
        "operationId": "get_notebook_delete_preview_api_notebooks__notebook_id__delete_preview_get",
        "parameters": [
          {
            "in": "path",
            "name": "notebook_id",
            "required": true,
            "schema": {
              "title": "Notebook Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/NotebookDeletePreview"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Notebook Delete Preview",
        "tags": [
          "notebooks"
        ]
      }
    },
    "/api/notebooks/{notebook_id}/drafts": {
      "get": {
        "operationId": "list_notebook_drafts_api_notebooks__notebook_id__drafts_get",
        "parameters": [
          {
            "in": "path",
            "name": "notebook_id",
            "required": true,
            "schema": {
              "title": "Notebook Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/DraftResponse"
                  },
                  "title": "Response List Notebook Drafts Api Notebooks  Notebook Id  Drafts Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "400": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Invalid draft request"
          },
          "404": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Draft or notebook not found"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          },
          "500": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Unexpected draft error"
          }
        },
        "summary": "List Notebook Drafts",
        "tags": [
          "drafts"
        ]
      },
      "post": {
        "operationId": "create_draft_api_notebooks__notebook_id__drafts_post",
        "parameters": [
          {
            "in": "path",
            "name": "notebook_id",
            "required": true,
            "schema": {
              "title": "Notebook Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/DraftCreateRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/DraftResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "400": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Invalid draft request"
          },
          "404": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Draft or notebook not found"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          },
          "500": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Unexpected draft error"
          }
        },
        "summary": "Create Draft",
        "tags": [
          "drafts"
        ]
      }
    },
    "/api/notebooks/{notebook_id}/research-threads": {
      "get": {
        "operationId": "list_research_threads_api_notebooks__notebook_id__research_threads_get",
        "parameters": [
          {
            "in": "path",
            "name": "notebook_id",
            "required": true,
            "schema": {
              "title": "Notebook Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/ResearchThreadResponse"
                  },
                  "title": "Response List Research Threads Api Notebooks  Notebook Id  Research Threads Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "400": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Invalid research thread request"
          },
          "404": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Research thread or notebook not found"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          },
          "500": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Unexpected research thread error"
          }
        },
        "summary": "List Research Threads",
        "tags": [
          "research-threads"
        ]
      },
      "post": {
        "operationId": "create_research_thread_api_notebooks__notebook_id__research_threads_post",
        "parameters": [
          {
            "in": "path",
            "name": "notebook_id",
            "required": true,
            "schema": {
              "title": "Notebook Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ResearchThreadCreateRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ResearchThreadResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "400": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Invalid research thread request"
          },
          "404": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Research thread or notebook not found"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          },
          "500": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Unexpected research thread error"
          }
        },
        "summary": "Create Research Thread",
        "tags": [
          "research-threads"
        ]
      }
    },
    "/api/notebooks/{notebook_id}/sources/{source_id}": {
      "delete": {
        "description": "Remove a source from a notebook (delete the reference).",
        "operationId": "remove_source_from_notebook_api_notebooks__notebook_id__sources__source_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "notebook_id",
            "required": true,
            "schema": {
              "title": "Notebook Id",
              "type": "string"
            }
          },
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Remove Source From Notebook",
        "tags": [
          "notebooks"
        ]
      },
      "post": {
        "description": "Add an existing source to a notebook (create the reference).",
        "operationId": "add_source_to_notebook_api_notebooks__notebook_id__sources__source_id__post",
        "parameters": [
          {
            "in": "path",
            "name": "notebook_id",
            "required": true,
            "schema": {
              "title": "Notebook Id",
              "type": "string"
            }
          },
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Add Source To Notebook",
        "tags": [
          "notebooks"
        ]
      }
    },
    "/api/notes": {
      "get": {
        "description": "Get all notes with optional notebook filtering.",
        "operationId": "get_notes_api_notes_get",
        "parameters": [
          {
            "description": "Filter by notebook ID",
            "in": "query",
            "name": "notebook_id",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "description": "Filter by notebook ID",
              "title": "Notebook Id"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/NoteResponse"
                  },
                  "title": "Response Get Notes Api Notes Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Notes",
        "tags": [
          "notes"
        ]
      },
      "post": {
        "description": "Create a new note.",
        "operationId": "create_note_api_notes_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/NoteCreate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/NoteResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Note",
        "tags": [
          "notes"
        ]
      }
    },
    "/api/notes/{note_id}": {
      "delete": {
        "description": "Delete a note.",
        "operationId": "delete_note_api_notes__note_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "note_id",
            "required": true,
            "schema": {
              "title": "Note Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Delete Note",
        "tags": [
          "notes"
        ]
      },
      "get": {
        "description": "Get a specific note by ID.",
        "operationId": "get_note_api_notes__note_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "note_id",
            "required": true,
            "schema": {
              "title": "Note Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/NoteResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Note",
        "tags": [
          "notes"
        ]
      },
      "put": {
        "description": "Update a note.",
        "operationId": "update_note_api_notes__note_id__put",
        "parameters": [
          {
            "in": "path",
            "name": "note_id",
            "required": true,
            "schema": {
              "title": "Note Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/NoteUpdate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/NoteResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Update Note",
        "tags": [
          "notes"
        ]
      }
    },
    "/api/podcasts/episodes": {
      "get": {
        "description": "List all podcast episodes",
        "operationId": "list_podcast_episodes_api_podcasts_episodes_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/PodcastEpisodeResponse"
                  },
                  "title": "Response List Podcast Episodes Api Podcasts Episodes Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "List Podcast Episodes",
        "tags": [
          "podcasts"
        ]
      }
    },
    "/api/podcasts/episodes/{episode_id}": {
      "delete": {
        "description": "Delete a podcast episode and its associated audio file",
        "operationId": "delete_podcast_episode_api_podcasts_episodes__episode_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "episode_id",
            "required": true,
            "schema": {
              "title": "Episode Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Delete Podcast Episode",
        "tags": [
          "podcasts"
        ]
      },
      "get": {
        "description": "Get a specific podcast episode",
        "operationId": "get_podcast_episode_api_podcasts_episodes__episode_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "episode_id",
            "required": true,
            "schema": {
              "title": "Episode Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/PodcastEpisodeResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Podcast Episode",
        "tags": [
          "podcasts"
        ]
      }
    },
    "/api/podcasts/episodes/{episode_id}/audio": {
      "get": {
        "description": "Stream the audio file associated with a podcast episode",
        "operationId": "stream_podcast_episode_audio_api_podcasts_episodes__episode_id__audio_get",
        "parameters": [
          {
            "in": "path",
            "name": "episode_id",
            "required": true,
            "schema": {
              "title": "Episode Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Stream Podcast Episode Audio",
        "tags": [
          "podcasts"
        ]
      }
    },
    "/api/podcasts/episodes/{episode_id}/retry": {
      "post": {
        "description": "Retry a failed podcast episode by deleting it and submitting a new job",
        "operationId": "retry_podcast_episode_api_podcasts_episodes__episode_id__retry_post",
        "parameters": [
          {
            "in": "path",
            "name": "episode_id",
            "required": true,
            "schema": {
              "title": "Episode Id",
              "type": "string"
            }
          },
          {
            "in": "header",
            "name": "Idempotency-Key",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Idempotency-Key"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Retry Podcast Episode",
        "tags": [
          "podcasts"
        ]
      }
    },
    "/api/podcasts/generate": {
      "post": {
        "description": "Generate a podcast episode using Episode Profiles.\nReturns immediately with job ID for status tracking.",
        "operationId": "generate_podcast_api_podcasts_generate_post",
        "parameters": [
          {
            "in": "header",
            "name": "Idempotency-Key",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Idempotency-Key"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/PodcastGenerationRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/PodcastGenerationResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Generate Podcast",
        "tags": [
          "podcasts"
        ]
      }
    },
    "/api/podcasts/jobs/{job_id}": {
      "get": {
        "description": "Get the status of a podcast generation job",
        "operationId": "get_podcast_job_status_api_podcasts_jobs__job_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "job_id",
            "required": true,
            "schema": {
              "title": "Job Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Podcast Job Status",
        "tags": [
          "podcasts"
        ]
      }
    },
    "/api/providers/policy": {
      "get": {
        "description": "Get provider policy used for modality routing and fallback.",
        "operationId": "get_policy_api_providers_policy_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ProviderPolicyResponse"
                }
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Get Policy",
        "tags": [
          "providers",
          "providers"
        ]
      },
      "put": {
        "description": "Update provider policy (Gemini-only).",
        "operationId": "update_policy_api_providers_policy_put",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ProviderPolicyUpdateRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ProviderPolicyResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Update Policy",
        "tags": [
          "providers",
          "providers"
        ]
      }
    },
    "/api/providers/policy/bootstrap-diagnostics": {
      "get": {
        "description": "Get startup diagnostics for Gemini-only readiness.",
        "operationId": "get_policy_bootstrap_diagnostics_api_providers_policy_bootstrap_diagnostics_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Get Policy Bootstrap Diagnostics",
        "tags": [
          "providers",
          "providers"
        ]
      }
    },
    "/api/research-threads/{thread_id}": {
      "get": {
        "operationId": "get_research_thread_api_research_threads__thread_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "thread_id",
            "required": true,
            "schema": {
              "title": "Thread Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ResearchThreadResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "400": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Invalid research thread request"
          },
          "404": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Research thread or notebook not found"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          },
          "500": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Unexpected research thread error"
          }
        },
        "summary": "Get Research Thread",
        "tags": [
          "research-threads"
        ]
      }
    },
    "/api/research-threads/{thread_id}/drafts": {
      "post": {
        "operationId": "create_draft_from_thread_api_research_threads__thread_id__drafts_post",
        "parameters": [
          {
            "in": "path",
            "name": "thread_id",
            "required": true,
            "schema": {
              "title": "Thread Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/DraftResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "400": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Invalid research thread request"
          },
          "404": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Research thread or notebook not found"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          },
          "500": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Unexpected research thread error"
          }
        },
        "summary": "Create Draft From Thread",
        "tags": [
          "research-threads"
        ]
      }
    },
    "/api/research-threads/{thread_id}/entries": {
      "post": {
        "operationId": "append_research_thread_entry_api_research_threads__thread_id__entries_post",
        "parameters": [
          {
            "in": "path",
            "name": "thread_id",
            "required": true,
            "schema": {
              "title": "Thread Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ResearchThreadEntryRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ResearchThreadResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "400": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Invalid research thread request"
          },
          "404": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Research thread or notebook not found"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          },
          "500": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ErrorResponse"
                }
              }
            },
            "description": "Unexpected research thread error"
          }
        },
        "summary": "Append Research Thread Entry",
        "tags": [
          "research-threads"
        ]
      }
    },
    "/api/search": {
      "post": {
        "description": "Search the knowledge base using text or vector search.",
        "operationId": "search_knowledge_base_api_search_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/SearchRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SearchResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Search Knowledge Base",
        "tags": [
          "search"
        ]
      }
    },
    "/api/search/ask": {
      "post": {
        "description": "Ask the knowledge base a question using AI models.",
        "operationId": "ask_knowledge_base_api_search_ask_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AskRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Ask Knowledge Base",
        "tags": [
          "search"
        ]
      }
    },
    "/api/search/ask/simple": {
      "post": {
        "description": "Ask the knowledge base a question and return a simple response (non-streaming).",
        "operationId": "ask_knowledge_base_simple_api_search_ask_simple_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AskRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/AskResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Ask Knowledge Base Simple",
        "tags": [
          "search"
        ]
      }
    },
    "/api/settings": {
      "get": {
        "description": "Get all application settings.",
        "operationId": "get_settings_api_settings_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SettingsResponse"
                }
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Get Settings",
        "tags": [
          "settings"
        ]
      },
      "put": {
        "description": "Update application settings.",
        "operationId": "update_settings_api_settings_put",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/SettingsUpdate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SettingsResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Update Settings",
        "tags": [
          "settings"
        ]
      }
    },
    "/api/sources": {
      "get": {
        "description": "Get sources with pagination and sorting support.",
        "operationId": "get_sources_api_sources_get",
        "parameters": [
          {
            "description": "Filter by notebook ID",
            "in": "query",
            "name": "notebook_id",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "description": "Filter by notebook ID",
              "title": "Notebook Id"
            }
          },
          {
            "description": "Number of sources to return (1-100)",
            "in": "query",
            "name": "limit",
            "required": false,
            "schema": {
              "default": 50,
              "description": "Number of sources to return (1-100)",
              "maximum": 100,
              "minimum": 1,
              "title": "Limit",
              "type": "integer"
            }
          },
          {
            "description": "Number of sources to skip",
            "in": "query",
            "name": "offset",
            "required": false,
            "schema": {
              "default": 0,
              "description": "Number of sources to skip",
              "minimum": 0,
              "title": "Offset",
              "type": "integer"
            }
          },
          {
            "description": "Field to sort by (created or updated)",
            "in": "query",
            "name": "sort_by",
            "required": false,
            "schema": {
              "default": "updated",
              "description": "Field to sort by (created or updated)",
              "title": "Sort By",
              "type": "string"
            }
          },
          {
            "description": "Sort order (asc or desc)",
            "in": "query",
            "name": "sort_order",
            "required": false,
            "schema": {
              "default": "desc",
              "description": "Sort order (asc or desc)",
              "title": "Sort Order",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/SourceListResponse"
                  },
                  "title": "Response Get Sources Api Sources Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Sources",
        "tags": [
          "sources"
        ]
      },
      "post": {
        "description": "Create a new source with support for both JSON and multipart form data.",
        "operationId": "create_source_api_sources_post",
        "requestBody": {
          "content": {
            "multipart/form-data": {
              "schema": {
                "$ref": "#/components/schemas/Body_create_source_api_sources_post"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SourceResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Source",
        "tags": [
          "sources"
        ]
      }
    },
    "/api/sources/json": {
      "post": {
        "description": "Create a new source using JSON payload (legacy endpoint for backward compatibility).",
        "operationId": "create_source_json_api_sources_json_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/SourceCreate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SourceResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Source Json",
        "tags": [
          "sources"
        ]
      }
    },
    "/api/sources/{source_id}": {
      "delete": {
        "description": "Delete a source.",
        "operationId": "delete_source_api_sources__source_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Delete Source",
        "tags": [
          "sources"
        ]
      },
      "get": {
        "description": "Get a specific source by ID.",
        "operationId": "get_source_api_sources__source_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SourceResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Source",
        "tags": [
          "sources"
        ]
      },
      "put": {
        "description": "Update a source.",
        "operationId": "update_source_api_sources__source_id__put",
        "parameters": [
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/SourceUpdate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SourceResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Update Source",
        "tags": [
          "sources"
        ]
      }
    },
    "/api/sources/{source_id}/auditable-runs": {
      "get": {
        "operationId": "list_auditable_runs_by_source_api_sources__source_id__auditable_runs_get",
        "parameters": [
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/AuditableRunResponse"
                  },
                  "title": "Response List Auditable Runs By Source Api Sources  Source Id  Auditable Runs Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "List Auditable Runs By Source",
        "tags": [
          "auditable-runs"
        ]
      },
      "post": {
        "operationId": "create_auditable_run_api_sources__source_id__auditable_runs_post",
        "parameters": [
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AuditableRunCreateRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/AuditableRunResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Auditable Run",
        "tags": [
          "auditable-runs"
        ]
      }
    },
    "/api/sources/{source_id}/chat/sessions": {
      "get": {
        "description": "Get all chat sessions for a source.",
        "operationId": "get_source_chat_sessions_api_sources__source_id__chat_sessions_get",
        "parameters": [
          {
            "description": "Source ID",
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "description": "Source ID",
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/SourceChatSessionResponse"
                  },
                  "title": "Response Get Source Chat Sessions Api Sources  Source Id  Chat Sessions Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Source Chat Sessions",
        "tags": [
          "source-chat"
        ]
      },
      "post": {
        "description": "Create a new chat session for a source.",
        "operationId": "create_source_chat_session_api_sources__source_id__chat_sessions_post",
        "parameters": [
          {
            "description": "Source ID",
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "description": "Source ID",
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/CreateSourceChatSessionRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SourceChatSessionResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Source Chat Session",
        "tags": [
          "source-chat"
        ]
      }
    },
    "/api/sources/{source_id}/chat/sessions/{session_id}": {
      "delete": {
        "description": "Delete a source chat session.",
        "operationId": "delete_source_chat_session_api_sources__source_id__chat_sessions__session_id__delete",
        "parameters": [
          {
            "description": "Source ID",
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "description": "Source ID",
              "title": "Source Id",
              "type": "string"
            }
          },
          {
            "description": "Session ID",
            "in": "path",
            "name": "session_id",
            "required": true,
            "schema": {
              "description": "Session ID",
              "title": "Session Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SuccessResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Delete Source Chat Session",
        "tags": [
          "source-chat"
        ]
      },
      "get": {
        "description": "Get a specific source chat session with its messages.",
        "operationId": "get_source_chat_session_api_sources__source_id__chat_sessions__session_id__get",
        "parameters": [
          {
            "description": "Source ID",
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "description": "Source ID",
              "title": "Source Id",
              "type": "string"
            }
          },
          {
            "description": "Session ID",
            "in": "path",
            "name": "session_id",
            "required": true,
            "schema": {
              "description": "Session ID",
              "title": "Session Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SourceChatSessionWithMessagesResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Source Chat Session",
        "tags": [
          "source-chat"
        ]
      },
      "put": {
        "description": "Update source chat session title and/or model override.",
        "operationId": "update_source_chat_session_api_sources__source_id__chat_sessions__session_id__put",
        "parameters": [
          {
            "description": "Source ID",
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "description": "Source ID",
              "title": "Source Id",
              "type": "string"
            }
          },
          {
            "description": "Session ID",
            "in": "path",
            "name": "session_id",
            "required": true,
            "schema": {
              "description": "Session ID",
              "title": "Session Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/UpdateSourceChatSessionRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SourceChatSessionResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Update Source Chat Session",
        "tags": [
          "source-chat"
        ]
      }
    },
    "/api/sources/{source_id}/chat/sessions/{session_id}/messages": {
      "post": {
        "description": "Send a message to source chat session with SSE streaming response.",
        "operationId": "send_message_to_source_chat_api_sources__source_id__chat_sessions__session_id__messages_post",
        "parameters": [
          {
            "description": "Source ID",
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "description": "Source ID",
              "title": "Source Id",
              "type": "string"
            }
          },
          {
            "description": "Session ID",
            "in": "path",
            "name": "session_id",
            "required": true,
            "schema": {
              "description": "Session ID",
              "title": "Session Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/SendMessageRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Send Message To Source Chat",
        "tags": [
          "source-chat"
        ]
      }
    },
    "/api/sources/{source_id}/download": {
      "get": {
        "description": "Download the original file associated with an uploaded source.",
        "operationId": "download_source_file_api_sources__source_id__download_get",
        "parameters": [
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Download Source File",
        "tags": [
          "sources"
        ]
      },
      "head": {
        "description": "Check if a source has a downloadable file.",
        "operationId": "check_source_file_api_sources__source_id__download_head",
        "parameters": [
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Check Source File",
        "tags": [
          "sources"
        ]
      }
    },
    "/api/sources/{source_id}/insights": {
      "get": {
        "description": "Get all insights for a specific source.",
        "operationId": "get_source_insights_api_sources__source_id__insights_get",
        "parameters": [
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/SourceInsightResponse"
                  },
                  "title": "Response Get Source Insights Api Sources  Source Id  Insights Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Source Insights",
        "tags": [
          "sources"
        ]
      },
      "post": {
        "description": "Start insight generation for a source by running a transformation.\n\nThis endpoint returns immediately with a 202 Accepted status.\nThe transformation runs asynchronously in the background via the job queue.\nPoll GET /sources/{source_id}/insights to see when the insight is ready.",
        "operationId": "create_source_insight_api_sources__source_id__insights_post",
        "parameters": [
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/CreateSourceInsightRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "202": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/InsightCreationResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Source Insight",
        "tags": [
          "sources"
        ]
      }
    },
    "/api/sources/{source_id}/processing-report": {
      "get": {
        "description": "Get a human-readable processing report for a source.",
        "operationId": "get_source_processing_report_api_sources__source_id__processing_report_get",
        "parameters": [
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SourceProcessingReportResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Source Processing Report",
        "tags": [
          "sources"
        ]
      }
    },
    "/api/sources/{source_id}/reprocess": {
      "post": {
        "description": "Canonical reprocess entrypoint for the Source QA console.",
        "operationId": "reprocess_source_api_sources__source_id__reprocess_post",
        "parameters": [
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SourceResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Reprocess Source",
        "tags": [
          "sources"
        ]
      }
    },
    "/api/sources/{source_id}/retry": {
      "post": {
        "description": "Retry processing for a failed or stuck source.",
        "operationId": "retry_source_processing_api_sources__source_id__retry_post",
        "parameters": [
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SourceResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Retry Source Processing",
        "tags": [
          "sources"
        ]
      }
    },
    "/api/sources/{source_id}/status": {
      "get": {
        "description": "Get processing status for a source.",
        "operationId": "get_source_status_api_sources__source_id__status_get",
        "parameters": [
          {
            "in": "path",
            "name": "source_id",
            "required": true,
            "schema": {
              "title": "Source Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SourceStatusResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Source Status",
        "tags": [
          "sources"
        ]
      }
    },
    "/api/speaker-profiles": {
      "get": {
        "description": "List all available speaker profiles",
        "operationId": "list_speaker_profiles_api_speaker_profiles_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/SpeakerProfileResponse"
                  },
                  "title": "Response List Speaker Profiles Api Speaker Profiles Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "List Speaker Profiles",
        "tags": [
          "speaker-profiles"
        ]
      },
      "post": {
        "description": "Create a new speaker profile",
        "operationId": "create_speaker_profile_api_speaker_profiles_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/SpeakerProfileCreate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SpeakerProfileResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Speaker Profile",
        "tags": [
          "speaker-profiles"
        ]
      }
    },
    "/api/speaker-profiles/{profile_id}": {
      "delete": {
        "description": "Delete a speaker profile",
        "operationId": "delete_speaker_profile_api_speaker_profiles__profile_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "profile_id",
            "required": true,
            "schema": {
              "title": "Profile Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Delete Speaker Profile",
        "tags": [
          "speaker-profiles"
        ]
      },
      "put": {
        "description": "Update an existing speaker profile",
        "operationId": "update_speaker_profile_api_speaker_profiles__profile_id__put",
        "parameters": [
          {
            "in": "path",
            "name": "profile_id",
            "required": true,
            "schema": {
              "title": "Profile Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/SpeakerProfileCreate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SpeakerProfileResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Update Speaker Profile",
        "tags": [
          "speaker-profiles"
        ]
      }
    },
    "/api/speaker-profiles/{profile_id}/duplicate": {
      "post": {
        "description": "Duplicate a speaker profile",
        "operationId": "duplicate_speaker_profile_api_speaker_profiles__profile_id__duplicate_post",
        "parameters": [
          {
            "in": "path",
            "name": "profile_id",
            "required": true,
            "schema": {
              "title": "Profile Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SpeakerProfileResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Duplicate Speaker Profile",
        "tags": [
          "speaker-profiles"
        ]
      }
    },
    "/api/speaker-profiles/{profile_name}": {
      "get": {
        "description": "Get a specific speaker profile by name",
        "operationId": "get_speaker_profile_api_speaker_profiles__profile_name__get",
        "parameters": [
          {
            "in": "path",
            "name": "profile_name",
            "required": true,
            "schema": {
              "title": "Profile Name",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/SpeakerProfileResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Speaker Profile",
        "tags": [
          "speaker-profiles"
        ]
      }
    },
    "/api/transformations": {
      "get": {
        "description": "Get all transformations.",
        "operationId": "get_transformations_api_transformations_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/TransformationResponse"
                  },
                  "title": "Response Get Transformations Api Transformations Get",
                  "type": "array"
                }
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Get Transformations",
        "tags": [
          "transformations"
        ]
      },
      "post": {
        "description": "Create a new transformation.",
        "operationId": "create_transformation_api_transformations_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/TransformationCreate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/TransformationResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Create Transformation",
        "tags": [
          "transformations"
        ]
      }
    },
    "/api/transformations/default-prompt": {
      "get": {
        "description": "Get the default transformation prompt.",
        "operationId": "get_default_prompt_api_transformations_default_prompt_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/DefaultPromptResponse"
                }
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Get Default Prompt",
        "tags": [
          "transformations"
        ]
      },
      "put": {
        "description": "Update the default transformation prompt.",
        "operationId": "update_default_prompt_api_transformations_default_prompt_put",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/DefaultPromptUpdate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/DefaultPromptResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Update Default Prompt",
        "tags": [
          "transformations"
        ]
      }
    },
    "/api/transformations/execute": {
      "post": {
        "description": "Execute a transformation on input text.",
        "operationId": "execute_transformation_api_transformations_execute_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/TransformationExecuteRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/TransformationExecuteResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Execute Transformation",
        "tags": [
          "transformations"
        ]
      }
    },
    "/api/transformations/{transformation_id}": {
      "delete": {
        "description": "Delete a transformation.",
        "operationId": "delete_transformation_api_transformations__transformation_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "transformation_id",
            "required": true,
            "schema": {
              "title": "Transformation Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Delete Transformation",
        "tags": [
          "transformations"
        ]
      },
      "get": {
        "description": "Get a specific transformation by ID.",
        "operationId": "get_transformation_api_transformations__transformation_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "transformation_id",
            "required": true,
            "schema": {
              "title": "Transformation Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/TransformationResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Transformation",
        "tags": [
          "transformations"
        ]
      },
      "put": {
        "description": "Update a transformation.",
        "operationId": "update_transformation_api_transformations__transformation_id__put",
        "parameters": [
          {
            "in": "path",
            "name": "transformation_id",
            "required": true,
            "schema": {
              "title": "Transformation Id",
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/TransformationUpdate"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/TransformationResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Update Transformation",
        "tags": [
          "transformations"
        ]
      }
    },
    "/api/ui-tests/run": {
      "post": {
        "operationId": "run_ui_test_api_ui_tests_run_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/UITestRunRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/UITestRunResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Run Ui Test",
        "tags": [
          "ui-tests"
        ]
      }
    },
    "/api/ui-tests/{run_id}": {
      "get": {
        "operationId": "get_ui_test_run_api_ui_tests__run_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "run_id",
            "required": true,
            "schema": {
              "title": "Run Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/UITestRunResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Ui Test Run",
        "tags": [
          "ui-tests"
        ]
      }
    },
    "/api/ui-tests/{run_id}/report": {
      "get": {
        "operationId": "get_ui_test_report_api_ui_tests__run_id__report_get",
        "parameters": [
          {
            "in": "path",
            "name": "run_id",
            "required": true,
            "schema": {
              "title": "Run Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/UITestReportResponse"
                }
              }
            },
            "description": "Successful Response"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          }
        },
        "summary": "Get Ui Test Report",
        "tags": [
          "ui-tests"
        ]
      }
    },
    "/health": {
      "get": {
        "operationId": "health_health_get",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {}
              }
            },
            "description": "Successful Response"
          }
        },
        "summary": "Health"
      }
    }
  }
}
`,
) as Readonly<Record<string, unknown>>;
