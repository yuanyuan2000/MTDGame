from azure import batch
from azure.batch import BatchServiceClient
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from azure.common.credentials import get_azure_cli_credentials
from azure.identity import AzureCliCredential
import azure.batch.models as batchmodels
import pkg_resources, time

from uuid import uuid4

DEFAULT_POOL_NAME = "mtdresearch"
DEFAULT_JOB_NAME = "simulation"
STARTUP_BLOB_NAME = "startup.sh"
NODE_OUTPUT_FILENAME = "output.json"
INIT_COMMAND = "/bin/bash " + STARTUP_BLOB_NAME

def wait_until_complete(batch_service_client: BatchServiceClient, job_id: str):
    time.sleep(60)

    has_completed = False

    while not has_completed:
        try:
            task_counts = batch_service_client.job.get_task_counts(job_id).task_counts
            has_completed = task_counts.active == 0 and task_counts.running == 0
        except:
            has_completed = False

def get_batch_service_client(batch_url: str):
    creds = get_azure_cli_credentials(resource = "https://batch.core.windows.net/")[0]
    return BatchServiceClient(creds, batch_url)

def get_blob_service_client(storage_url: str):
    creds = AzureCliCredential()
    return BlobServiceClient(account_url = storage_url, credential = creds)

def upload_startup_script(blob_service_client: BlobServiceClient, storage_url: str, container_name: str, sas_container_token: str):
    blob_client = blob_service_client.get_blob_client(container_name, STARTUP_BLOB_NAME)
    if blob_client.exists():
        blob_client.delete_blob()
    startup_script = pkg_resources.resource_string('mtdnetwork.azure', "scripts/startup.sh")
    blob_client.upload_blob(startup_script)

    container_url = storage_url + container_name + "?" + sas_container_token

    return [batchmodels.ResourceFile(
        storage_container_url = container_url,
        blob_prefix = STARTUP_BLOB_NAME,
        file_mode = "0555"
    )]

def create_job(batch_service_client, pool_id):
    job_id = DEFAULT_JOB_NAME + str(uuid4())

    job = batchmodels.JobAddParameter(
        id = job_id,
        pool_info = batchmodels.PoolInformation(pool_id = pool_id)
    )

    batch_service_client.job.add(job)
    return job_id

def create_batch_output_files(sas_container_token, storage_url, output_container_name, output_blobname):
    container_url = storage_url + output_container_name + "?" + sas_container_token

    return [
        batchmodels.OutputFile(
            file_pattern = NODE_OUTPUT_FILENAME,
            destination = batchmodels.OutputFileDestination(
                container = batchmodels.OutputFileBlobContainerDestination(
                    container_url = container_url,
                    path = output_blobname
                )
            ),
            upload_options = batchmodels.OutputFileUploadOptions(
                upload_condition = batchmodels.OutputFileUploadCondition.task_completion
            )
        )
    ]

def add_task(batch_service_client, job_id, task_name, cmd, sas_container_token, storage_url, output_container_name, output_blobname):
    output_files = create_batch_output_files(sas_container_token, storage_url, output_container_name, output_blobname)

    tasks = [
        batchmodels.TaskAddParameter(
            id = task_name,
            command_line = cmd,
            output_files = output_files,
            user_identity = batchmodels.UserIdentity(
                auto_user = batchmodels.AutoUserSpecification(
                    scope = batchmodels.AutoUserScope.pool,
                    elevation_level = batchmodels.ElevationLevel.admin
                )
            )
        )
    ]
    
    batch_service_client.task.add_collection(job_id, tasks)

def create_pool(batch_service_client: BatchServiceClient, resource_files: list,
                    total_nodes: int, vm_size = "STANDARD_E2S_V3", task_slots_per_node = 8):
    pool_id = DEFAULT_POOL_NAME + "-" + str(uuid4())

    new_pool = batchmodels.PoolAddParameter(
        id=pool_id,
        display_name=DEFAULT_POOL_NAME,
        virtual_machine_configuration=batchmodels.VirtualMachineConfiguration(
            image_reference=batchmodels.ImageReference(
                publisher="Canonical",
                offer="UbuntuServer",
                sku="18.04-LTS",
                version="latest"
        ),
        node_agent_sku_id="batch.node.ubuntu 18.04"),
        vm_size=vm_size,
        target_dedicated_nodes=total_nodes,
        task_slots_per_node=task_slots_per_node,
        start_task=batchmodels.StartTask(
        command_line=INIT_COMMAND,
        resource_files=resource_files,
        wait_for_success=True,
        user_identity=batchmodels.UserIdentity(
            auto_user=batchmodels.AutoUserSpecification(
                scope=batchmodels.AutoUserScope.pool,
                elevation_level=batchmodels.ElevationLevel.admin)),
        )
    )

    batch_service_client.pool.add(new_pool)
    return pool_id

def delete_pool(batch_service_account: BatchServiceClient, pool_id: str):
    batch_service_account.pool.delete(pool_id)

def delete_job(batch_service_account: BatchServiceClient, job_id: str):
    batch_service_account.job.delete(job_id)