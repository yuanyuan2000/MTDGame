from azure.batch import BatchServiceClient
from azure.storage.blob import BlobServiceClient
from azure.common.credentials import get_azure_cli_credentials
from azure.identity import AzureCliCredential
import azure.batch.models as batchmodels

from uuid import uuid4

DEFAULT_POOL_NAME = "mtdresearch"
INIT_COMMAND = []

def get_batch_service_client(batch_url):
    creds = get_azure_cli_credentials(resource = "https://batch.core.windows.net/")[0]
    return BatchServiceClient(creds, batch_url)

def get_blob_service_cliuent(storage_url):
    creds = AzureCliCredential()
    return BlobServiceClient(account_url = storage_url, credential = creds)

def create_pool(total_nodes):
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
        max_tasks_per_node=16,
        start_task=batchmodels.StartTask(
        command_line=init_cmd,
        resource_files=bash_script_resource_files,
        wait_for_success=True,
        user_identity=batchmodels.UserIdentity(
            auto_user=batchmodels.AutoUserSpecification(
                scope=batchmodels.AutoUserScope.pool,
                elevation_level=batchmodels.ElevationLevel.admin)),
        )
    )