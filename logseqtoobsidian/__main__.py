
import argparse
import logging
import os
import re
import shutil

import logseqtoobsidian.convert_notes
from logseqtoobsidian.convert_notes import add_bullet_before_indented_image, add_space_after_hyphen_that_ends_line, convert_empty_line, convert_spaces_to_tabs, convert_todos, escape_lt_gt, fix_escapes, get_namespace_hierarchy, is_collapsed_line, is_empty_markdown_file, is_markdown_file, prepend_code_block, remove_block_links_embeds, unencode_filenames_for_links, unindent_once, update_assets, update_image_dimensions, update_links_and_tags


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")

    parser = argparse.ArgumentParser()

    parser.add_argument("--logseq", help="base directory of logseq graph", required=True)
    parser.add_argument(
        "--output", help="base directory where output should go", required=True
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
        raise ValueError(f"The directory '{old_base}' does not exist or is not a valid directory.")

    if args.overwrite_output and os.path.exists(new_base):
        shutil.rmtree(new_base)

    os.makedirs(new_base, exist_ok=False)

    # Copy journals pages to their own subfolder
    old_journals = os.path.join(old_base, "journals")
    assert os.path.isdir(old_journals)

    new_journals = os.path.join(new_base, "journals")
    os.mkdir(new_journals)

    logging.info("Now beginning to copy the journal pages")
    for fname in os.listdir(old_journals):
        fpath = os.path.join(old_journals, fname)
        logging.info("Now copying the journal page: " + fpath)
        if os.path.isfile(fpath):
            if not is_empty_markdown_file(fpath):
                new_fpath = os.path.join(new_journals, fname)
                
                if args.journal_dashes:
                    new_fpath = new_fpath.replace("_","-")

                shutil.copyfile(fpath, new_fpath)
                old_to_new_paths[fpath] = new_fpath
                new_to_old_paths[new_fpath] = fpath
                new_paths.add(new_fpath)

                newfile = os.path.splitext(fname)[0]
                old_pagenames_to_new_paths[newfile] = new_fpath

                if args.journal_dashes:
                    old_pagenames_to_new_paths[newfile.replace("_","-")] = new_fpath
            else:
                pages_that_were_empty.add(fname)

    # Copy other markdown files to the new base folder, creating subfolders for namespaces
    old_pages = os.path.join(old_base, "pages")
    assert os.path.isdir(old_pages)

    logging.info("Now beginning to copy the non-journal pages")
    for fname in os.listdir(old_pages):
        fpath = os.path.join(old_pages, fname)
        logging.info("Now copying the non-journal page: " + fpath)
        if os.path.isfile(fpath) and is_markdown_file(fpath):
            hierarchy = get_namespace_hierarchy(args, fname)
            hierarchical_pagename = "/".join(hierarchy)
            if is_empty_markdown_file(fpath):
                pages_that_were_empty.add(fname)
            else:
                new_fpath = os.path.join(new_base, *hierarchy)
                new_fpath = fix_escapes(new_fpath)
                logging.info("Destination path: " + new_fpath)
                new_dirname = os.path.split(new_fpath)[0]
                os.makedirs(new_dirname, exist_ok=True)
                shutil.copyfile(fpath, new_fpath)
                old_to_new_paths[fpath] = new_fpath
                new_to_old_paths[new_fpath] = fpath
                new_paths.add(new_fpath)

                old_pagename = os.path.splitext(hierarchical_pagename)[0]
                old_pagenames_to_new_paths[
                    old_pagename
                ] = new_fpath
                # Add mapping of unencoded filename for links
                old_pagenames_to_new_paths[
                    unencode_filenames_for_links(old_pagename)
                ] = new_fpath

    # Second loop: for each new file, reformat its content appropriately
    for fpath in new_paths:
        newlines = []
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

            # First replace the 'title:: my note' style of front matter with the Obsidian style (triple dashed)
            front_matter = {}
            in_front_matter = False
            first_line_after_front_matter = 0
            for idx, line in enumerate(lines):
                match = re.match(r"(.*?)::[\s]*(.*)", line)
                if match is not None:
                    front_matter[match[1]] = match[2]
                    first_line_after_front_matter = idx + 1
                else:
                    break
            if bool(front_matter):
                # import ipdb; ipdb.set_trace()
                newlines.append("---\n")
                for key in front_matter:
                    if (key.find("tags") >= 0 or key.find("Tags") >= 0) and args.tag_prop_to_taglist:
                        # convert tags:: value1, #[[value 2]] 
                        # to
                        # taglinks: 
                        #   - "[[value1]]"
                        #   - "[[value 2]]"
                        tags = front_matter[key].split(",")

                        newlines.append("Taglinks:\n")
                        for tag in tags:
                            tag = tag.strip()
                            clean_tag = tag.replace("#","")
                            clean_tag = clean_tag.replace("[[","")
                            clean_tag = clean_tag.replace("]]","")

                            newlines.append('  - "[[' + clean_tag + ']]"' + "\n")
                    else:
                        newlines.append(key + ": " + front_matter[key] + "\n")
                newlines.append("---\n")

            for line in lines[first_line_after_front_matter:]:
                ORIGINAL_LINE = line

                # Update global state if this is the end of a code block
                if logseqtoobsidian.convert_notes.__dict__["INSIDE_CODE_BLOCK"] and line == "```\n":
                    logseqtoobsidian.convert_notes.__dict__["INSIDE_CODE_BLOCK"] = False

                # Ignore if the line if it's a collapsed:: true line
                if is_collapsed_line(line):
                    continue

                # Convert empty lines in logseq to empty lines in Obsidian
                line = convert_empty_line(line)

                # Convert 2-4 spaces to a tab
                line = convert_spaces_to_tabs(line)

                # Unindent once if the user requested it
                if args.unindent_once:
                    line = unindent_once(line)

                # Add a line above the start of a code block in a list
                lines = prepend_code_block(line)
                if len(lines) > 0:
                    newlines.append(lines[0])
                    line = lines[1]

                # Update links and tags
                line = update_links_and_tags(args, line, old_pagenames_to_new_paths, fpath)

                # Update assets
                line = update_assets(line, new_to_old_paths[fpath], fpath)

                # Update image dimensions
                line = update_image_dimensions(line)

                # Remove block links and embeds
                line = remove_block_links_embeds(line)

                # Self-explanatory
                line = add_space_after_hyphen_that_ends_line(line)

                # Self-explanatory
                line = convert_todos(line)

                # < and > need to be escaped to show up as normal characters in Obsidian
                line = escape_lt_gt(line)

                # Make sure images are indented correctly
                line = add_bullet_before_indented_image(line)

                newlines.append(line)

        with open(fpath, "w", encoding="utf-8") as f:
            f.writelines(newlines)

if __name__ == "__main__":
    main()
