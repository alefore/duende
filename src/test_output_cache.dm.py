import unittest
import asyncio

class OutputCacheTest(unittest.IsolatedAsyncioTestCase):

  def test_get_path_for_key_output_is_in_base_dir(self) -> None:
    pass  # {{🍄 Output is a file directly in `self._base_dir` (in `_get_path_for_key`).}}

  def test_get_path_for_key_changing_key_results_in_different_hash(self) -> None:
    pass  # {{🍄 Changing any of the parameters in `key` results in a different hash (in `_get_path_for_key`).}}

  async def test_save_uses_async_io(self) -> None:
    pass  # {{🍄 Uses async io (in `save`).}}

  async def test_load_uses_async_io(self) -> None:
    pass  # {{🍄 Uses async io (in `load`).}}

if __name__ == '__main__':
  unittest.main()