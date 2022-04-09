from pytest import raises
from reactivex import Subject
from reactivex.disposable import Disposable

from alleycat.common import AlreadyDisposedError, DisposableCollection, DisposableCollector


class FaultySubject(Subject[str]):
    def dispose(self) -> None:
        raise Exception("Imma bad subject!")


def test_disposable_collection():
    collection = DisposableCollection()

    disposable1 = FaultySubject()
    disposable2 = Disposable()

    collection.append(disposable1)
    collection.append(disposable2)

    assert not collection.is_disposed
    assert not disposable1.is_disposed
    assert not disposable2.is_disposed

    collection.dispose()

    assert collection.is_disposed
    assert not disposable1.is_disposed
    assert disposable2.is_disposed

    with raises(AlreadyDisposedError):
        collection.dispose()


def test_disposable_collector():
    class TestCollector(DisposableCollector):
        def __init__(self) -> None:
            super().__init__()

            self.result = []

            self.subject1 = FaultySubject()
            self.subject2 = Subject()
            self.subject3 = Subject()

            self._subscribe(self.subject1, self.result.append)
            self._subscribe(self.subject2, self.result.append)

            self._disposables.append(self.subject3)

    collector = TestCollector()

    assert not collector.is_disposed
    assert not collector.subject1.is_disposed
    assert not collector.subject2.is_disposed
    assert not collector.subject3.is_disposed

    assert collector.result == []

    collector.subject1.on_next("A")

    assert collector.result == ["A"]

    collector.subject2.on_next("B")

    assert collector.result == ["A", "B"]

    collector.dispose()

    collector.subject1.on_next("C")
    collector.subject2.on_next("D")

    assert collector.result == ["A", "B"]

    assert collector.is_disposed
    assert not collector.subject1.is_disposed
    assert not collector.subject2.is_disposed
    assert collector.subject3.is_disposed

    with raises(AlreadyDisposedError):
        collector.dispose()
