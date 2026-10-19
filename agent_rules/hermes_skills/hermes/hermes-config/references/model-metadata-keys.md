# Model Metadata Auto-Detection Keys

Source: `agent/model_metadata.py` and `agent/models_dev.py`

## Context Window Detection

Hermes queries the provider's model list and extracts context window from the first matching key:

```python
_CONTEXT_LENGTH_KEYS = (
    "context_length",
    "context_window",
    "context_size",
    "max_context_length",
    "max_position_embeddings",
    "max_model_len",
    "max_input_tokens",
    "max_sequence_length",
    "max_seq_len",
    "n_ctx_train",
    "n_ctx",
    "ctx_size",
)
```

## Output Token Detection

```python
_MAX_COMPLETION_KEYS = (
    "max_completion_tokens",
    "max_output_tokens",
    "max_tokens",
)
```

## ModelCapabilities Dataclass

```python
@dataclass
class ModelCapabilities:
    supports_tools: bool = True
    supports_vision: bool = False
    supports_reasoning: bool = False
    context_window: int = 200000      # default if detection fails
    max_output_tokens: int = 8192     # default if detection fails
    model_family: str = ""
```

## Custom Provider Behavior

When `provider: custom` and `base_url` points to a local server:
- Hermes attempts to fetch `/models` from the base_url
- If the server doesn't expose model metadata, context_window defaults to 200000 and max_output_tokens to 8192
- **Always set explicit values in config.yaml for custom providers** — auto-detection is unreliable for local/custom endpoints

## Compression Threshold Interaction

Compression fires when `estimated_tokens > context_window * threshold`.

With a custom provider that doesn't report context_window, Hermes uses 200000 as the window. If you set `model.context_window: 500000` in config, that overrides auto-detection. The compression engine reads the overridden value.
