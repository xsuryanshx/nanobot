# Tool Usage Notes

Tool signatures are provided automatically via function calling.
This file documents non-obvious constraints and usage patterns.

## exec — Safety Limits

- Commands have a configurable timeout (default 60s)
- Dangerous commands are blocked (rm -rf, format, dd, shutdown, etc.)
- Output is truncated at 10,000 characters
- `restrictToWorkspace` config can limit file access to the workspace

## cron — Scheduled Reminders

- Please refer to cron skill for usage.

## plan — Task Decomposition and Planning

The `plan` tool enables explicit task decomposition and structured planning for complex tasks.

### Actions

- **decompose**: Break down a complex task into smaller steps automatically
- **create**: Create a new plan with a name and description
- **add_step**: Add a step to an existing plan (supports dependencies)
- **start**: Begin executing a plan
- **execute_step**: Get the next step to execute
- **complete_step**: Mark a step as completed (with result or error)
- **cancel**: Cancel a running plan
- **pause**: Pause a running plan
- **resume**: Resume a paused plan
- **status**: Get detailed status of a plan including progress
- **list**: List all plans
- **delete**: Delete a plan

### Usage Example

```
# First decompose a complex task
plan(action="decompose", task="Fix the login bug and test it")

# Create a plan
plan(action="create", name="Fix Login Bug", description="Fix authentication issue")

# Add steps
plan(action="add_step", plan_id="<plan_id>", step_description="Identify the bug")
plan(action="add_step", plan_id="<plan_id>", step_description="Implement fix")
plan(action="add_step", plan_id="<plan_id>", step_description="Test the solution")

# Start execution
plan(action="start", plan_id="<plan_id>")

# Complete each step
plan(action="complete_step", plan_id="<plan_id>", result="Found issue in auth.py")
plan(action="complete_step", plan_id="<plan_id>", result="Fixed the code")
plan(action="complete_step", plan_id="<plan_id>", result="All tests pass")

# Check status
plan(action="status", plan_id="<plan_id>")
```

### Features

- **Step Dependencies**: Steps can depend on other steps, ensuring proper execution order
- **Progress Tracking**: Track completion percentage and current step
- **Plan Control**: Pause, resume, and cancel plans as needed
- **Error Handling**: Mark steps as failed with error messages
