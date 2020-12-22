# OKD-Openshift-community-operators-sync
I created this script out of pure frustration with the lack of support for syncing community operators in OKD/Openshift in a disconnected environment.
A lot of operators do not have shasums, which means the imagecontentsourcepolicy's will not work.

Disclaimer: the script needs work and i am not responsible when you use it.

## Requirements
- registry that supports nested repositories, i recommend Harbor
- registry credentials to push or pull

### Clone community operators repo
Clone the repo https://github.com/operator-framework/community-operators.
Got inside the directory ```upstream-community-operators```, you will see a lot of operators, remove the folders for operators you do not want.
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
./sync-images.py --dir ~/gitrepos/community-operators/upstream-community-operators --authfile auth.json --registry harbor.lab.local/olm --dumpjson
```

#### What will the script do?
The script will do the following steps:

- get a list of all the clusterserviceversion yaml files
- loop through those files and get image locations, i will also do a sanity check, and put's them in a dict
- it will copy all the images to the registry you specified
- it will alter the image locations inside the clusterserviceversion yaml files, so you can build the operator image and operators and images used will be pulled from you local registry

### Build the image
Go to the directory where you put the repository https://github.com/operator-framework/community-operators and build the operator catalog image.
Build the catalogindex image with docker file ```upstream.Dockerfile```
```
sudo buildah bud -f upstream.Dockerfile -t lab-ops
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
      interval: 30m
```

This will create the catalog pod inside project ```openshift-marketplace```


### Use the new catalog
You can see in the webui the new catalog source and deploy operators.
When you deploy operators you will see that images are pulled from you local registry.

Have fun!
