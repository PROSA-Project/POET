"""
This module contains miscellanea utility functions.
"""

import itertools
import re


# Returns a string containing all the elements of a given list in the form "a,b,c"
def pretty_list(list):
    return ", ".join(list)


def patch(text, wildcard, patch):
    # Given a text, replaces the occurrences of the wildcard with the given patch.
    # In case of single-line patches, the code just performs a replace. In case of
    # multi-line patches, the code tries to preserves the indentation of the wildcard
    # for all lines.
    # e.g.
    #              $PATCH$
    # <------------>
    #
    #  becomes...
    #              Patched line 1
    #              Patched line 2
    # <------------>
    patch = str(patch)
    patch_lines = patch.split("\n")
    if len(patch_lines) == 1:  # Single-line patch, easy.
        return text.replace(wildcard, patch)
    else:  # Multi-line patch. Here, we want to preserve indentation as much as possible.
        # match the preceding characters since the last newline (^) as a group for easy retrieval
        line_with_wildcard_re = re.compile("^(.*)" + re.escape(wildcard), re.MULTILINE)

        # function to replace one matched lined
        def insert_lines(match):
            first_indent = match.group(1)
            follow_indent = re.sub(r"\S", " ", match.group(1))
            first_line = [first_indent + patch_lines[0]]
            follow_lines = (follow_indent + line for line in patch_lines[1:])
            return "\n".join(itertools.chain(first_line, follow_lines))

        return line_with_wildcard_re.sub(insert_lines, text)


def conditional_cut_patch(text, wildcard_start, wildcard_end, cut):
    # Given a text, the code acts on every portion of text of the form
    # "wildcard_start ... wildcard_end".
    # If cut is specified, the text enclosed in the wildcards and the wildcards
    # are cut away. Otherwise, only the wildcards are removed.
    # e.g.
    # wildcard_start = $X$ and wildcard_end = $Y$
    # I am $X$not $Y$a bunny.
    # <------------>
    #
    #  becomes...
    #              I am a bunny.            if cut=True
    #              I am not a bunny.        if cut=False
    # <------------>
    # The function returns the update text and the cut text
    if cut:
        assert wildcard_start in text
        assert wildcard_end in text
        wc_re = re.compile(
            re.escape(wildcard_start) + r"([\S\s]*)" + re.escape(wildcard_end),
            re.MULTILINE,
        )
        match = wc_re.search(text)
        cut_text = match.group(1)
        return wc_re.sub("", text), cut_text
    else:
        text = text.replace(wildcard_start, "")
        text = text.replace(wildcard_end, "")
        return text, ""
