# acd-annotator-python
An ACD Annotator implemented as a python microservice that can be customized and included in an ACD annotator flow.


# Getting Started


## Prerequisites ##
Install python 3.8+


## Install dependencies in a virtualenv environment ##
Create a virtualenv environment and install required dependencies by running
```
bash ./scripts/install.sh
```

and activate your new virtualenv environment (installed in .venv) by running
```
source ./scripts/activate.sh  
```


## Run an example annotator ##
Run tests to make sure everything is working properly by doing
``` 
bash ./scripts/run_tests.sh
```

and then edit run_server.sh to uncomment the example you want to run. (Be aware that some of the example annotators have extra dependencies and 
won't work until you run `bash ./scripts/install_extras.sh`)

Then run
```
bash ./scripts/run_server.sh
```
and browse swagger at http://localhost:8000/docs


## Create and debug your own custom ACD Annotator ##
To get started creating your own custom annotator,
you'll want to install a python IDE like  
[PyDev](https://www.pydev.org/) or
[PyCharm](https://www.jetbrains.com/pycharm/) 
and import the project into it. Once your IDE is set up,
you can debug one of the example annotators by 
running it directly in your IDE (NOT via run_server.sh). Running in 
this mode, the service will reload code every time you save 
changes to a file in the project, which can make 
developing much easier.

Now copy an example from example_apps into your own git project.
Then modify the code paying attention to inline comments about how to:

1. Access the incoming container model's text and any annotations that already exist.
1. Implement your annotation logic in the annotate method, modifying the container model as necessary.
1. Add tests for your annotator logic.


## Pip install the ACD extension framework ##

In deployment scenarios, you will probably want to pip install 
the `acd_annotator_python` module instead of installing it from source. 
You can do this with 
```
pip3 install "git+https://github.com/Alvearie/acd-extension-framework/#egg=acd-annotator-python&subdirectory=acd-annotator-python"
```

## Build a docker image with your custom annotator ##
You can build your service as a docker image using the [Dockerfile](https://github.com/Alvearie/acd-extension-framework/blob/main/acd-annotator-python/example_apps/Dockerfile) inside of example_apps, which containerizes the code-resolution example annotator.  If you are ready to enable TLS, edit the Dockerfile. Build it by doing

```
cd example_apps/
docker build -t code-resolution:latest .
```
and then run it with
```
docker run -it -p 9443:9443 code-resolution:latest 
```

After the docker container starts, test it by going to `localhost:9443/docs` (use http or https as appropriate depending on whether you have TLS enabled in your Dockerfile)


## Deploy custom annotator into OpenShift cluster

Refer to [this page](https://github.com/Alvearie/acd-extension-framework/blob/main/acd-annotator-python/CustomAnnotatorSetup.md) when you are ready to deploy your custom annotator docker image into an OpenShift cluster
