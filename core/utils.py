from core.text import TEXT


def norm_dict(
        data: dict[int, float],
        total: float = 1.0,
        precision: int = 2,
        ) -> dict[int, float]:
    """Normalize the values in the dictionary to sum to 1.0."""

    total = total or sum(data.values())
    if total == 0:
        return {k: 0.0 for k in data}

    if precision is None:
        return {k: v / total for k, v in data.items()}

    return {k: round(v / total * 100, precision) for k, v in data.items()}


def convert_dict(
        data: dict[int, float],
        mode: str,
        ) -> dict[int, float]:
    """Convert the values in the dictionary according to the specified mode."""

    out = {}

    match mode:
        case TEXT.LE:
            out = {k: sum(v for key, v in data.items() if key <= k) for k in data}
        case TEXT.LT:
            out = {k: sum(v for key, v in data.items() if key < k) for k in data}
        case TEXT.GE:
            out = {k: sum(v for key, v in data.items() if key >= k) for k in data}
        case TEXT.GT:
            out = {k: sum(v for key, v in data.items() if key > k) for k in data}
        case TEXT.EQ:
            out = data.copy()
        case _:
            raise ValueError(f"Unknown conversion mode: {mode}")

    return out
