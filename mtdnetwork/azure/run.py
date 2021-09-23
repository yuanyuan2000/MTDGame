import argparse
from mtdnetwork.azure.batch_operations import *

def parse_args():
    parser = argparse.ArgumentParser(description="Runs the simulations using Azure Batch")

    parser.add_argument(
        "-b", "--batch_url",
        help = "The URL of the Azure Batch Account",
        type = str,
        required = True
    )

    parser.add_argument(
        "-s", "--storage_url",
        help = "The URL of the Azure Storage Account",
        type = str,
        required = True
    )

    parser.add_argument(
        "-t", "--sas_container_token",
        help = "The SAS token to access the storage container. Token needs racwdl permissions on the container",
        type = str,
        required = True
    )

    parser.add_argument(
        "-c", "--container_name",
        help = "The name of the container to store the data to",
        type = str,
        required = True
    )

    parser.add_argument(
        "-n", "--batch_nodes",
        help = "The number of nodes for the pool to run the simulation",
        type = int,
        default = 2
    )

    return parser.parse_args()

def main():
    args = parse_args()

    batch_service_client = get_batch_service_client(args.batch_url)
    blob_service_client = get_blob_service_client(args.storage_url)

    startup_resource_files= upload_startup_script(
        blob_service_client,
        args.storage_url,
        args.container_name,
        args.sas_container_token
    )

    print(create_pool(batch_service_client, startup_resource_files, args.batch_nodes))