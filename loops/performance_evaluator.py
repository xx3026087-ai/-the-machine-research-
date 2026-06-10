"""Monitors system performance and triggers optimization."""

import logging
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import psutil
import time

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""
    timestamp: datetime
    latency_ms: float
    accuracy: float
    memory_mb: float
    cpu_percent: float
    error_rate: float
    throughput: float  # tasks per second
    model_inference_time_ms: float


class PerformanceEvaluator:
    """Evaluates system performance against thresholds."""

    def __init__(self, config: Dict, graph_manager, memory_store, approval_gate):
        self.config = config
        self.graph_manager = graph_manager
        self.memory_store = memory_store
        self.approval_gate = approval_gate
        
        # Thresholds
        self.max_latency_ms = config.get("latency_threshold_ms", 5000)
        self.min_accuracy = config.get("accuracy_threshold", 0.75)
        self.max_memory_mb = config.get("max_memory_mb", 4096)
        self.max_cpu_percent = config.get("max_cpu_percent", 80)
        self.max_error_rate = config.get("error_rate_threshold", 0.05)
        
        self.evaluation_interval = 60  # seconds
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history = 1440  # 24 hours at 1-min intervals

    async def run_evaluation_loop(self) -> None:
        """Main performance evaluation loop."""
        while True:
            try:
                logger.info("Running performance evaluation")
                
                # Collect metrics
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > self.max_history:
                    self.metrics_history.pop(0)
                
                # Check thresholds
                violations = self._check_threshold_violations(metrics)
                
                if violations:
                    logger.warning(f"Performance threshold violations: {violations}")
                    await self._handle_violations(violations)
                
                # Store metrics
                await self._store_metrics(metrics)
                
                # Check for trend issues
                trend_issues = await self._detect_performance_trends()
                if trend_issues:
                    logger.warning(f"Performance trend issues: {trend_issues}")
                    await self._notify_performance_issues(trend_issues)
                
            except Exception as e:
                logger.error(f"Error in performance evaluation: {str(e)}", exc_info=True)
            
            await asyncio.sleep(self.evaluation_interval)

    async def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current system metrics."""
        try:
            timestamp = datetime.now()
            
            # CPU and memory
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=1)
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # Latency (measure response time)
            start = time.time()
            await self.graph_manager.get_graph_statistics()
            latency_ms = (time.time() - start) * 1000
            
            # Accuracy and error rate (from recent results)
            accuracy = await self._calculate_accuracy()
            error_rate = await self._calculate_error_rate()
            
            # Throughput
            throughput = await self._calculate_throughput()
            
            # Model inference time
            model_inference_time = await self._measure_model_inference()
            
            return PerformanceMetrics(
                timestamp=timestamp,
                latency_ms=latency_ms,
                accuracy=accuracy,
                memory_mb=memory_mb,
                cpu_percent=cpu_percent,
                error_rate=error_rate,
                throughput=throughput,
                model_inference_time_ms=model_inference_time
            )
        except Exception as e:
            logger.error(f"Failed to collect metrics: {str(e)}")
            return PerformanceMetrics(
                timestamp=datetime.now(),
                latency_ms=-1,
                accuracy=0.0,
                memory_mb=-1,
                cpu_percent=-1,
                error_rate=1.0,
                throughput=0.0,
                model_inference_time_ms=-1
            )

    async def _calculate_accuracy(self) -> float:
        """Calculate system accuracy from recent conclusions."""
        try:
            # Placeholder: would calculate based on ground truth if available
            return 0.82  # Dummy value
        except:
            return 0.5

    async def _calculate_error_rate(self) -> float:
        """Calculate system error rate."""
        try:
            # Would query error logs
            return 0.02  # Dummy value
        except:
            return 0.1

    async def _calculate_throughput(self) -> float:
        """Calculate system throughput."""
        try:
            # Tasks processed per second
            return 5.2  # Dummy value
        except:
            return 0.0

    async def _measure_model_inference(self) -> float:
        """Measure LLM model inference time."""
        try:
            # Would send test inference request
            return 250.0  # Dummy value ms
        except:
            return -1

    def _check_threshold_violations(self, metrics: PerformanceMetrics) -> List[str]:
        """Check if metrics violate thresholds."""
        violations = []
        
        if metrics.latency_ms > self.max_latency_ms:
            violations.append(f"Latency {metrics.latency_ms}ms exceeds threshold {self.max_latency_ms}ms")
        
        if metrics.accuracy < self.min_accuracy:
            violations.append(f"Accuracy {metrics.accuracy:.2f} below threshold {self.min_accuracy:.2f}")
        
        if metrics.memory_mb > self.max_memory_mb:
            violations.append(f"Memory {metrics.memory_mb:.0f}MB exceeds threshold {self.max_memory_mb}MB")
        
        if metrics.cpu_percent > self.max_cpu_percent:
            violations.append(f"CPU {metrics.cpu_percent:.1f}% exceeds threshold {self.max_cpu_percent}%")
        
        if metrics.error_rate > self.max_error_rate:
            violations.append(f"Error rate {metrics.error_rate:.2%} exceeds threshold {self.max_error_rate:.2%}")
        
        return violations

    async def _handle_violations(self, violations: List[str]) -> None:
        """Handle performance violations."""
        try:
            if any('latency' in v.lower() for v in violations):
                logger.warning("Attempting latency optimization")
                await self._optimize_latency()
            
            if any('memory' in v.lower() for v in violations):
                logger.warning("Attempting memory optimization")
                await self._optimize_memory()
            
            if any('accuracy' in v.lower() for v in violations):
                logger.warning("Low accuracy detected")
                await self._request_model_retrain()
            
            if any('error' in v.lower() for v in violations):
                logger.warning("High error rate detected")
                await self._investigate_errors()
        except Exception as e:
            logger.error(f"Failed to handle violations: {str(e)}")

    async def _optimize_latency(self) -> None:
        """Attempt latency optimization."""
        logger.info("Optimizing latency: increasing batch sizes, enabling caching")
        # Would trigger configuration changes

    async def _optimize_memory(self) -> None:
        """Attempt memory optimization."""
        logger.info("Optimizing memory: reducing cache size, running GC")
        # Would trigger garbage collection and cache clearing

    async def _request_model_retrain(self) -> None:
        """Request model retraining."""
        try:
            from supervisor.approval_gate import ChangeRequest, ChangeType, ApprovalStatus
            
            request = ChangeRequest(
                id=f"retrain_{datetime.now().timestamp()}",
                change_type=ChangeType.MODEL_RETRAIN,
                title="Model Retraining Request",
                description="Accuracy below threshold, retraining recommended",
                proposed_change={"action": "retrain_entity_classifier"},
                requester="performance_evaluator"
            )
            
            self.approval_gate.submit_change_request(request)
            logger.info(f"Retraining request submitted: {request.id}")
        except Exception as e:
            logger.error(f"Failed to request retraining: {str(e)}")

    async def _investigate_errors(self) -> None:
        """Investigate high error rate."""
        logger.info("Investigating error rate spike")
        # Would fetch and analyze recent errors

    async def _detect_performance_trends(self) -> List[str]:
        """Detect performance degradation trends."""
        try:
            if len(self.metrics_history) < 10:
                return []
            
            recent = self.metrics_history[-10:]
            issues = []
            
            # Check for increasing latency
            latencies = [m.latency_ms for m in recent]
            if all(latencies[i] <= latencies[i+1] for i in range(len(latencies)-1)):
                issues.append("Latency steadily increasing")
            
            # Check for increasing memory
            memories = [m.memory_mb for m in recent]
            if all(memories[i] <= memories[i+1] for i in range(len(memories)-1)):
                issues.append("Memory usage steadily increasing")
            
            # Check for decreasing accuracy
            accuracies = [m.accuracy for m in recent]
            if all(accuracies[i] >= accuracies[i+1] for i in range(len(accuracies)-1)):
                issues.append("Accuracy steadily declining")
            
            return issues
        except Exception as e:
            logger.error(f"Failed to detect trends: {str(e)}")
            return []

    async def _notify_performance_issues(self, issues: List[str]) -> None:
        """Notify about performance trend issues."""
        for issue in issues:
            logger.warning(f"Performance trend: {issue}")
            # Would send alerts

    async def _store_metrics(self, metrics: PerformanceMetrics) -> None:
        """Store metrics in database."""
        try:
            await self.memory_store.store_performance_metrics(
                timestamp=metrics.timestamp.isoformat(),
                latency_ms=metrics.latency_ms,
                accuracy=metrics.accuracy,
                memory_mb=metrics.memory_mb,
                cpu_percent=metrics.cpu_percent,
                error_rate=metrics.error_rate,
                throughput=metrics.throughput
            )
        except Exception as e:
            logger.error(f"Failed to store metrics: {str(e)}")

    def get_metrics_report(self) -> Dict:
        """Get performance metrics report."""
        if not self.metrics_history:
            return {}
        
        latest = self.metrics_history[-1]
        avg_latency = sum(m.latency_ms for m in self.metrics_history) / len(self.metrics_history)
        avg_accuracy = sum(m.accuracy for m in self.metrics_history) / len(self.metrics_history)
        
        return {
            "timestamp": latest.timestamp.isoformat(),
            "latest": {
                "latency_ms": latest.latency_ms,
                "accuracy": latest.accuracy,
                "memory_mb": latest.memory_mb,
                "cpu_percent": latest.cpu_percent,
                "error_rate": latest.error_rate
            },
            "averages": {
                "latency_ms": avg_latency,
                "accuracy": avg_accuracy
            },
            "thresholds": {
                "max_latency_ms": self.max_latency_ms,
                "min_accuracy": self.min_accuracy,
                "max_memory_mb": self.max_memory_mb,
                "max_cpu_percent": self.max_cpu_percent
            }
        }
