"""
Prometheus-compatible metrics collection for production monitoring.

Provides counters, gauges, histograms, and summaries compatible with
Prometheus scraping and Grafana visualization.
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading


class MetricType(Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Metric data structure."""

    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    help_text: str = ""

    def to_prometheus(self) -> str:
        """
        Convert metric to Prometheus text format.

        Returns:
            str: Prometheus-formatted metric
        """
        labels_str = ""
        if self.labels:
            labels_list = [f'{k}="{v}"' for k, v in self.labels.items()]
            labels_str = "{" + ",".join(labels_list) + "}"

        # Include HELP and TYPE for first occurrence
        output = []
        output.append(f"# HELP {self.name} {self.help_text}")
        output.append(f"# TYPE {self.name} {self.type.value}")
        output.append(f"{self.name}{labels_str} {self.value}")

        return "\n".join(output)


class MetricsCollector:
    """
    Thread-safe metrics collector with Prometheus compatibility.

    Collects and aggregates metrics for:
    - Request counts
    - Latency distributions
    - Resource utilization
    - Error rates
    - Custom application metrics

    Example:
        collector = MetricsCollector()

        # Increment counter
        collector.increment("requests_total", labels={"endpoint": "/api/simulate"})

        # Set gauge
        collector.set_gauge("memory_usage_bytes", 1024 * 1024 * 512)

        # Record histogram
        collector.observe_histogram("request_duration_seconds", 0.045)

        # Export to Prometheus
        print(collector.to_prometheus())
    """

    _instance: Optional['MetricsCollector'] = None
    _lock = threading.Lock()

    def __init__(self):
        """Initialize metrics collector."""
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._summaries: Dict[str, List[float]] = {}
        self._metric_metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> 'MetricsCollector':
        """Get singleton instance (thread-safe)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _metric_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Generate unique metric key from name and labels."""
        if not labels:
            return name

        # Sort labels for consistent key generation
        labels_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{labels_str}}}"

    def increment(self, name: str, value: float = 1.0,
                  labels: Optional[Dict[str, str]] = None,
                  help_text: str = "") -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Increment value (default: 1.0)
            labels: Optional labels dictionary
            help_text: Help text for metric
        """
        key = self._metric_key(name, labels)

        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + value

            if name not in self._metric_metadata:
                self._metric_metadata[name] = {
                    'type': MetricType.COUNTER,
                    'help': help_text or f"Counter metric {name}",
                    'labels': labels or {}
                }

    def set_gauge(self, name: str, value: float,
                  labels: Optional[Dict[str, str]] = None,
                  help_text: str = "") -> None:
        """
        Set a gauge metric.

        Args:
            name: Metric name
            value: Gauge value
            labels: Optional labels dictionary
            help_text: Help text for metric
        """
        key = self._metric_key(name, labels)

        with self._lock:
            self._gauges[key] = value

            if name not in self._metric_metadata:
                self._metric_metadata[name] = {
                    'type': MetricType.GAUGE,
                    'help': help_text or f"Gauge metric {name}",
                    'labels': labels or {}
                }

    def observe_histogram(self, name: str, value: float,
                         labels: Optional[Dict[str, str]] = None,
                         help_text: str = "") -> None:
        """
        Observe a value in a histogram metric.

        Args:
            name: Metric name
            value: Observed value
            labels: Optional labels dictionary
            help_text: Help text for metric
        """
        key = self._metric_key(name, labels)

        with self._lock:
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)

            if name not in self._metric_metadata:
                self._metric_metadata[name] = {
                    'type': MetricType.HISTOGRAM,
                    'help': help_text or f"Histogram metric {name}",
                    'labels': labels or {}
                }

    def observe_summary(self, name: str, value: float,
                       labels: Optional[Dict[str, str]] = None,
                       help_text: str = "") -> None:
        """
        Observe a value in a summary metric.

        Args:
            name: Metric name
            value: Observed value
            labels: Optional labels dictionary
            help_text: Help text for metric
        """
        key = self._metric_key(name, labels)

        with self._lock:
            if key not in self._summaries:
                self._summaries[key] = []
            self._summaries[key].append(value)

            if name not in self._metric_metadata:
                self._metric_metadata[name] = {
                    'type': MetricType.SUMMARY,
                    'help': help_text or f"Summary metric {name}",
                    'labels': labels or {}
                }

    def get_metrics(self) -> List[Metric]:
        """
        Get all collected metrics.

        Returns:
            List of Metric objects
        """
        metrics = []
        now = datetime.now()

        with self._lock:
            # Counters
            for key, value in self._counters.items():
                # Extract name and labels from key
                if "{" in key:
                    name = key.split("{")[0]
                    labels_str = key.split("{")[1].rstrip("}")
                    labels = dict(kv.split("=") for kv in labels_str.split(","))
                else:
                    name = key
                    labels = {}

                metadata = self._metric_metadata.get(name, {})
                metrics.append(Metric(
                    name=name,
                    type=MetricType.COUNTER,
                    value=value,
                    labels=labels,
                    timestamp=now,
                    help_text=metadata.get('help', '')
                ))

            # Gauges
            for key, value in self._gauges.items():
                if "{" in key:
                    name = key.split("{")[0]
                    labels_str = key.split("{")[1].rstrip("}")
                    labels = dict(kv.split("=") for kv in labels_str.split(","))
                else:
                    name = key
                    labels = {}

                metadata = self._metric_metadata.get(name, {})
                metrics.append(Metric(
                    name=name,
                    type=MetricType.GAUGE,
                    value=value,
                    labels=labels,
                    timestamp=now,
                    help_text=metadata.get('help', '')
                ))

            # Histograms - calculate quantiles
            for key, values in self._histograms.items():
                if not values:
                    continue

                if "{" in key:
                    name = key.split("{")[0]
                    labels_str = key.split("{")[1].rstrip("}")
                    labels = dict(kv.split("=") for kv in labels_str.split(","))
                else:
                    name = key
                    labels = {}

                sorted_values = sorted(values)
                n = len(sorted_values)

                # Add sum and count
                metrics.append(Metric(
                    name=f"{name}_sum",
                    type=MetricType.COUNTER,
                    value=sum(values),
                    labels=labels,
                    timestamp=now
                ))
                metrics.append(Metric(
                    name=f"{name}_count",
                    type=MetricType.COUNTER,
                    value=n,
                    labels=labels,
                    timestamp=now
                ))

                # Add quantiles (buckets)
                quantiles = [0.5, 0.9, 0.95, 0.99]
                for q in quantiles:
                    idx = int(n * q)
                    labels_with_quantile = labels.copy()
                    labels_with_quantile['quantile'] = str(q)
                    metrics.append(Metric(
                        name=name,
                        type=MetricType.HISTOGRAM,
                        value=sorted_values[idx] if idx < n else sorted_values[-1],
                        labels=labels_with_quantile,
                        timestamp=now
                    ))

        return metrics

    def to_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            str: Prometheus-formatted metrics
        """
        metrics = self.get_metrics()
        output = []

        # Group by metric name
        metrics_by_name: Dict[str, List[Metric]] = {}
        for metric in metrics:
            if metric.name not in metrics_by_name:
                metrics_by_name[metric.name] = []
            metrics_by_name[metric.name].append(metric)

        # Format for Prometheus
        for name, metric_list in sorted(metrics_by_name.items()):
            # Add HELP and TYPE once per metric
            first_metric = metric_list[0]
            output.append(f"# HELP {name} {first_metric.help_text}")
            output.append(f"# TYPE {name} {first_metric.type.value}")

            # Add all samples
            for metric in metric_list:
                labels_str = ""
                if metric.labels:
                    labels_list = [f'{k}="{v}"' for k, v in metric.labels.items()]
                    labels_str = "{" + ",".join(labels_list) + "}"

                output.append(f"{name}{labels_str} {metric.value}")

            output.append("")  # Blank line between metrics

        return "\n".join(output)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get human-readable summary of all metrics.

        Returns:
            Dictionary with metric summaries
        """
        summary = {
            'counters': {},
            'gauges': {},
            'histograms': {},
            'summaries': {},
            'timestamp': datetime.now().isoformat()
        }

        with self._lock:
            # Counters
            for key, value in self._counters.items():
                summary['counters'][key] = value

            # Gauges
            for key, value in self._gauges.items():
                summary['gauges'][key] = value

            # Histograms
            for key, values in self._histograms.items():
                if values:
                    sorted_values = sorted(values)
                    n = len(sorted_values)
                    summary['histograms'][key] = {
                        'count': n,
                        'sum': sum(values),
                        'min': sorted_values[0],
                        'max': sorted_values[-1],
                        'mean': sum(values) / n,
                        'p50': sorted_values[int(n * 0.5)],
                        'p95': sorted_values[int(n * 0.95)],
                        'p99': sorted_values[int(n * 0.99)]
                    }

        return summary

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._summaries.clear()
            self._metric_metadata.clear()


# Global singleton instance
_global_collector = MetricsCollector.get_instance()


def increment_counter(name: str, value: float = 1.0,
                     labels: Optional[Dict[str, str]] = None) -> None:
    """
    Increment a counter metric (convenience function).

    Args:
        name: Metric name
        value: Increment value
        labels: Optional labels
    """
    _global_collector.increment(name, value, labels)


def set_gauge(name: str, value: float,
             labels: Optional[Dict[str, str]] = None) -> None:
    """
    Set a gauge metric (convenience function).

    Args:
        name: Metric name
        value: Gauge value
        labels: Optional labels
    """
    _global_collector.set_gauge(name, value, labels)


def observe_histogram(name: str, value: float,
                     labels: Optional[Dict[str, str]] = None) -> None:
    """
    Observe a histogram value (convenience function).

    Args:
        name: Metric name
        value: Observed value
        labels: Optional labels
    """
    _global_collector.observe_histogram(name, value, labels)
