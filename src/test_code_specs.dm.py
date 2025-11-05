# Suggested validator: mypy $DMPATH && $PYTHON -m pytest $DMPATH

import asyncio
import pathlib
import unittest

import code_specs


class CodeSpecsTest(unittest.IsolatedAsyncioTestCase):

  async def test_comment_string_py_and_foo_bar_returns_foo_bar(self) -> None:
    pass  # {{🍄 "py" and "foo bar" returns "# foo bar"}}

  async def test_comment_string_html_and_my_test_returns_my_test(self) -> None:
    pass  # {{🍄 "html" and "my test" returns "<!-- my test -->"}}

  async def test_comment_string_html_and_foo_bar_quux_returns_foo_bar_quux(
      self) -> None:
    pass  # {{🍄 "html" and "foo\nbar\nquux" returns "<!-- foo\nbar\nquux -->"}}

  async def test_comment_string_cc_and_foo_bar_returns_foo_bar(self) -> None:
    pass  # {{🍄 "cc" and "foo\nbar" returns "// foo\n//bar"}}

  async def test_comment_string_css_and_foo_bar_returns_foo_bar(self) -> None:
    pass  # {{🍄 "css" and "foo bar" returns "/* foo bar */"}}

  async def test_comment_string_css_and_foo_bar_returns_foo_bar_2(self) -> None:
    pass  # {{🍄 "css" and "foo\nbar" returns "/* foo\nbar */" (in comment_string occurrence 2)}}

  async def test_MarkerName__fix_name_name_foo_is_turned_into_foo(self) -> None:
    pass  # {{🍄 Name " foo" is turned into "foo".}}

  async def test_MarkerName__fix_name_name_foo_is_turned_into_foo_2(
      self) -> None:
    pass  # {{🍄 Name "foo " is turned into "foo". (in _fix_name occurrence 2)}}

  async def test_MarkerName__fix_name_name_foo_is_turned_into_foo_3(
      self) -> None:
    pass  # {{🍄 Name " foo " is turned into "foo". (in _fix_name occurrence 3)}}

  async def test_MarkerName__fix_name_name_foo_bar_is_turned_into_foo_bar(
      self) -> None:
    pass  # {{🍄 Name "Foo\nBar" is turned into "Foo Bar".}}

  async def test_MarkerName__fix_name_name_foo_bar_is_turned_into_foo_bar_2(
      self) -> None:
    pass  # {{🍄 Name "  foo \n\n   \n   bar  " is turned into "foo bar". (in _fix_name occurrence 2)}}

  async def test_reindent_code_if_an_input_line_from_code_is_empty_or_only_contains_whitespace_characters_the_corresponding_line_in_the_output_is_empty(
      self) -> None:
    pass  # {{🍄 If an input line (from `code`) is empty or only contains whitespace characters, the corresponding line in the output is empty.}}

  async def test_reindent_code_if_the_whitespace_prefixes_are_removed_from_all_input_and_output_lines_the_output_is_identical_to_code(
      self) -> None:
    pass  # {{🍄 If the whitespace prefixes are removed (from all input and output lines), the output is identical to `code`.}}

  async def test_reindent_code_all_lines_in_the_output_must_begin_with_desired_spaces_spaces_or_be_empty(
      self) -> None:
    pass  # {{🍄 All lines in the output must begin with `desired_spaces` spaces or be empty.}}

  async def test_reindent_code_the_output_must_contain_at_least_one_line_where_if_desired_spaces_spaces_are_removed_from_the_start_the_line_starts_with_a_non_space_character(
      self) -> None:
    pass  # {{🍄 The output must contain at least one line where, if `desired_spaces` spaces are removed (from the start), the line starts with a non-space character.}}

  async def test_get_expanded_markers_given_an_empty_file_returns_an_empty_list(
      self) -> None:
    pass  # {{🍄 Given an empty file, returns an empty list.}}

  async def test_get_expanded_markers_raises_filenotfounderror_for_a_non_existent_file(
      self) -> None:
    pass  # {{🍄 Raises FileNotFoundError for a non-existent file (in get_expanded_markers)}}

  async def test_get_expanded_markers_given_an_file_with_four_different_markers_returns_a_list_with_four_elements_the_outputs_match_the_inputs_fields_in_the_expandedmarker_entries_are_correct_and_the_output_order_matches_the_input(
      self) -> None:
    pass  # {{🍄 Given an file with four different markers, returns a list with four elements. The outputs match the inputs: fields in the ExpandedMarker entries are correct, and the output order matches the input.}}

  async def test_get_expanded_markers_given_a_file_with_two_different_markers_each_ocurring_twice_raises_repeatedexpandedmarkerserror_the_exception_string_mentions_all_repeated_markers(
      self) -> None:
    pass  # {{🍄 Given a file with two different markers each ocurring twice, raises `RepeatedExpandedMarkersError`. The exception string mentions all repeated markers.}}

  async def test_get_markers_str_returns_for_an_empty_input(self) -> None:
    pass  # {{🍄 Returns {} for an empty input}}

  async def test_get_markers_str_returns_for_an_input_with_5_lines_but_no_markers(
      self) -> None:
    pass  # {{🍄 Returns {} for an input with 5 lines but no markers}}

  async def test_get_markers_str_correctly_returns_a_marker_in_an_input_with_just_1_marker(
      self) -> None:
    pass  # {{🍄 Correctly returns a marker in an input with just 1 marker}}

  async def test_get_markers_str_if_a_marker_starts_in_the_first_line_in_the_input_its_value_in_the_output_is_0(
      self) -> None:
    pass  # {{🍄 If a marker starts in the first line in the input, its value in the output is [0].}}

  async def test_get_markers_str_if_a_marker_starts_in_the_last_line_its_value_in_the_output_is_len_lines_1(
      self) -> None:
    pass  # {{🍄 If a marker starts in the last line, its value in the output is `len(lines) - 1`.}}

  async def test_get_markers_str_correctly_handles_an_input_where_a_marker_starts_in_the_first_line_and_finishes_in_the_last_line(
      self) -> None:
    pass  # {{🍄 Correctly handles an input where a marker starts in the first line and finishes in the last line.}}

  async def test_get_markers_str_spaces_are_correctly_removed_from_a_marker_named_foo_bar(
      self) -> None:
    pass  # {{🍄 Spaces are correctly removed from a marker named "  foo bar  ".}}

  async def test_get_markers_str_returns_all_markers_in_an_input_with_ten_markers(
      self) -> None:
    pass  # {{🍄 Returns all markers in an input with ten markers.}}

  async def test_get_markers_str_the_index_of_markers_returned_in_an_input_with_ten_markers_is_correct(
      self) -> None:
    pass  # {{🍄 The index of markers returned in an input with ten markers is correct.}}

  async def test_get_markers_str_an_input_can_have_repeated_markers_the_output_just_lists_their_positions(
      self) -> None:
    pass  # {{🍄 An input can have repeated markers; the output just lists their positions.}}

  async def test_get_markers_str_an_input_where_two_markers_overlap_one_ends_in_the_same_line_where_the_other_begins_raises_markersoverlaperror(
      self) -> None:
    pass  # {{🍄 An input where two markers overlap (one ends in the same line where the other begins) raises `MarkersOverlapError`.}}

  async def test_get_markers_str_the_returned_object_is_sorted_by_appearance_order_i_e_iterating_across_the_keys_of_the_returned_dictionary_matches_the_order_in_which_the_first_appearance_of_each_marker_was_found_in_the_input(
      self) -> None:
    pass  # {{🍄 The returned object is sorted by appearance order (i.e., iterating across the keys of the returned dictionary matches the order in which the first appearance of each marker was found in the input).}}

  async def test_get_markers_reads_path_asynchronously(self) -> None:
    pass  # {{🍄 Reads `path` asynchronously (in get_markers)}}

  async def test_get_markers_raises_filenotfounderror_for_a_non_existent_file(
      self) -> None:
    pass  # {{🍄 Raises FileNotFoundError for a non-existent file (in get_markers)}}


if __name__ == '__main__':
  unittest.main()
