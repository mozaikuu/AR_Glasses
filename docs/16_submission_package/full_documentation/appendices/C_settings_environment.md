# Appendix C — Settings and environment variables

All keys are defined on the `Settings` dataclass in `app/config/settings.py`. Environment variables override values from optional `local.settings.json` (repo root or `app/config/`).

| Attribute | Env key | Default (code literal) |
|-----------|---------|-------------------------|
| `api_host` | `API_HOST` | `0.0.0.0` |
| `api_port` | `API_PORT` | `8000` |
| `debug` | `DEBUG` | `false` |
| `auto_start_wakeword` | `AUTO_START_WAKEWORD` | `true` |
| `preload_on_startup` | `PRELOAD_ON_STARTUP` | `true` |
| `flask_host` | `FLASK_HOST` | `0.0.0.0` |
| `flask_port` | `FLASK_PORT` | `5000` |
| `enable_flask` | `ENABLE_FLASK` | `false` |
| `streamlit_host` | `STREAMLIT_HOST` | `0.0.0.0` |
| `streamlit_port` | `STREAMLIT_PORT` | `8501` |
| `streamlit_app_path` | `STREAMLIT_APP_PATH` | `streamlit_app.py` |
| `enable_streamlit` | `ENABLE_STREAMLIT` | `true` |
| `audio_sidecar_host` | `AUDIO_SIDECAR_HOST` | `0.0.0.0` |
| `audio_sidecar_port` | `AUDIO_SIDECAR_PORT` | `8010` |
| `enable_audio_sidecar` | `ENABLE_AUDIO_SIDECAR` | `true` |
| `mcp_host` | `MCP_HOST` | `127.0.0.1` |
| `mcp_port` | `MCP_PORT` | `8020` |
| `enable_mcp_server` | `ENABLE_MCP_SERVER` | `true` |
| `model_provider` | `MODEL_PROVIDER` | `cerebras` |
| `model_id` | `MODEL_ID` | `llama-3.1-8b` |
| `api_base_url` | `API_BASE_URL` | `https://api.cerebras.ai/v1` |
| `api_key` | `API_KEY` | *(empty)* |
| `max_agent_loops` | `MAX_AGENT_LOOPS` | `3` |
| `max_answer_sentences` | `MAX_ANSWER_SENTENCES` | `3` |
| `wake_words` | `WAKE_WORDS` | CSV default `computer, hey computer, ok computer, okay computer` |
| `wake_word_aliases` | `WAKE_WORD_ALIASES` | *(empty)* |
| `wake_context_chars` | `WAKE_CONTEXT_CHARS` | `600` |
| `wake_followup_window_seconds` | `WAKE_FOLLOWUP_WINDOW_SECONDS` | `8.0` |
| `wake_min_transcript_chars` | `WAKE_MIN_TRANSCRIPT_CHARS` | `2` |
| `stt_retry_attempts` | `STT_RETRY_ATTEMPTS` | `2` |
| `stt_retry_backoff_ms` | `STT_RETRY_BACKOFF_MS` | `250` |
| `wakeword_rollout_scope` | `WAKEWORD_ROLLOUT_SCOPE` | `streamlit-only` |
| `cors_allow_origins` | `CORS_ALLOW_ORIGINS` | `*` |
| `public_base_url` | `PUBLIC_BASE_URL` | *(empty)* |
| `unity_api_key` | `UNITY_API_KEY` | *(empty)* |
| `enable_piper_tts` | `ENABLE_PIPER_TTS` | `true` |
| `piper_exe` | `PIPER_EXE` | Windows: `Smart_Glasses/models/piper/piper.exe`; else `piper` |
| `piper_model_path` | `PIPER_MODEL_PATH` | `Smart_Glasses/models/piper/en_US-lessac-medium.onnx` |
| `piper_config_path` | `PIPER_CONFIG_PATH` | `Smart_Glasses/models/piper/en_US-lessac-medium.onnx.json` |
| `launcher_profile` | `LAUNCHER_PROFILE` | `production-local` |
| `restart_crashed_services` | `RESTART_CRASHED_SERVICES` | `true` |
| `auto_reload` | `AUTO_RELOAD` | `true` |

**Security note:** never commit real `API_KEY`, `UNITY_API_KEY`, or provider secrets into Git; use local environment or CI secrets.
