# ***************************************************************** #
#                                                                   #
# (C) Copyright IBM Corp. 2021                                      #
#                                                                   #
# SPDX-License-Identifier: Apache-2.0                               #
#                                                                   #
# ***************************************************************** #
# Regex annotator
uvicorn example_apps.regex_annotator:app --factory --workers 5 --limit-concurrency 10 --backlog 10 \
  --log-config ./acd_annotator_python/logSettings.json

## Spacy annotator requires extras to be installed
#uvicorn example_apps.extras.spacy_sentence_annotator:app --factory --workers 5 --limit-concurrency 10 --backlog 10 \
#  --log-config ./acd_annotator_python/logSettings.json --env-file ./example_apps/extras/server.env

## Stanza annotator requires extras to be installed
#uvicorn example_apps.extras.stanza_sentence_annotator:app --factory --workers 5 --limit-concurrency 10 --backlog 10 \
#  --log-config ./acd_annotator_python/logSettings.json --env-file ./example_apps/extras/server.env