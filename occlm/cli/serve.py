"""
Serve CLI - Phase 5 Production.

Typer CLI for starting TAKTKRONE-I servers (API + Gradio demo).
"""

import logging
import os

import typer

__all__ = [
    "app",
]

logger = logging.getLogger(__name__)
app = typer.Typer(help="Serve TAKTKRONE-I API and demo")


@app.command()
def api(
    model_path: str = typer.Option(
        "metrolm/taktkrone-i-v0.1",
        "--model-path",
        "-m",
        help="Path to model or HF model ID",
    ),
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Host to bind API server",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port for API server",
    ),
    device: str = typer.Option(
        "cuda",
        "--device",
        "-d",
        help="Device (cuda/cpu)",
    ),
    precision: str = typer.Option(
        "fp16",
        "--precision",
        help="Model precision (fp16/bf16/fp32)",
    ),
    workers: int = typer.Option(
        1,
        "--workers",
        "-w",
        help="Number of workers",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        help="Auto-reload on changes",
    ),
    log_level: str = typer.Option(
        "info",
        "--log-level",
        help="Log level (debug/info/warning/error)",
    ),
    log_dir: str = typer.Option(
        "./logs",
        "--log-dir",
        help="Directory for audit logs",
    ),
):
    """Start TAKTKRONE-I API server.

    Example:
        occlm serve api --model-path metrolm/taktkrone-i-v0.1 --port 8000
    """
    logger.info("Starting TAKTKRONE-I API server")
    logger.info(f"Model: {model_path}")
    logger.info(f"Device: {device}, Precision: {precision}")
    logger.info(f"Binding to {host}:{port}")

    # Set environment variables
    os.environ["OCCLM_MODEL_PATH"] = model_path
    os.environ["OCCLM_DEVICE"] = device
    os.environ["OCCLM_PRECISION"] = precision
    os.environ["OCCLM_LOG_DIR"] = log_dir

    # Start API server
    try:
        import uvicorn
        uvicorn.run(
            "occlm.serving.api:app",
            host=host,
            port=port,
            workers=workers,
            reload=reload,
            log_level=log_level,
        )
    except KeyboardInterrupt:
        logger.info("API server stopped")


@app.command()
def demo(
    api_url: str = typer.Option(
        "https://taktkrone.ai",
        "--api-url",
        help="URL for API server",
    ),
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Host to bind demo server",
    ),
    port: int = typer.Option(
        7860,
        "--port",
        "-p",
        help="Port for demo server",
    ),
    share: bool = typer.Option(
        False,
        "--share",
        help="Create public share link",
    ),
):
    """Start Gradio demo server.

    Example:
        occlm serve demo --api-url https://taktkrone.ai --port 7860
    """
    logger.info("Starting TAKTKRONE-I Gradio demo")
    logger.info(f"API URL: {api_url}")
    logger.info(f"Binding to {host}:{port}")

    try:
        from occlm.ui.demo import main as demo_main
        demo_main()
    except KeyboardInterrupt:
        logger.info("Demo server stopped")


@app.command()
def all(
    model_path: str = typer.Option(
        "metrolm/taktkrone-i-v0.1",
        "--model-path",
        "-m",
        help="Path to model or HF model ID",
    ),
    api_host: str = typer.Option(
        "0.0.0.0",
        "--api-host",
        help="Host for API server",
    ),
    api_port: int = typer.Option(
        8000,
        "--api-port",
        help="Port for API server",
    ),
    demo_host: str = typer.Option(
        "0.0.0.0",
        "--demo-host",
        help="Host for demo server",
    ),
    demo_port: int = typer.Option(
        7860,
        "--demo-port",
        help="Port for demo server",
    ),
    device: str = typer.Option(
        "cuda",
        "--device",
        "-d",
        help="Device (cuda/cpu)",
    ),
    workers: int = typer.Option(
        1,
        "--workers",
        "-w",
        help="Number of API workers",
    ),
    log_level: str = typer.Option(
        "info",
        "--log-level",
        help="Log level",
    ),
):
    """Start both API and demo servers.

    Starts API on api_port and demo on demo_port.
    Both run concurrently.

    Example:
        occlm serve all --model-path metrolm/taktkrone-i-v0.1
    """
    import threading
    import time

    logger.info("Starting TAKTKRONE-I API and Demo servers")
    logger.info(f"API: {api_host}:{api_port}")
    logger.info(f"Demo: {demo_host}:{demo_port}")

    # Set environment variables
    os.environ["OCCLM_MODEL_PATH"] = model_path
    os.environ["OCCLM_DEVICE"] = device

    # Start API in background thread
    api_url = f"http://localhost:{api_port}"

    def start_api():
        try:
            import uvicorn
            uvicorn.run(
                "occlm.serving.api:app",
                host=api_host,
                port=api_port,
                workers=workers,
                log_level=log_level,
            )
        except Exception as e:
            logger.error(f"API server failed: {e}")

    api_thread = threading.Thread(target=start_api, daemon=False)
    api_thread.start()

    # Wait for API to start
    logger.info("Waiting for API server to start...")
    time.sleep(3)

    # Start demo
    try:
        from occlm.ui.demo import create_demo
        demo = create_demo(api_url=api_url)
        if demo:
            demo.launch(
                server_name=demo_host,
                server_port=demo_port,
                share=False,
            )
    except Exception as e:
        logger.error(f"Demo server failed: {e}")


@app.command()
def health(
    api_url: str = typer.Option(
        "https://taktkrone.ai",
        "--api-url",
        help="API URL to check",
    ),
):
    """Check health of API server.

    Example:
        occlm serve health --api-url https://taktkrone.ai
    """
    try:
        import httpx
        response = httpx.get(f"{api_url}/health", timeout=5.0)
        response.raise_for_status()
        data = response.json()
        typer.echo(f"Status: {data.get('status', 'unknown')}")
        typer.echo(f"Model: {data.get('model_version', 'unknown')}")
        typer.echo(f"Model Loaded: {data.get('model_loaded', False)}")
    except Exception as e:
        typer.echo(f"Health check failed: {e}", err=True)
        raise typer.Exit(1)


def main():
    """Run CLI."""
    app()


if __name__ == "__main__":
    main()
