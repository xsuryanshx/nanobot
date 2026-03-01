"""Tests for task decomposition and planning mechanism."""

import pytest

from nanobot.agent.planner import Plan, PlanStep, PlanStatus, StepStatus, TaskPlanner


class TestPlanStep:
    """Tests for PlanStep class."""

    def test_create_step(self):
        """Test creating a step."""
        step = PlanStep(description="Test step")
        assert step.description == "Test step"
        assert step.status == StepStatus.PENDING
        assert step.result is None
        assert step.error is None

    def test_step_with_dependencies(self):
        """Test step with dependencies."""
        step = PlanStep(description="Step 2", dependencies=["step-1", "step-2"])
        assert step.dependencies == ["step-1", "step-2"]

    def test_can_execute_no_dependencies(self):
        """Test can_execute with no dependencies."""
        step = PlanStep(description="Test step")
        assert step.can_execute(set()) is True
        assert step.can_execute({"any"}) is True

    def test_can_execute_with_dependencies(self):
        """Test can_execute with dependencies."""
        step = PlanStep(description="Step 3", dependencies=["step-1", "step-2"])
        assert step.can_execute(set()) is False
        assert step.can_execute({"step-1"}) is False
        assert step.can_execute({"step-1", "step-2"}) is True
        assert step.can_execute({"step-1", "step-2", "other"}) is True


class TestPlan:
    """Tests for Plan class."""

    def test_create_plan(self):
        """Test creating a plan."""
        plan = Plan(name="Test Plan", description="A test plan")
        assert plan.name == "Test Plan"
        assert plan.description == "A test plan"
        assert plan.status == PlanStatus.PENDING
        assert plan.steps == []

    def test_get_pending_steps(self):
        """Test getting pending steps."""
        plan = Plan(name="Test")
        step1 = PlanStep(description="Step 1")
        step2 = PlanStep(description="Step 2")
        step3 = PlanStep(description="Step 3")
        step2.status = StepStatus.COMPLETED
        plan.steps = [step1, step2, step3]

        pending = plan.get_pending_steps()
        assert len(pending) == 2
        assert step1 in pending
        assert step3 in pending
        assert step2 not in pending

    def test_get_next_step_no_dependencies(self):
        """Test getting next step with no dependencies."""
        plan = Plan(name="Test")
        plan.steps = [
            PlanStep(description="Step 1"),
            PlanStep(description="Step 2"),
            PlanStep(description="Step 3"),
        ]

        next_step = plan.get_next_step()
        assert next_step is not None
        assert next_step.description == "Step 1"

    def test_get_next_step_with_dependencies(self):
        """Test getting next step with dependencies."""
        step1 = PlanStep(id="s1", description="Step 1")
        step2 = PlanStep(id="s2", description="Step 2", dependencies=["s1"])
        step3 = PlanStep(id="s3", description="Step 3", dependencies=["s1"])
        step4 = PlanStep(id="s4", description="Step 4", dependencies=["s2", "s3"])

        plan = Plan(name="Test", steps=[step1, step2, step3, step4])

        # First step should be s1
        next_step = plan.get_next_step()
        assert next_step.id == "s1"

        # Complete s1, next should be either s2 or s3
        step1.status = StepStatus.COMPLETED
        next_step = plan.get_next_step()
        assert next_step.id in ["s2", "s3"]

    def test_is_complete(self):
        """Test plan completion check."""
        plan = Plan(name="Test")
        plan.steps = [
            PlanStep(description="Step 1"),
            PlanStep(description="Step 2"),
        ]

        assert plan.is_complete() is False

        plan.steps[0].status = StepStatus.COMPLETED
        assert plan.is_complete() is False

        plan.steps[1].status = StepStatus.COMPLETED
        assert plan.is_complete() is True

    def test_get_progress(self):
        """Test getting progress."""
        plan = Plan(name="Test")
        plan.steps = [
            PlanStep(description="Step 1"),
            PlanStep(description="Step 2"),
            PlanStep(description="Step 3"),
            PlanStep(description="Step 4"),
        ]

        plan.steps[0].status = StepStatus.COMPLETED
        plan.steps[1].status = StepStatus.COMPLETED

        completed, total = plan.get_progress()
        assert completed == 2
        assert total == 4


class TestTaskPlanner:
    """Tests for TaskPlanner class."""

    def test_create_planner(self):
        """Test creating a planner."""
        planner = TaskPlanner()
        assert planner.get_all_plans() == []

    def test_create_plan(self):
        """Test creating a plan."""
        planner = TaskPlanner()
        plan = planner.create_plan(name="My Plan", description="Test description")
        assert plan.name == "My Plan"
        assert plan.description == "Test description"

        # Plan should be in the planner
        assert planner.get_plan(plan.id) is not None

    def test_create_plan_with_steps(self):
        """Test creating a plan with predefined steps."""
        planner = TaskPlanner()
        steps = [
            {"description": "Step 1"},
            {"description": "Step 2", "dependencies": []},
            {"description": "Step 3", "dependencies": ["step-0"]},
        ]
        plan = planner.create_plan(name="Test", steps=steps)
        assert len(plan.steps) == 3
        assert plan.steps[0].description == "Step 1"
        assert plan.steps[1].description == "Step 2"
        assert plan.steps[2].description == "Step 3"
        assert plan.steps[2].dependencies == ["step-0"]

    def test_add_step(self):
        """Test adding a step to a plan."""
        planner = TaskPlanner()
        plan = planner.create_plan(name="Test")
        step = planner.add_step(plan.id, "New step", ["dep1", "dep2"])

        assert step is not None
        assert step.description == "New step"
        assert step.dependencies == ["dep1", "dep2"]
        assert plan in planner.get_all_plans()

    def test_add_step_invalid_plan(self):
        """Test adding step to non-existent plan."""
        planner = TaskPlanner()
        step = planner.add_step("invalid-id", "New step")
        assert step is None

    def test_start_plan(self):
        """Test starting a plan."""
        planner = TaskPlanner()
        plan = planner.create_plan(name="Test")
        plan.steps.append(PlanStep(description="Step 1"))

        result = planner.start_plan(plan.id)
        assert result is True
        assert plan.status == PlanStatus.IN_PROGRESS
        assert planner.get_current_plan() is plan

    def test_start_invalid_plan(self):
        """Test starting invalid plan."""
        planner = TaskPlanner()
        result = planner.start_plan("invalid-id")
        assert result is False

    def test_start_already_running_plan(self):
        """Test starting an already running plan."""
        planner = TaskPlanner()
        plan = planner.create_plan(name="Test")
        planner.start_plan(plan.id)

        # Try to start again
        result = planner.start_plan(plan.id)
        assert result is False

    def test_execute_step(self):
        """Test executing a step."""
        planner = TaskPlanner()
        plan = planner.create_plan(name="Test")
        step = planner.add_step(plan.id, "Step 1")
        planner.start_plan(plan.id)

        executed = planner.execute_step(plan.id, step_id=step.id, result="Success!")
        assert executed is not None
        assert executed.status == StepStatus.COMPLETED
        assert executed.result == "Success!"

    def test_execute_step_with_error(self):
        """Test executing a step with error."""
        planner = TaskPlanner()
        plan = planner.create_plan(name="Test")
        step = planner.add_step(plan.id, "Step 1")
        planner.start_plan(plan.id)

        executed = planner.execute_step(plan.id, step_id=step.id, error="Something went wrong")
        assert executed is not None
        assert executed.status == StepStatus.FAILED
        assert executed.error == "Something went wrong"
        assert plan.status == PlanStatus.FAILED

    def test_execute_step_auto_advance(self):
        """Test auto-advancing to next step."""
        planner = TaskPlanner()
        plan = planner.create_plan(name="Test")
        step1 = planner.add_step(plan.id, "Step 1")
        step2 = planner.add_step(plan.id, "Step 2")
        planner.start_plan(plan.id)

        # Execute without specifying step_id - should auto-advance
        executed = planner.execute_step(plan.id, result="Done 1")
        assert executed.id == step1.id

        # Get next step
        next_step = plan.get_next_step()
        assert next_step.id == step2.id

    def test_complete_plan(self):
        """Test completing entire plan."""
        planner = TaskPlanner()
        plan = planner.create_plan(name="Test")
        step1 = planner.add_step(plan.id, "Step 1")
        step2 = planner.add_step(plan.id, "Step 2")
        planner.start_plan(plan.id)

        planner.execute_step(plan.id, step_id=step1.id, result="Done")
        planner.execute_step(plan.id, step_id=step2.id, result="Done")

        assert plan.status == PlanStatus.COMPLETED
        assert plan.completed_at == "completed"
        assert planner.get_current_plan() is None

    def test_cancel_plan(self):
        """Test cancelling a plan."""
        planner = TaskPlanner()
        plan = planner.create_plan(name="Test")
        planner.add_step(plan.id, "Step 1")
        planner.add_step(plan.id, "Step 2")
        planner.start_plan(plan.id)

        result = planner.cancel_plan(plan.id)
        assert result is True
        assert plan.status == PlanStatus.CANCELLED

        # Steps should be marked as skipped
        for step in plan.steps:
            assert step.status == StepStatus.SKIPPED

    def test_pause_and_resume_plan(self):
        """Test pausing and resuming a plan."""
        planner = TaskPlanner()
        plan = planner.create_plan(name="Test")
        planner.add_step(plan.id, "Step 1")
        planner.start_plan(plan.id)

        # Pause
        result = planner.pause_plan(plan.id)
        assert result is True
        assert plan.status == PlanStatus.PAUSED

        # Resume
        result = planner.resume_plan(plan.id)
        assert result is True
        assert plan.status == PlanStatus.IN_PROGRESS

    def test_get_plan_status(self):
        """Test getting plan status."""
        planner = TaskPlanner()
        plan = planner.create_plan(name="Test Plan", description="A test")
        step1 = planner.add_step(plan.id, "Step 1")
        planner.add_step(plan.id, "Step 2")
        planner.start_plan(plan.id)

        status = planner.get_plan_status(plan.id)
        assert status is not None
        assert status["name"] == "Test Plan"
        assert status["description"] == "A test"
        assert status["status"] == "in_progress"
        assert status["progress"]["total"] == 2
        assert status["progress"]["completed"] == 0
        assert status["current_step"]["id"] == step1.id

    def test_delete_plan(self):
        """Test deleting a plan."""
        planner = TaskPlanner()
        plan = planner.create_plan(name="Test")

        result = planner.delete_plan(plan.id)
        assert result is True
        assert planner.get_plan(plan.id) is None

    def test_delete_invalid_plan(self):
        """Test deleting invalid plan."""
        planner = TaskPlanner()
        result = planner.delete_plan("invalid-id")
        assert result is False


class TestTaskDecomposition:
    """Tests for task decomposition."""

    def test_decompose_search_task(self):
        """Test decomposing a search task."""
        planner = TaskPlanner()
        steps = planner.decompose_task("Search for information about Python")

        assert len(steps) > 0
        assert any("search" in s.lower() for s in steps)

    def test_decompose_create_task(self):
        """Test decomposing a create task."""
        planner = TaskPlanner()
        steps = planner.decompose_task("Create a new file with content")

        assert len(steps) > 0

    def test_decompose_fix_task(self):
        """Test decomposing a fix task."""
        planner = TaskPlanner()
        steps = planner.decompose_task("Fix the bug in the code")

        assert len(steps) > 0

    def test_decompose_explicit_steps(self):
        """Test decomposing task with explicit steps."""
        planner = TaskPlanner()
        steps = planner.decompose_task(
            "First, analyze the requirements. Then, implement the solution. Finally, test it."
        )

        # Should extract explicit steps
        assert len(steps) >= 2

    def test_decompose_respects_max_steps(self):
        """Test that decompose respects max_steps limit."""
        planner = TaskPlanner()
        steps = planner.decompose_task("Do many things", max_steps=2)

        assert len(steps) <= 2
