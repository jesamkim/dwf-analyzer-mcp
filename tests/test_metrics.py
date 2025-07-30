"""
Tests for metrics collection and observability features.
"""

import pytest
import time
from datetime import datetime, timedelta
from dwf_analyzer_mcp.utils.metrics import MetricsCollector, track_tool_usage


class TestMetricsCollector:
    """Test cases for MetricsCollector."""
    
    def test_record_tool_usage_success(self):
        """Test recording successful tool usage."""
        collector = MetricsCollector()
        
        collector.record_tool_usage(
            tool_name="test_tool",
            duration_ms=100.5,
            success=True,
            file_size_bytes=1024,
            file_type=".dwf"
        )
        
        stats = collector.get_tool_usage_stats()
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 1
        assert stats["failed_requests"] == 0
        assert "test_tool" in stats["tools"]
        assert stats["tools"]["test_tool"]["total_calls"] == 1
        assert stats["tools"]["test_tool"]["successful_calls"] == 1
    
    def test_record_tool_usage_failure(self):
        """Test recording failed tool usage."""
        collector = MetricsCollector()
        
        collector.record_tool_usage(
            tool_name="test_tool",
            duration_ms=50.0,
            success=False,
            error_type="FileNotFoundError",
            error_message="File not found"
        )
        
        stats = collector.get_tool_usage_stats()
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 0
        assert stats["failed_requests"] == 1
        
        error_stats = collector.get_error_statistics()
        assert "FileNotFoundError" in error_stats["errors"]
        assert error_stats["errors"]["FileNotFoundError"]["count"] == 1
    
    def test_performance_metrics(self):
        """Test performance metrics calculation."""
        collector = MetricsCollector()
        
        # Record multiple tool usages with different durations
        durations = [100, 200, 150, 300, 250]
        for duration in durations:
            collector.record_tool_usage(
                tool_name="test_tool",
                duration_ms=duration,
                success=True
            )
        
        perf_metrics = collector.get_performance_metrics()
        assert perf_metrics["response_times"]["avg_ms"] == 200.0
        assert perf_metrics["response_times"]["min_ms"] == 100
        assert perf_metrics["response_times"]["max_ms"] == 300
    
    def test_track_tool_usage_decorator(self):
        """Test the track_tool_usage decorator."""
        collector = MetricsCollector()
        
        @track_tool_usage("decorated_tool")
        def sample_function(value: int) -> dict:
            time.sleep(0.01)  # Simulate some work
            if value < 0:
                return {"error": True, "message": "Negative value"}
            return {"success": True, "result": value * 2}
        
        # Test successful execution
        result = sample_function(5)
        assert result["success"] is True
        assert result["result"] == 10
        
        # Test failed execution
        result = sample_function(-1)
        assert result["error"] is True
        
        # Check metrics were recorded
        stats = collector.get_tool_usage_stats()
        assert stats["total_requests"] == 2
        assert stats["successful_requests"] == 1
        assert stats["failed_requests"] == 1
    
    def test_export_metrics(self):
        """Test metrics export functionality."""
        collector = MetricsCollector()
        
        collector.record_tool_usage(
            tool_name="export_test",
            duration_ms=123.45,
            success=True
        )
        
        exported_data = collector.export_metrics()
        assert "export_timestamp" in exported_data
        assert "tool_usage_stats" in exported_data
        assert "error_statistics" in exported_data
        assert "performance_metrics" in exported_data


class TestObservabilityIntegration:
    """Test cases for observability integration."""
    
    def test_metrics_collection_thread_safety(self):
        """Test that metrics collection is thread-safe."""
        import threading
        
        collector = MetricsCollector()
        
        def record_metrics():
            for i in range(10):
                collector.record_tool_usage(
                    tool_name=f"thread_tool_{threading.current_thread().ident}",
                    duration_ms=i * 10,
                    success=True
                )
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=record_metrics)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        stats = collector.get_tool_usage_stats()
        assert stats["total_requests"] == 50  # 5 threads * 10 records each
    
    def test_time_based_filtering(self):
        """Test time-based filtering of metrics."""
        collector = MetricsCollector()
        
        # Record old metric (simulate by manually setting timestamp)
        old_metric = collector.record_tool_usage(
            tool_name="old_tool",
            duration_ms=100,
            success=True
        )
        
        # Manually adjust timestamp to be older than 1 hour
        if collector.metrics:
            collector.metrics[-1].timestamp = datetime.now() - timedelta(hours=2)
        
        # Record recent metric
        collector.record_tool_usage(
            tool_name="recent_tool",
            duration_ms=200,
            success=True
        )
        
        # Get stats for last 1 hour
        recent_stats = collector.get_tool_usage_stats(hours=1)
        assert recent_stats["total_requests"] == 1  # Only recent metric
        
        # Get stats for last 3 hours
        all_stats = collector.get_tool_usage_stats(hours=3)
        assert all_stats["total_requests"] == 2  # Both metrics


if __name__ == "__main__":
    pytest.main([__file__])
