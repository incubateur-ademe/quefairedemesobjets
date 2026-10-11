def fbeta(precision: float, recall: float, beta: float = 0.5) -> float:
    """F-bêta : beta < 1 favorise la précision par rapport au rappel."""
    if precision == 0 and recall == 0:
        return 0.0
    b2 = beta**2
    return (1 + b2) * precision * recall / (b2 * precision + recall)
