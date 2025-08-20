# Settings Reference

There are [user-side](./settings.md) explanations about the settings, and more [detailed ones](../devs/settings_architecture.md) for developers.

### LLM Configuration (`llm`)

| Setting         | Description                                | Default                | Access Level | Environment Variable |
|-----------------|--------------------------------------------|------------------------|--------------|---------------------|
| provider_enum   | LLM provider to use ('ollama' or 'openai').| `ollama`               | normal       | `LLM_PROVIDER`      |
| model           | Default LLM to use for the selected provider.                                | `llama3.2`             | normal       | `LLM_MODEL`         |
| models          | List of LLMs the user can choose from.     | See code default       | normal       | `LLM_MODELS`        |

### Ollama Configuration (`ollama`)

| Setting           | Description                                | Default                | Access Level | Environment Variable |
|-------------------|--------------------------------------------|------------------------|--------------|---------------------|
| ip                | IP address for the Ollama API endpoint.    | `localhost`            | protected    | `OLLAMA_IP`         |
| port              | Port for the Ollama API endpoint.          | `11434`                | protected    | `OLLAMA_PORT`       |
| num_ctx           | Context window size for token generation.  | `4096`                 | normal       | `OLLAMA_NUM_CTX`    |
| repeat_last_n     | How far back to look to prevent repetition.| `64`                   | normal       | `OLLAMA_REPEAT_LAST_N` |
| repeat_penalty    | Strength of repetition penalty.            | `1.1`                  | normal       | `OLLAMA_REPEAT_PENALTY` |
| temperature       | Sampling temperature.                      | `0.8`                  | normal       | `OLLAMA_TEMPERATURE`|
| timeout           | Timeout in seconds for API requests.       | `30.0`                 | normal       | `OLLAMA_TIMEOUT`    |
| seed              | Random seed for generation.                | `0`                    | normal       | `OLLAMA_SEED`       |
| stop              | Stop sequences for generation.             | `None`                 | normal       |                     |
| num_predict       | Maximum tokens to predict.                 | `-1`                   | normal       | `OLLAMA_NUM_PREDICT`|
| top_k             | Top-k sampling parameter.                  | `40`                   | normal       | `OLLAMA_TOP_K`      |
| top_p             | Top-p sampling parameter.                  | `0.9`                  | normal       | `OLLAMA_TOP_P`      |
| min_p             | Minimum probability for sampling.          | `0.0`                  | normal       | `OLLAMA_MIN_P`      |

### OpenAI Configuration (`openai`)

| Setting               | Description                                | Default                | Access Level | Environment Variable |
|-----------------------|--------------------------------------------|------------------------|--------------|---------------------|
| api_key               | API key for OpenAI services.               | From env               | protected    | `OPENAI_API_KEY`    |
| api_base              | Base URL for OpenAI API requests.          | `https://api.openai.com/v1` | read_only    |                     |
| timeout               | Timeout in seconds for API requests.       | `60`                   | normal       | `OPENAI_TIMEOUT`    |
| max_completion_tokens | Maximum tokens for completions.            | `2048`                 | normal       | `OPENAI_MAX_COMPLETION_TOKENS` |
| temperature           | Sampling temperature.                      | `0.7`                  | normal       | `OPENAI_TEMPERATURE`|
| top_p                 | Nucleus sampling parameter.                | `1.0`                  | normal       | `OPENAI_TOP_P`      |
| tool_choice           | Tool choice for API requests.              | `auto`                 | normal       | `OPENAI_TOOL_CHOICE`|

### Path Configuration (`paths`)

| Setting               | Description                                | Default                | Access Level | Environment Variable |
|-----------------------|--------------------------------------------|------------------------|--------------|---------------------|
| hatchling_source_dir  | Directory where Hatchling source code is located. | Auto-detected          | read_only    | `HATCHLING_SOURCE_DIR` |
| envs_dir              | Directory for Hatch environments.          | Auto-detected          | read_only    | `HATCH_ENVS_DIR`    |
| hatchling_cache_dir   | Directory for Hatchling cache and data storage.                             | `~/.hatch`             | read_only    | `HATCHLING_CACHE_DIR`|
| hatchling_settings_dir| Directory for Hatchling settings storage.  | `~/.hatch/settings`    | read_only    | `HATCHLING_SETTINGS_DIR`|

### Tool Calling (`tool_calling`)

| Setting             | Description                                | Default                | Access Level | Environment Variable |
|---------------------|--------------------------------------------|------------------------|--------------|---------------------|
| max_iterations      | Maximum number of tool call iterations.    | `5`                    | normal       |                     |
| max_working_time    | Maximum time in seconds for tool operations.                                | `60.0`                 | normal       |                     |
| max_tool_working_time | Maximum time in seconds for a single tool operation.                      | `12.0`                 | normal       |                     |

### User Interface (`ui`)

| Setting         | Description                                | Default                | Access Level | Environment Variable |
|-----------------|--------------------------------------------|------------------------|--------------|---------------------|
| language_code   | Language code for user interface localization.  | `en`                   | normal       | `HATCHLING_DEFAULT_LANGUAGE` |
| language_code   | Language code for user interface localization.  | `en`                   | `fr`                     | normal       | `HATCHLING_DEFAULT_LANGUAGE` |
