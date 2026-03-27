"""
TAKTKRONE-I Gradio Demo - Phase 5 Production.

Interactive web interface for OCC inference with streaming, examples, export.
"""

import json
import logging
from datetime import datetime
from typing import Any

try:
    import gradio as gr
except ImportError:
    gr = None

import httpx

__all__ = [
    "create_demo",
    "main",
]

logger = logging.getLogger(__name__)


class OCCDemoClient:
    """Client for TAKTKRONE-I API."""

    def __init__(self, api_url: str = "https://taktkrone.ai"):
        """Initialize demo client.

        Args:
            api_url: Base URL for API
        """
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.query_history = []

    async def query(
        self,
        query: str,
        operator: str = "generic",
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """Send query to API.

        Args:
            query: Input query
            operator: Operator code
            max_tokens: Max tokens
            temperature: Temperature

        Returns:
            API response
        """
        try:
            response = await self.client.post(
                f"{self.api_url}/v1/query",
                json={
                    "query": query,
                    "operator": operator,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            result = response.json()

            # Store in history
            self.query_history.append({
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "operator": operator,
                "result": result,
            })

            return result
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "error": str(e),
                "request_id": "error",
                "response": {
                    "summary": f"Error: {str(e)}",
                    "error": str(e),
                },
                "latency_ms": 0,
                "model_version": "unknown",
            }

    async def get_model_info(self) -> dict[str, Any]:
        """Get model information.

        Returns:
            Model info
        """
        try:
            response = await self.client.get(f"{self.api_url}/v1/model/info")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {}

    async def get_operators(self) -> list[dict[str, str]]:
        """Get available operators.

        Returns:
            List of operators
        """
        try:
            response = await self.client.get(f"{self.api_url}/v1/operators")
            response.raise_for_status()
            data = response.json()
            return data.get("operators", [])
        except Exception as e:
            logger.error(f"Failed to get operators: {e}")
            return []


def create_demo(api_url: str = "https://taktkrone.ai") -> gr.Blocks | None:
    """Create Gradio demo interface.

    Args:
        api_url: Base URL for API

    Returns:
        Gradio Blocks instance
    """
    if gr is None:
        logger.error("Gradio not installed")
        return None

    client = OCCDemoClient(api_url=api_url)

    # Example queries
    examples = [
        "Service disruption on Line 1 - power issue reported",
        "How to handle passenger congestion during peak hours?",
        "What are the safety protocols for emergency situations?",
        "Analyze traffic pattern disruption in downtown area",
    ]

    with gr.Blocks(title="TAKTKRONE-I OCC Assistant") as demo:
        gr.Markdown("# TAKTKRONE-I - OCC Decision Support")
        gr.Markdown(
            "Metro Operations Control Center assistant for disruption analysis "
            "and decision support."
        )

        with gr.Row():
            with gr.Column(scale=2):
                # Query input section
                gr.Markdown("## Query")
                query_input = gr.Textbox(
                    label="Query",
                    placeholder="Describe the situation...",
                    lines=4,
                    info="Describe the operational situation or ask for assistance",
                )

                # Settings
                with gr.Row():
                    operator_dropdown = gr.Dropdown(
                        label="Operator",
                        choices=["generic", "mta_nyct", "mbta", "wmata", "bart", "tfl"],
                        value="generic",
                    )
                    max_tokens = gr.Slider(
                        label="Max Tokens",
                        minimum=128,
                        maximum=2048,
                        value=512,
                        step=128,
                    )
                    temperature = gr.Slider(
                        label="Temperature",
                        minimum=0.0,
                        maximum=2.0,
                        value=0.7,
                        step=0.1,
                    )

                # Examples dropdown
                gr.Markdown("## Examples")
                example_dropdown = gr.Dropdown(
                    label="Example Queries",
                    choices=examples,
                    value=examples[0],
                    interactive=True,
                )

                def load_example(example: str):
                    return example

                example_dropdown.change(
                    load_example,
                    inputs=[example_dropdown],
                    outputs=[query_input],
                )

            with gr.Column(scale=3):
                # Response output section
                gr.Markdown("## Response")
                summary_output = gr.Textbox(
                    label="Summary",
                    lines=4,
                    interactive=False,
                )
                confidence_output = gr.Number(
                    label="Confidence",
                    interactive=False,
                )
                review_output = gr.Checkbox(
                    label="Review Required",
                    interactive=False,
                )
                latency_output = gr.Number(
                    label="Latency (ms)",
                    interactive=False,
                )

        # Detailed results
        with gr.Accordion("Detailed Results", open=False):
            json_output = gr.Code(
                label="Full Response (JSON)",
                language="json",
                interactive=False,
            )

        # Export section
        with gr.Row():
            export_json = gr.Button("Export as JSON")
            export_csv = gr.Button("Export History as CSV")
            clear_history = gr.Button("Clear History")

        # Status
        status_output = gr.Textbox(
            label="Status",
            interactive=False,
            value="Ready",
        )

        # Processing function
        async def process_query(
            query: str,
            operator: str,
            max_tokens: int,
            temperature: float,
        ) -> tuple[str, float, bool, float, str, str]:
            """Process query and return results."""
            if not query.strip():
                return "", 0.0, False, 0.0, "Please enter a query", "{}"

            status = "Processing..."

            try:
                result = await client.query(
                    query=query,
                    operator=operator,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                if "error" in result:
                    return (
                        result.get("response", {}).get("summary", "Error"),
                        0.0,
                        False,
                        0.0,
                        f"Error: {result.get('error')}",
                        json.dumps(result, indent=2),
                    )

                response = result.get("response", {})
                summary = response.get("summary", "")
                confidence = response.get("confidence", 0.0)
                review_required = response.get("review_required", False)
                latency = result.get("latency_ms", 0.0)

                status = f"Complete - {latency:.2f}ms"

                return (
                    summary,
                    confidence,
                    review_required,
                    latency,
                    status,
                    json.dumps(result, indent=2),
                )
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                return "", 0.0, False, 0.0, error_msg, "{}"

        # Submit button
        submit_btn = gr.Button("Submit Query", variant="primary")

        submit_btn.click(
            process_query,
            inputs=[query_input, operator_dropdown, max_tokens, temperature],
            outputs=[
                summary_output,
                confidence_output,
                review_output,
                latency_output,
                status_output,
                json_output,
            ],
        )

        # Export functions
        def export_last_as_json():
            if client.query_history:
                return json.dumps(client.query_history[-1], indent=2)
            return "{}"

        def export_history_as_csv():
            if not client.query_history:
                return "No history"

            lines = ["timestamp,query,operator,confidence,review_required"]
            for entry in client.query_history:
                timestamp = entry.get("timestamp", "")
                query = entry.get("query", "").replace(",", ";")
                operator = entry.get("operator", "")
                confidence = entry.get("result", {}).get("response", {}).get("confidence", 0)
                review = entry.get("result", {}).get("response", {}).get("review_required", False)
                lines.append(f'"{timestamp}","{query}","{operator}",{confidence},{review}')

            return "\n".join(lines)

        export_json.click(
            export_last_as_json,
            outputs=[json_output],
        )

        export_csv.click(
            export_history_as_csv,
            outputs=[status_output],
        )

        clear_history.click(
            lambda: (client.query_history.clear(), "History cleared"),
            outputs=[status_output],
        )

    return demo


def main():
    """Run Gradio demo."""
    import argparse

    parser = argparse.ArgumentParser(description="Run TAKTKRONE-I Gradio demo")
    parser.add_argument(
        "--api-url",
        default="https://taktkrone.ai",
        help="API base URL",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to bind",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Share link",
    )

    args = parser.parse_args()

    demo = create_demo(api_url=args.api_url)
    if demo is None:
        logger.error("Failed to create demo")
        return

    demo.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
    )


if __name__ == "__main__":
    main()
