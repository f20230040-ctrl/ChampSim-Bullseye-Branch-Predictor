"""
Cache geometry calculations and validation for ChampSim.
Validates the mathematical relationship:
    Capacity (bytes) = Sets * Ways * Line_Size (64 bytes)
"""

def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def calculate_sets(capacity_bytes: int, ways: int, line_size: int = 64) -> int:
    """
    Calculate required set count per core for a given capacity and associativity.
    Validates power-of-two constraints and exact integer divisibility.
    """
    if capacity_bytes <= 0:
        raise ValueError(f"Capacity must be positive, got {capacity_bytes}")
    if ways <= 0 or not is_power_of_two(ways):
        raise ValueError(f"Associativity (ways) must be a positive power of two, got {ways}")
    if line_size <= 0 or not is_power_of_two(line_size):
        raise ValueError(f"Line size must be a positive power of two, got {line_size}")

    bytes_per_set = ways * line_size
    if capacity_bytes % bytes_per_set != 0:
        raise ValueError(
            f"Capacity ({capacity_bytes} bytes) is not divisible by bytes per set "
            f"({bytes_per_set} bytes = {ways} ways * {line_size} bytes)"
        )

    sets = capacity_bytes // bytes_per_set
    if not is_power_of_two(sets):
        raise ValueError(f"Calculated set count ({sets}) is not a power of two")

    return sets


def calculate_capacity_bytes(sets: int, ways: int, line_size: int = 64) -> int:
    """Calculate cache capacity in bytes from sets, ways, and line size."""
    if sets <= 0 or not is_power_of_two(sets):
        raise ValueError(f"Sets must be a positive power of two, got {sets}")
    if ways <= 0 or not is_power_of_two(ways):
        raise ValueError(f"Ways must be a positive power of two, got {ways}")
    if line_size <= 0 or not is_power_of_two(line_size):
        raise ValueError(f"Line size must be a positive power of two, got {line_size}")

    return sets * ways * line_size


class CacheGeometry:
    """Represents a validated Last-Level Cache (LLC) geometry."""
    def __init__(self, capacity_mb: float, ways: int, line_size: int = 64, num_cpus: int = 1):
        self.capacity_mb = capacity_mb
        self.capacity_bytes = int(capacity_mb * 1024 * 1024)
        self.ways = ways
        self.line_size = line_size
        self.num_cpus = num_cpus

        # Sets per core
        self.sets_per_core = calculate_sets(self.capacity_bytes, self.ways, self.line_size)
        # Total sets across all cores in ChampSim (NUM_CPUS * sets_per_core)
        self.total_sets = self.sets_per_core * self.num_cpus
        self.total_capacity_bytes = self.capacity_bytes * self.num_cpus

        # Sanity check
        computed = calculate_capacity_bytes(self.sets_per_core, self.ways, self.line_size)
        assert computed == self.capacity_bytes, (
            f"Geometry mismatch: {computed} != {self.capacity_bytes}"
        )

    def get_cflags(self) -> str:
        """Returns macro definition flags for the compiler."""
        return f"-DLLC_SET=NUM_CPUS*{self.sets_per_core} -DLLC_WAY={self.ways}"

    def __repr__(self) -> str:
        return (
            f"CacheGeometry({self.capacity_mb}MiB, {self.ways}-way, "
            f"sets_per_core={self.sets_per_core}, line_size={self.line_size}B, "
            f"cpus={self.num_cpus})"
        )
