import pytest

from nanobot.cron.service import CronService
from nanobot.cron.types import CronSchedule


def test_add_job_rejects_unknown_timezone(tmp_path) -> None:
    service = CronService(tmp_path / "cron" / "jobs.json")

    with pytest.raises(ValueError, match="unknown timezone 'America/Vancovuer'"):
        service.add_job(
            name="tz typo",
            schedule=CronSchedule(kind="cron", expr="0 9 * * *", tz="America/Vancovuer"),
            message="hello",
        )

    assert service.list_jobs(include_disabled=True) == []


def test_add_job_accepts_valid_timezone(tmp_path) -> None:
    service = CronService(tmp_path / "cron" / "jobs.json")

    job = service.add_job(
        name="tz ok",
        schedule=CronSchedule(kind="cron", expr="0 9 * * *", tz="America/Vancouver"),
        message="hello",
    )

    assert job.schedule.tz == "America/Vancouver"
    assert job.state.next_run_at_ms is not None


def test_add_job_at_with_delete_after_run(tmp_path) -> None:
    """Test that one-time 'at' jobs can be configured to delete after running."""
    service = CronService(tmp_path / "cron" / "jobs.json")

    # Add a job with delete_after_run=True
    job = service.add_job(
        name="one-time",
        schedule=CronSchedule(kind="at", at_ms=2000000000000),  # Some future time
        message="hello",
        delete_after_run=True,
    )

    assert job.delete_after_run is True
    assert job.schedule.kind == "at"


def test_add_job_with_channel(tmp_path) -> None:
    """Test adding a job with a specific channel."""
    service = CronService(tmp_path / "cron" / "jobs.json")

    job = service.add_job(
        name="channel job",
        schedule=CronSchedule(kind="every", every_ms=60000),
        message="hello",
        channel="telegram",
        to="123456",
    )

    assert job.payload.channel == "telegram"
    assert job.payload.to == "123456"


def test_remove_job(tmp_path) -> None:
    """Test removing a job by ID."""
    service = CronService(tmp_path / "cron" / "jobs.json")

    job = service.add_job(
        name="to remove",
        schedule=CronSchedule(kind="every", every_ms=60000),
        message="hello",
    )

    job_id = job.id
    assert len(service.list_jobs()) == 1

    result = service.remove_job(job_id)
    assert result is True
    assert len(service.list_jobs()) == 0


def test_remove_nonexistent_job(tmp_path) -> None:
    """Test removing a job that doesn't exist returns False."""
    service = CronService(tmp_path / "cron" / "jobs.json")

    result = service.remove_job("nonexistent-id")
    assert result is False


def test_enable_disable_job(tmp_path) -> None:
    """Test enabling and disabling a job."""
    service = CronService(tmp_path / "cron" / "jobs.json")

    job = service.add_job(
        name="toggle job",
        schedule=CronSchedule(kind="every", every_ms=60000),
        message="hello",
    )

    assert job.enabled is True

    # Disable the job
    updated = service.enable_job(job.id, enabled=False)
    assert updated is not None
    assert updated.enabled is False

    # Enable the job again
    updated = service.enable_job(job.id, enabled=True)
    assert updated is not None
    assert updated.enabled is True


def test_list_jobs_includes_disabled(tmp_path) -> None:
    """Test that list_jobs with include_disabled shows disabled jobs."""
    service = CronService(tmp_path / "cron" / "jobs.json")

    job = service.add_job(
        name="to disable",
        schedule=CronSchedule(kind="every", every_ms=60000),
        message="hello",
    )

    service.enable_job(job.id, enabled=False)

    # Without include_disabled
    assert len(service.list_jobs()) == 0

    # With include_disabled
    jobs = service.list_jobs(include_disabled=True)
    assert len(jobs) == 1
    assert jobs[0].enabled is False


def test_status(tmp_path) -> None:
    """Test getting service status."""
    service = CronService(tmp_path / "cron" / "jobs.json")

    service.add_job(
        name="job1",
        schedule=CronSchedule(kind="every", every_ms=60000),
        message="hello",
    )

    service.add_job(
        name="job2",
        schedule=CronSchedule(kind="every", every_ms=120000),
        message="hello",
    )

    status = service.status()
    assert status["enabled"] is False  # Not started
    assert status["jobs"] == 2


def test_add_job_rejects_tz_with_non_cron(tmp_path) -> None:
    """Test that timezone can only be used with cron schedules."""
    service = CronService(tmp_path / "cron" / "jobs.json")

    with pytest.raises(ValueError, match="tz can only be used with cron schedules"):
        service.add_job(
            name="tz with every",
            schedule=CronSchedule(kind="every", every_ms=60000, tz="America/Vancouver"),
            message="hello",
        )


def test_compute_next_run_every(tmp_path) -> None:
    """Test computing next run for 'every' schedule."""
    service = CronService(tmp_path / "cron" / "jobs.json")

    job = service.add_job(
        name="every job",
        schedule=CronSchedule(kind="every", every_ms=60000),
        message="hello",
    )

    # Next run should be approximately 60 seconds from now
    assert job.state.next_run_at_ms is not None
    # Should be in the future (within a reasonable margin)
    import time
    now_ms = int(time.time() * 1000)
    assert job.state.next_run_at_ms > now_ms
