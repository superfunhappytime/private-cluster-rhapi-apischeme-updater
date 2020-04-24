#!/usr/bin/env python

import oyaml as yaml

import os
import argparse
import copy


def get_yaml_all(filename):
    with open(filename, 'r') as input_file:
        return list(yaml.load_all(input_file))


def get_yaml(filename):
    with open(filename, 'r') as input_file:
        return yaml.safe_load(input_file)


def get_all_yaml_files(path):
    file_paths = []
    for r, d, f in os.walk(path):
        for file in f:
            if file.endswith('.yml') or file.endswith('.yaml'):
                file_paths.append(os.path.join(r, file))
        # break, so we don't recurse
        break
    file_paths = sorted(file_paths)
    return file_paths


def get_all_yaml_obj(file_paths):
    yaml_objs = []
    for file in file_paths:
        objects = get_yaml_all(file)
        for obj in objects:
            yaml_objs.append(obj)
    return yaml_objs


def process_yamls(name, directory, obj):
    o = copy.deepcopy(obj)
    # Get all yaml files as array of yaml objects
    yamls = get_all_yaml_obj(get_all_yaml_files(directory))
    if len(yamls) == 0:
        return

    # Find all Roles bound to the SA where the subject is in the same NS as the SA.
    # These Roles are managed by CSV only.
    sa_role_names = []
    for y in yamls:
        if y['kind'] == 'RoleBinding':
            if 'namespace' not in y['metadata']:
                print("RoleBinding '{}' is missing .metadata.namespace".format(y['metadata']['name']))
            for s in y['subjects']:
                if 'namespace' not in s:
                    print("RoleBinding '{}' is missing .subjects[].namespace".format(y['metadata']['name']))
                if y['roleRef']['kind'] == "Role" and s['kind'] == 'ServiceAccount' and y['metadata']['namespace'] == s['namespace']:
                    sa_role_names.append(y['roleRef']['name'])

        # it's something we want to have in the template
        if 'patch' in y:
            if not 'patches' in o['spec']:
                o['spec']['patches'] = []
            o['spec']['patches'].append(y)
        else:
            if not 'objects' in o:
                o['objects'] = []
            o['objects'].append(y)

    o['metadata']['name'] = name
    # append object to the template's objects
    for obj in o['objects']:
        if obj['kind'] != 'Template':
            template_data['objects'].append(obj)


if __name__ == '__main__':
    # Argument parser
    parser = argparse.ArgumentParser(description="template generation tool", usage='%(prog)s [options]')
    parser.add_argument("--template-dir", "-t", required=True, help="Path to template directory [required]")
    parser.add_argument("--yaml-directory", "-y", required=True, help="Path to folder containing yaml files [required]")
    parser.add_argument("--destination", "-d", required=True, help="Destination for template file [required]")
    parser.add_argument("--repo-name", "-r", required=True, help="Name of the repository [required]")
    arguments = parser.parse_args()

    # Get the template data
    template_data = get_yaml(os.path.join(arguments.template_dir, "updater-template.yaml"))

    # The templates and script are shared across repos (copy & paste).
    # Set the REPO_NAME parameter.
    for p in template_data['parameters']:
        if p['name'] == 'REPO_NAME':
            p['value'] = arguments.repo_name

    # for each subdir of yaml_directory append 'object' to template
    for (dirpath, dirnames, filenames) in os.walk(arguments.yaml_directory):
        # skip 'crds' directory, these are bundled in the CSV
        if filenames:
            object_name = dirpath.replace('/', '-').replace(arguments.yaml_directory, arguments.repo_name)
            process_yamls(object_name, dirpath, template_data)

    # write template file ordering by keys
    with open(arguments.destination, 'w') as outfile:
        yaml.dump(template_data, outfile, default_flow_style=False)
