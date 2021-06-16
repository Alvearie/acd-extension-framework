# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

import re
import json

import acd_annotator_python.container_model.main as acd_datamodel


def java2python(container_group_dict: dict):
    """
    Java reports offsets slightly differently from Python in cases where
    there are high code point unicode characters.

    For example, in java:
    "\u0000".length() == 1
    ...
    "\uffff".length() == 1
    "\u10000".length() == 2
    ...
    "\u10ffff".length() == 2

    whereas python reports the length of all of these strings to be 1.
    This method translates from java-centric begin/end spans (returned by most ACD annotators)
    to python-centric spans.

    :param container_group_dict:
    :return:
    """
    return span_conversion_helper(container_group_dict, additive_adjustments=False)


def python2java(container_group_dict: dict):
    """
    Java reports offsets slightly differently from Python in cases where
    there are high code point unicode characters.

    For example, in java:
    "\u0000".length() == 1
    ...
    "\uffff".length() == 1
    "\u10000".length() == 2
    ...
    "\u10ffff".length() == 2

    whereas python reports the length of all of these strings to be 1.
    This method translates from python-centric begin/end spans
    to java-centric spans (returned by most ACD annotators).

    :param container_group_dict:
    :return:
    """
    return span_conversion_helper(container_group_dict, additive_adjustments=True)


# this regex finds any characters between \u10000 - \u10ffff, which java will encode as len()==2
# surprisingly, in this case regex is faster than any other kind of search we experimented with
unicode_surrogate_pair_regex = re.compile('[{}-{}]'.format(chr(0x10000), chr(0x10ffff)))


def compute_java_to_python_character_alignment(text: str):
    """
    Constructs a list that adjusts alignment between the Java character count and the python character count.

    Given text that looks like this:
            the_cow_?_jumped_
    Java       3   7 11     17
    python     3   7 10     16

    And a concept that looks like this:
        text: Jumped
        begin: 11
        end  : 17

    We need to convert this to begin=10,end=16. To do this we need to first construct the following
    alignment that maps indices in the java character string to an aggregate count of surrogate pairs that preceded it.

    0...7  8  9  10 ... 17
    |   |  |  |  |      |
    V   V  V  V  V      V
    0   0  0  1  1      1

    :param text:
    :return:
    """
    if text is None:
        return None
    java2python_alignment = []
    previous_start = 0
    num_preceding_surrogate_pairs = 0
    for match in unicode_surrogate_pair_regex.finditer(text):
        # add the chunk from the previous position up to but not including ourselves
        chars_since_previous_match = match.start() - previous_start
        java2python_alignment.extend([num_preceding_surrogate_pairs] * chars_since_previous_match)
        # now add one additional character because this is where java double-count surrogate pairs
        # this corresponds to the first character of the surrogate pair.
        java2python_alignment.append(num_preceding_surrogate_pairs)
        # now increment the number of surrogate pairs we've seen and update our start position
        # so we'll be ready to add the next chunk
        num_preceding_surrogate_pairs += 1
        previous_start = match.start()
    # finish off the last chunk
    chars_since_previous_match = len(text) - previous_start
    java2python_alignment.extend([num_preceding_surrogate_pairs] * chars_since_previous_match)
    return java2python_alignment


def update_spans(adict: dict, java2py_alignment: list, additive_adjustments: bool):
    """adjust begin/end spans either upwards (if additive_adjustments is True)
      of downwards (if additive_adjustments is False) according to how many
      surrogate pairs preceded it in the text."""
    # recurse (this isn't protected against backlinks, etc, but if we just call this on
    # container groups parsed from json that's fine)
    for k, v in adict.items():
        if isinstance(v, dict):
            update_spans(v, java2py_alignment, additive_adjustments)
        elif isinstance(v, list):
            for item in v:
                update_spans(item, java2py_alignment, additive_adjustments)
    # update any begin/end in current dictionary
    if 'begin' in adict:
        # compute span adjustments, default to the last if the index is off the back edge of the container.
        try:
            begin = int(adict['begin'])
            begin_adjustment = java2py_alignment[begin] if begin < len(java2py_alignment) else java2py_alignment[-1]
            # apply the adjustments
            if additive_adjustments:
                adict['begin'] = begin + begin_adjustment
            else:
                adict['begin'] = begin - begin_adjustment
        except ValueError:
            pass  # there's a begin that isn't an int value. That seems weird, but we'll wait and let validation explode
    if 'end' in adict:
        try:
            end = int(adict['end'])
            end_adjustment = java2py_alignment[end] if end < len(java2py_alignment) else java2py_alignment[-1]
            # apply the adjustments
            if additive_adjustments:
                adict['end'] = end + end_adjustment
            else:
                adict['end'] = end - end_adjustment
        except ValueError:
            pass  # there's a begin that isn't an int value. That seems weird, but we'll wait and let validation explode


def span_conversion_helper(container_group_dict, additive_adjustments: bool, mutate_inplace=True):
    """adjust begin/end spans either upwards (if additive_adjustments is True)
      of downwards (if additive_adjustments is False) according to how many
      surrogate pairs preceded it in the text."""
    if container_group_dict is None:
        return container_group_dict
    # optionally make a deep copy. This should not normally be necessary
    if not mutate_inplace:
        container_group_dict = json.loads(json.dumps(container_group_dict))
    if 'unstructured' in container_group_dict:
        for unstructured_container in container_group_dict['unstructured']:
            # each unstructured container has text, data
            if unstructured_container is not None:
                if 'data' in unstructured_container and 'text' in unstructured_container:
                    data = unstructured_container['data']
                    text = unstructured_container['text']
                    # only proceed if there are surrogate pairs in the doc. Otherwise, nothing to do.
                    if bool(unicode_surrogate_pair_regex.search(text)):
                        # yes, computing the alignment runs the regex a second time, but the search above is
                        # significantly faster (.4 secs for 1M iters over a word vs .6 secs), so it's worth doing
                        # it up front and then following up with this given that most docs won't have these kinds
                        # of characters.
                        java2python_alignment = compute_java_to_python_character_alignment(text)
                        update_spans(data, java2python_alignment, additive_adjustments)
    return container_group_dict


def from_dict(container_group_dict):
    """Create an object from from a dictionary"""
    return acd_datamodel.ContainerGroup(**container_group_dict)


def create_unstructured_container():
    """create a new object to slot into unstructured.data"""
    return acd_datamodel.UnstructuredContainerData()

def create_structured_container():
    """create a new object to slot into structured.data"""
    return acd_datamodel.StructuredContainerData()


def to_dict(container_group):
    """convert an object model to a python dictionary"""
    return container_group.dict(exclude_none=True)
