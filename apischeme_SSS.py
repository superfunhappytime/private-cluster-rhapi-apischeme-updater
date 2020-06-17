#!/usr/bin/env python3

import sys
import yaml
import os


from kubernetes import config
from kubernetes.client import ApiClient

from openshift.dynamic import DynamicClient

APISCHEME_SSS_NAME = "cloud-ingress-operator-apischeme"

# from kubeconfig
# k8s_client = config.new_client_from_config()
# dyn_client = DynamicClient(k8s_client)

# in cluster client creation
k8s_client = ApiClient(config.load_incluster_config())
dyn_client = DynamicClient(k8s_client)


def get_hive_ips():
    nodes = dyn_client.resources.get(api_version='v1', kind='Node')

    hive_ips = []
    for node in nodes.get().items:
        for a in node.status.addresses:
            if a.type == "ExternalIP":
                # add /32 to the end since they're not recorded as CIDR blocks
                hive_ips.append("{}/32".format(a.address))

    if len(hive_ips) == 0:
        print("not enough hive ips")
        sys.exit(1)
    return hive_ips


def get_bastion_ips():
    bastion_ip_str = os.getenv("ALLOWED_CIDR_BLOCKS", [])
    bastion_ips = bastion_ip_str.split(",")
    if len(bastion_ips) == 0:
        print("not enough bastion ips")
        sys.exit(1)
    return bastion_ips


apischeme_sss = """
apiVersion: hive.openshift.io/v1
kind: SelectorSyncSet
metadata:
  labels:
    managed.openshift.io/osd: "true"
  name: "filled-in-later"
spec:
  clusterDeploymentSelector:
    matchLabels:
      api.openshift.com/managed: "true"
      hive.openshift.io/cluster-platform: "aws"
  resourceApplyMode: Sync
  resources:
  - kind: APIScheme
    apiVersion: cloudingress.managed.openshift.io/v1alpha1
    metadata:
      name: rh-api
      namespace: openshift-cloud-ingress-operator
    spec:
      managementAPIServerIngress:
        enabled: true
        dnsName: rh-api
        allowedCIDRBlocks: []
"""

api_yaml = yaml.safe_load(apischeme_sss)

api_yaml['metadata']['name'] = APISCHEME_SSS_NAME

all_ips = get_hive_ips() + get_bastion_ips()
ips_len = len(all_ips)

for i in range(ips_len):
    api_yaml['spec']['resources'][0]['spec']['managementAPIServerIngress']['allowedCIDRBlocks'].append(all_ips[i])

sss_resources = dyn_client.resources.get(api_version='hive.openshift.io/v1', kind='SelectorSyncSet')
dyn_client.apply(sss_resources, body=api_yaml)
