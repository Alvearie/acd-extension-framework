# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #

# Note: StrictFloat is not suitable because it will not cast from int->float.
# So, e.g., 0 will fail validation
from typing import List, Optional

from acd_annotator_python.container_model.common import BaseModelACD, BaseAnnotation, Entity


class InsightModelModifiers(BaseModelACD):
    sites: Optional[List[BaseAnnotation]]
    associatedProcedures: Optional[List[BaseAnnotation]]
    associatedDiagnoses: Optional[List[BaseAnnotation]]


class BaseInsightModel(BaseModelACD):
    modifiers: Optional[InsightModelModifiers]


class InsightModelMedicationUsage(BaseModelACD):
    explicitScore: Optional[float]
    consideringScore: Optional[float]
    discussedScore: Optional[float]


class InsightModelMedicationLifecycleEvent(BaseModelACD):
    score: Optional[float]
    usage: Optional[InsightModelMedicationUsage]


class InsightModelMedicationAdverseEvent(BaseInsightModel):
    score: Optional[float]
    allergyScore: Optional[float]
    usage: Optional[InsightModelMedicationUsage]


class InsightModelMedication(BaseInsightModel):
    usage: Optional[InsightModelMedicationUsage]
    startedEvent: Optional[InsightModelMedicationLifecycleEvent]
    stoppedEvent: Optional[InsightModelMedicationLifecycleEvent]
    doseChangedEvent: Optional[InsightModelMedicationLifecycleEvent]
    adverseEvent: Optional[InsightModelMedicationAdverseEvent]


class InsightModelDiagnosisUsage(BaseModelACD):
    explicitScore: Optional[float]
    implicitScore: Optional[float]
    patientReportedScore: Optional[float]
    discussedScore: Optional[float]


class InsightModelDiagnosis(BaseModelACD):
    usage: Optional[InsightModelDiagnosisUsage]
    suspectedScore: Optional[float]
    symptomScore: Optional[float]
    traumaScore: Optional[float]
    familyHistoryScore: Optional[float]
    modifiers: Optional[InsightModelModifiers]


class InsightModelProcedureUsage(BaseModelACD):
    explicitScore: Optional[float]
    pendingScore: Optional[float]
    discussedScore: Optional[float]


class InsightModelProcedureTask(BaseModelACD):
    therapeuticScore: Optional[float]
    diagnosticScore: Optional[float]
    labTestScore: Optional[float]
    surgicalTaskScore: Optional[float]
    clinicalAssessmentScore: Optional[float]


class InsightModelProcedureType(BaseModelACD):
    deviceScore: Optional[float]
    materialScore: Optional[float]
    medicationScore: Optional[float]
    procedureScore: Optional[float]
    conditionManagementScore: Optional[float]


class InsightModelProcedure(BaseModelACD):
    usage: Optional[InsightModelProcedureUsage]
    task: Optional[InsightModelProcedureTask]
    type: Optional[InsightModelProcedureType]
    modifiers: Optional[InsightModelModifiers]


class InsightModelNormalityUsage(BaseModelACD):
    normalScore: Optional[float]
    abnormalScore: Optional[float]
    unknownScore: Optional[float]
    quantitativeScore: Optional[float]
    nonFindingScore: Optional[float]


class InsightModelNormality(BaseModelACD):
    usage: Optional[InsightModelNormalityUsage]
    directlyAffectedScore: Optional[float]
    evidence: Optional[List[BaseAnnotation]]
    modifiers: Optional[InsightModelModifiers]


class TemporalType(Entity):
    dateScore: Optional[float]
    timeScore: Optional[float]
    relativeScore: Optional[float]


class TemporalRelTypes(Entity):
    overlapsScore: Optional[float]
    durationScore: Optional[float]


class TemporalData(BaseAnnotation):
    temporalType: Optional[TemporalType]
    relationTypes: Optional[TemporalRelTypes]


class InsightModelTobaccoUsage(BaseModelACD):
    useScore: Optional[float]
    noneScore: Optional[float]
    unknownScore: Optional[float]
    discussedScore: Optional[float]


class InsightModelTobaccoUseStatus(BaseModelACD):
    currentScore: Optional[float]
    stoppedScore: Optional[float]
    neverScore: Optional[float]


class InsightModelTobacco(BaseModelACD):
    usage: Optional[InsightModelTobaccoUsage]
    useStatus: Optional[InsightModelTobaccoUseStatus]
    exposureScore: Optional[float]
    familyHistoryScore: Optional[float]
    nonPatientScore: Optional[float]
    treatmentScore: Optional[float]


class InsightModelAlcoholUsage(BaseModelACD):
    useScore: Optional[float]
    noneScore: Optional[float]
    unknownScore: Optional[float]
    discussedScore: Optional[float]


class InsightModelAlcoholUseStatus(BaseModelACD):
    stoppedScore: Optional[float]
    neverScore: Optional[float]


class InsightModelAlcoholUseQualifier(BaseModelACD):
    lightScore: Optional[float]
    moderateScore: Optional[float]
    heavyScore: Optional[float]
    abuseScore: Optional[float]


class InsightModelAlcohol(BaseModelACD):
    usage: Optional[InsightModelAlcoholUsage]
    useStatus: Optional[InsightModelAlcoholUseStatus]
    useQualifier: Optional[InsightModelAlcoholUseQualifier]
    exposureScore: Optional[float]
    nonPatientScore: Optional[float]
    treatmentScore: Optional[float]


class InsightModelIllicitDrugUsage(BaseModelACD):
    useScore: Optional[float]
    noneScore: Optional[float]
    unknownScore: Optional[float]
    discussedScore: Optional[float]
    treatmentScore: Optional[float]


class InsightModelIllicitDrugUseStatus(BaseModelACD):
    currentScore: Optional[float]
    stoppedScore: Optional[float]
    neverScore: Optional[float]
    complianceScore: Optional[float]


class InsightModelIllicitDrugUseQualifier(BaseModelACD):
    lightScore: Optional[float]
    moderateScore: Optional[float]
    heavyScore: Optional[float]


class InsightModelIllicitDrugUseDimension(BaseModelACD):
    medicalScore: Optional[float]
    abuseScore: Optional[float]


class InsightModelIllicitDrug(BaseModelACD):
    usage: Optional[InsightModelIllicitDrugUsage]
    useStatus: Optional[InsightModelIllicitDrugUseStatus]
    useQualifier: Optional[InsightModelIllicitDrugUseQualifier]
    useDimension: Optional[InsightModelIllicitDrugUseDimension]
    exposureScore: Optional[float]
    nonPatientScore: Optional[float]
    treatmentScore: Optional[float]


class InsightModelData(Entity):
    medication: Optional[InsightModelMedication]
    diagnosis: Optional[InsightModelDiagnosis]
    procedure: Optional[InsightModelProcedure]
    normality: Optional[InsightModelNormality]
    tobacco: Optional[InsightModelTobacco]
    alcohol: Optional[InsightModelAlcohol]
    illicitDrug: Optional[InsightModelIllicitDrug]
