"""Task decomposition and planning mechanism."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PlanStatus(Enum):
    """Status of a plan."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(Enum):
    """Status of a plan step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """A single step in a plan."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    status: StepStatus = StepStatus.PENDING
    result: str | None = None
    error: str | None = None
    dependencies: list[str] = field(default_factory=list)

    def can_execute(self, completed_steps: set[str]) -> bool:
        """Check if this step can be executed based on dependencies."""
        return all(dep in completed_steps for dep in self.dependencies)


@dataclass
class Plan:
    """A plan containing multiple steps for task execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    current_step_index: int = 0
    created_at: str = ""
    completed_at: str | None = None

    def get_pending_steps(self) -> list[PlanStep]:
        """Get all pending steps."""
        return [s for s in self.steps if s.status == StepStatus.PENDING]

    def get_next_step(self) -> PlanStep | None:
        """Get the next step to execute."""
        # Find the first pending step whose dependencies are met
        completed = {s.id for s in self.steps if s.status == StepStatus.COMPLETED}
        for step in self.steps:
            if step.status == StepStatus.PENDING and step.can_execute(completed):
                return step
        return None

    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return all(s.status == StepStatus.COMPLETED for s in self.steps)

    def get_progress(self) -> tuple[int, int]:
        """Get progress as (completed, total)."""
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        return completed, len(self.steps)


class TaskPlanner:
    """
    Task decomposition and planning mechanism.

    This class provides explicit task decomposition by breaking down
    complex tasks into smaller, manageable steps and creating
    executable plans.
    """

    def __init__(self):
        self._plans: dict[str, Plan] = {}
        self._current_plan_id: str | None = None

    def create_plan(
        self,
        name: str,
        description: str = "",
        steps: list[dict[str, Any]] | None = None,
    ) -> Plan:
        """
        Create a new plan.

        Args:
            name: Plan name
            description: Plan description
            steps: Optional list of step definitions. Each step can have:
                - description: str - Step description
                - dependencies: list[str] - IDs of steps this depends on

        Returns:
            The created Plan
        """
        plan = Plan(
            name=name,
            description=description,
        )

        if steps:
            for step_def in steps:
                step = PlanStep(
                    description=step_def.get("description", ""),
                    dependencies=step_def.get("dependencies", []),
                )
                plan.steps.append(step)

        self._plans[plan.id] = plan
        return plan

    def decompose_task(
        self,
        task: str,
        max_steps: int = 10,
    ) -> list[str]:
        """
        Decompose a complex task into smaller steps.

        This is a simple heuristic-based decomposition. In a real
        implementation, this could use an LLM to analyze the task
        and break it down intelligently.

        Args:
            task: The complex task to decompose
            max_steps: Maximum number of steps to generate

        Returns:
            List of step descriptions
        """
        # Simple decomposition based on common patterns
        steps = []

        # Keywords that often indicate distinct phases
        phase_markers = [
            "first", "then", "next", "finally", "lastly",
            "step 1", "step 2", "step 3",
            "1.", "2.", "3.",
            "and then", "after that", "before",
            "analyze", "review", "check",
            "create", "update", "delete",
            "test", "verify", "validate",
        ]

        # Check if the task already contains explicit steps
        task_lower = task.lower()
        has_explicit_steps = any(marker in task_lower for marker in phase_markers[:8])

        if has_explicit_steps:
            # Try to extract explicit steps
            import re
            # Split by common separators
            parts = re.split(r'(?:,|\.|;|(?:and\s+)?then\s+|(?:and\s+)?next\s+|(?:and\s+)?finally\s+)', task, flags=re.IGNORECASE)
            for part in parts:
                part = part.strip()
                if part and len(part) > 10:
                    # Clean up the step
                    step = re.sub(r'^(?:step\s*\d+[\.):]?\s*)', '', part, flags=re.IGNORECASE)
                    step = re.sub(r'^(?:\d+[\.):]\s*)', '', step)
                    if step:
                        steps.append(step.capitalize())
        else:
            # Generate implicit steps based on task type
            task_lower = task.lower()

            if any(kw in task_lower for kw in ["search", "find", "look for"]):
                steps.append("Identify search criteria and sources")
                steps.append("Execute search queries")
                steps.append("Compile and review results")

            if any(kw in task_lower for kw in ["create", "build", "make", "generate"]):
                steps.append("Define requirements and specifications")
                steps.append("Implement the solution")
                steps.append("Verify the implementation")

            if any(kw in task_lower for kw in ["fix", "debug", "repair", "resolve"]):
                steps.append("Identify the problem and root cause")
                steps.append("Implement the fix")
                steps.append("Test the solution")

            if any(kw in task_lower for kw in ["analyze", "review", "examine"]):
                steps.append("Gather relevant data")
                steps.append("Perform analysis")
                steps.append("Summarize findings")

            if any(kw in task_lower for kw in ["update", "modify", "change"]):
                steps.append("Review current state")
                steps.append("Make necessary changes")
                steps.append("Verify changes")

            # If no specific pattern matched, create generic steps
            if not steps:
                steps.append("Understand the task requirements")
                steps.append("Break down into actionable items")
                steps.append("Execute the plan")
                steps.append("Verify results")

        # Limit to max_steps
        return steps[:max_steps]

    def add_step(
        self,
        plan_id: str,
        description: str,
        dependencies: list[str] | None = None,
    ) -> PlanStep | None:
        """
        Add a step to an existing plan.

        Args:
            plan_id: ID of the plan
            description: Step description
            dependencies: List of step IDs this depends on

        Returns:
            The created step, or None if plan not found
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        step = PlanStep(
            description=description,
            dependencies=dependencies or [],
        )
        plan.steps.append(step)
        return step

    def get_plan(self, plan_id: str) -> Plan | None:
        """Get a plan by ID."""
        return self._plans.get(plan_id)

    def get_all_plans(self) -> list[Plan]:
        """Get all plans."""
        return list(self._plans.values())

    def start_plan(self, plan_id: str) -> bool:
        """
        Start executing a plan.

        Args:
            plan_id: ID of the plan to start

        Returns:
            True if plan was started, False if not found or already running
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return False

        if plan.status != PlanStatus.PENDING and plan.status != PlanStatus.PAUSED:
            return False

        plan.status = PlanStatus.IN_PROGRESS
        self._current_plan_id = plan_id
        return True

    def execute_step(
        self,
        plan_id: str,
        step_id: str | None = None,
        result: str | None = None,
        error: str | None = None,
    ) -> PlanStep | None:
        """
        Mark a step as completed (or failed).

        Args:
            plan_id: ID of the plan
            step_id: ID of the step, or None for next pending step
            result: Result of step execution
            error: Error message if step failed

        Returns:
            The executed step, or None if not found
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        # Find the step
        if step_id:
            step = next((s for s in plan.steps if s.id == step_id), None)
        else:
            step = plan.get_next_step()

        if not step:
            return None

        # Update step status
        if error:
            step.status = StepStatus.FAILED
            step.error = error
            plan.status = PlanStatus.FAILED
        else:
            step.status = StepStatus.COMPLETED
            step.result = result

            # Check if plan is complete
            if plan.is_complete():
                plan.status = PlanStatus.COMPLETED
                plan.completed_at = "completed"
                self._current_plan_id = None

        return step

    def cancel_plan(self, plan_id: str) -> bool:
        """
        Cancel a plan.

        Args:
            plan_id: ID of the plan to cancel

        Returns:
            True if plan was cancelled, False if not found
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return False

        plan.status = PlanStatus.CANCELLED

        # Mark all pending steps as skipped
        for step in plan.steps:
            if step.status == StepStatus.PENDING:
                step.status = StepStatus.SKIPPED

        if self._current_plan_id == plan_id:
            self._current_plan_id = None

        return True

    def pause_plan(self, plan_id: str) -> bool:
        """
        Pause a running plan.

        Args:
            plan_id: ID of the plan to pause

        Returns:
            True if plan was paused, False if not found
        """
        plan = self._plans.get(plan_id)
        if not plan or plan.status != PlanStatus.IN_PROGRESS:
            return False

        plan.status = PlanStatus.PAUSED
        self._current_plan_id = None
        return True

    def resume_plan(self, plan_id: str) -> bool:
        """
        Resume a paused plan.

        Args:
            plan_id: ID of the plan to resume

        Returns:
            True if plan was resumed, False if not found
        """
        plan = self._plans.get(plan_id)
        if not plan or plan.status != PlanStatus.PAUSED:
            return False

        plan.status = PlanStatus.IN_PROGRESS
        self._current_plan_id = plan_id
        return True

    def get_plan_status(self, plan_id: str) -> dict[str, Any] | None:
        """
        Get the status of a plan.

        Args:
            plan_id: ID of the plan

        Returns:
            Dictionary with plan status, or None if not found
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        completed, total = plan.get_progress()
        next_step = plan.get_next_step()

        return {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "status": plan.status.value,
            "progress": {
                "completed": completed,
                "total": total,
                "percentage": (completed / total * 100) if total > 0 else 0,
            },
            "current_step": {
                "id": next_step.id,
                "description": next_step.description,
            } if next_step else None,
            "steps": [
                {
                    "id": s.id,
                    "description": s.description,
                    "status": s.status.value,
                    "result": s.result,
                    "error": s.error,
                }
                for s in plan.steps
            ],
        }

    def delete_plan(self, plan_id: str) -> bool:
        """
        Delete a plan.

        Args:
            plan_id: ID of the plan to delete

        Returns:
            True if plan was deleted, False if not found
        """
        if plan_id in self._plans:
            del self._plans[plan_id]
            if self._current_plan_id == plan_id:
                self._current_plan_id = None
            return True
        return False

    def get_current_plan(self) -> Plan | None:
        """Get the currently executing plan."""
        if self._current_plan_id:
            return self._plans.get(self._current_plan_id)
        return None
