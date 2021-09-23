import argparse, itertools
from mtdnetwork.azure.batch_operations import *

MTD_STRATEGIES = sorted([
    "PortShuffle",
    "IPShuffle",
    "OSShuffle",
    "ServiceShuffle",
    "UserShuffle",
    "HostTopologyShuffle",
    "CompleteTopologyShuffle"
])

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
        default = 5
    )

    parser.add_argument(
        "--trials",
        help = "Trials for each MTD strategy",
        default = 50,
        type = int
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

    pool_id = create_pool(batch_service_client, startup_resource_files, args.batch_nodes)
    job_id = create_job(batch_service_client, pool_id)

    all_mtd_types = []

    for i in range(1, 4):
        mtd_combinations  = list(itertools.combinations(MTD_STRATEGIES, i))

        if i == 1:
            mtd_combinations.append((None,))
        all_mtd_types = all_mtd_types + mtd_combinations

    for mtd_strat in all_mtd_types:
        for i in range(args.trials):
            if len(mtd_strat) == 0 and mtd_strat[0] == None:
                cmd = "/usr/local/bin/mtdsim output.json",
                task_id = "none-{}".format(i)
            else:
                cmd = "/usr/local/bin/mtdsim -m '{}' output.json".format(
                    ','.join(mtd_strat)
                )
                task_id = "{}-{}".format(
                    "-".join(mtd_strat),
                    i
                )

            add_task(
                batch_service_client, 
                job_id, 
                task_id, 
                cmd, 
                args.sas_container_token,
                args.storage_url,
                args.container_name,
                "results/200-nodes-50-endpoints-20-subnets-3-layers-250000-time/{}.json".format(task_id)
            )

    print("Waiting for the simulation to complete!")
    wait_until_complete(batch_service_client, job_id)

    delete_job(batch_service_client, job_id)
    delete_pool(batch_service_client, pool_id)
    print("Done!")