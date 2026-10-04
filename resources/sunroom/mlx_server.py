"""Private, app-owned MLX worker. Local model files only; no code execution tools.

The native app starts this on demand. A random loopback port and a per-launch
token prevent accidental cross-talk with another app. One inference at a time
keeps memory bounded on the 16 GB target Mac. No cloud fallback.
"""
from __future__ import annotations
import argparse
import ctypes
import hmac
import json
import math
import os
from pathlib import Path
import secrets
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def process_exists(pid: int) -> bool:
    """True when pid is still running.

    POSIX signal 0 only probes. On Windows, os.kill(pid, 0) calls
    TerminateProcess, so a parent-liveness check must not use it.
    """
    if pid <= 0:
        return False
    if os.name == "nt":
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        process_query_limited_information = 0x1000
        still_active = 259
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            # ERROR_ACCESS_DENIED: the process exists, but this token cannot open it.
            return ctypes.get_last_error() == 5
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def publish_private(path: Path, text: str) -> None:
    """Write text so other users cannot read it. Unix mode 0600, Windows ACL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    if os.name == "nt":
        user = os.environ.get("USERNAME")
        if user:
            # Lock the temp file before it is published under the final name.
            subprocess.run(
                ["icacls", str(temporary), "/inheritance:r", "/grant:r", f"{user}:(R,W)"],
                check=False,
                capture_output=True,
            )
        os.replace(temporary, path)
        return
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--ready-file", type=Path, required=True)
    parser.add_argument("--parent-pid", type=int, default=0)
    args = parser.parse_args()
    if not (args.model / "config.json").is_file():
        raise SystemExit("Local MLX model is missing. Run scripts/setup_sunroom_ai.py first.")
    token = secrets.token_urlsafe(32)
    lock = threading.Lock()
    state = {"model": None, "tokenizer": None, "used": time.monotonic()}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *unused):
            pass  # Prompts and replies never go into HTTP access logs.

        def send_json(self, status, value):
            encoded = json.dumps(value, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self):
            if self.path == "/health":
                self.send_json(200, {"ready": True, "loaded": state["model"] is not None})
            else:
                self.send_json(404, {"error": "Unknown endpoint"})

        def do_POST(self):
            if self.path != "/v1/chat/completions":
                return self.send_json(404, {"error": "Unknown endpoint"})
            if not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + token):
                return self.send_json(401, {"error": "Unauthorized"})
            if self.headers.get("Origin"):
                return self.send_json(403, {"error": "Browser origins are not accepted"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 65536:
                    return self.send_json(413, {"error": "Request too large"})
                self.connection.settimeout(120)
                data = json.loads(self.rfile.read(size))
                messages = data.get("messages", [])
                if not messages or len(messages) > 24 or any(
                    not isinstance(m, dict) or m.get("role") not in ("system", "user", "assistant")
                    or not isinstance(m.get("content"), str) for m in messages
                ):
                    return self.send_json(400, {"error": "Invalid messages"})
                temperature = data.get("temperature", 0.5)
                if not isinstance(temperature, (int, float)) or not math.isfinite(temperature) or not 0 <= temperature <= 1:
                    return self.send_json(400, {"error": "Temperature must be a number between 0 and 1"})
                if data.get("tools"):
                    return self.send_json(400, {"error": "Use SUNROOM's validated actions"})
                if not lock.acquire(blocking=False):
                    return self.send_json(409, {"error": "The local assistant is busy"})
                try:
                    import mlx.core as mx
                    from mlx_lm import load, stream_generate
                    from mlx_lm.sample_utils import make_sampler
                    mx.set_cache_limit(256 * 1024 * 1024)
                    started = time.monotonic()
                    if state["model"] is None:
                        state["model"], state["tokenizer"] = load(str(args.model),
                            tokenizer_config={"trust_remote_code": False})
                    tokenizer = state["tokenizer"]
                    prompt = tokenizer.apply_chat_template(messages, tokenize=False,
                        add_generation_prompt=True, enable_thinking=False)
                    if len(tokenizer.encode(prompt)) > 7000:
                        return self.send_json(400, {"error": "Conversation is too long. Start a fresh question."})
                    chunks = []
                    last = None
                    timed_out = False
                    for response in stream_generate(state["model"], tokenizer, prompt,
                            max_tokens=min(1024, max(32, int(data.get("max_tokens", 512)))),
                            sampler=make_sampler(temp=temperature, top_p=0.9), prefill_step_size=256):
                        chunks.append(response.text)
                        last = response
                        if time.monotonic() - started > 100:
                            timed_out = True
                            break
                    state["used"] = time.monotonic()
                    if timed_out or getattr(last, "finish_reason", None) == "length":
                        return self.send_json(422, {"error": "The local model ran out of time or space before finishing. Try one shorter request. No partial actions were applied."})
                    self.send_json(200, {
                        "choices": [{"message": {"role": "assistant", "content": "".join(chunks)}}],
                        "model": "SUNROOM / Qwen3.5-4B / MLX 4-bit",
                        "sunroom_metrics": {"seconds": round(time.monotonic() - started, 3),
                            "tokens_per_second": getattr(last, "generation_tps", 0),
                            "peak_memory_gb": getattr(last, "peak_memory", 0)},
                    })
                finally:
                    lock.release()
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as error:
                self.send_json(500, {"error": str(error)[:400]})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    ready = {"port": server.server_address[1], "token": token, "pid": os.getpid()}
    # Publish atomically so consumers never read a truncated ready file.
    publish_private(args.ready_file, json.dumps(ready))

    def maintenance():
        while True:
            time.sleep(5)
            if args.parent_pid and not process_exists(args.parent_pid):
                os._exit(0)
            if time.monotonic() - state["used"] > 180 and lock.acquire(blocking=False):
                try:
                    if state["model"] is not None:
                        state["model"] = state["tokenizer"] = None
                        import gc
                        import mlx.core as mx
                        gc.collect()
                        mx.clear_cache()
                finally:
                    lock.release()
    threading.Thread(target=maintenance, daemon=True).start()
    try:
        server.serve_forever()
    finally:
        args.ready_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
