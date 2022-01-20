# Air-gapped_community_operators
I created this script for syncing community operators in OKD/Openshift in a disconnected environment.
A lot of operators do not have shasums, which means the imagecontentsourcepolicy's will not work.
Disclaimer: the code and procedure is provided as is, you may need to change it to suit your needs.

# Tested Community Operators
The following list of operators are tested with this script

```
- strimzi-kafka-operator
- dell-csi-operator
```

## Requirements
- registry that supports nested repositories, i recommend Harbor
- registry credentials to push or pull (robot)

### Clone community operators repo
Clone the repo https://github.com/k8s-operatorhub/community-operators
Got inside the directory ```operators```, you will see a lot of operators, remove the folders for operators you do not want.
A example in which i only keep ```strimzi``` and ```grafana``` operators:
```
ls | egrep -v '(strimzi|grafana)' | xargs rm -rf -
```

### Run the script
Run the script ```sync-images.py```.
These are the options:
```
usage: sync-images.py [-h] --dir DIR --registry REGISTRY --authfile AUTHFILE [--dumpjson]

Community Operator Syncer

optional arguments:
  -h, --help           show this help message and exit
  --dir DIR            directory containing the operators information
  --registry REGISTRY  registry location
  --authfile AUTHFILE  registry authentication file
  --dumpjson           option to dump json mapping file
```

Example run:
```
./sync-images.py --dir ~/gitrepos/community-operators/operators --authfile auth.json --registry harbor.lab.local/olm --dumpjson
```

#### What will the script do?
The script will do the following steps:

- get a list of all the clusterserviceversion yaml files
- loop through those files and get image locations, i will also do a sanity check, and put's them in a dict
- it will copy all the images to the registry you specified
- it will alter the image locations inside the clusterserviceversion yaml files, so you can build the operator image and operators and images used will be pulled from you local registry

### Build the image
Go to the directory where you put the repository https://github.com/operator-framework/community-operators and build the operator catalog image.
Build the catalogindex image with docker file ```upstream.Dockerfile```, this one is broken, see my adjustement in the code.
```
buildah bud -f upstream.Dockerfile -t lab-ops
```

After that, tag and push the image.


### Create catalogsource
All you need to do now is create a catalogsource, see the following example:

```
apiVersion: operators.coreos.com/v1alpha1
kind: CatalogSource
metadata:
  name: lab-ops
  namespace: openshift-marketplace
spec:
  sourceType: grpc
  image: harbor.lab.local/olm/lab-ops:v1.0
  displayName: Lab Community Operators
  publisher: Mokkinksystems
  updateStrategy:
    registryPoll: 
      interval: 20m
```

** The interval must be in multiple of 10 minutes, because of a bug in openshift/OKD **

This will create the catalog pod inside project ```openshift-marketplace```


### Use the new catalog
You can see in the webui the new catalog source and deploy operators.
When you deploy operators you will see that images are pulled from you local registry.
Disclaimer: Not all operators have proper clusterserviceversion files, you may need adjust some, or better, participate in the upstream project to create better operators.

Have fun!
