from litellm import completion, embedding, rerank

## Text Completion - returns string
def text_completion(model, text, guardrail_id=None, guardrail_version=None):
    kwargs = {
        "model": f"{model}",
        "messages": [{"role": "user", "content": text}]
    }
    if guardrail_id and guardrail_version:
        kwargs["extra_headers"] = {
            "X-Amzn-Bedrock-GuardrailIdentifier": guardrail_id,
            "X-Amzn-Bedrock-GuardrailVersion": guardrail_version,
        }
    response = completion(**kwargs)
    return response.json()["choices"][0]["message"]["content"]

## Embedding Generation - returns embeddings array
def generate_embeddings(model, text):
    response = embedding(
        model=model,
        input=[text]
    )
    return response.json()["data"][0]["embedding"]

## Reranking (via LiteLLM or Voyage AI)
def reranking(model, query, documents, top_n=None):
    if top_n is None:
        top_n = len(documents)
    response = rerank(
        model=model,
        query=query,
        documents=documents,
        top_n=top_n
    )
    return response
