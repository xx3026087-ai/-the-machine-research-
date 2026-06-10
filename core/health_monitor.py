"""Health monitoring and self-healing for distributed system."""

import logging
import asyncio
from typing import Dict, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health states."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"


@dataclass
class HealthCheck:
    """Result of a single health check."""
    service: str
    status: ServiceStatus
    timestamp: datetime
    latency_ms: float
    error: str = None
    consecutive_failures: int = 0


class HealthMonitor:
    """Monitors all system services and triggers restarts."""

    def __init__(self, config: Dict):
        self.config = config
        self.services = [
            "kafka",
            "postgres",
            "neo4j",
            "opensearch",
            "whisper",
            "spacy",
            "ray",
            "llm"
        ]
        self.health_state: Dict[str, HealthCheck] = {}
        self.check_interval = config.get("check_interval_seconds", 30)
        self.failure_threshold = config.get("failure_threshold", 3)
        self.restart_backoff = config.get("restart_backoff_seconds", 5)

    async def check_health(self) -> Dict[str, HealthCheck]:
        """Check health of all services."""
        tasks = [
            self._check_service(service)
            for service in self.services
        ]
        results = await asyncio.gather(*tasks)
        
        for result in results:
            self.health_state[result.service] = result
        
        return self.health_state

    async def _check_service(self, service: str) -> HealthCheck:
        """Check single service."""
        try:
            start = datetime.now()
            
            # Service-specific health checks
            if service == "kafka":
                await self._check_kafka()
            elif service == "postgres":
                await self._check_postgres()
            elif service == "neo4j":
                await self._check_neo4j()
            elif service == "opensearch":
                await self._check_opensearch()
            elif service == "ray":
                await self._check_ray()
            elif service == "llm":
                await self._check_llm()
            
            latency = (datetime.now() - start).total_seconds() * 1000
            
            return HealthCheck(
                service=service,
                status=ServiceStatus.HEALTHY,
                timestamp=datetime.now(),
                latency_ms=latency,
                consecutive_failures=0
            )
        
        except Exception as e:
            logger.error(f"Health check failed for {service}: {str(e)}")
            
            prev = self.health_state.get(service)
            consecutive = (prev.consecutive_failures + 1) if prev else 1
            
            return HealthCheck(
                service=service,
                status=ServiceStatus.FAILED,
                timestamp=datetime.now(),
                latency_ms=-1,
                error=str(e),
                consecutive_failures=consecutive
            )

    async def _check_kafka(self) -> None:
        """Verify Kafka broker is responding."""
        # Implementation: connect to Kafka, list topics
        pass

    async def _check_postgres(self) -> None:
        """Verify PostgreSQL is responding."""
        # Implementation: execute SELECT 1
        pass

    async def _check_neo4j(self) -> None:
        """Verify Neo4j is responding."""
        # Implementation: execute RETURN 1
        pass

    async def _check_opensearch(self) -> None:
        """Verify OpenSearch is responding."""
        # Implementation: check cluster health
        pass

    async def _check_ray(self) -> None:
        """Verify Ray cluster is healthy."""
        # Implementation: check Ray dashboard API
        pass

    async def _check_llm(self) -> None:
        """Verify LLM server is responding."""
        # Implementation: send test inference request
        pass

    async def handle_failures(self) -> None:
        """Handle service failures and restarts."""
        for service, check in self.health_state.items():
            if check.status == ServiceStatus.FAILED:
                if check.consecutive_failures >= self.failure_threshold:
                    logger.warning(f"Restarting {service} after {check.consecutive_failures} failures")
                    await self._restart_service(service)
                    await asyncio.sleep(self.restart_backoff)

    async def _restart_service(self, service: str) -> None:
        """Restart a failed service."""
        logger.info(f"Attempting restart of {service}")
        # Implementation: Docker restart or systemd restart
        pass

    async def monitor_loop(self) -> None:
        """Main health monitoring loop."""
        while True:
            try:
                await self.check_health()
                await self.handle_failures()
                
                # Log health summary
                healthy = sum(1 for c in self.health_state.values() if c.status == ServiceStatus.HEALTHY)
                total = len(self.services)
                logger.info(f"Health check: {healthy}/{total} services healthy")
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {str(e)}")
            
            await asyncio.sleep(self.check_interval)

    def get_status_report(self) -> Dict:
        """Get current system health status."""
        return {
            "timestamp": datetime.now().isoformat(),
            "services": [
                {
                    "name": check.service,
                    "status": check.status.value,
                    "latency_ms": check.latency_ms,
                    "consecutive_failures": check.consecutive_failures,
                    "error": check.error
                }
                for check in self.health_state.values()
            ],
            "summary": {
                "healthy": sum(1 for c in self.health_state.values() if c.status == ServiceStatus.HEALTHY),
                "degraded": sum(1 for c in self.health_state.values() if c.status == ServiceStatus.DEGRADED),
                "failed": sum(1 for c in self.health_state.values() if c.status == ServiceStatus.FAILED),
                "total": len(self.services)
            }
        }
