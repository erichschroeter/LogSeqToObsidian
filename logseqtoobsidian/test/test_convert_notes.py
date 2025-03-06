import tempfile
import os
import shutil
import unittest
from unittest.mock import Mock

from logseqtoobsidian.convert_notes import (
    is_markdown_file,
    is_empty_markdown_file,
    get_namespace_hierarchy,
    update_links_and_tags,
    update_assets,
    update_image_dimensions,
    is_collapsed_line,
    remove_block_links_embeds,
    convert_spaces_to_tabs,
    convert_empty_line,
    add_space_after_hyphen_that_ends_line,
    prepend_code_block,
    escape_lt_gt,
    convert_todos,
    add_bullet_before_indented_image,
    unindent_once,
    fix_escapes,
    unencode_filenames_for_links,
)


class TestConvertNotes(unittest.TestCase):

    def test_is_markdown_file(self):
        self.assertTrue(is_markdown_file("test.md"))
        self.assertFalse(is_markdown_file("test.txt"))

    def test_is_empty_markdown_file(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            tmp.write(b"   \n")
            tmp_path = tmp.name
        self.assertTrue(is_empty_markdown_file(tmp_path))
        os.remove(tmp_path)

    def test_get_namespace_hierarchy_when_ignore_dot_for_namespace_false(self):
        args = Mock()
        args.ignore_dot_for_namespaces = False
        self.assertEqual(
            get_namespace_hierarchy(args, "A%2FB%2FC.md"), ["A", "B", "C.md"]
        )
        self.assertEqual(
            get_namespace_hierarchy(args, "A___B___C.md"), ["A", "B", "C.md"]
        )
        self.assertEqual(get_namespace_hierarchy(args, "A.B.C.md"), ["A", "B", "C.md"])

    def test_get_namespace_hierarchy_when_ignore_dot_for_namespace_true(self):
        args = Mock()
        args.ignore_dot_for_namespaces = True
        self.assertEqual(
            get_namespace_hierarchy(args, "A%2FB%2FC.md"), ["A", "B", "C.md"]
        )
        self.assertEqual(
            get_namespace_hierarchy(args, "A___B___C.md"), ["A", "B", "C.md"]
        )
        self.assertEqual(get_namespace_hierarchy(args, "A.B.C.md"), ["A.B.C.md"])

    def test_update_assets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_path = os.path.join(tmpdir, "old.md")
            new_path = os.path.join(tmpdir, "new.md")
            asset_path = os.path.join(tmpdir, "image.png")
            with open(asset_path, "w") as f:
                f.write("image content")
            line = "![image](image.png)"
            updated_line = update_assets(line, old_path, new_path)
            self.assertIn("attachments/image.png", updated_line)

    def test_update_image_dimensions(self):
        line = "![image](image.png){:height 319, :width 568}"
        self.assertEqual(update_image_dimensions(line), "![image|568](image.png)")

    def test_is_collapsed_line(self):
        self.assertTrue(is_collapsed_line("collapsed:: true"))
        self.assertFalse(is_collapsed_line("not collapsed"))

    def test_remove_block_links_embeds(self):
        line = "This is a block link ((12345)) and an embed {{embed 12345}}."
        self.assertEqual(
            remove_block_links_embeds(line), "This is a block link  and an embed ."
        )

    def test_convert_spaces_to_tabs(self):
        line = "    indented line"
        self.assertEqual(convert_spaces_to_tabs(line), "\tindented line")

    def test_convert_empty_line(self):
        line = "- "
        self.assertEqual(convert_empty_line(line), "")

    def test_add_space_after_hyphen_that_ends_line(self):
        line = "line ends with hyphen-"
        self.assertEqual(
            add_space_after_hyphen_that_ends_line(line), "line ends with hyphen- "
        )

    def test_prepend_code_block(self):
        line = "\t- ```python"
        self.assertEqual(
            prepend_code_block(line),
            ["\t- python code block below:\n", "\t```python\n"],
        )

    def test_escape_lt_gt(self):
        line = "This is a <test> line."
        self.assertEqual(escape_lt_gt(line), r"This is a \<test\> line.")

    def test_convert_todos(self):
        line = "- TODO"
        self.assertEqual(convert_todos(line), "- [ ]")
        line = "- DONE"
        self.assertEqual(convert_todos(line), "- [X]")

    def test_add_bullet_before_indented_image(self):
        line = "\t![image](image.png)"
        self.assertEqual(
            add_bullet_before_indented_image(line), "\t- ![image](image.png)"
        )

    def test_unindent_once(self):
        line = "\tindented line"
        self.assertEqual(unindent_once(line), "indented line")
        line = "- indented line"
        self.assertEqual(unindent_once(line), "indented line")

    def test_fix_escapes(self):
        old_str = "filename%3Aexample"
        self.assertEqual(fix_escapes(old_str), "filename.example")

    def test_unencode_filenames_for_links(self):
        old_str = "filename%3Aexample"
        self.assertEqual(unencode_filenames_for_links(old_str), "filename:example")


class TestUpdateLinksAndTags(unittest.TestCase):
    def setUp(self):
        self.args = type("", (), {})()  # Create a simple object to hold arguments
        self.args.convert_tags_to_links = False
        self.name_to_path = {
            "This/Type/OfLink": "/path/to/This/Type/OfLink",
            "Another/Link": "/path/to/Another/Link",
        }
        self.curr_path = "/path/to/current/file"

    def test_reformat_dates_in_links_with_convert_tags_to_links_true(self):
        self.args.convert_tags_to_links = True
        line = "[[Aug 24th, 2022]]"
        expected = "[[2022-08-24]]"
        result = update_links_and_tags(
            self.args, line, self.name_to_path, self.curr_path
        )
        self.assertEqual(result, expected)

    def test_reformat_dates_in_links_with_convert_tags_to_links_false(self):
        self.args.convert_tags_to_links = False
        line = "[[Aug 24th, 2022]]"
        expected = "#2022-08-24"
        result = update_links_and_tags(
            self.args, line, self.name_to_path, self.curr_path
        )
        self.assertEqual(result, expected)

    def test_fix_long_tag_convert_to_links(self):
        self.args.convert_tags_to_links = True
        line = "#[[this type of tag]]"
        expected = "[[this type of tag]]"
        result = update_links_and_tags(
            self.args, line, self.name_to_path, self.curr_path
        )
        self.assertEqual(result, expected)

    def test_fix_long_tag_convert_to_underscore(self):
        self.args.convert_tags_to_links = False
        line = "#[[this type of tag]]"
        expected = "#this_type_of_tag"
        result = update_links_and_tags(
            self.args, line, self.name_to_path, self.curr_path
        )
        self.assertEqual(result, expected)

    def test_convert_tag_to_link(self):
        self.args.convert_tags_to_links = True
        line = "#tag"
        expected = "[[tag]]"
        result = update_links_and_tags(
            self.args, line, self.name_to_path, self.curr_path
        )
        self.assertEqual(result, expected)

    def test_fix_link_existing_page_with_convert_tags_to_links_true(self):
        self.args.convert_tags_to_links = True
        line = "[[This/Type/NamespaceLink]]"
        expected = "[[This/Type/NamespaceLink]]"
        result = update_links_and_tags(
            self.args, line, self.name_to_path, self.curr_path
        )
        self.assertEqual(result, expected)

    def test_fix_link_existing_page_with_convert_tags_to_links_false(self):
        self.args.convert_tags_to_links = False
        line = "[[This/Type/NamespaceLink]]"
        expected = "#This/Type/NamespaceLink"
        result = update_links_and_tags(
            self.args, line, self.name_to_path, self.curr_path
        )
        self.assertEqual(result, expected)

    def test_fix_link_non_existing_page_convert_to_links(self):
        self.args.convert_tags_to_links = True
        line = "[[NonExistingPage]]"
        expected = "[[NonExistingPage]]"
        result = update_links_and_tags(
            self.args, line, self.name_to_path, self.curr_path
        )
        self.assertEqual(result, expected)

    def test_fix_link_non_existing_page_convert_to_tags(self):
        self.args.convert_tags_to_links = False
        line = "[[NonExistingPage]]"
        expected = "#NonExistingPage"
        result = update_links_and_tags(
            self.args, line, self.name_to_path, self.curr_path
        )
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
