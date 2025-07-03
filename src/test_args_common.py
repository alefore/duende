import unittest
import argparse
import os
import sys
import tempfile
import shutil
from typing import List, Optional
from unittest.mock import patch, MagicMock, call

from args_common import CreateCommonParser, CreateFileAccessPolicy
from file_access_policy import FileAccessPolicy

# From args_common.py, CreateCommonParser, --file-access-regex-path default
DEFAULT_FILE_ACCESS_REGEX_PATH = 'agent/file-access-regex.txt'


class TestArgsCommon(unittest.TestCase):

  def setUp(self) -> None:
    self.parser = CreateCommonParser()

    self.test_dir = tempfile.mkdtemp()
    self.original_cwd = os.getcwd()
    os.chdir(self.test_dir)

    os.makedirs(os.path.dirname(DEFAULT_FILE_ACCESS_REGEX_PATH), exist_ok=True)
    self.policy: Optional[FileAccessPolicy] = None

  def tearDown(self) -> None:
    os.chdir(self.original_cwd)
    shutil.rmtree(self.test_dir)

  def _create_policy(self, args_list: List[str]):
    args = self.parser.parse_args(args_list)
    self.policy = CreateFileAccessPolicy(args.file_access_regex,
                                         args.file_access_regex_path)

  def _check_access(self, path: str) -> bool:
    if self.policy is None:
      raise ValueError("Policy not created. Call _create_policy first.")
    return self.policy.allow_access(os.path.abspath(path))

  def test_no_regex_specified(self) -> None:
    self._create_policy(['--task', 'dummy.txt'])

    self.assertTrue(self._check_access('./file.txt'))
    self.assertTrue(self._check_access('./src/file.py'))
    self.assertFalse(self._check_access('/absolute/path/file.txt'))
    self.assertFalse(self._check_access('../parent_dir/file.txt'))

  def test_from_default_path(self) -> None:
    with open(DEFAULT_FILE_ACCESS_REGEX_PATH, 'w') as f:
      f.write(r'^default/.*$')

    self._create_policy(['--task', 'dummy.txt'])

    self.assertTrue(self._check_access('default/file.txt'))
    self.assertFalse(self._check_access('another/file.txt'))
    self.assertTrue(self._check_access('default/subdirectory/another_file.py'))
    self.assertFalse(self._check_access('src/my_code.js'))

  @patch('sys.stderr')
  def test_no_default_path_is_empty(self, mock_stderr: MagicMock) -> None:
    with open(DEFAULT_FILE_ACCESS_REGEX_PATH, 'w') as f:
      empty = ''
      f.write(empty)

    with self.assertRaises(SystemExit) as cm:
      self._create_policy(['--task', 'dummy.txt'])
    self.assertEqual(cm.exception.code, 1)

    expected_message_part = f"Error: Invalid usage: --file-access-regex-path: {DEFAULT_FILE_ACCESS_REGEX_PATH}: File is empty."
    self.assertTrue(
        any(expected_message_part in call_args[0][0]
            for call_args in mock_stderr.write.call_args_list),
        f"Expected error message '{expected_message_part}' not found in stderr output."
    )

  def test_provided_directly(self) -> None:
    with open(DEFAULT_FILE_ACCESS_REGEX_PATH, 'w') as f:
      empty = ''
      f.write(empty)

    self._create_policy(
        ['--task', 'dummy.txt', '--file-access-regex', r'^src/.*\.py$'])

    self.assertTrue(self._check_access('src/my_module.py'))
    self.assertFalse(self._check_access('other_file.txt'))
    self.assertFalse(self._check_access('src/data.txt'))
    self.assertFalse(self._check_access('my_module.py'))
    self.assertTrue(self._check_access('src/sub/another.py'))
    self.assertFalse(self._check_access('../src/module.py'))

  def test_from_non_default_path(self) -> None:
    explicit_regex_path = 'path/to/regex.txt'
    os.makedirs(os.path.dirname(explicit_regex_path), exist_ok=True)
    with open(explicit_regex_path, 'w') as f:
      f.write(r'^test_regex_file.*\.txt$')

    self._create_policy([
        '--task', 'dummy.txt', '--file-access-regex-path', explicit_regex_path
    ])

    self.assertTrue(self._check_access('test_regex_file_match.txt'))
    self.assertFalse(self._check_access('no_match.txt'))
    self.assertFalse(self._check_access('test_regex_file_match.log'))
    self.assertTrue(self._check_access('test_regex_file_123.txt'))

  @patch('sys.stderr')
  def test_both_flags_provided(self, mock_stderr: MagicMock) -> None:
    args_list = [
        '--task', 'dummy.txt', '--file-access-regex', 'regex1',
        '--file-access-regex-path', 'path/to/regex.txt'
    ]

    with self.assertRaises(SystemExit) as cm:
      self._create_policy(args_list)
    self.assertEqual(cm.exception.code, 1)

    expected_message_part = "Error: Invalid usage: At most one of `--file-access-regex` and `--file-access-regex-path` can be used."
    self.assertTrue(
        any(expected_message_part in call_args[0][0]
            for call_args in mock_stderr.write.call_args_list),
        f"Expected error message '{expected_message_part}' not found in stderr output."
    )

  @patch('sys.stderr')
  def test_path_file_not_found(self, mock_stderr: MagicMock) -> None:
    non_existent_path = 'nonexistent/path.txt'
    args_list = [
        '--task', 'dummy.2txt', '--file-access-regex-path', non_existent_path
    ]

    with self.assertRaises(SystemExit) as cm:
      self._create_policy(args_list)
    self.assertEqual(cm.exception.code, 1)

    expected_message_part = f"Error: --file-access-regex-path: {non_existent_path}:"
    second_expected_message_part = "No such file or directory"
    self.assertTrue(
        any(expected_message_part in call_args[0][0] and
            second_expected_message_part in call_args[0][0]
            for call_args in mock_stderr.write.call_args_list),
        f"Expected error message '{expected_message_part}' and '{second_expected_message_part}' not found in stderr output."
    )


if __name__ == '__main__':
  unittest.main()
