from dataclasses import dataclass
import pathlib


@dataclass
class PathBox:
  path: pathlib.Path = pathlib.Path('.')

  def __truediv__(self, other: pathlib.Path | str) -> pathlib.Path:
    return self.path / other
