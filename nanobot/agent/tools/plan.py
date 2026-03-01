"""Plan tool for task decomposition and planning."""

from typing import TYPE_CHECKING, Any

from nanobot.agent.tools.base import Tool
from nanobot.agent.planner import PlanStatus, StepStatus, TaskPlanner

if TYPE_CHECKING:
    from nanobot.agent.planner import Plan


class PlanTool(Tool):
    """
    Tool for creating and managing task plans.

    Use this tool when you need to break down a complex task into
    smaller steps and track progress through a structured plan.
    """

    def __init__(self, planner: TaskPlanner):
        self._planner = planner

    @property
    def name(self) -> str:
        return "plan"

    @property
    def description(self) -> str:
        return (
            "Create and manage task plans with explicit steps. "
            "Use this for complex tasks that need to be broken down into smaller steps. "
            "Supports creating plans, adding steps, executing plans, and tracking progress."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action to perform",
                    "enum": [
                        "create",
                        "decompose",
                        "add_step",
                        "start",
                        "execute_step",
                        "complete_step",
                        "cancel",
                        "pause",
                        "resume",
                        "status",
                        "list",
                        "delete",
                    ],
                },
                "plan_id": {
                    "type": "string",
                    "description": "ID of the plan (required for most actions)",
                },
                "name": {
                    "type": "string",
                    "description": "Plan name (for create action)",
                },
                "description": {
                    "type": "string",
                    "description": "Plan or step description",
                },
                "task": {
                    "type": "string",
                    "description": "Task to decompose into steps (for decompose action)",
                },
                "step_description": {
                    "type": "string",
                    "description": "Step description (for add_step action)",
                },
                "dependencies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of step IDs this step depends on",
                },
                "step_id": {
                    "type": "string",
                    "description": "ID of a specific step",
                },
                "result": {
                    "type": "string",
                    "description": "Result of step execution (for complete_step action)",
                },
                "error": {
                    "type": "string",
                    "description": "Error message if step failed (for complete_step action)",
                },
            },
            "required": ["action"],
        }

    async def execute(
        self,
        action: str,
        plan_id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        task: str | None = None,
        step_description: str | None = None,
        dependencies: list[str] | None = None,
        step_id: str | None = None,
        result: str | None = None,
        error: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Execute the requested plan action."""
        if action == "decompose":
            return await self._handle_decompose(task or description or "")
        elif action == "create":
            return self._handle_create(name or "Untitled Plan", description or "")
        elif action == "add_step":
            return self._handle_add_step(plan_id, step_description or description or "", dependencies)
        elif action == "start":
            return self._handle_start(plan_id)
        elif action == "execute_step":
            return self._handle_execute_step(plan_id, step_id)
        elif action == "complete_step":
            return self._handle_complete_step(plan_id, step_id, result, error)
        elif action == "cancel":
            return self._handle_cancel(plan_id)
        elif action == "pause":
            return self._handle_pause(plan_id)
        elif action == "resume":
            return self._handle_resume(plan_id)
        elif action == "status":
            return self._handle_status(plan_id)
        elif action == "list":
            return self._handle_list()
        elif action == "delete":
            return self._handle_delete(plan_id)
        else:
            return f"Unknown action: {action}"

    async def _handle_decompose(self, task: str) -> str:
        """Decompose a task into steps."""
        if not task:
            return "Error: No task provided for decomposition"

        steps = self._planner.decompose_task(task)
        if not steps:
            return "Could not decompose task into steps"

        output = f"Decomposed task into {len(steps)} steps:\n\n"
        for i, step in enumerate(steps, 1):
            output += f"{i}. {step}\n"

        output += "\nUse 'create' action to create a plan with these steps."
        return output

    def _handle_create(self, name: str, description: str) -> str:
        """Create a new plan."""
        plan = self._planner.create_plan(name=name, description=description)
        return f"Created plan '{plan.name}' with ID: {plan.id}\nUse 'add_step' to add steps or 'start' to begin execution."

    def _handle_add_step(
        self,
        plan_id: str | None,
        description: str,
        dependencies: list[str] | None,
    ) -> str:
        """Add a step to a plan."""
        if not plan_id:
            return "Error: plan_id is required"

        step = self._planner.add_step(plan_id, description, dependencies)
        if not step:
            return f"Error: Plan not found: {plan_id}"

        deps_info = f" (depends on: {', '.join(dependencies)})" if dependencies else ""
        return f"Added step to plan {plan_id}: {step.id} - '{description}'{deps_info}"

    def _handle_start(self, plan_id: str | None) -> str:
        """Start executing a plan."""
        if not plan_id:
            return "Error: plan_id is required"

        if self._planner.start_plan(plan_id):
            plan = self._planner.get_plan(plan_id)
            if plan:
                next_step = plan.get_next_step()
                if next_step:
                    return f"Started plan '{plan.name}' ({plan_id}). Next step: {next_step.description}"
                return f"Started plan '{plan.name}' ({plan_id}). No pending steps."
        return f"Error: Could not start plan {plan_id}. It may already be running or completed."

    def _handle_execute_step(self, plan_id: str | None, step_id: str | None = None) -> str:
        """Get the next step to execute."""
        if not plan_id:
            return "Error: plan_id is required"

        plan = self._planner.get_plan(plan_id)
        if not plan:
            return f"Error: Plan not found: {plan_id}"

        step = plan.get_next_step() if not step_id else next((s for s in plan.steps if s.id == step_id), None)
        if not step:
            return f"No step to execute in plan {plan_id}"

        return f"Step {step.id}: {step.description}"

    def _handle_complete_step(
        self,
        plan_id: str | None,
        step_id: str | None,
        result: str | None,
        error: str | None,
    ) -> str:
        """Mark a step as completed."""
        if not plan_id:
            return "Error: plan_id is required"

        step = self._planner.execute_step(plan_id, step_id, result, error)
        if not step:
            return f"Error: Could not complete step in plan {plan_id}"

        if error:
            plan = self._planner.get_plan(plan_id)
            status = plan.status.value if plan else "unknown"
            return f"Step {step.id} failed: {error}. Plan status: {status}"

        plan = self._planner.get_plan(plan_id)
        completed, total = plan.get_progress() if plan else (0, 0)

        if plan and plan.status == PlanStatus.COMPLETED:
            return f"Step {step.id} completed! Plan '{plan.name}' is now complete ({completed}/{total} steps)."

        next_step = plan.get_next_step() if plan else None
        if next_step:
            return f"Step {step.id} completed ({completed}/{total}). Next: {next_step.description}"
        return f"Step {step.id} completed ({completed}/{total})."

    def _handle_cancel(self, plan_id: str | None) -> str:
        """Cancel a plan."""
        if not plan_id:
            return "Error: plan_id is required"

        if self._planner.cancel_plan(plan_id):
            return f"Cancelled plan {plan_id}"
        return f"Error: Could not cancel plan {plan_id}"

    def _handle_pause(self, plan_id: str | None) -> str:
        """Pause a plan."""
        if not plan_id:
            return "Error: plan_id is required"

        if self._planner.pause_plan(plan_id):
            return f"Paused plan {plan_id}"
        return f"Error: Could not pause plan {plan_id}"

    def _handle_resume(self, plan_id: str | None) -> str:
        """Resume a plan."""
        if not plan_id:
            return "Error: plan_id is required"

        if self._planner.resume_plan(plan_id):
            plan = self._planner.get_plan(plan_id)
            if plan:
                next_step = plan.get_next_step()
                if next_step:
                    return f"Resumed plan {plan_id}. Next step: {next_step.description}"
                return f"Resumed plan {plan_id}."
        return f"Error: Could not resume plan {plan_id}"

    def _handle_status(self, plan_id: str | None) -> str:
        """Get plan status."""
        if not plan_id:
            return "Error: plan_id is required"

        status = self._planner.get_plan_status(plan_id)
        if not status:
            return f"Error: Plan not found: {plan_id}"

        output = f"Plan: {status['name']} ({status['id']})\n"
        output += f"Status: {status['status']}\n"
        output += f"Progress: {status['progress']['completed']}/{status['progress']['total']} "
        output += f"({status['progress']['percentage']:.0f}%)\n\n"

        if status.get("current_step"):
            output += f"Current: {status['current_step']['description']}\n\n"

        output += "Steps:\n"
        for step in status["steps"]:
            icon = {
                "pending": "[ ]",
                "in_progress": "[>]",
                "completed": "[✓]",
                "failed": "[✗]",
                "skipped": "[-]",
            }.get(step["status"], "[?]")
            output += f"  {icon} {step['id']}: {step['description']}"
            if step.get("result"):
                output += f" -> {step['result'][:50]}{'...' if len(step['result']) > 50 else ''}"
            elif step.get("error"):
                output += f" -> Error: {step['error']}"
            output += "\n"

        return output

    def _handle_list(self) -> str:
        """List all plans."""
        plans = self._planner.get_all_plans()
        if not plans:
            return "No plans found"

        output = f"Plans ({len(plans)}):\n\n"
        for plan in plans:
            completed, total = plan.get_progress()
            output += f"- {plan.id}: {plan.name} - {plan.status.value} ({completed}/{total} steps)\n"

        return output

    def _handle_delete(self, plan_id: str | None) -> str:
        """Delete a plan."""
        if not plan_id:
            return "Error: plan_id is required"

        if self._planner.delete_plan(plan_id):
            return f"Deleted plan {plan_id}"
        return f"Error: Could not delete plan {plan_id}"
