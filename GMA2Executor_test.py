#import pytest

from GMA2Executor import GMA2Executor

def test_defaultInit():
    executor = GMA2Executor(5)

    assert executor.number == 5
    assert executor.fader == -1
    assert executor.cue == -1

def test_fullInit():
    executor = GMA2Executor(5, 3, 2)

    assert executor.number == 5
    assert executor.fader == 3
    assert executor.cue == 2


def test_cueUpdate():
    executor = GMA2Executor(5)

    executor2 = GMA2Executor(5)
    executor2.cue = 3

    executor.update(executor2)

    assert executor.number == 5
    assert executor.cue == 3
    assert executor.fader == -1
    assert executor.lastUpdate == executor2.lastUpdate
