from dataclasses import dataclass


@dataclass(frozen=True)
class Lid:
    prefix: str
    bundle: str
    collection: str = None
    product: str = None

    @staticmethod
    def parse(lidstr: str) -> "Lid":
        tokens = lidstr.split(":")
        return Lid(
            prefix=":".join(tokens[0:3]),
            bundle=tokens[3],
            collection=tokens[4] if len(tokens) >= 5 else None,
            product=tokens[5] if len(tokens) >= 6 else None
        )

    def __str__(self) -> str:
        if self.product and self.collection:
            return f"{self.prefix}:{self.bundle}:{self.collection}:{self.product}"
        if self.collection:
            return f"{self.prefix}:{self.bundle}:{self.collection}"
        return f"{self.prefix}:{self.bundle}"


@dataclass(frozen=True, order=True)
class Vid:
    major: int
    minor: int

    @staticmethod
    def parse(vidstr: str) -> 'Vid':
        tokens = vidstr.split(".")
        return Vid(
            major=int(tokens[0]),
            minor=int(tokens[1])
        )

    def __str__(self) -> str:
        return f'{self.major}.{self.minor}'

    def inc_major(self) -> 'Vid':
        return Vid(self.major + 1, 0)

    def inc_minor(self) -> 'Vid':
        return Vid(self.major, self.minor + 1)

    def is_superseding(self) -> bool:
        return self.major > 1 or self.minor > 0


@dataclass(frozen=True)
class LidVid:
    lid: Lid
    vid: Vid

    @staticmethod
    def parse(lidvidstr: str) -> 'LidVid':
        lid, vid = lidvidstr.split("::")
        return LidVid.assemble(lid, vid)

    @staticmethod
    def assemble(lid: str, vid: str) -> 'LidVid':
        return LidVid(
            lid=Lid.parse(lid),
            vid=Vid.parse(vid)
        )

    def __str__(self):
        return f'{self.lid}::{self.vid}'

    def inc_major(self) -> "LidVid":
        return LidVid(self.lid, self.vid.inc_major())

    def inc_minor(self) -> "LidVid":
        return LidVid(self.lid, self.vid.inc_minor())