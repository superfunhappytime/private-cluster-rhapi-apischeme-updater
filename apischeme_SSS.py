#!/usr/bin/env python3

import sys
import yaml
import os
import json


from kubernetes import config
from kubernetes.client import ApiClient

from openshift.dynamic import DynamicClient

APISCHEME_SSS_NAME = "cloud-ingress-operator"

# from kubeconfig
# k8s_client = config.new_client_from_config()
# dyn_client = DynamicClient(k8s_client)

# in cluster client creation
k8s_client = ApiClient(config.load_incluster_config())
dyn_client = DynamicClient(k8s_client)


def get_sss():
    selectorsyncsets = dyn_client.resources.get(
        api_version="hive.openshift.io/v1", kind="SelectorSyncSet"
    )
    return selectorsyncsets.get(name=APISCHEME_SSS_NAME)


def get_hive_ips():
    nodes = dyn_client.resources.get(api_version="v1", kind="Node")

    hive_ips = []
    for node in nodes.get().items:
        for a in node.status.addresses:
            if a.type == "ExternalIP":
                # add /32 to the end since they're not recorded as CIDR blocks
                hive_ips.append("{}/32".format(a.address))

    print("found %d hive IPs" % len(hive_ips))

    return hive_ips


def get_bastion_ips(resource):
    bastion_ips = resource.metadata.annotations.allowedCIDRBlocks or ""

    bastion_ips = json.loads(bastion_ips)
    print("found %d bastion IPs" % len(bastion_ips))

    return bastion_ips


sss = get_sss()

for resource in sss.spec.resources:
    if resource.kind == "APIScheme" and resource.metadata.name == "rh-api":
        break
else:
    print("Couldn't find the rh-api APIScheme!")
    sys.exit(1)

hive_ips = get_hive_ips()
if not hive_ips:
    print("Couldn't find any hive IPs! Assuming this means we're running "
          "on v4, and not that there's an actual problem. Bailing with "
          "'success' status.")
    sys.exit(0)

all_ips = set(hive_ips + get_bastion_ips(resource))
if not all_ips:
    print("Not enough IPs!")
    sys.exit(1)

ingress = resource.spec.managementAPIServerIngress

if set(ingress.allowedCIDRBlocks) == all_ips:
    print("Same IPs, no-op\n%s" % all_ips)
    sys.exit(0)

# Overwrite the list of IPs
ingress.allowedCIDRBlocks = list(all_ips)
print("Applying IPs: %s" % ingress.allowedCIDRBlocks)

# Tell cloud-ingress-operator it's okay to apply the CIDRs now.
if not ingress.enabled:
    print("Enabling ingress")
    ingress.enabled = True  # As opposed to the string "true".

sss_resources = dyn_client.resources.get(
    api_version="hive.openshift.io/v1", kind="SelectorSyncSet"
)
dyn_client.apply(sss_resources, body=sss.to_dict())
