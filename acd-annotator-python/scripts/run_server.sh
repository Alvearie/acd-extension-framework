# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #
# Regex annotator
uvicorn example_apps.regex_annotator:app --host 0.0.0.0 --port 8000 --factory --workers 5 --limit-concurrency 10 --backlog 10 \
  --log-config ./acd_annotator_python/defaultLogSettings.json

# BMI annotator (structured containers)
#uvicorn example_apps.bmi_annotator:app --host 0.0.0.0 --port 8000 --factory --workers 5 --limit-concurrency 10 --backlog 10 \
#  --log-config ./acd_annotator_python/defaultLogSettings.json

## Spacy annotator requires extras to be installed
#uvicorn example_apps.extras.spacy_sentence_annotator:app --host 0.0.0.0 --port 8000 --factory --workers 5 --limit-concurrency 10 --backlog 10 \
#  --log-config ./acd_annotator_python/defaultLogSettings.json --env-file ./example_apps/extras/server.env

## Stanza annotator requires extras to be installed
#uvicorn example_apps.extras.stanza_sentence_annotator:app --host 0.0.0.0 --port 8000 --factory --workers 5 --limit-concurrency 10 --backlog 10 \
#  --log-config ./acd_annotator_python/defaultLogSettings.json --env-file ./example_apps/extras/server.env
