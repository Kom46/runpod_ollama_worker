import os
import sys
import traceback

print("handler.py: starting imports...", flush=True)
try:
    import runpod
    print(f"handler.py: runpod {runpod.__version__}", flush=True)
except Exception as e:
    print(f"handler.py: FAILED to import runpod: {e}", flush=True)
    sys.exit(1)

try:
    from utils import JobInput
    from engine import OllamaEngine, OllamaOpenAiEngine
    print("handler.py: engine imports OK", flush=True)
except Exception as e:
    print(f"handler.py: FAILED to import engine/utils: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

_MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "8"))


async def handler(job):
    print("Job:", job)
    job_input = JobInput(job["input"])
    engine_class = OllamaOpenAiEngine if job_input.openai_route else OllamaEngine
    engine = engine_class()
    async for batch in engine.generate(job_input):
        yield batch


print("handler.py: calling runpod.serverless.start()", flush=True)
try:
    runpod.serverless.start(
        {
            "handler": handler,
            "concurrency_modifier": lambda x: _MAX_CONCURRENCY,
            "return_aggregate_stream": True,
        }
    )
except Exception as e:
    print(f"handler.py: FAILED in serverless.start: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)
