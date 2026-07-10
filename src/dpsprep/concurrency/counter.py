from collections.abc import MutableMapping


class PageCounter:
    total: int
    images: MutableMapping[int, bool]
    text: MutableMapping[int, bool]

    def __init__(self, total: int) -> None:
        self.total = total
        self.images = dict.fromkeys(range(total), False)
        self.text = dict.fromkeys(range(total), False)
