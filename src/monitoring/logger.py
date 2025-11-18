"""
Structured performance logging for production monitoring.

Provides JSON-structured logging for performance metrics with integration
to standard logging libraries.
"""

import json
import logging
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PerformanceLogger:
    """
    Structured logger for performance metrics.

    Outputs JSON-formatted logs suitable for ingestion by:
    - ELK Stack (Elasticsearch, Logstash, Kibana)
    - Splunk
    - CloudWatch Logs
    - Datadog

    Example:
        logger = PerformanceLogger("hbcm_simulation")

        logger.log_latency(
            operation="simulate",
            duration_ms=45.2,
            metadata={"particles": 1000}
        )

        logger.log_throughput(
            operation="control_loop",
            requests_per_second=1000.0
        )
    """

    def __init__(self, component: str, log_file: Optional[str] = None):
        """
        Initialize performance logger.

        Args:
            component: Component name (e.g., "hbcm", "motorhand", "api")
            log_file: Optional log file path (logs to stdout if not specified)
        """
        self.component = component
        self.logger = logging.getLogger(f"performance.{component}")

        # Configure logger
        self.logger.setLevel(logging.DEBUG)

        # Add handler
        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler()

        handler.setLevel(logging.DEBUG)

        # JSON formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def _log(self, level: LogLevel, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log a structured event.

        Args:
            level: Log level
            event_type: Event type (e.g., "latency", "throughput")
            data: Event data dictionary
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'component': self.component,
            'event_type': event_type,
            **data
        }

        log_message = json.dumps(log_entry)

        if level == LogLevel.DEBUG:
            self.logger.debug(log_message)
        elif level == LogLevel.INFO:
            self.logger.info(log_message)
        elif level == LogLevel.WARNING:
            self.logger.warning(log_message)
        elif level == LogLevel.ERROR:
            self.logger.error(log_message)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(log_message)

    def log_latency(self, operation: str, duration_ms: float,
                   metadata: Optional[Dict[str, Any]] = None,
                   level: LogLevel = LogLevel.INFO) -> None:
        """
        Log a latency measurement.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            metadata: Optional metadata
            level: Log level
        """
        data = {
            'operation': operation,
            'duration_ms': duration_ms,
            'duration_s': duration_ms / 1000.0,
        }

        if metadata:
            data['metadata'] = metadata

        self._log(level, 'latency', data)

    def log_throughput(self, operation: str, requests_per_second: float,
                      metadata: Optional[Dict[str, Any]] = None,
                      level: LogLevel = LogLevel.INFO) -> None:
        """
        Log a throughput measurement.

        Args:
            operation: Operation name
            requests_per_second: Requests per second
            metadata: Optional metadata
            level: Log level
        """
        data = {
            'operation': operation,
            'requests_per_second': requests_per_second,
        }

        if metadata:
            data['metadata'] = metadata

        self._log(level, 'throughput', data)

    def log_error(self, operation: str, error: str,
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an error.

        Args:
            operation: Operation name
            error: Error message
            metadata: Optional metadata
        """
        data = {
            'operation': operation,
            'error': error,
        }

        if metadata:
            data['metadata'] = metadata

        self._log(LogLevel.ERROR, 'error', data)

    def log_resource_usage(self, memory_mb: float, cpu_percent: float,
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log resource usage.

        Args:
            memory_mb: Memory usage in megabytes
            cpu_percent: CPU usage percentage
            metadata: Optional metadata
        """
        data = {
            'memory_mb': memory_mb,
            'cpu_percent': cpu_percent,
        }

        if metadata:
            data['metadata'] = metadata

        self._log(LogLevel.INFO, 'resource_usage', data)

    def log_custom(self, event_type: str, data: Dict[str, Any],
                  level: LogLevel = LogLevel.INFO) -> None:
        """
        Log a custom event.

        Args:
            event_type: Event type
            data: Event data
            level: Log level
        """
        self._log(level, event_type, data)
