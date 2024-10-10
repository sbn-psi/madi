def is_ignored(candidate: str) -> bool:
    return any([".DS_Store" in candidate, candidate.startswith("?")])


def is_below(base: str, candidate: str) -> bool:
    return candidate.startswith(base) or (not "://" in candidate and not candidate.startswith("/") and not candidate.startswith(".."))


def is_absolute(candidate: str) -> bool:
    return "://" in candidate


def make_absolute(base: str, candidate: str) -> str:
    if is_absolute(candidate):
        if candidate.startswith(base):
            return candidate
        else:
            raise Exception(f"{candidate} cannot be made absolute. It is already absolute, and not below {base}")
    return base + candidate


