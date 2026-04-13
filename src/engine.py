import json
import os
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url="http://localhost:11434/v1/",
    api_key="ollama",  # required by openai client, ignored by Ollama
)


class OllamaEngine:
    async def generate(self, job_input):
        model = os.getenv("OLLAMA_CHAT_MODEL_NAME", os.getenv("OLLAMA_MODEL_NAME", "llama3.2:1b"))

        if isinstance(job_input.llm_input, str):
            from utils import JobInput
            delegate = JobInput({
                "openai_route": "/v1/completions",
                "openai_input": {
                    "model": model,
                    "prompt": job_input.llm_input,
                    "stream": job_input.stream,
                },
            })
        else:
            from utils import JobInput
            delegate = JobInput({
                "openai_route": "/v1/chat/completions",
                "openai_input": {
                    "model": model,
                    "messages": job_input.llm_input,
                    "stream": job_input.stream,
                },
            })

        engine = OllamaOpenAiEngine()
        async for batch in engine.generate(delegate):
            yield batch


class OllamaOpenAiEngine(OllamaEngine):
    async def generate(self, job_input):
        route = job_input.openai_route
        openai_input = job_input.openai_input or {}

        if route == "/v1/models":
            async for r in self._handle_models():
                yield r
        elif route in ("/v1/chat/completions", "/v1/completions"):
            async for r in self._handle_completion(openai_input, chat=route == "/v1/chat/completions"):
                yield r
        elif route == "/v1/embeddings":
            async for r in self._handle_embeddings(openai_input):
                yield r
        else:
            yield {"error": f"Unsupported route: {route}"}

    async def _handle_models(self):
        try:
            response = await client.models.list()
            yield {"object": "list", "data": [m.model_dump() for m in response.data]}
        except Exception as e:
            yield {"error": str(e)}

    async def _handle_completion(self, openai_input, chat=False):
        try:
            streaming = openai_input.get("stream", False)
            if chat:
                response = await client.chat.completions.create(**openai_input)
            else:
                response = await client.completions.create(**openai_input)

            if not streaming:
                yield response.model_dump()
                return

            async for chunk in response:
                yield "data: " + json.dumps(chunk.model_dump(), separators=(",", ":")) + "\n\n"
            yield "data: [DONE]"
        except Exception as e:
            if openai_input.get("stream", False):
                yield "data: " + json.dumps({"error": str(e)}, separators=(",", ":")) + "\n\n"
            else:
                yield {"error": str(e)}

    async def _handle_embeddings(self, openai_input):
        try:
            response = await client.embeddings.create(**openai_input)
            yield response.model_dump()
        except Exception as e:
            yield {"error": str(e)}
