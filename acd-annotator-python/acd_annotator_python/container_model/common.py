# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

from pydantic import BaseModel, validator, root_validator, Extra, Field
# StrictInt, etc does not attempt to do automatic type casting, e.g., "1" -> 1
from pydantic import StrictInt, StrictStr
from pydantic.fields import ModelField
from typing import Optional, Any, Dict


def normalize_field_names(fields):
    """
    Map field names to a normalized form to check for collisions like 'coveredText' vs 'covered_text'
    """
    return set(s.replace('_','').lower() for s in fields)


class BaseModelACD(BaseModel):
    """
    Every new object should extend this one directly or indirectly, treating it
    like you normally would pydantic.BaseModel.
    """

    class Config:
        """Additional config that should be inherited by every object in our data model."""
        # allow extra fields to be parsed/created and preserve them so they are
        # still there in the output.
        extra = Extra.allow
        # allow the object graph to be edited. This is true by default, but can't hurt to be explicit.
        allow_mutation = True
        # run validation whenever an item in the object graph is edited
        validate_assignment = True
        # Note: we experimented briefly with aliases to allow snake case to be converted to camelCase,
        # but it changed some behavior deep in pydantic and broke some seemingly unrelated test cases.
        # Also, it would probably cause more confusion that it was worth to allow code to specify snake case
        # when the container is in camelCase--not worth the convenience.
        # alias_generator = camel_to_snake_case
        # allow_population_by_field_name = True

    # TODO: pydantic happily casts [] -> {} for class creation, which isn't ideal.
    # But the following doesn't work, because the cast has already happened before the pre root
    # validator is called. Not a super critical validation case, but we can work out how to
    # accomplish this later.
    # @root_validator(pre=True, allow_reuse=True)
    # def input_is_dict(cls, values):
    #     """Make sure that every object is a dict. Don't promote empty lists."""
    #     if values is not None and not isinstance(values, dict):
    #         raise ValueError('input must be a dict. Found {}'.format(type(values)))
    #     return values

    @classmethod
    def add_fields(cls, **field_definitions: Any):
        """
        This class lets a caller define new custom fields in the container model by
        dynamically inserting fields inplace, so that when the service parses an incoming container
        that container can be parsed with the new fields in mind, applying validation, etc.
        """
        new_fields: Dict[str, ModelField] = {}
        new_annotations: Dict[str, Optional[type]] = {}

        for f_name, f_annotation in field_definitions.items():
            new_annotations[f_name] = f_annotation
            new_fields[f_name] = ModelField.infer(name=f_name, value=None, annotation=f_annotation,
                                                  class_validators=None, config=cls.__config__)

        cls.__fields__.update(new_fields)
        cls.__annotations__.update(new_annotations)

    @root_validator(pre=True, skip_on_failure=True)
    def check_for_misspellings(cls, values):
        """
        Make sure that we don't allow input that is likely to be a misspelling by
        normalizing text and then checking for collisions (like coveredText vs covered_text).
        """
        normalized_values = normalize_field_names(values.keys())
        # these are all the provided values that don't exactly match a known field
        non_matches = set(values.keys()).difference(cls.__fields__.keys())
        # if any non-matches collide with a known field after normalization, complain
        normalized_non_matches = normalize_field_names(non_matches)
        # normalize the built-in fields (cache these per class so we don't have to re-normalize a bunch of times)
        if not hasattr(cls, '_normalized_pydantic_fields)'):
            cls._normalized_pydantic_fields = normalize_field_names(cls.__fields__.keys())
        collisions = normalized_non_matches.intersection(cls._normalized_pydantic_fields)
        assert len(collisions) == 0, \
            f'Misspelling detected: {non_matches} collides with expected field in {list(cls.__fields__.keys())}'
        return values


class Entity(BaseModelACD):
    id: Optional[StrictStr]
    uid: Optional[StrictInt]
    type: Optional[StrictStr]
    mergeid: Optional[StrictInt]


class BaseAnnotation(Entity):
    begin: StrictInt
    end: StrictInt
    coveredText: Optional[StrictStr]

    @validator('begin', 'end')
    def gte_zero(cls, v):
        if not v >= 0:
            raise ValueError(f'begin,end must be greater than or equal to 0. Found {v}')
        return v

    # pre=False means run this after regular validators.
    # skip_on_failure means we won't try to run this if a previous validator failed
    # because in that case we might not have begin,end
    @root_validator(pre=False, skip_on_failure=True)
    def begin_lt_end(cls, values):
        begin, end = values['begin'], values['end']
        if not begin < end:
            raise ValueError(f'begin must be strictly less than end. Found begin={begin}, end={end}')
        return values

    @root_validator(pre=False, skip_on_failure=True)
    def covered_text_len(cls, values):
        begin, end, covered_text = values['begin'], values['end'], values.get('coveredText')
        if covered_text is not None:
            if (end - begin) != len(covered_text):
                # Note: don't log the covered text itself!
                raise ValueError(f'covered text length must be equal to end-begin. '
                                 f'Found begin={begin}, end={end}, coveredText length={len(covered_text)}')
        return values
