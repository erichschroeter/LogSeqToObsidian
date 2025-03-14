import argparse
import logging
import os
import re
import shutil

import logseqtoobsidian.convert_notes
from logseqtoobsidian.convert_notes import (
    convert_contents,
    copy_journals,
    copy_pages,
)


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    # Define the color codes
    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset_color = self.COLORS["RESET"]
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        return super().format(record)


def main():
    # Set up logging with custom formatter
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter("%(levelname)s: %(message)s"))
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--logseq", help="base directory of logseq graph", required=True
    )
    parser.add_argument(
        "--output", help="base directory where output should go", required=True
    )
    parser.add_argument(
        "--assets_dir", help="directory where assets are copied", default="attachments", required=False
    )
    parser.add_argument(
        "--dryrun",
        help="don't actually do anything, just see what would happen",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--overwrite_output",
        dest="overwrite_output",
        default=False,
        action="store_true",
        help="overwrites output directory if included",
    )
    parser.add_argument(
        "--unindent_once",
        default=False,
        action="store_true",
        help="unindents all lines once - lines at the highest level will have their bullet point removed",
    )
    parser.add_argument(
        "--journal_dashes",
        default=False,
        action="store_true",
        help="use dashes in daily journal - e.g. 2023-12-03.md",
    )
    parser.add_argument(
        "--tag_prop_to_taglist",
        default=False,
        action="store_true",
        help="convert tags in tags:: property to a list of tags in front matter",
    )
    parser.add_argument(
        "--ignore_dot_for_namespaces",
        default=False,
        action="store_true",
        help="ignore the use of '.' as a namespace character",
    )
    parser.add_argument(
        "--convert_tags_to_links",
        default=False,
        action="store_true",
        help="Convert #[[long tags]] to [[long tags]]",
    )

    args = parser.parse_args()

    old_base = args.logseq
    new_base = args.output

    old_to_new_paths = {}
    new_to_old_paths = {}
    new_paths = set()
    pages_that_were_empty = set()
    old_pagenames_to_new_paths = {}

    # First loop: copy files to their new location, populate the maps and list of paths

    if not os.path.exists(old_base) or not os.path.isdir(old_base):
        raise ValueError(
            f"The directory '{old_base}' does not exist or is not a valid directory."
        )

    if args.overwrite_output and os.path.exists(new_base):
        shutil.rmtree(new_base)

    os.makedirs(new_base, exist_ok=args.overwrite_output)

    # Copy journals pages to their own subfolder
    old_journals = os.path.join(old_base, "journals")
    assert os.path.isdir(old_journals)

    new_journals = os.path.join(new_base, "journals")
    os.mkdir(new_journals)

    logging.debug("Beginning to copy the journal pages")
    copy_journals(
        args,
        old_journals,
        new_journals,
        old_to_new_paths,
        new_to_old_paths,
        new_paths,
        pages_that_were_empty,
        old_pagenames_to_new_paths,
    )

    # Copy other markdown files to the new base folder, creating subfolders for namespaces
    old_pages = os.path.join(old_base, "pages")
    assert os.path.isdir(old_pages)

    logging.debug("Beginning to copy the non-journal pages")
    copy_pages(
        args,
        old_pages,
        new_base,
        old_to_new_paths,
        new_to_old_paths,
        new_paths,
        pages_that_were_empty,
        old_pagenames_to_new_paths,
    )

    # Second loop: for each new file, reformat its content appropriately
    convert_contents(
        args,
        new_paths,
        old_pagenames_to_new_paths,
        new_to_old_paths,
    )


if __name__ == "__main__":
    main()
