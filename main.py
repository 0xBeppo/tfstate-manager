#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script is intended to run with a URL of a git repository, where a Terraform project should be stored.
The script will need AWS keys, so it's recommended to have AWS cli installed and configured.

The purpose of this script is to delete or update any resource from the Terraform tfstate if this resource
doesn't exist any more, or if it's configuration has been modified without using Terraform.

If the tfstate file is located in a external s3 bucket, your AWS keys will need access to that bucket.
"""

__author__ = "Markel Elorza"
__email__ = "eamarkel@gmail.com"
__version__ = "0.1.0"

import boto3
import git
import re
import subprocess
import json
import sys
import os

# Configuración de AWS
aws_region = "eu-west-1"
aws_client = boto3.client("ec2", region_name=aws_region)
#REPO_DIRECTORY = "./code"
REPO_DIRECTORY = "/home/markel/workspace/managing-tfstate"
url = ""

def clone_and_init(repo_url):
    # Clonar el repositorio en la ubicación especificada
    git.Repo.clone_from(repo_url, REPO_DIRECTORY)

    # Ejecutar el comando terraform init en el directorio clonado
    subprocess.run(["terraform", "init"], cwd=REPO_DIRECTORY)

def get_tfstate() -> list:
    # Configuración de Terraform
    output = subprocess.check_output(["terraform", "show", "-json"], cwd=REPO_DIRECTORY)
    resources = []
    show_out = json.loads(output)

    for resource in show_out['values']['root_module']['resources']:
        resources.append(resource)

    for module in show_out['values']['root_module']['child_modules']:
        rscs = module['resources']
        for resource in rscs:
            resources.append(resource)

    #print(resources)
    
    return resources

def obtener_arn(arr) -> list:
    arns = []
    for dic in arr:
        if 'values' in dic:
            values = dic['values']
            if 'arn' in values:
                arns.append(values['arn'])
    
    print(arns)
    return arns

def check_s3_bucket_exists(bucket_arn):
    s3 = boto3.resource('s3')
    bucket_name = bucket_arn.split(':')[-1]
    try:
        s3.meta.client.head_bucket(Bucket=bucket_name)
        return True
    except:
        return False

def check_security_group_exists(arn):
    ec2 = boto3.client('ec2')
    group_id = arn.split('/')[-1]
    try:
        response = ec2.describe_security_groups(GroupIds=[group_id])
        print(response)
        if len(response['SecurityGroups']) > 0:
            return True
        else:
            return False
    except:
        return False

def get_ec2_resource_type(arn):
    resource = arn.split(':')[-1]
    resource_type = resource.split('/')[0]

    return resource_type

def resource_existence_check(arn) -> bool:
    """
    Returns the function to check if a resource exists based on its ARN
    """
    resource_type = arn.split(':')[2]
    if resource_type == 's3':
        return check_s3_bucket_exists(arn)
    elif resource_type == 'dynamodb':
        return boto3.resource('dynamodb').Table(arn.split(':')[-1]).table_status
    elif resource_type == 'lambda':
        return boto3.client('lambda').get_function(FunctionName=arn.split(':')[-1])
    elif resource_type == 'ec2':
        ec2_type = get_ec2_resource_type(arn)
        print(ec2_type)
        if ec2_type == "security-group":
            return check_security_group_exists(arn)
    else:
        raise ValueError(f"Unsupported resource type: {resource_type}")

def get_terraform_resource_id_from_arn(arn, tfstate_resources) -> str:
    for entry in tfstate_resources:
        if 'arn' in entry['values'] and entry['values']['arn'] == arn:
            return entry['address']
    return None

def get_tf_import_params(tfstate_resources) -> str:
    tf_id = tfstate_resources['values']['id']
    return tf_id

def delete_resource_from_tfstate(tf_resource_id):
    delete_command = 'terraform -chdir=' + REPO_DIRECTORY + ' state rm "' + tf_resource_id + '"'
    print(f"runing: {delete_command}")
    os.system(delete_command)

def update_resource_if_distinct(tf_resource_addr, tf_resource_id):
    update_command = 'terraform -chdir=' + REPO_DIRECTORY + ' import "'+ tf_resource_addr + '" ' + tf_resource_id 
    print(f"runing: {update_command}")
    os.system(update_command)

def delete_function():
    tfstate_resources = get_tfstate()
    resource_arns = obtener_arn(tfstate_resources)
    for arn in resource_arns:
        resource_addr = get_terraform_resource_id_from_arn(arn, tfstate_resources)
        resource_type = arn.split(':')[2]
        if resource_type == "dynamodb": # Not implemented
            continue
        if resource_type == "iam": # Not implemented
            continue
        exists = resource_existence_check(arn)
        if not exists:
            delete_resource_from_tfstate(resource_addr) 

def update_function():
    tfstate_resources = get_tfstate()
    resource_arns = obtener_arn(tfstate_resources)
    for arn in resource_arns:
        resource_addr = get_terraform_resource_id_from_arn(arn, tfstate_resources)
        resource_id = get_tf_import_params(tfstate_resources)
        exists = resource_existence_check(arn)
        if exists:
            update_resource_if_distinct(resource_addr, resource_id)

def default_function():
    tfstate_resources = get_tfstate()
    resource_arns = obtener_arn(tfstate_resources)
    for arn in resource_arns:
        resource_addr = get_terraform_resource_id_from_arn(arn, tfstate_resources)
        resource_id = get_tf_import_params(tfstate_resources)
        exists = resource_existence_check(arn)
        if not exists:
            delete_resource_from_tfstate(resource_addr) 
        else:
            update_resource_if_distinct(resource_addr, resource_id)

def main(args):
    if len(args) == 2:
        # Si solo se pasó un argumento, verificamos si es una URL
        url = args[1]
        if not re.match(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', url):
            print("Error: Si solo se pasa un argumento, debe ser una URL válida.")
            print("Uso: python main.py [<delete|update>] <url>")
        else:
            default_function()
    elif len(args) == 3:
        # Si se pasan dos argumentos, verificamos si el primer argumento es 'delete' o 'update'
        parametro = args[1]
        url = args[2]
        if parametro == "delete":
            delete_function()
        elif parametro == "update":
            update_function()
        else:
            print("Parámetro no válido. Debe ser 'delete' o 'update'.")
            print("Uso: python main.py [<delete|update>] <url>")
    else:
        # Si no se pasan los argumentos correctos, imprimimos las instrucciones de uso
        print("Error: El script debe recibir uno o dos parámetros.")
        print("Uso: python main.py [<delete|update>] <url>")

if __name__ == "__main__":
    main(sys.argv)