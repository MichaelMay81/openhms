import asyncio
import logging
import signal
from aiohttp import web
import aiohttp_jinja2
import jinja2
import os

from .config import AppConfig
from .state import SharedState
from .mqtt import MQTTTask
from .inverter import InverterTask
from .web import setup_routes

# Internal cap on graceful shutdown so we exit under Python control even if
# BLE teardown hangs; systemd's TimeoutStopSec is a backstop above this.
SHUTDOWN_TIMEOUT = 15

def main():
    try:
        asyncio.run(run_main())
    except (KeyboardInterrupt, SystemExit):
        pass

async def run_main():
    # 1. Load Config
    config = AppConfig.load()

    # 2. Initialize State
    state = SharedState()
    await state.add_log("INFO", "OpenHMS Service starting...")

    # 3. Setup Web App
    app = web.Application()
    app["state"] = state
    app["config"] = config

    # Setup Jinja2
    template_path = os.path.join(os.path.dirname(__file__), "templates")
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(template_path))

    setup_routes(app)

    # 4. Prepare Background Tasks
    inverter_task = InverterTask(config, state)
    mqtt_task = MQTTTask(config, state)

    # Setup Shutdown Handling
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    # Run the web server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.web_port)
    await site.start()

    await state.add_log("INFO", f"Web UI available at http://localhost:{config.web_port}")

    # Start background tasks
    bg_tasks = [
        asyncio.create_task(inverter_task.run()),
        asyncio.create_task(mqtt_task.run())
    ]

    # Wait for stop signal
    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        pass

    await state.add_log("INFO", "Service shutting down gracefully...")

    # Flip the cooperative flags first (belt-and-suspenders: prevents a fresh
    # connection attempt from starting during teardown), then cancel the
    # tasks outright. Unlike the flags alone, cancellation interrupts an
    # in-progress sleep (including the up-to-300s reconnect backoff)
    # immediately, raising CancelledError at the current await point. That
    # propagates up through `async with HiFlow(...) as hf:` and triggers a
    # real BLE disconnect via its __aexit__, instead of leaving the
    # connection dangling until a SIGKILL cuts it off uncleanly.
    inverter_task.stop()
    mqtt_task.stop()
    for t in bg_tasks:
        t.cancel()

    # Bounded wait, not asyncio.wait_for(gather(...)): asyncio.wait does not
    # re-cancel its arguments on timeout, so a slow-but-in-progress clean
    # disconnect is never itself interrupted by this bound.
    _, pending = await asyncio.wait(bg_tasks, timeout=SHUTDOWN_TIMEOUT)
    if pending:
        await state.add_log(
            "WARNING",
            f"Background task(s) did not stop within {SHUTDOWN_TIMEOUT}s; proceeding to exit.",
        )

    await runner.cleanup()

if __name__ == "__main__":
    main()

