## Deploying a custom annotator into ACD

**Prerequisites** - Before following the directions in this document, ensure the following conditions are met:

1. Have a [container edition of ACD](https://ibm.github.io/acd-containers/) installed on an OpenShift cluster.

2. Create a Docker build of your custom annotator as [documented here](https://github.com/Alvearie/acd-extension-framework/tree/main/acd-annotator-python#build-a-docker-image-with-your-custom-annotator).  Note that the directions that follow use an https url.  **Before proceeding, ensure your Dockerfile is using the SSL enabled web server invocation.**

3. Push your custom annotator docker image to a docker repository.  We'll setup the OpenShift pull secret later in the instructions.

4. Appropriate network policies - No action necessary unless you have more stringent network policies than OpenShift comes with by default.  Network communication does need to work between your ACD project and the project we will create for your custom annotator.

**Other Notes**

1. At inference time, ACD will send the following http headers to your service on a request.
   - x-correlation-id - The correlation id for a given ACD request.
   - x-tenant-artifact-version - The version field for your COS tenant (if one exists).
   - x-supertenant-artifact-version - The version field for your COS supertenant (if one exists).

   All of these fields should be logged as part of the Mapped Diagnostic Context (MDC) on any log messages to make troubleshooting easier.

2. Your custom annotator should use an OpenShift CA issued certificate (This should happen naturally as part of the directions below). ACD will trust anything from the OpenShift CA in your cluster. Note that OpenShift CA issued certificates are only valid in the cluster DNS and target service url should have the form `https://<service.name>.<service.namespace>.svc`.


**Installation instructions**

1) This repository contains [helm chart templates](https://github.com/Alvearie/acd-extension-framework/blob/main/acd-annotator-python/helm-charts/custom-annotator-template) for deploying your custom annotator.  We will modify these templates to deploy your custom annotator to your OpenShift cluster.  You can copy the templates to a different working location or simply edit them in place in your project space.

    The `Charts.yaml` and `values.yaml` files contain templated variables that you should replace with values that are appropriate for your environment.  Each of the variables is described below.  Ensure that you replace all templated variables in `Charts.yaml` and `values.yaml` before proceeding.

    * <CUSTOM_PROJECT_NAME> - The name of the OpenShift project that you will create for your custom annotator deployment.  **This should be a different project name than the project under which ACD is deployed.**
    * <ACD_PROJECT_NAME> - The name of the OpenShift project that your ACD instance is deployed into.
    * <APPLICATION_NAME> - The application name for your custom annotator.  We'll use `custom-annotator` for this demo.
    * <DOCKER_IMAGE_PATH> - The path to your custom annotator's Docker image.

2) Create a custom project/namespace in OpenShift where your custom annotator will be deployed.

    Note that the login command for your OpenShift instance can be obtained from the OpenShift console.

    `oc login --token=<YOUR TOKEN> --server=<YOUR SERVER>`

    `oc new-project <CUSTOM_PROJECT_NAME> --display-name '<WHATEVER DISPLAY TEXT YOU WANT>'`

3) Setup a pull secret in OpenShift for your docker repository.

    You'll need to have a pull secret configured in OpenShift so it can pull your custom annotator image.  Project level secrets are recommended over global secrets as global secrets force all nodes in the cluster to be drained.

    For a repository hosted in IBM Cloud, [these instructions](https://cloud.ibm.com/docs/openshift?topic=openshift-registry#other_registry_accounts) show you how to set that up a pull secret in your OpenShift cluster.  

    For repositories hosted elsewhere, follow [these instructions](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#add-imagepullsecrets-to-a-service-account).


4) From your helm chart working directory, do a helm deploy of your chart.

    ```
    helm install <APPLICATION_NAME> .
    ```

5) Confirm that the all of the replicas of your custom annotator come up in OpenShift and are healthy.

6) Confirm that the networking rules are working.  From your OpenShift console, open up a terminal on one of the custom annotator pods you created in step 4 and run a curl command to get the annotator status.

    ```
    bash$ curl -k https://<APPLICATION_NAME>.<CUSTOM_PROJECT_NAME>.svc:443/services/example_acd_service/api/v1/status

    {"version":"2021-04-06T15:37:31Z","upTime":"0d 00:38:53","serviceState":"OK","hostName":"custom-annotator-
    5df7f54c5f-r96fj","requestCount":44,"maxMemoryMb":30,"inUseMemoryMb":31,"commitedMemoryMb":47,"availableProcessors":16}
    ```

    If the check above works, go over to your ACD namespace and run the same curl command from an ACD pod (find a pod that starts with
`ibm-wh-acd-acd`).  Note that your container must be built with SSL support for the https version of the url to work.

7) Wait for the config map to be recognized by the ACD pods - This typically happens within a minute.  You can check the config map contents by executing a `cat /etc/config/ibm-wh-acd-config.json` on one of the ACD pods.  Check that the contents look correct.

    NOTE: Ensure that the url you specify here is correct (no http vs https mismatch).  Otherwise, the ACD pods will fail to restart.

    ```
    sh-4.4$ cat /etc/config/ibm-wh-acd-config.json
    {
      "acd.customAnnotators" : {
        "<APPLICATION_NAME>" : {
          "url" : "https://<APPLICATION_NAME>.<PROJECT_NAME>:443/services/example_acd_service/api/v1/process",
          "description" : "My custom annotator"
        }
      }
    }
    sh-4.4$
    ```

8) Restart your ACD deployment - To trigger a restart, you can delete the ACD pods individually or restart the ACD deployment.

9) Check that the new annotator is recognized by ACD

    Open a terminal to one of your ACD pods (find a pod that starts with `ibm-wh-acd-acd`) and call the GET annotators endpoint to confirm that your annotator is in the list.

    Run
    `curl -k  https://localhost:9443/services/clinical_data_annotator/api/v1/annotators?version=2021-03-01`

    Ensure that your custom annotator is somewhere in the JSON response

    `"custom-annotator":{"description":"My custom annotator","version":"2021-04-06T15:37:31Z"}}`

    If your custom annotator(s) are present in the response, you're ready to use them as part of an ACD flow.

    If you don't see your custom annotator in the list of returned annotators, check `/logs/messages.log` for your annotator's unique key or the word "custom" for information on why it was not added to the ACD pipeline definition.

10) Final checks

    First, run a flow that references your custom annotator from an ACD pod (find a pod that starts with `ibm-wh-acd-acd`).  

    ```
    curl -k -X POST --header "Content-Type: application/json" --header "Accept: application/json" -d "{
      \"annotatorFlows\": [
        {
          \"flow\": {
            \"elements\": [
              {
                \"annotator\": {
                  \"name\": \"concept_detection\"
                }
              },
              {
                \"annotator\": {
                  \"name\": \"<APPLICATION_NAME>\"
                 }
              }
            ],
            \"async\": false
          }
        }
      ],
      \"unstructured\": [
        {
          \"text\": \"Patient has lung cancer\"
        }
      ]
    }" "https://localhost:9443/services/clinical_data_annotator/api/v1/analyze?debug_text_restore=false&version=2021-07-12&return_analyzed_text=false"
    ```

    You should see a JSON response that includes your custom annotator in the `annotatorFlows` list.

    ```
    {"annotatorFlows":[{"flow":{"elements":[{"annotator":{"name":"concept_detection"}},{"annotator":{"name":"custom-annotator"}}],"async":false}}],"unstructured":[{"data":{"concepts":[{"cui":"C0332310","preferredName":"Has patient","semanticType":"ftcn","source":"umls","sourceVersion":"2020AA","type":"umls.FunctionalConcept","begin":0,"end":11,"coveredText":"Patient has"},{"cui":"C1306460","preferredName":"Primary malignant neoplasm of lung","semanticType":"neop","source":"umls","sourceVersion":"2020AA","type":"umls.NeoplasticProcess","begin":12,"end":23,"coveredText":"lung cancer"},{"cui":"C0684249","preferredName":"Carcinoma of lung","semanticType":"neop","source":"umls","sourceVersion":"2020AA","type":"umls.NeoplasticProcess","begin":12,"end":23,"coveredText":"lung cancer"},{"cui":"C0242379","preferredName":"Malignant neoplasm of lung","semanticType":"neop","source":"umls","sourceVersion":"2020AA","type":"umls.NeoplasticProcess","begin":12,"end":23,"coveredText":"lung cancer"}]}}]}
    ```

    If this works, you can test from the external endpoint as [documented here](https://ibm.github.io/acd-containers/security/manage-access/)
