"""Tests for PlanTool."""

import pytest

from nanobot.agent.planner import PlanStatus, StepStatus, TaskPlanner
from nanobot.agent.tools.plan import PlanTool


class TestPlanTool:
    """Tests for PlanTool class."""

    @pytest.fixture
    def planner(self):
        """Create a fresh planner for each test."""
        return TaskPlanner()

    @pytest.fixture
    def tool(self, planner):
        """Create a PlanTool with the planner."""
        return PlanTool(planner)

    @pytest.mark.asyncio
    async def test_create_plan(self, tool, planner):
        """Test creating a plan via the tool."""
        result = await tool.execute(action="create", name="Test Plan", description="A test")

        assert "Created plan" in result
        assert "Test Plan" in result
        assert planner.get_all_plans()

    @pytest.mark.asyncio
    async def test_decompose_task(self, tool):
        """Test decomposing a task."""
        result = await tool.execute(
            action="decompose", task="Search for Python tutorials and create a summary"
        )

        assert "Decomposed" in result
        assert "steps:" in result

    @pytest.mark.asyncio
    async def test_add_step(self, tool, planner):
        """Test adding a step."""
        plan = planner.create_plan(name="Test")
        result = await tool.execute(
            action="add_step", plan_id=plan.id, step_description="First step"
        )

        assert "Added step" in result

    @pytest.mark.asyncio
    async def test_add_step_no_plan_id(self, tool):
        """Test adding step without plan_id."""
        result = await tool.execute(action="add_step", step_description="Step")

        assert "Error: plan_id is required" in result

    @pytest.mark.asyncio
    async def test_start_plan(self, tool, planner):
        """Test starting a plan."""
        plan = planner.create_plan(name="Test")
        planner.add_step(plan.id, "Step 1")

        result = await tool.execute(action="start", plan_id=plan.id)

        assert "Started" in result
        assert plan.status == PlanStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_complete_step(self, tool, planner):
        """Test completing a step."""
        plan = planner.create_plan(name="Test")
        step = planner.add_step(plan.id, "Step 1")
        planner.start_plan(plan.id)

        result = await tool.execute(
            action="complete_step", plan_id=plan.id, step_id=step.id, result="Done!"
        )

        assert "completed" in result.lower()

    @pytest.mark.asyncio
    async def test_complete_step_with_error(self, tool, planner):
        """Test completing step with error."""
        plan = planner.create_plan(name="Test")
        step = planner.add_step(plan.id, "Step 1")
        planner.start_plan(plan.id)

        result = await tool.execute(
            action="complete_step", plan_id=plan.id, step_id=step.id, error="Failed"
        )

        assert "failed" in result.lower()

    @pytest.mark.asyncio
    async def test_cancel_plan(self, tool, planner):
        """Test cancelling a plan."""
        plan = planner.create_plan(name="Test")
        planner.add_step(plan.id, "Step 1")
        planner.start_plan(plan.id)

        result = await tool.execute(action="cancel", plan_id=plan.id)

        assert "Cancelled" in result
        assert plan.status == PlanStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_pause_plan(self, tool, planner):
        """Test pausing a plan."""
        plan = planner.create_plan(name="Test")
        planner.add_step(plan.id, "Step 1")
        planner.start_plan(plan.id)

        result = await tool.execute(action="pause", plan_id=plan.id)

        assert "Paused" in result
        assert plan.status == PlanStatus.PAUSED

    @pytest.mark.asyncio
    async def test_resume_plan(self, tool, planner):
        """Test resuming a plan."""
        plan = planner.create_plan(name="Test")
        planner.add_step(plan.id, "Step 1")
        planner.start_plan(plan.id)
        planner.pause_plan(plan.id)

        result = await tool.execute(action="resume", plan_id=plan.id)

        assert "Resumed" in result
        assert plan.status == PlanStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_get_status(self, tool, planner):
        """Test getting plan status."""
        plan = planner.create_plan(name="Test Plan")
        planner.add_step(plan.id, "Step 1")

        result = await tool.execute(action="status", plan_id=plan.id)

        assert "Test Plan" in result
        assert "pending" in result

    @pytest.mark.asyncio
    async def test_list_plans(self, tool, planner):
        """Test listing all plans."""
        planner.create_plan(name="Plan 1")
        planner.create_plan(name="Plan 2")

        result = await tool.execute(action="list")

        assert "Plans" in result
        assert "Plan 1" in result
        assert "Plan 2" in result

    @pytest.mark.asyncio
    async def test_delete_plan(self, tool, planner):
        """Test deleting a plan."""
        plan = planner.create_plan(name="Test")

        result = await tool.execute(action="delete", plan_id=plan.id)

        assert "Deleted" in result
        assert planner.get_plan(plan.id) is None

    @pytest.mark.asyncio
    async def test_unknown_action(self, tool):
        """Test handling unknown action."""
        result = await tool.execute(action="unknown")

        assert "Unknown action" in result


class TestPlanToolIntegration:
    """Integration tests for PlanTool with full workflow."""

    @pytest.mark.asyncio
    async def test_full_plan_workflow(self):
        """Test a complete plan workflow."""
        planner = TaskPlanner()
        tool = PlanTool(planner)

        # 1. Decompose a task
        result = await tool.execute(
            action="decompose", task="Fix the login bug and test it"
        )
        assert "Decomposed" in result

        # 2. Create a plan
        result = await tool.execute(action="create", name="Fix Login Bug")
        assert "Created plan" in result

        # Get plan ID from result
        plans = planner.get_all_plans()
        plan_id = plans[0].id

        # 3. Add steps
        await tool.execute(action="add_step", plan_id=plan_id, step_description="Identify the bug")
        await tool.execute(action="add_step", plan_id=plan_id, step_description="Implement fix")
        await tool.execute(action="add_step", plan_id=plan_id, step_description="Test the solution")

        # 4. Start the plan
        result = await tool.execute(action="start", plan_id=plan_id)
        assert "Started" in result

        # 5. Get status
        result = await tool.execute(action="status", plan_id=plan_id)
        assert "in_progress" in result
        assert "Identify" in result

        # 6. Complete first step
        result = await tool.execute(
            action="complete_step", plan_id=plan_id, result="Found the issue in auth.py"
        )
        assert "completed" in result.lower()

        # 7. Complete second step
        result = await tool.execute(
            action="complete_step", plan_id=plan_id, result="Fixed the code"
        )
        assert "completed" in result.lower()

        # 8. Complete third step
        result = await tool.execute(
            action="complete_step", plan_id=plan_id, result="All tests pass"
        )
        assert "complete" in result.lower() or "completed" in result.lower()

        # 9. Verify plan is complete
        plan = planner.get_plan(plan_id)
        assert plan.status == PlanStatus.COMPLETED
