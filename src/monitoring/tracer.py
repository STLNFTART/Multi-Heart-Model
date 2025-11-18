"""
Distributed tracing support for end-to-end request tracking.

Provides trace context propagation compatible with OpenTelemetry standards.
"""

import uuid
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager


@dataclass
class Span:
    """
    A single span in a distributed trace.

    Represents one operation in the request flow.
    """

    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)

    def finish(self) -> None:
        """Mark span as finished."""
        self.end_time = time.time()
        if self.start_time:
            self.duration_ms = (self.end_time - self.start_time) * 1000.0

    def log_event(self, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an event within the span.

        Args:
            event: Event name
            data: Optional event data
        """
        log_entry = {
            'timestamp': time.time(),
            'event': event,
        }
        if data:
            log_entry['data'] = data

        self.logs.append(log_entry)

    def set_tag(self, key: str, value: Any) -> None:
        """
        Set a tag on the span.

        Args:
            key: Tag key
            value: Tag value
        """
        self.tags[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        return {
            'span_id': self.span_id,
            'trace_id': self.trace_id,
            'parent_span_id': self.parent_span_id,
            'operation': self.operation,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_ms': self.duration_ms,
            'tags': self.tags,
            'logs': self.logs,
        }


@dataclass
class TraceContext:
    """
    Trace context for request tracking.

    Contains trace ID and current span information.
    """

    trace_id: str
    current_span: Optional[Span] = None
    spans: List[Span] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace context to dictionary."""
        return {
            'trace_id': self.trace_id,
            'spans': [span.to_dict() for span in self.spans],
        }

    def get_duration_ms(self) -> Optional[float]:
        """Get total trace duration."""
        if not self.spans:
            return None

        start_times = [s.start_time for s in self.spans if s.start_time]
        end_times = [s.end_time for s in self.spans if s.end_time]

        if not start_times or not end_times:
            return None

        return (max(end_times) - min(start_times)) * 1000.0


class EndToEndTracer:
    """
    End-to-end distributed tracer.

    Tracks requests across multiple components with span relationships.

    Features:
    - Trace ID generation and propagation
    - Parent-child span relationships
    - Tag and log support
    - OpenTelemetry-compatible format

    Example:
        # Start a trace
        tracer = EndToEndTracer()
        trace_ctx = tracer.start_trace("api_request")

        # Create child span
        with tracer.start_span("database_query", trace_ctx) as span:
            span.set_tag("query", "SELECT * FROM users")
            result = db.query(...)

        # Create another span
        with tracer.start_span("process_results", trace_ctx) as span:
            span.set_tag("result_count", len(result))
            processed = process(result)

        # Finish trace
        tracer.finish_trace(trace_ctx)

        # Get trace data
        print(f"Total duration: {trace_ctx.get_duration_ms():.3f} ms")
    """

    _active_traces: Dict[str, TraceContext] = {}

    def __init__(self):
        """Initialize tracer."""
        pass

    @staticmethod
    def generate_trace_id() -> str:
        """Generate a unique trace ID."""
        return str(uuid.uuid4())

    @staticmethod
    def generate_span_id() -> str:
        """Generate a unique span ID."""
        return str(uuid.uuid4())[:16]

    def start_trace(self, operation: str, tags: Optional[Dict[str, Any]] = None) -> TraceContext:
        """
        Start a new trace.

        Args:
            operation: Root operation name
            tags: Optional tags for root span

        Returns:
            TraceContext for the new trace
        """
        trace_id = self.generate_trace_id()
        span_id = self.generate_span_id()

        # Create root span
        root_span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=None,
            operation=operation,
            start_time=time.time(),
            tags=tags or {}
        )

        # Create trace context
        trace_ctx = TraceContext(
            trace_id=trace_id,
            current_span=root_span,
            spans=[root_span]
        )

        self._active_traces[trace_id] = trace_ctx

        return trace_ctx

    @contextmanager
    def start_span(self, operation: str, trace_ctx: TraceContext,
                  tags: Optional[Dict[str, Any]] = None):
        """
        Start a new span within a trace (context manager).

        Args:
            operation: Span operation name
            trace_ctx: Parent trace context
            tags: Optional tags

        Yields:
            Span: The created span
        """
        parent_span_id = trace_ctx.current_span.span_id if trace_ctx.current_span else None
        span_id = self.generate_span_id()

        span = Span(
            span_id=span_id,
            trace_id=trace_ctx.trace_id,
            parent_span_id=parent_span_id,
            operation=operation,
            start_time=time.time(),
            tags=tags or {}
        )

        # Add to trace
        trace_ctx.spans.append(span)

        # Save previous current span
        previous_span = trace_ctx.current_span
        trace_ctx.current_span = span

        try:
            yield span
        finally:
            # Finish span
            span.finish()

            # Restore previous span
            trace_ctx.current_span = previous_span

    def finish_trace(self, trace_ctx: TraceContext) -> None:
        """
        Finish a trace.

        Args:
            trace_ctx: Trace context to finish
        """
        # Finish all unfinished spans
        for span in trace_ctx.spans:
            if span.end_time is None:
                span.finish()

        # Remove from active traces
        if trace_ctx.trace_id in self._active_traces:
            del self._active_traces[trace_ctx.trace_id]

    def get_trace(self, trace_id: str) -> Optional[TraceContext]:
        """
        Get an active trace by ID.

        Args:
            trace_id: Trace ID

        Returns:
            TraceContext if found, None otherwise
        """
        return self._active_traces.get(trace_id)

    def get_all_traces(self) -> List[TraceContext]:
        """Get all active traces."""
        return list(self._active_traces.values())

    @staticmethod
    def inject_trace_context(trace_ctx: TraceContext) -> Dict[str, str]:
        """
        Inject trace context into HTTP headers (for propagation).

        Args:
            trace_ctx: Trace context

        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            'X-Trace-Id': trace_ctx.trace_id,
        }

        if trace_ctx.current_span:
            headers['X-Span-Id'] = trace_ctx.current_span.span_id

        return headers

    @staticmethod
    def extract_trace_context(headers: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Extract trace context from HTTP headers.

        Args:
            headers: HTTP headers dictionary

        Returns:
            Dictionary with trace_id and span_id if found
        """
        trace_id = headers.get('X-Trace-Id') or headers.get('x-trace-id')
        span_id = headers.get('X-Span-Id') or headers.get('x-span-id')

        if not trace_id:
            return None

        return {
            'trace_id': trace_id,
            'parent_span_id': span_id,
        }
