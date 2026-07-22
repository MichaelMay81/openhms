import datetime
import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
from .state import SharedState
from .config import AppConfig

async def get_dashboard_context(request):
    state: SharedState = request.app["state"]
    last_update_str = "Never"
    if state.metrics.last_update > 0:
        last_update_str = datetime.datetime.fromtimestamp(state.metrics.last_update).strftime("%H:%M:%S")
    return {
        "metrics": state.metrics,
        "inverter_info": state.inverter_info,
        "last_update_str": last_update_str
    }

async def get_logs_context(request):
    state: SharedState = request.app["state"]
    logs_data = []
    for log in state.logs:
        logs_data.append({
            "time_str": datetime.datetime.fromtimestamp(log.timestamp).strftime("%H:%M:%S"),
            "level": log.level,
            "message": log.message
        })
    return {"logs": logs_data}

async def handle_dashboard(request):
    context = await get_dashboard_context(request)
    if "HX-Request" in request.headers:
        return aiohttp_jinja2.render_template("dashboard.html", request, context)
    return aiohttp_jinja2.render_template("base.html", request, {"page": "dashboard", **context})

async def handle_logs(request):
    context = await get_logs_context(request)
    if "HX-Request" in request.headers:
        return aiohttp_jinja2.render_template("logs.html", request, context)
    return aiohttp_jinja2.render_template("base.html", request, {"page": "logs", **context})

async def handle_settings(request):
    config = request.app["config"]
    if "HX-Request" in request.headers:
        return aiohttp_jinja2.render_template("settings.html", request, {"config": config})
    return aiohttp_jinja2.render_template("base.html", request, {"page": "settings", "config": config})

async def api_settings_post(request):
    data = await request.post()
    config = request.app["config"]
    state = request.app["state"]
    
    try:
        # Update config object
        config.ble_address = data.get("ble_address", config.ble_address)
        config.inverter_sn = data.get("inverter_sn", config.inverter_sn)
        config.inverter_pin = data.get("inverter_pin", config.inverter_pin)
        config.scan_interval = int(data.get("scan_interval", config.scan_interval))
        config.mqtt_enabled = data.get("mqtt_enabled") == "on"
        config.mqtt_broker = data.get("mqtt_broker", config.mqtt_broker)
        config.mqtt_port = int(data.get("mqtt_port", config.mqtt_port))
        config.mqtt_client_id = data.get("mqtt_client_id", config.mqtt_client_id)
        config.mqtt_prefix = data.get("mqtt_prefix", config.mqtt_prefix)
        config.mqtt_username = data.get("mqtt_username") or None
        config.mqtt_password = data.get("mqtt_password") or None
        
        # Save to disk
        config.save()
        await state.add_log("INFO", "Configuration updated and saved to disk.")
        
        return web.Response(text="<span style='color: var(--accent-green);'>Configuration saved! Restart service to apply.</span>", content_type='text/html')
    except Exception as e:
        return web.Response(text=f"<span style='color: var(--error-color);'>Error: {str(e)}</span>", content_type='text/html')

async def api_restart(request):
    state = request.app["state"]
    await state.add_log("WARNING", "Restart requested via Web UI...")
    
    # In a proper systemd setup, we just exit and let systemd restart us.
    # To support manual runs, we'll schedule a graceful exit.
    async def do_graceful_exit():
        await asyncio.sleep(1)
        import os
        import signal
        # Send SIGTERM to ourselves to trigger the graceful shutdown logic in main.py
        os.kill(os.getpid(), signal.SIGTERM)

    asyncio.create_task(do_graceful_exit())
    return web.Response(text="<span style='color: var(--accent-blue);'>Graceful restart initiated... check logs/status in a few seconds.</span>", content_type='text/html')

from .health import get_system_health

async def handle_health(request):
    health = get_system_health()
    if "HX-Request" in request.headers:
        return aiohttp_jinja2.render_template("health.html", request, {"health": health})
    return aiohttp_jinja2.render_template("base.html", request, {"page": "health", "health": health})

# ... update setup_routes ...
async def handle_info(request):
    state = request.app["state"]
    if "HX-Request" in request.headers:
        return aiohttp_jinja2.render_template("info.html", request, {"info": state.inverter_info})
    return aiohttp_jinja2.render_template("base.html", request, {"page": "info", "info": state.inverter_info})

async def handle_opendtu_status(request):
    state: SharedState = request.app["state"]
    config: AppConfig = request.app["config"]

    yield_day_wh = int(state.metrics.daily_energy * 1000)
    is_connected = state.metrics.is_connected

    # Use live limit values if available, otherwise fall back to rated defaults
    limit_relative = round(state.metrics.power_limit_pct, 1) if state.metrics.power_limit_pct is not None else 100
    limit_absolute = round(state.metrics.power_limit_w, 0) if state.metrics.power_limit_w is not None else 800

    payload = {
        "inverters": [
            {
                "serial": config.inverter_sn or "unknown",
                "name": state.inverter_info.hardware_model,
                "reachable": is_connected,
                "producing": is_connected and state.metrics.active_power > 0,
                "limit_relative": limit_relative,
                "limit_absolute": limit_absolute,
            }
        ],
        "total": {
            "Power": {"v": round(state.metrics.active_power, 1), "u": "W", "d": 1},
            "YieldDay": {"v": yield_day_wh, "u": "Wh", "d": 0},
            "YieldTotal": {"v": round(state.metrics.total_energy, 3), "u": "kWh", "d": 3},
        }
    }
    return web.json_response(payload)

def setup_routes(app: web.Application):
    app.router.add_get("/", handle_dashboard)
    app.router.add_get("/logs", handle_logs)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/info", handle_info)
    app.router.add_get("/settings", handle_settings)
    
    # API endpoints
    app.router.add_get("/api/dashboard", handle_dashboard)
    app.router.add_get("/api/logs_page", handle_logs)
    app.router.add_get("/api/health", handle_health)
    app.router.add_get("/api/info", handle_info)
    app.router.add_get("/api/settings", handle_settings)
    app.router.add_post("/api/settings", api_settings_post)
    app.router.add_post("/api/restart", api_restart)
    app.router.add_get("/api/livedata/status", handle_opendtu_status)
