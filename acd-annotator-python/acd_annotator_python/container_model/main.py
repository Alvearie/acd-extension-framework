# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

from pydantic import BaseModel, validator, root_validator, Extra
# StrictInt, etc does not attempt to do automatic type casting, e.g., "1" -> 1
from pydantic import StrictInt, StrictStr, StrictBool, StrictFloat
from pydantic.fields import ModelField
from typing import List, Optional, Any, Dict

from acd_annotator_python.container_model.common import BaseModelACD, BaseAnnotation, Entity
from acd_annotator_python.container_model.clinical_insights import InsightModelData, TemporalData
from acd_annotator_python.container_model.annotations import Annotation
from acd_annotator_python.container_model.annotations import Concept
from acd_annotator_python.container_model.annotations import ConceptValue
from acd_annotator_python.container_model.annotations import SymptomDiseaseInd
from acd_annotator_python.container_model.annotations import ProcedureInd
from acd_annotator_python.container_model.annotations import MedicationInd
from acd_annotator_python.container_model.annotations import LabValueInd
from acd_annotator_python.container_model.annotations import AttributeValue
from acd_annotator_python.container_model.annotations import HypotheticalSpan
from acd_annotator_python.container_model.annotations import Section
from acd_annotator_python.container_model.annotations import NegatedSpan
from acd_annotator_python.container_model.annotations import NluEntity
from acd_annotator_python.container_model.annotations import Relation
from acd_annotator_python.container_model.annotations import SpellingCorrection
from acd_annotator_python.container_model.annotations import SpellCorrectedText


class UnstructuredContainerData(BaseModelACD):

    # mature annotators
    attributeValues: Optional[List[AttributeValue]]
    concepts: Optional[List[Concept]]
    conceptValues: Optional[List[ConceptValue]]
    hypotheticalSpans: Optional[List[HypotheticalSpan]]
    sections: Optional[List[Section]]
    negatedSpans: Optional[List[NegatedSpan]]
    nluEntities: Optional[List[NluEntity]]
    relations: Optional[List[Relation]]
    spellingCorrections: Optional[List[SpellingCorrection]]
    spellCorrectedText: Optional[List[SpellCorrectedText]]
    temporalSpans: Optional[List[TemporalData]]

    SymptomDiseaseInd: Optional[List[SymptomDiseaseInd]]
    ProcedureInd: Optional[List[ProcedureInd]]
    MedicationInd: Optional[List[MedicationInd]]
    LabValueInd: Optional[List[LabValueInd]]

    # experimental annotators
    AllergyMedicationInd: Optional[List[Annotation]]
    AllergyInd: Optional[List[Annotation]]
    BathingAssistanceInd: Optional[List[Annotation]]
    IcaCancerDiagnosisInd: Optional[List[Annotation]]
    DressingAssistanceInd: Optional[List[Annotation]]
    EatingAssistanceInd: Optional[List[Annotation]]
    EjectionFractionInd: Optional[List[Annotation]]
    EmailAddressInd: Optional[List[Annotation]]
    PersonInd: Optional[List[Annotation]]
    US_PhoneNumberInd: Optional[List[Annotation]]
    LocationInd: Optional[List[Annotation]]
    MedicalInstitutionInd: Optional[List[Annotation]]
    OrganizationInd: Optional[List[Annotation]]
    SeeingAssistanceInd: Optional[List[Annotation]]
    SmokingInd: Optional[List[Annotation]]
    ToiletingAssistanceInd: Optional[List[Annotation]]
    WalkingAssistanceInd: Optional[List[Annotation]]


class Container(BaseModelACD):
    id: Optional[str] = None
    type: Optional[str] = None
    data: Optional[UnstructuredContainerData]
    metadata: Optional[Dict[str, Any]] = None
    uid: Optional[int] = None


class UnstructuredContainer(Container):
    text: StrictStr


class StructuredContainer(Container):
    pass


class ContainerGroup(BaseModel):
    class Config:
        """extra='forbid' tells pydantic to throw a validation error if it sees any extra fields at this level."""
        extra = Extra.forbid
    unstructured: Optional[List[UnstructuredContainer]]
    structured: Optional[List[StructuredContainer]]

