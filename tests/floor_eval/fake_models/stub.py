#!/usr/bin/env python3
"""Canned offline subprocess with observable calls and deterministic fault injection."""

import fcntl
import json
import os
import sys
import time
from pathlib import Path


def scenario(data, request):
    configured = data.get("facts", {}).get(
        request["fact_id"], data.get("default", "all_correct")
    )
    configured = (
        data["scenarios"][configured] if isinstance(configured, str) else configured
    )
    if "models" in configured:
        configured = configured["models"].get(
            request["model"], data["scenarios"]["all_correct"]
        )
    return data["scenarios"][configured] if isinstance(configured, str) else configured


def main() -> int:
    request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    data = json.loads(
        (Path(__file__).parent / "scenarios.json").read_text(encoding="utf-8")
    )
    spec = scenario(data, request)
    log = Path(request["log"])
    log.parent.mkdir(parents=True, exist_ok=True)
    key = {k: request[k] for k in ("kind", "fact_id", "model", "trial")}
    started = time.time()
    # A locked append makes repeated-call injection deterministic under concurrency.
    with log.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        previous = [json.loads(line) for line in handle if line.strip()]
        count = sum(all(row.get(k) == v for k, v in key.items()) for row in previous)
        handle.write(json.dumps({**key, "started": started, "pid": os.getpid()}) + "\n")
        handle.flush()
    injection = spec.get("inject")
    active = not spec.get("inject_kind") or spec["inject_kind"] == request["kind"]
    active = active and (
        not spec.get("inject_trial") or spec["inject_trial"] == request["trial"]
    )
    if active and injection == "timeout":
        print("fixture partial stdout", flush=True)
        print("fixture partial stderr", file=sys.stderr, flush=True)
        time.sleep(float(spec.get("seconds", 2)))
    time.sleep(float(spec.get("delay", 0)))
    if active and (
        injection == "failure" or injection == "failure_once" and count == 0
    ):
        print("fixture failure", file=sys.stderr)
        return 23
    if request["kind"] == "judge":
        if active and (
            injection == "malformed_judge"
            or injection == "malformed_judge_once"
            and count == 0
        ):
            print("not json")
            return 0
        if "judge_response" in spec:
            print(json.dumps(spec["judge_response"]))
            return 0
        correct = spec["correct"]
        contradictions = spec.get(
            "contradictions",
            [bool(spec.get("contradiction")) and not answer for answer in correct],
        )
        uncertain = spec.get(
            "uncertain",
            [
                not answer and not opposite
                for answer, opposite in zip(correct, contradictions)
            ],
        )
        print(
            spec.get("judge_prefix", "")
            + json.dumps(
                {
                    "correct": correct,
                    "reason": "fixture scoring",
                    "contradiction": any(contradictions),
                    "contradictions": contradictions,
                    "uncertain": uncertain,
                    "consistent_contradiction": spec.get(
                        "consistent_contradiction", sum(contradictions) >= 4
                    ),
                    "contradiction_claim": "fixture opposite claim"
                    if any(contradictions)
                    else "",
                    "certainty": spec.get("certainty", "certain"),
                }
            )
            + spec.get("judge_suffix", "")
        )
    else:
        correct = spec["correct"][request["trial"] - 1]
        if correct:
            print("Expected fact: " + request["expected"])
        elif (
            spec.get("contradiction")
            or spec.get("contradictions", [False] * 5)[request["trial"] - 1]
        ):
            print("This is confidently the opposite of the expected fact.")
        else:
            print("I am not sure about this fact.")
    # A separate completion log supports concurrency verification without rewriting call records.
    with log.with_name("fake-completions.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {**key, "started": started, "finished": time.time(), "pid": os.getpid()}
            )
            + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
