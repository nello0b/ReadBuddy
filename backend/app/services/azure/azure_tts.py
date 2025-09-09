import os
import uuid
import time
import asyncio
import aiohttp
import aiofiles
from typing import List
from xml.etree.ElementTree import Element, tostring
from config import AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, DEBUG_MODE
from app.services.tts_interface import TTSService

import logging
logger = logging.getLogger(__name__)

MAX_CONCURRENT_JOBS = 5  # Tune based on system/API limits
RETRY_LIMIT = 3  # Max number of retries for a failed job

class AzureTTSService(TTSService):
    def __init__(self):
        self.api_version = "2024-04-01"
        self.base_url = (
            f"https://{AZURE_SPEECH_REGION}.api.cognitive.microsoft.com/texttospeech/batchsyntheses"
        )
        self.headers = {
            "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
            "Content-Type": "application/json",
        }
        # Remove the semaphore initialization from __init__
        self._semaphore = None
    
    @property
    def semaphore(self):
        """Lazily create semaphore in the current event loop."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)
        return self._semaphore

    async def _submit_job(
        self,
        ssml_string: str,
        voice: str,
        image_id: str,
        index: int,
        attempt: int = 0,
    ) -> str:
        job_id = f"job-{image_id}-{index}-{attempt}"
        url = f"{self.base_url}/{job_id}?api-version={self.api_version}"

        payload = {
            "description": f"TTS job for {job_id}",
            "inputKind": "SSML",
            "synthesisConfig": {"voice": voice},
            "inputs": [{"content": ssml_string}],
            "properties": {
                "outputFormat": "audio-16khz-32kbitrate-mono-mp3",
                "wordBoundaryEnabled": True,
                "sentenceBoundaryEnabled": True,
                "concatenateResult": False
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=self.headers, json=payload) as resp:
                resp.raise_for_status()

        return job_id

    async def _poll_and_download(self, job_id: str) -> str:
        status_url = f"{self.base_url}/{job_id}?api-version={self.api_version}"
        print(f"⏳ Polling job {job_id}...")

        result_url = await poll_status_async(status_url, self.headers, job_id)
        result_zip_path = f"static/audio/{job_id}.zip"
        os.makedirs(os.path.dirname(result_zip_path), exist_ok=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(result_url) as resp:
                resp.raise_for_status()
                content = await resp.read()

            async with aiofiles.open(result_zip_path, "wb") as f:
                await f.write(content)

        print(f"✅ Downloaded {result_zip_path}")
        return result_zip_path

    async def synthesize_multi(self, ssml_chunks: List[Element], voice: str = "en-US-AriaNeural") -> List[str]:
        print(f"🚀 Launching TTS jobs for {len(ssml_chunks)} paragraphs...")
        image_id = f"i-{uuid.uuid4().hex[:12]}"
        
        # Reset semaphore for each new synthesize_multi call to ensure it's in the correct event loop
        self._semaphore = None

        async def submit_and_poll_with_retries(chunk, i):
            async with self.semaphore:
                ssml_string = tostring(chunk, encoding="unicode", method="xml")
                # Validate SSML
                if not ssml_string.strip() or "<voice" not in ssml_string:
                    print(f"⚠️ Chunk {i} has invalid SSML: {ssml_string}")
                    return None  # Skip empty/invalid chunks
                attempts = 0
                while attempts < RETRY_LIMIT:
                    try:
                        if DEBUG_MODE:
                            t0 = time.time()
                        job_id = await self._submit_job(ssml_string, voice, image_id, i, attempts)
                        if DEBUG_MODE:
                            t1 = time.time()
                            print(f"⏱️ Chunk {i}: Job submission took {t1 - t0:.2f} seconds")
                        result_path = await self._poll_and_download(job_id)
                        if DEBUG_MODE:
                            t2 = time.time()
                            print(f"⏱️ Chunk {i}: Poll & download took {t2 - t1:.2f} seconds")
                        return result_path
                    except Exception as e:
                        # Check if this is an EmptyInput error - don't retry these
                        if "EmptyInput" in str(e) or "synthesized audio is empty" in str(e):
                            print(f"🚫 Chunk {i}: Skipping empty/invalid content - {e}")
                            return f"static/audio/job-{image_id}-{i}-Error"  # Return None for empty content instead of raising
                        
                        attempts += 1
                        print(f"⚠️ Retry {attempts}/{RETRY_LIMIT} for chunk {i} due to error: {e}")
                        await asyncio.sleep(min(2 ** attempts, 10))
                        if attempts >= RETRY_LIMIT:
                            raise

        tasks = [submit_and_poll_with_retries(chunk, i) for i, chunk in enumerate(ssml_chunks)]
        zip_paths = await asyncio.gather(*tasks)  # Exceptions propagate explicitly

        if DEBUG_MODE:
            start_sort_time = time.time()
        
        zip_paths.sort()
        
        zip_paths = [(path if not path.endswith("Error") else None) for path in zip_paths] 

        if DEBUG_MODE:
            print(f"⏰ Sorting completed in {time.time() - start_sort_time:.2f} seconds")

        return zip_paths


async def poll_status_async(status_url, headers, job_id, timeout=300, max_retries=20):
    wait_time = 0.5
    max_wait = 3
    retries = 0
    start = asyncio.get_event_loop().time()

    async with aiohttp.ClientSession() as session:
        while retries < max_retries:
            elapsed = asyncio.get_event_loop().time() - start
            if elapsed > timeout:
                raise TimeoutError(f"Job {job_id} polling timed out after {timeout} seconds")

            async with session.get(status_url, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                status = data.get("status")

                if status == "Succeeded":
                    return data["outputs"]["result"]
                elif status == "Failed":
                    raise RuntimeError(f"Job {job_id} failed: {data}")

            print(f"🌙 Job {job_id} sleeps...")
            await asyncio.sleep(wait_time)
            wait_time = min(wait_time * 2, max_wait)
            retries += 1

        raise TimeoutError(f"Job {job_id} polling exceeded retry limit ({max_retries})")
