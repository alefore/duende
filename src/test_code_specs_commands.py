import unittest
import asyncio

class TestCodeSpecsCommands(unittest.IsolatedAsyncioTestCase):

  async def test_get_file_extension_given_foo_py_returns_py(self) -> None:
    pass  # {{🍄 _get_file_extension: Given 'foo.py', returns 'py'.}}

  async def test_get_file_extension_given_src_foo_dm_py_returns_py(self) -> None:
    pass  # {{🍄 _get_file_extension: Given 'src/foo.dm.py', returns 'py'.}}

  async def test_read_duende_implementation_marker_run_if_not_found_returns_error_with_list_of_markers(self) -> None:
    pass  # {{🍄 read_duende_implementation_marker_run: If the marker is not found in the file, returns an error. The error includes the explicit list of all markers found in the file (or an explicit explanation if the file contains no markers.}}

  async def test_update_duende_marker_implementation_get_updated_content_only_reads_path_does_not_modify_it(self) -> None:
    pass  # {{🍄 update_duende_marker_implementation_get_updated_content: Only reads `path`, does not modify it.}}

  async def test_update_duende_marker_implementation_get_updated_content_raises_marker_update_error_on_invalid_condition(self) -> None:
    pass  # {{🍄 update_duende_marker_implementation_get_updated_content: Raises MarkerUpdateError on any invalid condition: marker is not found, file can't be read, marker is duplicated in the file.}}

  async def test_update_duende_marker_implementation_get_updated_content_if_marker_not_found_error_includes_available_markers(self) -> None:
    pass  # {{🍄 update_duende_marker_implementation_get_updated_content: If the marker is not found, the `MarkerUpdateError` exception includes a list of all available markers.}}

  async def test_update_duende_marker_implementation_get_updated_content_handles_content_with_or_without_marker_comments(self) -> None:
    pass  # {{🍄 update_duende_marker_implementation_get_updated_content: `content` may start with the marker-start comment but it doesn't need to. Correctly handles both cases (without repeating the marker-start comment in the output). Same for the marker-end comment.}}


if __name__ == '__main__':
  unittest.main()