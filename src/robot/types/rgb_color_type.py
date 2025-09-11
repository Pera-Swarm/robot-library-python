from __future__ import annotations

from typing import Iterable

from robot.exception import RGBColorException


class RGBColorType:
    def __init__(self, R: int | str | Iterable[int], G: int | None = None, B: int | None = None):
        # Overloads similar to Java constructors
        if isinstance(R, str):
            # "R G B" format or hex code like "#00AAFF"
            s = R.strip()
            if s.startswith("#"):
                self.set_color_from_hex_code(s)
            else:
                self.set_color_from_str(s)
        elif G is None and B is None and not isinstance(R, int):
            vals = list(R)
            if not (len(vals) == 3 or len(vals) == 4):
                raise ValueError("length of the color[] should be equal to 3 (ambient ignored)")
            self.set_color(vals[0], vals[1], vals[2])
        else:
            assert G is not None and B is not None
            self.set_color(R, G, B)

    def set_color_from_str(self, s: str) -> None:
        parts = s.split()
        if not (len(parts) == 3 or len(parts) == 4):
            raise RGBColorException()
        self.set_color(int(parts[0]), int(parts[1]), int(parts[2]))

    def set_color_from_hex_code(self, hex_code: str) -> None:
        # Expecting format like "#RRGGBB"
        self.R = self._validate(int(hex_code[1:3], 16))
        self.G = self._validate(int(hex_code[3:5], 16))
        self.B = self._validate(int(hex_code[5:7], 16))

    def set_color(self, R: int, G: int, B: int) -> None:
        self.R = self._validate(R)
        self.G = self._validate(G)
        self.B = self._validate(B)

    def _validate(self, v: int) -> int:
        if v < 0 or v > 255:
            raise RGBColorException(v, v, v)
        return v

    def get_r(self) -> int:
        return self.R

    def get_g(self) -> int:
        return self.G

    def get_b(self) -> int:
        return self.B

    def get_color(self) -> list[int]:
        return [self.R, self.G, self.B]

    def __str__(self) -> str:
        return f"R:{self.R}, G:{self.G}, B:{self.B}"

    def to_string_color(self) -> str:
        return f"{self.R} {self.G} {self.B}"

    def compare_to(self, color: "RGBColorType") -> bool:
        return (color.get_r() == self.R) and (color.get_g() == self.G) and (color.get_b() == self.B)

