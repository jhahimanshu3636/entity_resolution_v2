"""
Logging Configuration for Entity Resolution System
=================================================

Structured logging using structlog for audit trails and debugging.

Author: Entity Resolution System
"""

import structlog
import logging
import sys
from typing import Optional
from datetime import datetime


def configure_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None
) -> None:
    """
    Configure structured logging
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_type: Format type ("json" or "console")
        log_file: Optional file path for logging
    """
    
    # Set logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure processors
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if format_type == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=handlers
    )


def get_logger(name: str = "entity_resolution"):
    """
    Get a configured logger instance
    
    Args:
        name: Logger name
        
    Returns:
        Structured logger
    """
    return structlog.get_logger(name)


# ============================================================================
# LOGGING HELPERS
# ============================================================================

class StageLogger:
    """Logger for pipeline stages"""
    
    def __init__(self, stage_name: str, block_id: str):
        self.logger = get_logger()
        self.stage_name = stage_name
        self.block_id = block_id
        self.start_time = None
    
    def start(self, **kwargs):
        """Log stage start"""
        self.start_time = datetime.utcnow()
        self.logger.info(
            "stage_started",
            stage=self.stage_name,
            block_id=self.block_id,
            timestamp=self.start_time.isoformat(),
            **kwargs
        )
    
    def complete(self, **kwargs):
        """Log stage completion"""
        end_time = datetime.utcnow()
        duration_seconds = (end_time - self.start_time).total_seconds() if self.start_time else 0
        
        self.logger.info(
            "stage_completed",
            stage=self.stage_name,
            block_id=self.block_id,
            duration_seconds=duration_seconds,
            timestamp=end_time.isoformat(),
            **kwargs
        )
    
    def error(self, error: Exception, **kwargs):
        """Log stage error"""
        self.logger.error(
            "stage_error",
            stage=self.stage_name,
            block_id=self.block_id,
            error_type=type(error).__name__,
            error_message=str(error),
            **kwargs,
            exc_info=True
        )


def log_constraint_violation(
    logger,
    constraint_type: str,
    constraint_name: str,
    edge: tuple,
    reason: str,
    **kwargs
):
    """Log constraint violation"""
    logger.warning(
        "constraint_violation",
        constraint_type=constraint_type,
        constraint_name=constraint_name,
        edge=edge,
        reason=reason,
        **kwargs
    )


def log_graph_metrics(logger, block_id: str, stage: str, **metrics):
    """Log graph metrics"""
    logger.info(
        "graph_metrics",
        block_id=block_id,
        stage=stage,
        **metrics
    )


def log_fraud_detection(
    logger,
    entity_id: str,
    fraud_pattern: str,
    confidence: float,
    evidence: list,
    **kwargs
):
    """Log fraud detection"""
    logger.warning(
        "fraud_detected",
        entity_id=entity_id,
        fraud_pattern=fraud_pattern,
        confidence=confidence,
        evidence=evidence,
        **kwargs
    )
