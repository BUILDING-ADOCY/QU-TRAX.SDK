#!/usr/bin/env python3
"""
Q-TRAX traffic generator (HTTP-poll only).
Enqueues random scenarios at a fixed rate, polls results, and optionally
appends each finished job to a JSONL file.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os # type: ignore
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp # type: ignore
from aiohttp import ClientTimeout, ClientSession, ClientResponse # type: ignore

# ───────────────────────────────────────── helpers ──────────────────────────


def init_logging(log_path: str) -> None:
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
    )


def build_payload(num_nodes: int = 5, max_weight: float = 30.0) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = [{"id": i, "attributes": {}} for i in range(1, num_nodes + 1)]
    edges: List[Dict[str, Any]] = [
        {
            "source": i,
            "target": j,
            "weight": round(random.uniform(5.0, max_weight), 1),
        }
        for i in range(1, num_nodes + 1)
        for j in range(1, num_nodes + 1)
        if i != j
    ]
    starts = random.sample(range(1, num_nodes + 1), 2)
    remaining = [n for n in range(1, num_nodes + 1) if n not in starts]
    goals = random.sample(remaining, 2) if len(remaining) >= 2 else remaining * 2
    agents = [ # type: ignore
        {"id": f"A{random.randint(1, 1000)}", "start": starts[0], "goal": goals[0]},
        {"id": f"A{random.randint(1001, 2000)}", "start": starts[1], "goal": goals[1]},
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "constraints": {},
        "agents": agents,
        "events": [],
        "solver_params": {
            "max_tick": 20,
            "mini_iter": 50,
            "start_temp": 50.0,
            "cooling_rate": 0.95,
            "min_temp": 0.01,
            "quantum_jump_prob": 0.1,
        },
    }


# ─────────────────────────────────── HTTP helpers ───────────────────────────


async def poll_http_result(
    session: ClientSession, # type: ignore
    api_url: str,
    job_id: str,
    max_attempts: int,
    base_delay: float,
) -> Optional[Dict[str, Any]]:
    """Poll /job/{job_id}/result until finished or max_attempts exhausted."""
    for attempt in range(1, max_attempts + 1):
        try:
            async with session.get(f"{api_url}/job/{job_id}/result") as resp: # type: ignore
                if resp.status == 200: # type: ignore
                    return await resp.json() # type: ignore

                if resp.status == 202: # type: ignore
                    delay = base_delay * (2 ** (attempt - 1))
                    logging.info("Job %s not ready; retrying in %.1fs", job_id, delay)
                    await asyncio.sleep(delay)
                    continue

                txt = await resp.text() # type: ignore
                logging.error("Unexpected %s for job %s: %s", resp.status, job_id, txt) # type: ignore
                return None
        except Exception:
            logging.exception("Polling error for job %s", job_id)
            await asyncio.sleep(base_delay)

    logging.error("🚨 Gave up on job %s after %d attempts", job_id, max_attempts)
    return None


async def send_random_scenario(
    session: ClientSession, # type: ignore
    api_url: str,
    http_retries: int,
    http_base_delay: float,
    save_path: Optional[str],
) -> None:
    """Enqueue one random scenario and wait for its result."""
    payload = build_payload()

    # enqueue
    try:
        async with session.post(f"{api_url}/enqueue_dynamic", json=payload) as resp: # type: ignore
            resp.raise_for_status() # type: ignore
            data: Dict[str, Any] = await resp.json() # type: ignore
            job_id = data.get("job_id") # type: ignore
            if not job_id:
                logging.error("No job_id in response: %s", data) # type: ignore
                return
    except Exception:
        logging.exception("Failed to enqueue scenario")
        return

    # poll
    result = await poll_http_result(session, api_url, job_id, http_retries, http_base_delay) # type: ignore
    logging.info("[HTTP] Job %s => %s", job_id, result.get("routes") if result else None) # type: ignore

    # optional JSONL dump
    if result and save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "a") as fh:
            fh.write(json.dumps({"job_id": job_id, "result": result}) + "\n")


async def generate_traffic(
    rate_per_sec: int,
    api_url: str,
    http_retries: int,
    http_base_delay: float,
    save_path: Optional[str],
) -> None:
    timeout = ClientTimeout(connect=5, total=30) # type: ignore
    async with aiohttp.ClientSession(timeout=timeout) as session: # type: ignore
        while True:
            tasks = [
                asyncio.create_task(
                    send_random_scenario(session, api_url, http_retries, http_base_delay, save_path) # type: ignore
                )
                for _ in range(rate_per_sec)
            ]
            await asyncio.gather(*tasks)
            await asyncio.sleep(2)  # brief stagger before next burst


# ────────────────────────────────── CLI / main ──────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Q-TRAX Traffic Generator")
    parser.add_argument("--rate", type=int, default=5, help="Requests per second")
    parser.add_argument("--api", default="http://127.0.0.1:8000", help="Base API URL")
    parser.add_argument("--http-retries", type=int, default=8, help="Max poll attempts")
    parser.add_argument("--http-delay", type=float, default=1.0, help="Base back-off delay (s)")
    parser.add_argument("--log", default="logs/traffic_results.log", help="Log file path")
    parser.add_argument("--save", default=None, help="Optional JSONL results path")
    args = parser.parse_args()

    init_logging(args.log)
    logging.info("Starting Q-TRAX traffic generator")

    try:
        asyncio.run(
            generate_traffic(
                args.rate,
                args.api.rstrip("/"),
                args.http_retries,
                args.http_delay,
                args.save,
            )
        )
    except KeyboardInterrupt:
        logging.info("Traffic generator stopped by user")


if __name__ == "__main__":
    main()