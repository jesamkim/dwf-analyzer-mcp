"""
Metrics collection and observability utilities for DWF Analyzer MCP Server.
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from threading import Lock
import os


@dataclass
class ToolUsageMetric:
    """Represents a single tool usage metric."""
    tool_name: str
    timestamp: datetime
    duration_ms: float
    success: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_type: Optional[str] = None


@dataclass
class ErrorStatistic:
    """Represents error statistics for a specific error type."""
    error_type: str
    count: int
    last_occurrence: datetime
    sample_messages: List[str]


class MetricsCollector:
    """Collects and manages metrics for the DWF Analyzer MCP Server."""
    
    def __init__(self, max_metrics: int = 1000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.error_stats: Dict[str, ErrorStatistic] = {}
        self.tool_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "avg_duration_ms": 0.0,
            "total_duration_ms": 0.0,
            "last_used": None
        })
        self._lock = Lock()
    
    def record_tool_usage(
        self,
        tool_name: str,
        duration_ms: float,
        success: bool,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        file_type: Optional[str] = None
    ):
        """Record a tool usage metric."""
        with self._lock:
            metric = ToolUsageMetric(
                tool_name=tool_name,
                timestamp=datetime.now(),
                duration_ms=duration_ms,
                success=success,
                error_type=error_type,
                error_message=error_message,
                file_size_bytes=file_size_bytes,
                file_type=file_type
            )
            
            self.metrics.append(metric)
            self._update_tool_stats(metric)
            
            if not success and error_type:
                self._update_error_stats(error_type, error_message or "Unknown error")
    
    def _update_tool_stats(self, metric: ToolUsageMetric):
        """Update aggregated tool statistics."""
        stats = self.tool_stats[metric.tool_name]
        stats["total_calls"] += 1
        stats["last_used"] = metric.timestamp.isoformat()
        
        if metric.success:
            stats["successful_calls"] += 1
        else:
            stats["failed_calls"] += 1
        
        # Update duration statistics
        stats["total_duration_ms"] += metric.duration_ms
        stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["total_calls"]
    
    def _update_error_stats(self, error_type: str, error_message: str):
        """Update error statistics."""
        if error_type not in self.error_stats:
            self.error_stats[error_type] = ErrorStatistic(
                error_type=error_type,
                count=0,
                last_occurrence=datetime.now(),
                sample_messages=[]
            )
        
        error_stat = self.error_stats[error_type]
        error_stat.count += 1
        error_stat.last_occurrence = datetime.now()
        
        # Keep only the last 5 sample messages
        if len(error_stat.sample_messages) >= 5:
            error_stat.sample_messages.pop(0)
        error_stat.sample_messages.append(error_message)
    
    def get_tool_usage_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get tool usage statistics for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            recent_metrics = [
                m for m in self.metrics 
                if m.timestamp >= cutoff_time
            ]
            
            stats = {
                "time_period_hours": hours,
                "total_requests": len(recent_metrics),
                "successful_requests": sum(1 for m in recent_metrics if m.success),
                "failed_requests": sum(1 for m in recent_metrics if not m.success),
                "tools": dict(self.tool_stats),
                "recent_activity": []
            }
            
            # Add recent activity (last 10 requests)
            for metric in list(self.metrics)[-10:]:
                stats["recent_activity"].append({
                    "tool_name": metric.tool_name,
                    "timestamp": metric.timestamp.isoformat(),
                    "duration_ms": metric.duration_ms,
                    "success": metric.success,
                    "error_type": metric.error_type
                })
            
            return stats
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        with self._lock:
            return {
                "total_error_types": len(self.error_stats),
                "errors": {
                    error_type: {
                        "count": stat.count,
                        "last_occurrence": stat.last_occurrence.isoformat(),
                        "sample_messages": stat.sample_messages
                    }
                    for error_type, stat in self.error_stats.items()
                }
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        with self._lock:
            if not self.metrics:
                return {"message": "No metrics available"}
            
            durations = [m.duration_ms for m in self.metrics]
            file_sizes = [m.file_size_bytes for m in self.metrics if m.file_size_bytes]
            
            return {
                "response_times": {
                    "avg_ms": sum(durations) / len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                    "p95_ms": self._percentile(durations, 95),
                    "p99_ms": self._percentile(durations, 99)
                },
                "file_processing": {
                    "avg_file_size_bytes": sum(file_sizes) / len(file_sizes) if file_sizes else 0,
                    "max_file_size_bytes": max(file_sizes) if file_sizes else 0,
                    "files_processed": len(file_sizes)
                }
            }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a list of numbers."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def export_metrics(self, file_path: Optional[str] = None) -> str:
        """Export metrics to JSON format."""
        with self._lock:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "tool_usage_stats": self.get_tool_usage_stats(),
                "error_statistics": self.get_error_statistics(),
                "performance_metrics": self.get_performance_metrics(),
                "raw_metrics": [
                    asdict(metric) for metric in list(self.metrics)[-100:]  # Last 100 metrics
                ]
            }
            
            # Convert datetime objects to strings for JSON serialization
            def datetime_converter(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            json_data = json.dumps(export_data, indent=2, default=datetime_converter)
            
            if file_path:
                with open(file_path, 'w') as f:
                    f.write(json_data)
            
            return json_data


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def track_tool_usage(tool_name: str):
    """Decorator to track tool usage metrics."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            collector = get_metrics_collector()
            
            try:
                # Extract file information if available
                file_path = None
                file_size = None
                file_type = None
                
                if args and isinstance(args[0], str) and os.path.exists(args[0]):
                    file_path = args[0]
                    file_size = os.path.getsize(file_path)
                    file_type = os.path.splitext(file_path)[1].lower()
                elif 'file_path' in kwargs and os.path.exists(kwargs['file_path']):
                    file_path = kwargs['file_path']
                    file_size = os.path.getsize(file_path)
                    file_type = os.path.splitext(file_path)[1].lower()
                
                # Execute the function
                result = func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Determine success based on result
                success = True
                error_type = None
                error_message = None
                
                if isinstance(result, dict) and result.get('error'):
                    success = False
                    error_message = result.get('message', 'Unknown error')
                    error_type = type(Exception).__name__  # Default error type
                
                # Record metrics
                collector.record_tool_usage(
                    tool_name=tool_name,
                    duration_ms=duration_ms,
                    success=success,
                    error_type=error_type,
                    error_message=error_message,
                    file_size_bytes=file_size,
                    file_type=file_type
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Record error metrics
                collector.record_tool_usage(
                    tool_name=tool_name,
                    duration_ms=duration_ms,
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    file_size_bytes=file_size,
                    file_type=file_type
                )
                
                raise
        
        return wrapper
    return decorator
