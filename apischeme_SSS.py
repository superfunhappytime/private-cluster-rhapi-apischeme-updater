#!/usr/bin/env python3

import sys
import yaml
import os
import json

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


def get_bastion_ips(sss):
    bastion_ips = sss.metadata.annotations.allowedCIDRBlocks or ""

    bastion_ips = json.loads(bastion_ips)
    print("found %d bastion IPs" % len(bastion_ips))

    return bastion_ips


sss = get_sss()

all_ips = set(get_hive_ips() + get_bastion_ips(sss))

if not all_ips:
    print("Not enough IPs!")
    sys.exit(1)

ingress = sss.spec.resources[0].spec.managementAPIServerIngress

if set(ingress.allowedCIDRBlocks) == all_ips:
    print("Same IPs, no-op\n%s" % all_ips)
    sys.exit(0)

# Blow away last config so it doesn't recurse
setattr(
    sss.metadata.annotations, "kubectl.kubernetes.io/last-applied-configuration", ""
)

# Overwrite the list of IPs
ingress.allowedCIDRBlocks = list(all_ips)
print("Applying IPs: %s" % ingress.allowedCIDRBlocks)
sss_resources = dyn_client.resources.get(
    api_version="hive.openshift.io/v1", kind="SelectorSyncSet"
)
dyn_client.apply(sss_resources, body=sss.to_dict())
