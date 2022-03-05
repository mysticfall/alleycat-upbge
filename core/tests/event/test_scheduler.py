from datetime import datetime, timedelta

from pytest import approx, mark
from pytest_mock import MockerFixture

from alleycat.event import EventLoopScheduler, TimeMode


@mark.parametrize("mode", TimeMode)
@mark.parametrize("interval", (10, 250, 1000))
def test_now(mocker: MockerFixture, mode: TimeMode, interval: int):
    timer = mocker.patch(f"bge.logic.get{mode.name}Time")
    timer.return_value = interval

    now = datetime.now()
    yesterday = now + timedelta(days=-1)

    assert EventLoopScheduler(mode=mode).now.timestamp() == approx(now.timestamp() + interval, abs=1)
    assert EventLoopScheduler(yesterday, mode).now.timestamp() == approx(yesterday.timestamp() + interval, abs=1)


@mark.parametrize("mode", TimeMode)
def test_schedule(mocker: MockerFixture, mode: TimeMode):
    timer = mocker.patch(f"bge.logic.get{mode.name}Time")
    timer.return_value = 0.

    scheduler = EventLoopScheduler(mode=mode)

    action = mocker.MagicMock()

    scheduler.schedule(action, "State")

    action.assert_not_called()

    scheduler.process()

    action.assert_called_once_with(scheduler, "State")

    scheduler.process()
    scheduler.process()

    action.assert_called_once()


@mark.parametrize("mode", TimeMode)
@mark.parametrize("interval", (10, 250, 1000))
def test_schedule_relative(mocker: MockerFixture, mode: TimeMode, interval: int):
    timer = mocker.patch(f"bge.logic.get{mode.name}Time")
    timer.return_value = 0.

    scheduler = EventLoopScheduler(mode=mode)

    action = mocker.MagicMock()

    scheduler.schedule_relative(interval, action, "State")
    scheduler.process()

    action.assert_not_called()

    timer.return_value = interval * 0.5
    scheduler.process()

    action.assert_not_called()

    timer.return_value = interval + 1
    scheduler.process()

    action.assert_called_with(scheduler, "State")

    timer.return_value = interval * 1.2
    scheduler.process()

    action.assert_called_once()


@mark.parametrize("mode", TimeMode)
@mark.parametrize("interval", (10, 250, 1000))
def test_schedule_absolute(mocker: MockerFixture, mode: TimeMode, interval: int):
    timer = mocker.patch(f"bge.logic.get{mode.name}Time")
    timer.return_value = 0

    start = datetime.now()
    due = start + timedelta(seconds=interval)

    scheduler = EventLoopScheduler(start, mode)

    action = mocker.MagicMock()

    scheduler.schedule_absolute(due, action, "State")
    scheduler.process()

    action.assert_not_called()

    timer.return_value = interval * 0.8
    scheduler.process()

    action.assert_not_called()

    timer.return_value = interval + 1
    scheduler.process()

    action.assert_called_with(scheduler, "State")

    timer.return_value = interval * 1.1
    scheduler.process()

    action.assert_called_once()


def test_dispose_action(mocker: MockerFixture):
    timer = mocker.patch("bge.logic.getFrameTime")
    timer.return_value = 0.

    scheduler = EventLoopScheduler(mode=TimeMode.Frame)

    action = mocker.MagicMock()

    disposable = scheduler.schedule_relative(10, action, "State")

    assert disposable

    scheduler.process()

    action.assert_not_called()

    disposable.dispose()

    timer.return_value = 100

    scheduler.process()

    action.assert_not_called()


def test_on_process(mocker: MockerFixture):
    timer = mocker.patch("bge.logic.getFrameTime")
    timer.return_value = 0.

    scheduler = EventLoopScheduler(mode=TimeMode.Frame)

    ticks = []

    scheduler.process()

    with scheduler.on_process.subscribe(ticks.append):
        timer.return_value = 10.
        scheduler.process()

        timer.return_value = 250.
        scheduler.process()

        timer.return_value = 1000.
        scheduler.process()

    assert len(ticks) == 3
