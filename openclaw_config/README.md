# OpenClaw Configuration Guide

This directory contains the local OpenClaw configuration used by
FORTE. Users only need to edit two files after copying the examples:

- `.env`: stores API keys, gateway tokens, and optional extra headers.
- `openclaw.json`: stores OpenClaw provider, model, agent, and gateway settings.

Both files are gitignored. Do not commit real API keys.

## Files To Copy

```bash
cp openclaw_config/openclaw.json.example openclaw_config/openclaw.json
cp openclaw_config/.env.example openclaw_config/.env
```

After copying, fill in `.env` first, then make `openclaw.json` reference the
environment variable names defined in `.env`.

## Basic Rules

- Put secrets in `.env`, not directly in `openclaw.json`.
- Keep provider names consistent across `models.providers`,
  `agents.defaults.model.primary`, and `agents.defaults.models`.
- For custom providers, every model that may be selected later must be listed in
  `models.providers.<provider>.models[]`.
- For LLM judge tasks, fill `JUDGE_BASE_URL`, `JUDGE_API_KEY`, and
  `JUDGE_MODEL`.
- If your gateway requires extra request headers, configure them in both
  `openclaw.json` for the agent and `JUDGE_HEADERS` for the judge.

## `.env`

`.env` stores local secrets and environment variables. A typical file contains:

```dotenv
OPENCLAW_GATEWAY_TOKEN=<random-token>

PROVIDER_API_KEY=sk-...
PROVIDER_EXTRA_HEADER_VALUE=<optional-header-value>

JUDGE_BASE_URL=https://api.example.com/v1
JUDGE_API_KEY=sk-...
JUDGE_MODEL=<judge-model-id>
JUDGE_HEADERS={"x-custom-header":"<optional-header-value>"}
```

Field meanings:

- `OPENCLAW_GATEWAY_TOKEN`: local token used by the OpenClaw gateway. Any strong
  random string is fine.
- `PROVIDER_API_KEY`: API key used by the agent provider. The name can be
  customized, but it must exactly match `apiKey.id` in `openclaw.json`.
- `PROVIDER_EXTRA_HEADER_VALUE`: optional value for provider-specific headers,
  such as user id, tenant id, project id, or organization id.
- `JUDGE_BASE_URL`: OpenAI-compatible base URL for the judge. Use the base path,
  for example `https://api.example.com/v1`, not the full
  `/chat/completions` endpoint.
- `JUDGE_API_KEY`: API key used by the judge.
- `JUDGE_MODEL`: model id used by the judge.
- `JUDGE_HEADERS`: optional single-line JSON object for extra judge request
  headers. Leave it commented out if the judge gateway does not need extra
  headers.

If the agent and judge use the same gateway, `PROVIDER_API_KEY` and
`JUDGE_API_KEY` may contain the same key. They are kept separate so users can
also choose different models or gateways for agent execution and judging.

## `openclaw.json`

`openclaw.json` tells OpenClaw which provider and model ids are available to the
agent.

The important sections are:

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "provider_name": {
        "baseUrl": "https://api.example.com/v1",
        "apiKey": {
          "source": "env",
          "provider": "default",
          "id": "PROVIDER_API_KEY"
        },
        "api": "openai-completions",
        "models": [
          {
            "id": "model-a",
            "name": "model-a",
            "reasoning": false,
            "input": ["text"],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 200000,
            "maxTokens": 8192
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "provider_name/model-a"
      },
      "models": {
        "provider_name/model-a": {
          "alias": "model-a"
        }
      },
      "workspace": "/home/node/.openclaw/workspace",
      "compaction": {
        "mode": "safeguard"
      }
    }
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "loopback",
    "auth": {
      "mode": "token",
      "token": "${OPENCLAW_GATEWAY_TOKEN}"
    }
  }
}
```

Field meanings:

- `models.providers.provider_name`: local provider id. Choose a short stable
  name, such as `openrouter`, `custom`, or your gateway name.
- `baseUrl`: OpenAI-compatible base URL. Use `https://host/v1`, not
  `https://host/v1/chat/completions`.
- `apiKey.id`: environment variable name from `.env`.
- `api`: OpenClaw provider API type. Use `openai-completions` for OpenAI-compatible custom providers.
- `models[].id`: model id sent to the provider.
- `agents.defaults.model.primary`: default model reference in
  `<provider>/<model-id>` form.
- `agents.defaults.models`: model references exposed to OpenClaw agents. Keep
  the keys in the same `<provider>/<model-id>` form.
- `gateway.auth.token`: should reference `${OPENCLAW_GATEWAY_TOKEN}` so the
  actual token remains in `.env`.

## Extra Headers

Some gateways require additional headers besides `Authorization`.

Do not manually configure these two headers:

- `Authorization: Bearer ...`
- `Content-Type: application/json`

They are handled by the client.

Only configure provider-specific headers. For example, if the gateway requires
`x-user-id`, put the value in `.env`:

```dotenv
PROVIDER_API_KEY=sk-...
PROVIDER_USER_ID=user-123

JUDGE_HEADERS={"x-user-id":"user-123"}
```

Then reference the value from `openclaw.json`:

```json
"headers": {
  "x-user-id": "${PROVIDER_USER_ID}"
}
```

If the judge uses the same extra header, keep `JUDGE_HEADERS` in sync:

```dotenv
JUDGE_HEADERS={"x-user-id":"user-123"}
```

If no extra headers are required, omit `headers` in `openclaw.json` and leave
`JUDGE_HEADERS` commented out.

## OpenRouter Example

For OpenRouter, `.env` usually needs:

```dotenv
OPENCLAW_GATEWAY_TOKEN=<random-token>
OPENROUTER_API_KEY=sk-or-...

JUDGE_BASE_URL=https://openrouter.ai/api/v1
JUDGE_API_KEY=sk-or-...
JUDGE_MODEL=anthropic/claude-opus-4.6
```

The provider id should stay consistent:

```json
"providers": {
  "openrouter": {
    "baseUrl": "https://openrouter.ai/api/v1",
    "apiKey": {
      "source": "env",
      "provider": "default",
      "id": "OPENROUTER_API_KEY"
    },
    "api": "openai-completions",
    "models": [
      {
        "id": "anthropic/claude-sonnet-4.6",
        "name": "claude-sonnet-4.6",
        "reasoning": true,
        "input": ["text"],
        "cost": {
          "input": 0,
          "output": 0,
          "cacheRead": 0,
          "cacheWrite": 0
        },
        "contextWindow": 200000,
        "maxTokens": 32768
      }
    ]
  }
}
```

And the agent model references should use the same provider id:

```json
"model": {
  "primary": "openrouter/anthropic/claude-sonnet-4.6"
},
"models": {
  "openrouter/anthropic/claude-sonnet-4.6": {
    "alias": "claude-sonnet-4.6"
  }
}
```

## Custom Gateway Example

For a generic OpenAI-compatible gateway, use a neutral provider id such as
`custom`:

```dotenv
OPENCLAW_GATEWAY_TOKEN=<random-token>

CUSTOM_API_KEY=sk-...
CUSTOM_USER_ID=user-123

JUDGE_BASE_URL=https://api.example.com/v1
JUDGE_API_KEY=sk-...
JUDGE_MODEL=model-a
JUDGE_HEADERS={"x-user-id":"user-123"}
```

Then configure the provider:

```json
"providers": {
  "custom": {
    "baseUrl": "https://api.example.com/v1",
    "apiKey": {
      "source": "env",
      "provider": "default",
      "id": "CUSTOM_API_KEY"
    },
    "api": "openai-completions",
    "headers": {
      "x-user-id": "${CUSTOM_USER_ID}"
    },
    "models": [
      {
        "id": "model-a",
        "name": "model-a",
        "reasoning": false,
        "input": ["text"],
        "cost": {
          "input": 0,
          "output": 0,
          "cacheRead": 0,
          "cacheWrite": 0
        },
        "contextWindow": 200000,
        "maxTokens": 8192
      }
    ]
  }
}
```

And keep the agent model references aligned:

```json
"model": {
  "primary": "custom/model-a"
},
"models": {
  "custom/model-a": {
    "alias": "model-a"
  }
}
```

## Multiple Models

To make several models available, add them to the provider model list:

```json
"models": [
  {
    "id": "model-a",
    "name": "model-a",
    "reasoning": false,
    "input": ["text"],
    "contextWindow": 200000,
    "maxTokens": 8192
  },
  {
    "id": "model-b",
    "name": "model-b",
    "reasoning": false,
    "input": ["text"],
    "contextWindow": 200000,
    "maxTokens": 8192
  }
]
```

Then expose the same fully qualified ids under `agents.defaults.models`:

```json
"models": {
  "custom/model-a": {
    "alias": "model-a"
  },
  "custom/model-b": {
    "alias": "model-b"
  }
}
```

The default model can point to any one of the registered models:

```json
"model": {
  "primary": "custom/model-a"
}
```

## Common Mistakes

- Provider mismatch: `models.providers` defines `custom`, but
  `agents.defaults.model.primary` uses another provider name.
- Environment variable mismatch: `openclaw.json` references one variable name,
  but `.env` defines a different name.
- Missing model registration: a model appears in `agents.defaults.models`, but
  not in `models.providers.<provider>.models[]`.
- Missing judge credentials: LLM judge tasks require `JUDGE_BASE_URL`,
  `JUDGE_API_KEY`, and `JUDGE_MODEL`.
- Malformed `JUDGE_HEADERS`: it must be a single-line JSON object, for example
  `JUDGE_HEADERS={"x-user-id":"user-123"}`.
- Wrong base URL: use `https://host/v1`, not
  `https://host/v1/chat/completions`.
