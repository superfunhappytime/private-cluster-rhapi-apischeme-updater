# private-cluster-rhapi-apischeme-updater

The private-cluster-rhapi-apischeme-updater is designed to assist the [cloud-ingress-operator](https://github.com/openshift/cloud-ingress-operator) in toggling OpenShift Dedicated 4.x clusters as "public" or "private". 

Part of the cloud-ingress-operator's functionality is creating an additional API endpoint that will allow [Hive](https://github.com/openshift/hive) and the OSD SRE team to have continued access to manage the clusters on behalf of the customers. This API endpoint is named by default `rh-api.<cluster-domain>`, and is created using the custom Kubernetes resource `APIScheme`.

The purpose of this updater is to maintain the `rh-api APIScheme` resource's `spec.allowedCIDRBlocks` in an automated way to ensure that the cloud load balancer allows Hive and the SRE team continuous access to the cluster. It does this by dynamically pulling the IPs that Hive and the SRE team may use to access the cluster and updating the `rh-api APIScheme` resource.

## Implementation Details

At its core, the private-cluster-rhapi-apischeme-updater exists as a `CronJob` that is deployed to Hive environments. When this `CronJob` runs, it executes the `apischeme_SSS.py` script in a containerized environment.

The `apischeme_SSS.py` script dynamically gathers the CIDR blocks necessary for the `rh-api APIScheme` resource, and creates or updates a `SelectorSyncSet` object within the Hive environment. The `SelectorSyncSet` object is then used to update the `rh-api APIScheme` resource on each OSD cluster that the Hive environment manages.

This ultimately ensures continued access to OSD clusters through such events as IP lease expirations.