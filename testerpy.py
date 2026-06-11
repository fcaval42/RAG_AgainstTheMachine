import sys
from typing import Dict, List, Tuple, Optional, Any
from typing_extensions import Self
from pydantic import (BaseModel, Field, field_validator, model_validator)


def get_tuple(entry: str, exit_coord: str) -> List[Tuple[int, int]]:
    """Convert entry and exit coordinates strings into coordinate tuples.

    Args:
        entry: Entry coordinate as "x,y".
        exit_coord: Exit coordinate as "x,y".

    Returns:
        A list containing entry and exit coordinates as tuples.
    """
    ent_x, ent_y = map(int, entry.split(","))
    ext_x, ext_y = map(int, exit_coord.split(","))

    return [(ent_x, ent_y), (ext_x, ext_y)]


def maze_data_extract(file: str) -> Tuple[List[str], str, str, str]:
    """Read a generated maze file and extract maze content and metadata.

    Args:
        file: Path to the maze output file.

    Returns:
        A tuple containing maze rows, entry coordinate, exit coordinate,
        and path directions.
    """
    try:
        with open(file, 'r', encoding="utf-8") as lines:
            all_lines = [line.strip() for line in lines if line.strip()]

            if len(all_lines) <= 4:
                raise ValueError("The file must contain at least 4 lines "
                                 "(maze + entry + exit + path)")

            maze = all_lines[:-3]
            entry = all_lines[-3]
            exit_coord = all_lines[-2]
            path = all_lines[-1]

            return maze, entry, exit_coord, path

    except FileNotFoundError:
        print(f"\nError : The file {file} has not been generated\n")
        sys.exit()
    except ValueError as e:
        print(f"\nError : {e}\n")
        sys.exit()


class MazeConfig(BaseModel):
    """Validated configuration model for maze generation and rendering."""
    WIDTH: int = Field(gt=1, le=50)
    HEIGHT: int = Field(gt=1, le=50)
    ENTRY: str
    EXIT: str
    OUTPUT_FILE: str
    PERFECT: bool
    SEED: Optional[Any] = Field(default="")

    @field_validator("ENTRY", "EXIT")
    @classmethod
    def check_coordinates_format(cls, value: str) -> str:
        """Validate that a coordinate uses the expected "x,y" format.

        Args:
            value: Coordinate string to validate.

        Returns:
            The validated coordinate string.
        """
        if "," not in value:
            raise ValueError("Coordinates must be 'x,y' format")
        parts = value.split(",")
        if len(parts) != 2:
            raise ValueError("Coordinates must be 'x,y' format")
        return value

    @field_validator("OUTPUT_FILE")
    @classmethod
    def check_outputfile(cls, value: str) -> str:
        """Validate output file extension.

        Args:
            value: Output file path.

        Returns:
            The validated output file path.
        """
        if not value.endswith(".txt"):
            raise ValueError("The file must be in .txt format")
        if value.count(".txt") > 1:
            raise ValueError("There can't be two “.txt” files")
        return value

    @model_validator(mode="after")
    def validate_maze(self) -> Self:
        """Validate consistency and bounds of maze configuration fields.

        Returns:
            The validated model instance.
        """
        x, y = map(int, self.ENTRY.split(","))
        x2, z2 = map(int, self.EXIT.split(","))

        if (x, y) == (x2, z2):
            raise ValueError("ENTRY and EXIT cannot have the same coordinates")
        if self.WIDTH * self.HEIGHT < 4:
            raise ValueError("Maze dimensions must be at least 2x2.")
        if not (0 <= x < self.WIDTH and 0 <= y < self.HEIGHT):
            raise ValueError("ENTRY coordinates are out of bounds.")
        if not (0 <= x2 < self.WIDTH and 0 <= z2 < self.HEIGHT):
            raise ValueError("EXIT coordinates are out of bounds.")

        return self


def extract_config(file_path: str) -> Dict[str, str]:
    """Parse a key=value configuration file into a dictionary.

    Args:
        file_path: Path to the configuration file.

    Returns:
        Parsed configuration key/value pairs.
    """
    config = {}
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.count("=") != 1:
                    raise ValueError(f"\nError: Invalid line format ("
                                     f"must contain exactly one '='): {line}")

                key, value = map(str.strip, line.split("=", 1))
                if not key:
                    raise ValueError(f"\nError: Invalid key in line: {line}")

                if value == "" and key != "SEED":
                    raise ValueError(f"\nError: Invalid value for key '{key}'"
                                     f" in line: {line}")

                config[key] = value

        mandatory_keys = ["WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE",
                          "PERFECT"]
        for key in mandatory_keys:
            if key not in config or not config[key]:
                raise ValueError(f"the key {key} is missing or empty")

        return config

    except (FileNotFoundError) as e:
        print(f"\nERROR parsing: {e}\n")
        sys.exit()