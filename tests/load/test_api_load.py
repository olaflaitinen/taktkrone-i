"""
Load Testing for TAKTKRONE-I API - Phase 5 Production.

Concurrent request testing, latency measurements, error tracking.
"""

import asyncio
import json
import statistics
import time
from typing import Dict, List, Optional, Tuple

import httpx
import pytest

__all__ = [
    "test_single_request",
    "test_concurrent_requests",
    "test_batch_endpoint",
    "test_cache_performance",
]


@pytest.fixture
async def api_client():
    """Create API client."""
    async with httpx.AsyncClient(
        base_url="https://taktkrone.ai",
        timeout=60.0,
    ) as client:
        yield client


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return "Service disruption on Line 1 - power issue reported"


@pytest.fixture
def sample_queries():
    """Multiple sample queries for batch testing."""
    return [
        "Service disruption on Line 1 - power issue reported",
        "How to handle passenger congestion during peak hours?",
        "What are the safety protocols for emergency situations?",
        "Analyze traffic pattern disruption in downtown area",
        "Signal failure on the main track - need immediate action",
    ]


class LoadTester:
    """Load testing utility."""

    def __init__(self):
        """Initialize load tester."""
        self.latencies: List[float] = []
        self.errors: List[str] = []
        self.success_count = 0
        self.total_requests = 0

    def record_latency(self, latency_ms: float) -> None:
        """Record latency measurement.

        Args:
            latency_ms: Latency in milliseconds
        """
        self.latencies.append(latency_ms)

    def record_error(self, error: str) -> None:
        """Record error.

        Args:
            error: Error message
        """
        self.errors.append(error)

    def record_success(self) -> None:
        """Record successful request."""
        self.success_count += 1

    def record_request(self) -> None:
        """Record total request."""
        self.total_requests += 1

    def get_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics.

        Returns:
            Dict with latency stats
        """
        if not self.latencies:
            return {}

        sorted_latencies = sorted(self.latencies)
        return {
            "count": len(self.latencies),
            "mean": statistics.mean(self.latencies),
            "median": statistics.median(self.latencies),
            "stdev": statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0,
            "min": min(self.latencies),
            "max": max(self.latencies),
            "p50": sorted_latencies[int(len(sorted_latencies) * 0.50)],
            "p95": sorted_latencies[int(len(sorted_latencies) * 0.95)],
            "p99": sorted_latencies[int(len(sorted_latencies) * 0.99)],
        }

    def get_error_rate(self) -> float:
        """Get error rate.

        Returns:
            Error rate (0.0-1.0)
        """
        if self.total_requests == 0:
            return 0.0
        return len(self.errors) / self.total_requests

    def get_report(self) -> Dict:
        """Get complete test report.

        Returns:
            Test report
        """
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.success_count,
            "failed_requests": len(self.errors),
            "error_rate": self.get_error_rate(),
            "latency_stats": self.get_latency_stats(),
            "errors": self.errors[:10],  # First 10 errors
        }


@pytest.mark.asyncio
async def test_single_request(api_client, sample_query):
    """Test single API request."""
    start_time = time.time()

    response = await api_client.post(
        "/v1/query",
        json={
            "query": sample_query,
            "operator": "generic",
            "max_tokens": 512,
            "temperature": 0.7,
        },
    )

    latency_ms = (time.time() - start_time) * 1000

    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()

    assert "request_id" in data
    assert "response" in data
    assert "latency_ms" in data
    assert latency_ms > 0


@pytest.mark.asyncio
async def test_health_check(api_client):
    """Test health check endpoint."""
    response = await api_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "model_version" in data


@pytest.mark.asyncio
async def test_model_info(api_client):
    """Test model info endpoint."""
    response = await api_client.get("/v1/model/info")
    assert response.status_code == 200

    data = response.json()
    assert "model_path" in data
    assert "model_version" in data
    assert "device" in data


@pytest.mark.asyncio
async def test_concurrent_requests(api_client, sample_query, num_concurrent: int = 10):
    """Test concurrent requests.

    Args:
        api_client: HTTP client
        sample_query: Query to test
        num_concurrent: Number of concurrent requests
    """
    tester = LoadTester()

    async def make_request():
        tester.record_request()
        start_time = time.time()

        try:
            response = await api_client.post(
                "/v1/query",
                json={
                    "query": sample_query,
                    "operator": "generic",
                    "max_tokens": 512,
                    "temperature": 0.7,
                },
            )

            latency_ms = (time.time() - start_time) * 1000
            tester.record_latency(latency_ms)

            if response.status_code == 200:
                tester.record_success()
            else:
                tester.record_error(f"Status {response.status_code}")

        except Exception as e:
            tester.record_error(str(e))

    # Run concurrent requests
    tasks = [make_request() for _ in range(num_concurrent)]
    await asyncio.gather(*tasks)

    report = tester.get_report()

    # Assertions
    assert report["successful_requests"] > 0
    assert report["error_rate"] < 0.1  # Less than 10% error rate
    assert report["latency_stats"]["p99"] < 30000  # P99 less than 30 seconds

    print(json.dumps(report, indent=2))


@pytest.mark.asyncio
async def test_batch_endpoint(api_client, sample_queries):
    """Test batch query endpoint."""
    tester = LoadTester()
    start_time = time.time()

    try:
        response = await api_client.post(
            "/v1/batch",
            json={
                "queries": [
                    {
                        "query": q,
                        "operator": "generic",
                        "max_tokens": 512,
                        "temperature": 0.7,
                    }
                    for q in sample_queries
                ]
            },
        )

        latency_ms = (time.time() - start_time) * 1000
        tester.record_latency(latency_ms)

        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()

        assert "results" in data
        assert len(data["results"]) == len(sample_queries)
        assert "total_latency_ms" in data
        assert "batch_id" in data

        tester.record_success()

    except Exception as e:
        tester.record_error(str(e))

    tester.record_request()
    report = tester.get_report()
    assert report["successful_requests"] == 1


@pytest.mark.asyncio
async def test_cache_performance(api_client, sample_query):
    """Test caching performance.

    Verify that cached queries are faster than uncached.
    """
    # First request (cache miss)
    start1 = time.time()
    response1 = await api_client.post(
        "/v1/query",
        json={
            "query": sample_query,
            "operator": "generic",
            "max_tokens": 512,
            "temperature": 0.7,
        },
    )
    latency1 = (time.time() - start1) * 1000

    assert response1.status_code == 200

    # Second request (cache hit - should be faster)
    start2 = time.time()
    response2 = await api_client.post(
        "/v1/query",
        json={
            "query": sample_query,
            "operator": "generic",
            "max_tokens": 512,
            "temperature": 0.7,
        },
    )
    latency2 = (time.time() - start2) * 1000

    assert response2.status_code == 200

    # Cache hit should be faster
    print(f"Cache miss: {latency1:.2f}ms")
    print(f"Cache hit: {latency2:.2f}ms")
    print(f"Speedup: {latency1 / latency2:.2f}x")

    # In general, cached should be faster
    # But we allow some variance due to system load
    assert latency2 < latency1 or latency2 < 100  # Either faster or very fast


@pytest.mark.asyncio
async def test_error_handling(api_client):
    """Test error handling."""
    # Empty query
    response = await api_client.post(
        "/v1/query",
        json={"query": "hi"},  # Too short
    )
    assert response.status_code == 400

    # Missing required field
    response = await api_client.post(
        "/v1/query",
        json={},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_load_test_scenario(api_client, sample_queries):
    """Run complete load test scenario.

    Tests various request patterns and measures performance.
    """
    tester = LoadTester()

    async def test_pattern():
        # Mix of single and batch requests
        for i in range(5):
            tester.record_request()
            start = time.time()

            try:
                if i % 2 == 0:
                    # Single request
                    response = await api_client.post(
                        "/v1/query",
                        json={
                            "query": sample_queries[i % len(sample_queries)],
                            "operator": "generic",
                            "max_tokens": 512,
                            "temperature": 0.7,
                        },
                    )
                else:
                    # Batch request
                    response = await api_client.post(
                        "/v1/batch",
                        json={
                            "queries": [
                                {
                                    "query": q,
                                    "operator": "generic",
                                    "max_tokens": 256,
                                    "temperature": 0.7,
                                }
                                for q in sample_queries[:2]
                            ]
                        },
                    )

                latency_ms = (time.time() - start) * 1000
                tester.record_latency(latency_ms)

                if response.status_code == 200:
                    tester.record_success()
                else:
                    tester.record_error(f"Status {response.status_code}")

            except Exception as e:
                tester.record_error(str(e))

    # Run 3 concurrent patterns
    await asyncio.gather(
        test_pattern(),
        test_pattern(),
        test_pattern(),
    )

    report = tester.get_report()
    print(json.dumps(report, indent=2))

    assert report["successful_requests"] > 0
    assert report["error_rate"] < 0.1


@pytest.mark.asyncio
async def test_cache_stats(api_client):
    """Test cache statistics endpoint."""
    response = await api_client.get("/v1/cache/stats")
    assert response.status_code == 200

    data = response.json()
    assert "size" in data
    assert "hits" in data
    assert "misses" in data


@pytest.mark.asyncio
async def test_audit_logs(api_client):
    """Test audit logs endpoint."""
    response = await api_client.get("/v1/audit/logs?last_n=10")
    assert response.status_code == 200

    data = response.json()
    assert "total" in data
    assert "logs" in data
    assert isinstance(data["logs"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
