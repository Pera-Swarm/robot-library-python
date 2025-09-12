from __future__ import annotations

from robot.exception import ProximityException

from .rgb_color_type import RGBColorType


class ProximityReadingType:
    def __init__(self, angles: list[int] | tuple[int, ...], s: str):
        reading_count = len(angles)
        values = s.split()

        self._distances: list[int] = [0] * reading_count
        self._colors: list[RGBColorType] = [
            RGBColorType(0, 0, 0) for _ in range(reading_count)
        ]

        if len(values) != reading_count * 2:
            raise ProximityException(
                f"ProximityReadingType: length mismatch {len(values)}"
            )

        for i in range(reading_count):
            vi = values[i]
            if vi == "Infinity":
                print(f"Proximity: Infinity reading received for {i}")
                self._distances[i] = -1
            else:
                self._distances[i] = int(vi)

            color = RGBColorType(0, 0, 0)
            color.set_color_from_hex_code(values[reading_count + i])
            self._colors[i] = color

    def distances(self) -> list[int]:
        return self._distances

    def colors(self) -> list[RGBColorType]:
        return self._colors

    def __str__(self) -> str:
        parts: list[str] = []
        parts.extend(str(d) for d in self._distances)
        parts.append(" ")
        parts.extend(str(c) for c in self._colors)
        return " ".join(parts)
