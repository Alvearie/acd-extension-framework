# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

from acd_annotator_python import container_utils


def test_compute_java_to_python_character_alignment():
    align = container_utils.compute_java_to_python_character_alignment(None)
    assert align is None

    align = container_utils.compute_java_to_python_character_alignment(u"")
    assert len(align) == 0

    align = container_utils.compute_java_to_python_character_alignment(u"a")
    assert len(align) == 1
    assert align[0] == 0  # a

    align = container_utils.compute_java_to_python_character_alignment(u"{}".format(chr(0x10000)))
    assert len(align) == 2
    assert align[0] == 0  # 0x10000 (surrogate pair char)
    assert align[1] == 1  # 0x10000 (surrogate pair char)

    align = container_utils.compute_java_to_python_character_alignment(u"{}a".format(chr(0x10000), chr(0x10ffff)))
    assert len(align) == 3
    assert align[0] == 0  # 0x10000 (surrogate pair char)
    assert align[1] == 1  # 0x10000 (surrogate pair char)
    assert align[2] == 1  # a

    align = container_utils.compute_java_to_python_character_alignment(u"a{}".format(chr(0x10000), chr(0x10ffff)))
    assert len(align) == 3
    assert align[0] == 0  # a
    assert align[1] == 0  # 0x10000 (surrogate pair char)
    assert align[2] == 1  # 0x10000 (surrogate pair char)

    align = container_utils.compute_java_to_python_character_alignment(u"a{}a{}a{}a"
                                                                       .format(chr(0xffff),
                                                                               chr(0x10000),
                                                                               chr(0x10ffff)))
    assert len(align) == 9
    assert align[0] == 0  # a
    assert align[1] == 0  # 0xffff (highest char that is not a surrogate pair)
    assert align[2] == 0  # a
    assert align[3] == 0  # 0x10000 (surrogate pair char)
    assert align[4] == 1  # 0x10000 (surrogate pair char)
    assert align[5] == 1  # a
    assert align[6] == 1  # 0x10ffff (surrogate pair char)
    assert align[7] == 2  # 0x10ffff (surrogate pair char)
    assert align[8] == 2  # a


def test_java2python():
    test_container = {}
    result = container_utils.java2python(test_container)
    assert result == test_container

    test_container = {'unstructured': []}
    result = container_utils.java2python(test_container)
    assert result == test_container

    test_container = {'unstructured': [{
        'text': 'the_cow_{}_jumped'.format(chr(0x10000))
    }]}
    result = container_utils.java2python(test_container)
    assert result == test_container

    test_container = {'unstructured': [{
        'text': 'the_cow_{}_jumped'.format(chr(0x10000)),
        'data': {}
    }]}
    result = container_utils.java2python(test_container)
    assert result == test_container

    # basic test
    test_container = {'unstructured': [{
        'text': 'the_cow_{}_jumped'.format(chr(0x10000)),
        'data': {"concepts": [
            {'cui': 'abc', 'coveredText': 'jumped', 'begin': 11, 'end': 17}
        ]}
    }]}
    result = container_utils.java2python(test_container)
    assert result['unstructured'][0]['data']['concepts'][0]['begin'] == 10
    assert result['unstructured'][0]['data']['concepts'][0]['end'] == 16

    # add more unknown hierarchy and make sure we find all begin/end spans
    test_container = {'unstructured': [{
        'text': 'the_cow_{}_jumped'.format(chr(0x10000)),
        'data': {"unknown_field": [{"unknown_field2": [
            {'coveredText': 'jumped', 'begin': 11, 'end': 17}
        ]}]}
    }]}
    result = container_utils.java2python(test_container)
    assert result['unstructured'][0]['data']['unknown_field'][0]['unknown_field2'][0]['begin'] == 10
    assert result['unstructured'][0]['data']['unknown_field'][0]['unknown_field2'][0]['end'] == 16

    # two surrogate pair characters. make sure we increment once after the first and twice after the second.
    test_container = {'unstructured': [{
        'text': 'the_cow_{}_jumped_{}_over'.format(chr(0x10000), chr(0x10ffff)),
        'data': {"concepts": [
            {'cui': 'abc', 'coveredText': 'jumped', 'begin': 11, 'end': 17},
            {'cui': 'abc', 'coveredText': 'over', 'begin': 21, 'end': 25}
        ]}
    }]}
    result = container_utils.java2python(test_container)
    # decremented once
    assert result['unstructured'][0]['data']['concepts'][0]['begin'] == 10
    assert result['unstructured'][0]['data']['concepts'][0]['end'] == 16
    # decremented twice
    assert result['unstructured'][0]['data']['concepts'][1]['begin'] == 19
    assert result['unstructured'][0]['data']['concepts'][1]['end'] == 23


def test_python2java():
    test_container = {}
    result = container_utils.python2java(test_container)
    assert result == test_container

    test_container = {'unstructured': []}
    result = container_utils.python2java(test_container)
    assert result == test_container

    test_container = {'unstructured': [{
        'text': 'the_cow_{}_jumped'.format(chr(0x10000))
    }]}
    result = container_utils.python2java(test_container)
    assert result == test_container

    test_container = {'unstructured': [{
        'text': 'the_cow_{}_jumped'.format(chr(0x10000)),
        'data': {}
    }]}
    result = container_utils.python2java(test_container)
    assert result == test_container

    # basic test
    test_container = {'unstructured': [{
        'text': 'the_cow_{}_jumped'.format(chr(0x10000)),
        'data': {"concepts": [
            {'cui': 'abc', 'coveredText': 'jumped', 'begin': 10, 'end': 16}
        ]}
    }]}
    result = container_utils.python2java(test_container)
    assert result['unstructured'][0]['data']['concepts'][0]['begin'] == 11
    assert result['unstructured'][0]['data']['concepts'][0]['end'] == 17

    # add more unknown hierarchy and make sure we find all begin/end spans
    test_container = {'unstructured': [{
        'text': 'the_cow_{}_jumped'.format(chr(0x10000)),
        'data': {"unknown_field": [{"unknown_field2": [
            {'coveredText': 'jumped', 'begin': 10, 'end': 16}
        ]}]}
    }]}
    result = container_utils.python2java(test_container)
    assert result['unstructured'][0]['data']['unknown_field'][0]['unknown_field2'][0]['begin'] == 11
    assert result['unstructured'][0]['data']['unknown_field'][0]['unknown_field2'][0]['end'] == 17

    # two surrogate pair characters. make sure we increment once after the first and twice after the second.
    test_container = {'unstructured': [{
        'text': 'the_cow_{}_jumped_{}_over'.format(chr(0x10000), chr(0x10ffff)),
        'data': {"concepts": [
            {'cui': 'abc', 'coveredText': 'jumped', 'begin': 10, 'end': 16},
            {'cui': 'abc', 'coveredText': 'over', 'begin': 19, 'end': 23}
        ]}
    }]}
    result = container_utils.python2java(test_container)
    # decremented once
    assert result['unstructured'][0]['data']['concepts'][0]['begin'] == 11
    assert result['unstructured'][0]['data']['concepts'][0]['end'] == 17
    # decremented twice
    assert result['unstructured'][0]['data']['concepts'][1]['begin'] == 21
    assert result['unstructured'][0]['data']['concepts'][1]['end'] == 25

