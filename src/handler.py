import os
import runpod
from utils import JobInput
from engine import OllamaEngine, OllamaOpenAiEngine

_MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "8"))


async def handler(job):
    print("Job:", job)
    job_input = JobInput(job["input"])
    engine_class = OllamaOpenAiEngine if job_input.openai_route else OllamaEngine
    engine = engine_class()
    async for batch in engine.generate(job_input):
        yield batch


runpod.serverless.start(
    {
        "handler": handler,
        "concurrency_modifier": lambda x: _MAX_CONCURRENCY,
        "return_aggregate_stream": True,
    }
)
