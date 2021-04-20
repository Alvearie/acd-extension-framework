# acd-annotator-python
An ACD Annotator implemented as a python microservice that can be customized and included in an ACD annotator flow.


# Getting Started

## Install python3.8+ and virtualenv ##
You can check whether virtualenv is already installed by running `virtualenv -h`. 
The best way to install virtualenv will depend on your environment, 
but most users should be able to do `pip3 install --user virtualenv` and then 
make sure that your `PATH` is set up to point to the location where virtualenv was installed.
(Hint: Os X users may need to adjust their PATH in .bash_profile; 
Linux users may need to adjust their PATH in .bashrc)

For example, Os X prints out the following helpful message after pip installing virtualenv
telling your how to adjust your path:

```
Installing collected packages: virtualenv
  WARNING: The script virtualenv is installed in '/Users/[username]/Library/Python/3.9/bin' which is not on PATH.
  Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
```

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
Edit run.server.sh to uncomment the example you want to run. (Be aware that some of the example annotators have extra dependencies and 
won't work until you run `bash ./scripts/install_extras.sh`)

Then run
```
bash ./scripts/run_server.sh
```
and browse swagger at http://localhost:8000/docs


## Run Unit Tests ##
``` 
bash ./scripts/run_tests 
```

## Create your own custom ACD Annotator ##
To get started creating your own custom annotator, 
first copy an example from example_apps into your own git project.
Then modify the code paying attention to inline comments about how to:

1. Access the incoming container model's text and any annotations that already exist.
1. Implement your annotation logic in the annotate method, modifying the container model as necessary.
1. Add tests for your annotator logic.

The example apps are already configured to be debugged from a 
python IDE simply by running them directly in debug mode.


## Running a custom ACD annotator in your own managed ACD pipeline 

...under construction...
