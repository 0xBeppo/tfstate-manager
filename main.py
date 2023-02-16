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

def obtener_arn(arr):
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


def get_resource_existence_check_function(arn):
    """
    Returns the function to check if a resource exists based on its ARN
    """
    resource_type = arn.split(':')[2]
    if resource_type == 's3':
        print(check_s3_bucket_exists(arn))
    elif resource_type == 'dynamodb':
        return boto3.resource('dynamodb').Table(arn.split(':')[-1]).table_status
    elif resource_type == 'lambda':
        return boto3.client('lambda').get_function(FunctionName=arn.split(':')[-1])
    elif resource_type == 'ec2':
        ec2_type = get_ec2_resource_type(arn)
        print(ec2_type)
        if ec2_type == "security-group":
            print(check_security_group_exists(arn))
    else:
        raise ValueError(f"Unsupported resource type: {resource_type}")


def get_missing_resource() -> str: 
    pass

def delete(url):
    pass

def update(url):
    pass

if __name__ == "__main__":
    arn_array = obtener_arn(get_tfstate())
    get_resource_existence_check_function(arn_array[3])
    exit()
    if len(sys.argv) == 2:
        # Si solo se pasó un argumento, verificamos si es una URL
        url = sys.argv[1]
        if not re.match(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', url):
            print("Error: Si solo se pasa un argumento, debe ser una URL válida.")
            print("Uso: python main.py [<delete|update>] <url>")
        else:
            update(url)
    elif len(sys.argv) == 3:
        # Si se pasan dos argumentos, verificamos si el primer argumento es 'delete' o 'update'
        parametro = sys.argv[1]
        url = sys.argv[2]
        if parametro == "delete":
            delete()
        elif parametro == "update":
            update(url)
        else:
            print("Parámetro no válido. Debe ser 'delete' o 'update'.")
            print("Uso: python main.py [<delete|update>] <url>")
    else:
        # Si no se pasan los argumentos correctos, imprimimos las instrucciones de uso
        print("Error: El script debe recibir uno o dos parámetros.")
        print("Uso: python main.py [<delete|update>] <url>")