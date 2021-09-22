from azure.batch import BatchServiceClient
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from azure.common.credentials import get_azure_cli_credentials
from azure.identity import AzureCliCredential
import azure.batch.models as batchmodels
import pkg_resources

from uuid import uuid4

DEFAULT_POOL_NAME = "mtdresearch"
INIT_COMMAND = "/bin/bash ./startup.sh"
STARTUP_BLOB_NAME = "startup.sh"

def get_batch_service_client(batch_url: str):
    creds = get_azure_cli_credentials(resource = "https://batch.core.windows.net/")[0]
    return BatchServiceClient(creds, batch_url)

def get_blob_service_client(storage_url: str):
    creds = AzureCliCredential()
    return BlobServiceClient(account_url = storage_url, credential = creds)

def upload_startup_script(blob_service_client: BlobServiceClient, container_name: str):
    blob_client = blob_service_client.get_blob_client(container_name, STARTUP_BLOB_NAME)
    if blob_client.exists():
        blob_client.delete_blob()
    startup_script = pkg_resources.resource_string('mtdnetwork.azure', "scripts/startup.sh")
    blob_client.upload_blob(startup_script)

    sas_token = generate_blob_sas(
        blob_service_client.account_name,
        container_name,
        STARTUP_BLOB_NAME,
        account_key = blob_service_client.credential.account_key,
        permission = BlobSasPermissions(read = True)
    )

    print(sas_token)

    return [batchmodels.ResourceFile(
        auto_storage_container_name = container_name,
        file_path = "startup.sh",
        file_mode = "0555"
    )]

def create_pool(batch_service_client: BatchServiceClient, resource_files: list,
                    total_nodes: int):
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
        vm_size="STANDARD_E4S_V3",
        target_dedicated_nodes=total_nodes,
        task_slots_per_node=16,
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