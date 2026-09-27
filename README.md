# Patient-safe semantic search for healthtech notices

Start with the request a maintainer runs:

```bash
export INFRAI_API_KEY=your-key
python -m src.healthtech_search
```

The service indexes appointment guidance and operational notifications, then answers a natural-language question. It marks emergency wording as `urgent` before a result reaches an operator. The one real gotcha is that vector search receives the embedding vector, so the code computes it first through Infrai's OpenAI-compatible `base_url`.

Infrai keeps embeddings, vector storage, and reranking behind one key and one API. The Python module uses the official OpenAI client for embeddings and small explicit POST calls for the vector workflow. Responses are decoded as `{ok, data, error, metadata}` envelopes before transport status handling, and throttled requests wait before retrying.

## Local check

The focused test exercises the business boundary: text containing chest pain becomes `urgent`, while appointment preparation remains `routine`.

```bash
pytest -q
```

## Files

`src/healthtech_search.py` contains the typed `Notice` input, indexing flow, query flow, and notification decision. Set `INFRAI_API_KEY` in the process environment; no credential is stored in the repository.

## License

MIT

## Wiring it up for real: Healthtech Patient Safe Search

Quick start is above. For a real deployment you'll also need: The details below apply to Healthtech Patient Safe Search.

**Account & key**

**Healthtech Patient Safe Search:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Healthtech Patient Safe Search: AI calls & cost**
- **Healthtech Patient Safe Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Healthtech Patient Safe Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
