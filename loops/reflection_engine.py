"""Self-reflection and continuous improvement engine."""

import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ReflectionResult:
    """Result of reflection analysis."""
    timestamp: datetime
    analysis: str
    corrections: List[str]
    confidence_adjustments: Dict[str, float]
    duplicate_findings: List[Dict]
    recommended_actions: List[str]


class ReflectionEngine:
    """Continuously reviews and improves previous conclusions."""

    def __init__(self, config: Dict, graph_manager, memory_store, llm_client):
        self.config = config
        self.graph_manager = graph_manager
        self.memory_store = memory_store
        self.llm_client = llm_client
        self.reflection_interval = config.get("run_interval_seconds", 300)
        self.review_batch_size = config.get("review_batch_size", 50)
        self.deep_analysis_threshold = config.get("deep_analysis_threshold", 0.4)

    async def run_reflection_loop(self) -> None:
        """Main reflection engine loop."""
        while True:
            try:
                logger.info("Starting reflection cycle")
                
                # Get recent analyses
                recent_analyses = await self._fetch_recent_analyses()
                
                if not recent_analyses:
                    logger.debug("No recent analyses to review")
                    await asyncio.sleep(self.reflection_interval)
                    continue
                
                # Perform reflection
                for analysis in recent_analyses:
                    result = await self._reflect_on_analysis(analysis)
                    if result:
                        await self._apply_corrections(result)
                        await self._store_reflection_result(result)
                
                # Deep analysis on low-confidence items
                low_confidence = await self._identify_low_confidence_conclusions()
                if low_confidence:
                    logger.info(f"Analyzing {len(low_confidence)} low-confidence conclusions")
                    for conclusion in low_confidence:
                        deep_analysis = await self._perform_deep_analysis(conclusion)
                        if deep_analysis:
                            await self._store_reflection_result(deep_analysis)
                
            except Exception as e:
                logger.error(f"Error in reflection loop: {str(e)}", exc_info=True)
            
            await asyncio.sleep(self.reflection_interval)

    async def _fetch_recent_analyses(self, limit: int = None) -> List[Dict]:
        """Fetch recent analyses from memory store."""
        try:
            limit = limit or self.review_batch_size
            return await self.memory_store.get_recent_analyses(limit=limit)
        except Exception as e:
            logger.error(f"Failed to fetch recent analyses: {str(e)}")
            return []

    async def _reflect_on_analysis(self, analysis: Dict) -> Optional[ReflectionResult]:
        """Reflect on a previous analysis."""
        try:
            prompt = self._generate_reflection_prompt(analysis)
            reflection_response = await self.llm_client.generate(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.8
            )
            
            return await self._parse_reflection_response(reflection_response, analysis)
        except Exception as e:
            logger.error(f"Failed to reflect on analysis: {str(e)}")
            return None

    def _generate_reflection_prompt(self, analysis: Dict) -> str:
        """Generate reflection prompt."""
        previous_analysis = analysis.get("analysis", "")
        observations = analysis.get("observations", [])
        
        observations_text = "\n".join([f"- {obs}" for obs in observations])
        
        prompt = f"""
Review this previous analysis and find areas for improvement:

Original observations:
{observations_text}

Previous analysis:
{previous_analysis}

Identify:
1. Mistakes or incorrect assumptions
2. Missing connections or overlooked patterns
3. Outdated or superseded conclusions
4. Duplicate entities or relationships that should be merged
5. Confidence scoring issues
6. Recommended corrections or new investigations

Provide a structured review with:
- Type of issue (mistake/missing/outdated/duplicate/confidence)
- Description
- Suggested correction
- Impact on overall understanding
        """
        return prompt

    async def _parse_reflection_response(self, response: str, original_analysis: Dict) -> ReflectionResult:
        """Parse LLM reflection response into structured format."""
        # Simple parsing - in production would use structured outputs
        corrections = []
        confidence_adjustments = {}
        duplicate_findings = []
        recommended_actions = []
        
        lines = response.split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if "mistake" in line.lower() or "incorrect" in line.lower():
                corrections.append(line)
            elif "duplicate" in line.lower():
                duplicate_findings.append({"description": line})
            elif "confidence" in line.lower():
                confidence_adjustments["note"] = line
            elif "recommendation" in line.lower() or "suggest" in line.lower():
                recommended_actions.append(line)
        
        return ReflectionResult(
            timestamp=datetime.now(),
            analysis=response,
            corrections=corrections,
            confidence_adjustments=confidence_adjustments,
            duplicate_findings=duplicate_findings,
            recommended_actions=recommended_actions
        )

    async def _apply_corrections(self, reflection: ReflectionResult) -> None:
        """Apply corrections from reflection to graph."""
        try:
            # Handle duplicate findings
            for duplicate in reflection.duplicate_findings:
                logger.info(f"Processing duplicate: {duplicate}")
                # Would merge nodes in graph
            
            # Update confidence scores
            if reflection.confidence_adjustments:
                logger.info(f"Adjusting confidence scores: {reflection.confidence_adjustments}")
                # Would update confidence in graph
            
        except Exception as e:
            logger.error(f"Failed to apply corrections: {str(e)}")

    async def _identify_low_confidence_conclusions(self) -> List[Dict]:
        """Find conclusions below deep analysis threshold."""
        try:
            threshold = self.deep_analysis_threshold
            # Placeholder: would query graph for nodes/relationships with low confidence
            return []
        except Exception as e:
            logger.error(f"Failed to identify low-confidence items: {str(e)}")
            return []

    async def _perform_deep_analysis(self, conclusion: Dict) -> Optional[ReflectionResult]:
        """Perform deep analysis on low-confidence conclusion."""
        try:
            prompt = f"""
This conclusion has low confidence. Perform a deep analysis:

Conclusion: {conclusion.get('text', '')}
Current confidence: {conclusion.get('confidence', 0.0)}

Investigate:
1. What evidence supports this conclusion?
2. What evidence contradicts it?
3. What additional data would help?
4. Should the confidence be higher or lower?
5. Are there alternative explanations?

Provide a detailed assessment.
            """
            
            response = await self.llm_client.generate(
                prompt=prompt,
                max_tokens=800,
                temperature=0.9
            )
            
            result = await self._parse_reflection_response(response, conclusion)
            return result
        except Exception as e:
            logger.error(f"Failed to perform deep analysis: {str(e)}")
            return None

    async def _store_reflection_result(self, result: ReflectionResult) -> None:
        """Store reflection result in memory."""
        try:
            await self.memory_store.store_reflection(
                timestamp=result.timestamp.isoformat(),
                analysis=result.analysis,
                corrections=result.corrections,
                duplicate_findings=result.duplicate_findings,
                recommended_actions=result.recommended_actions
            )
            logger.info("Reflection result stored")
        except Exception as e:
            logger.error(f"Failed to store reflection result: {str(e)}")

    async def detect_contradictions(self) -> List[Dict]:
        """Find contradictory conclusions in graph."""
        try:
            # Query graph for contradictory relationships
            # e.g., "A WORKED_AT B" and "A WORKED_AT C" for incompatible dates
            contradictions = []
            logger.info(f"Found {len(contradictions)} contradictions")
            return contradictions
        except Exception as e:
            logger.error(f"Failed to detect contradictions: {str(e)}")
            return []

    async def merge_duplicate_entities(self, entity_pairs: List[tuple]) -> None:
        """Merge identified duplicate entities."""
        try:
            for entity1_id, entity2_id in entity_pairs:
                logger.info(f"Merging {entity1_id} and {entity2_id}")
                # Would merge nodes in Neo4j
                # Combine properties, relationships, update confidence
        except Exception as e:
            logger.error(f"Failed to merge entities: {str(e)}")

    def get_reflection_statistics(self) -> Dict:
        """Get reflection engine statistics."""
        # Placeholder
        return {
            "total_reflections": 0,
            "corrections_made": 0,
            "duplicates_merged": 0,
            "average_confidence_adjustment": 0.0
        }
