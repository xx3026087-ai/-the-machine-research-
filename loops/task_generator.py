"""Generates investigation tasks based on observations and gaps."""

import logging
import asyncio
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TaskType(Enum):
    """Types of investigation tasks."""
    ENTITY_SEARCH = "entity_search"
    RELATIONSHIP_INFERENCE = "relationship_inference"
    CLUSTER_ANALYSIS = "cluster_analysis"
    CONFIDENCE_VALIDATION = "confidence_validation"
    ANOMALY_INVESTIGATION = "anomaly_investigation"
    CROSS_REFERENCE = "cross_reference"
    DATA_ENRICHMENT = "data_enrichment"


@dataclass
class InvestigationTask:
    """Task for the system to investigate."""
    id: str
    type: TaskType
    title: str
    description: str
    target_entities: List[str]
    priority: TaskPriority
    expected_gain: float  # 0.0-1.0
    estimated_effort: float  # 0.0-1.0
    created_at: datetime
    due_at: Optional[datetime] = None
    status: str = "pending"
    result: Optional[str] = None


class TaskGenerator:
    """Generates prioritized investigation tasks."""

    def __init__(self, config: Dict, graph_manager, memory_store, llm_client):
        self.config = config
        self.graph_manager = graph_manager
        self.memory_store = memory_store
        self.llm_client = llm_client
        self.loop_interval = config.get("run_interval_seconds", 120)
        self.max_tasks_per_iteration = config.get("max_tasks_per_iteration", 10)
        self.priority_decay_hours = config.get("priority_decay_hours", 24)
        self.duplicate_threshold = config.get("duplicate_task_threshold", 0.85)
        self.pending_tasks: Dict[str, InvestigationTask] = {}

    async def run_task_generation_loop(self) -> None:
        """Main task generation loop."""
        while True:
            try:
                logger.info("Starting task generation cycle")
                
                # Analyze current observations
                observations = await self._get_current_observations()
                
                # Identify gaps
                gaps = await self._identify_information_gaps(observations)
                
                # Generate tasks from gaps
                new_tasks = await self._generate_tasks_from_gaps(gaps)
                
                if new_tasks:
                    logger.info(f"Generated {len(new_tasks)} new tasks")
                    await self._dedup_and_store_tasks(new_tasks)
                
                # Get ready-to-execute tasks
                executable_tasks = await self._get_executable_tasks()
                if executable_tasks:
                    await self._dispatch_tasks(executable_tasks)
                
            except Exception as e:
                logger.error(f"Error in task generation loop: {str(e)}", exc_info=True)
            
            await asyncio.sleep(self.loop_interval)

    async def _get_current_observations(self) -> List[str]:
        """Get current system observations."""
        try:
            observations = []
            
            # Graph statistics
            stats = self.graph_manager.get_graph_statistics()
            observations.append(f"Graph has {stats.get('nodes', 0)} entities")
            
            # Recent entities
            recent_entities = await self.memory_store.get_recent_entities(limit=5)
            if recent_entities:
                observations.append(f"Recent entities: {', '.join([e.get('name') for e in recent_entities])}")
            
            # Low-confidence items
            low_conf = await self.memory_store.get_low_confidence_items(threshold=0.6)
            observations.append(f"Found {len(low_conf)} items with confidence < 0.6")
            
            return observations
        except Exception as e:
            logger.error(f"Failed to get observations: {str(e)}")
            return []

    async def _identify_information_gaps(self, observations: List[str]) -> List[Dict]:
        """Identify gaps in current understanding."""
        try:
            observations_text = "\n".join([f"- {obs}" for obs in observations])
            
            prompt = f"""
Based on these observations, what information is missing or needs clarification?

Observations:
{observations_text}

Identify gaps:
1. Entities that need more research
2. Relationships that are uncertain
3. Time periods or locations with incomplete data
4. Contradictions that need investigation
5. Clusters that need analysis

For each gap, suggest:
- Description
- Why it matters
- How to investigate it
            """
            
            response = await self.llm_client.generate(
                prompt=prompt,
                max_tokens=800,
                temperature=0.7
            )
            
            gaps = await self._parse_gap_response(response)
            return gaps
        except Exception as e:
            logger.error(f"Failed to identify gaps: {str(e)}")
            return []

    async def _parse_gap_response(self, response: str) -> List[Dict]:
        """Parse LLM gap analysis response."""
        gaps = []
        lines = response.split("\n")
        
        current_gap = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if any(marker in line for marker in ["gap", "missing", "uncertain", "contradiction", "cluster"]):
                if current_gap:
                    gaps.append(current_gap)
                current_gap = {
                    "description": line,
                    "priority": TaskPriority.MEDIUM.value
                }
        
        if current_gap:
            gaps.append(current_gap)
        
        return gaps

    async def _generate_tasks_from_gaps(self, gaps: List[Dict]) -> List[InvestigationTask]:
        """Create investigation tasks from identified gaps."""
        tasks = []
        
        for i, gap in enumerate(gaps):
            task_type = self._infer_task_type(gap)
            priority = self._calculate_priority(gap)
            expected_gain = self._estimate_information_gain(gap)
            
            task = InvestigationTask(
                id=f"task_{datetime.now().timestamp()}_{i}",
                type=task_type,
                title=f"Investigate: {gap.get('description', '')[:50]}",
                description=gap.get('description', ''),
                target_entities=[],  # Would extract from gap
                priority=priority,
                expected_gain=expected_gain,
                estimated_effort=0.3,
                created_at=datetime.now(),
                due_at=datetime.now() + timedelta(hours=24)
            )
            tasks.append(task)
        
        # Sort by priority and expected gain
        tasks.sort(
            key=lambda t: (t.priority.value, -t.expected_gain)
        )
        
        return tasks[:self.max_tasks_per_iteration]

    def _infer_task_type(self, gap: Dict) -> TaskType:
        """Infer task type from gap description."""
        desc = gap.get('description', '').lower()
        
        if 'relationship' in desc:
            return TaskType.RELATIONSHIP_INFERENCE
        elif 'cluster' in desc or 'group' in desc:
            return TaskType.CLUSTER_ANALYSIS
        elif 'confidence' in desc or 'uncertain' in desc:
            return TaskType.CONFIDENCE_VALIDATION
        elif 'anomal' in desc or 'unusual' in desc:
            return TaskType.ANOMALY_INVESTIGATION
        elif 'cross' in desc or 'verify' in desc:
            return TaskType.CROSS_REFERENCE
        else:
            return TaskType.ENTITY_SEARCH

    def _calculate_priority(self, gap: Dict) -> TaskPriority:
        """Calculate task priority based on gap importance."""
        priority_hint = gap.get('priority', 'medium').lower()
        
        if 'critical' in priority_hint or 'contradiction' in gap.get('description', '').lower():
            return TaskPriority.CRITICAL
        elif 'high' in priority_hint or 'important' in priority_hint:
            return TaskPriority.HIGH
        elif 'low' in priority_hint:
            return TaskPriority.LOW
        else:
            return TaskPriority.MEDIUM

    def _estimate_information_gain(self, gap: Dict) -> float:
        """Estimate expected information gain from investigating gap."""
        desc = gap.get('description', '').lower()
        
        if any(term in desc for term in ['critical', 'contradiction', 'conflict']):
            return 0.9
        elif any(term in desc for term in ['relationship', 'connected']):
            return 0.7
        elif any(term in desc for term in ['cluster', 'pattern']):
            return 0.6
        else:
            return 0.5

    async def _dedup_and_store_tasks(self, new_tasks: List[InvestigationTask]) -> None:
        """Deduplicate tasks and store new ones."""
        try:
            for task in new_tasks:
                # Check for duplicates
                is_duplicate = await self._is_duplicate_task(task)
                if not is_duplicate:
                    self.pending_tasks[task.id] = task
                    await self.memory_store.store_task(task)
                    logger.info(f"Task created: {task.id}")
                else:
                    logger.debug(f"Duplicate task filtered: {task.title}")
        except Exception as e:
            logger.error(f"Failed to store tasks: {str(e)}")

    async def _is_duplicate_task(self, task: InvestigationTask) -> bool:
        """Check if task is duplicate of existing task."""
        try:
            for existing in self.pending_tasks.values():
                # Simple string similarity check
                from difflib import SequenceMatcher
                sim = SequenceMatcher(
                    None,
                    task.title.lower(),
                    existing.title.lower()
                ).ratio()
                
                if sim > self.duplicate_threshold:
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to check for duplicates: {str(e)}")
            return False

    async def _get_executable_tasks(self) -> List[InvestigationTask]:
        """Get tasks ready for execution."""
        try:
            executable = [
                task for task in self.pending_tasks.values()
                if task.status == "pending" and task.priority.value <= 2  # HIGH and CRITICAL
            ]
            return sorted(executable, key=lambda t: t.priority.value)
        except Exception as e:
            logger.error(f"Failed to get executable tasks: {str(e)}")
            return []

    async def _dispatch_tasks(self, tasks: List[InvestigationTask]) -> None:
        """Dispatch tasks for execution."""
        try:
            for task in tasks[:5]:  # Process top 5
                logger.info(f"Executing task: {task.id}")
                task.status = "executing"
                
                # Execute task based on type
                result = await self._execute_task(task)
                
                if result:
                    task.result = result
                    task.status = "completed"
                    await self.memory_store.update_task_result(task.id, result)
        except Exception as e:
            logger.error(f"Failed to dispatch tasks: {str(e)}")

    async def _execute_task(self, task: InvestigationTask) -> Optional[str]:
        """Execute a single investigation task."""
        try:
            if task.type == TaskType.ENTITY_SEARCH:
                return await self._search_entity(task)
            elif task.type == TaskType.RELATIONSHIP_INFERENCE:
                return await self._infer_relationships(task)
            elif task.type == TaskType.CLUSTER_ANALYSIS:
                return await self._analyze_clusters(task)
            elif task.type == TaskType.CONFIDENCE_VALIDATION:
                return await self._validate_confidence(task)
            else:
                return None
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            return None

    async def _search_entity(self, task: InvestigationTask) -> str:
        """Search for entities mentioned in task."""
        # Placeholder: would search external sources
        return f"Search completed for {task.title}"

    async def _infer_relationships(self, task: InvestigationTask) -> str:
        """Infer relationships between entities."""
        # Placeholder: would use LLM to infer relationships
        return f"Inferred relationships for {task.title}"

    async def _analyze_clusters(self, task: InvestigationTask) -> str:
        """Analyze entity clusters."""
        clusters = self.graph_manager.detect_clusters()
        return f"Found {len(clusters)} clusters"

    async def _validate_confidence(self, task: InvestigationTask) -> str:
        """Validate confidence scores."""
        # Placeholder: would re-evaluate confidence
        return f"Confidence validation completed for {task.title}"

    def get_task_statistics(self) -> Dict:
        """Get task generation statistics."""
        pending = [t for t in self.pending_tasks.values() if t.status == "pending"]
        executing = [t for t in self.pending_tasks.values() if t.status == "executing"]
        completed = [t for t in self.pending_tasks.values() if t.status == "completed"]
        
        return {
            "pending": len(pending),
            "executing": len(executing),
            "completed": len(completed),
            "total": len(self.pending_tasks)
        }
