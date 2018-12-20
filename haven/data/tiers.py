
class Tier:
    """
    Define data tiers
    """
    # Tier zero: public
    ZERO = 0

    # Tier 1: publishable
    ONE = 1

    # Tier 2: official
    TWO = 2

    # Tier 3: sensitive
    THREE = 3

    # Tier 4 is secret
    FOUR = 4


TIER_CHOICES = [
    (Tier.ZERO, 'Tier 0'),
    (Tier.ONE, 'Tier 1'),
    (Tier.TWO, 'Tier 2'),
    (Tier.THREE, 'Tier 3'),
    (Tier.FOUR, 'Tier 4'),
]
