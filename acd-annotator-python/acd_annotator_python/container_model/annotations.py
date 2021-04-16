# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

from pydantic import BaseModel
# StrictInt, etc does not attempt to do automatic type casting, e.g., "1" -> 1
from pydantic import StrictInt, StrictStr, StrictBool
from typing import List, Optional

from acd_annotator_python.container_model.common import BaseModelACD, BaseAnnotation, Entity
from acd_annotator_python.container_model.clinical_insights import InsightModelData, TemporalData


class Annotation(BaseAnnotation):
    negated: Optional[StrictBool]
    hypothetical: Optional[StrictBool]
    hypotheticalType: Optional[StrictStr]
    insightModelData: Optional[InsightModelData]
    temporal: Optional[List[TemporalData]]


class Trigger(Annotation):
    source: Optional[StrictStr]


class SectionTrigger(Trigger):
    sectionNormalizedName: Optional[StrictStr]


class Section(Annotation):
    trigger: Optional[SectionTrigger]
    sectionType: Optional[StrictStr]
    applyOnlyToACI: Optional[StrictBool]


class NluEntity(Annotation):
    relevance: Optional[float]
    source: Optional[StrictStr]


class Reference(BaseModelACD):
    uid: StrictInt
    type: StrictStr


class RelationNode(Entity):
    entity: Optional[Reference]


class Relation(Entity):
    source: Optional[StrictStr]
    score: Optional[float]
    nodes: List[RelationNode]


class SpellingCorrectionSuggestion(Entity):
    applied: StrictBool
    confidence: float
    semtypes: Optional[List[StrictStr]]
    text: Optional[StrictStr]


class SpellingCorrection(BaseAnnotation):
    suggestions: Optional[List[SpellingCorrectionSuggestion]]


class SpellCorrectedText(Entity):
    correctedText: Optional[StrictStr]
    debugText: Optional[StrictStr]


class SubjectConceptRelationship(Annotation):
    reference: Optional[StrictStr]
    score: Optional[float]
    term: Optional[StrictStr]


class DisambiguationData(BaseModelACD):
    validity: Optional[StrictStr]


class Concept(Annotation):
    componentId: Optional[StrictStr]
    conceptName: Optional[StrictStr]
    confidence: Optional[float]
    cui: Optional[StrictStr]
    links: Optional[StrictStr]
    mappings: Optional[StrictStr]
    mentionType: Optional[StrictStr]
    preferredName: Optional[StrictStr]
    semanticType: Optional[StrictStr]
    source: Optional[StrictStr]
    sourceVersion: Optional[StrictStr]
    subject: Optional[SubjectConceptRelationship]
    disambiguationData: Optional[DisambiguationData]


class ConceptValueEntry(BaseModelACD):
    value: Optional[StrictStr]
    unit: Optional[StrictStr]


class ConceptValue(Annotation):
    cui: Optional[StrictStr]
    dimension: Optional[StrictStr]
    preferredName: Optional[StrictStr]
    trigger: Optional[StrictStr]
    unit: Optional[StrictStr]
    value: Optional[StrictStr]
    rangeBegin: Optional[StrictStr]
    rangeEnd: Optional[StrictStr]
    values: Optional[List[ConceptValueEntry]]
    valuesFunction: Optional[StrictStr]
    normality: Optional[StrictStr]
    normalityTrigger: Optional[StrictStr]


class AttributeValueEntry(BaseModel):
    value: Optional[StrictStr]
    unit: Optional[StrictStr]
    frequency: Optional[StrictStr]
    duration: Optional[StrictStr]
    dimension: Optional[StrictStr]


class AttributeValueReference(BaseModel):
    valueIndex: Optional[StrictInt]
    uid: StrictInt
    type: StrictStr


class AttributeValueQualifierEntry(Annotation):
    value: Optional[StrictStr]
    qualifier: Optional[StrictStr]


class AttributeValue(Annotation):
    name: Optional[StrictStr]
    identifier: Optional[StrictStr]
    preferredName: Optional[StrictStr]
    values: Optional[List[AttributeValueEntry]]
    qualifiers: Optional[List[AttributeValueQualifierEntry]]
    operator: Optional[StrictStr]
    normality: Optional[StrictStr]
    normalityOperator: Optional[StrictStr]
    mode: Optional[StrictStr]
    source: Optional[StrictStr]
    sourceVersion: Optional[StrictStr]
    concept: Optional[Reference]
    conceptValue: Optional[Reference]
    disambiguationData: Optional[DisambiguationData]
    derivedFrom: Optional[List[AttributeValueReference]]


class HypotheticalSpan(Annotation):
    pass


class NegatedSpan(Annotation):
    trigger: Optional[Trigger]


class LabValueInd(Annotation):
    pass


class MedicationInd(Annotation):
    pass


class ProcedureInd(Annotation):
    pass


class SymptomDiseaseInd(Annotation):
    pass
