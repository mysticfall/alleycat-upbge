from collections import OrderedDict

from alleycat.core import Bootstrap


def test_on_ready():
    bootstrap = Bootstrap()

    count = [0]

    def when_ready():
        count.append(count.pop() + 1)

    Bootstrap.when_ready(when_ready)

    assert count[0] == 0

    bootstrap.start(OrderedDict((('key', 'alleycat'), ('config', '//config.json'))))

    assert count[0] == 1

    Bootstrap.when_ready(when_ready)

    assert count[0] == 2
