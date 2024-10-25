from opencensus.ext.azure.log_exporter import AzureLogHandler
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import json

class AzureConn():
    def __init__(self,logger):
        self.logger = logger
        
        # Setup Azure blob storage connection
        try:
            logger.info("appsim: creating azure blob connection")

            connect_str = 'DefaultEndpointsProtocol=https;AccountName=motorskillsjson;AccountKey=K83/FrGiYxU71XE5d+MFRY0OtOTqvoVTs0pSBDPzxs72GgLWwGwXtO+tTTnGh83eZiTdy98fUp/J+ASte5hwcQ==;EndpointSuffix=core.windows.net'
            blob_service_client = BlobServiceClient.from_connection_string(connect_str)

            exercise_def_container_name = 'exercise-definitions'
            result_container_name = 'exercise-results'

            self.exercise_def_container_client = blob_service_client.get_container_client(container = exercise_def_container_name)
            self.result_container_client = blob_service_client.get_container_client(container = result_container_name) 

        except Exception as ex:
            logger.error("AzureConn: Problem creating azure connection: %s",ex)

    def get_exercise_definition(self):
        file_name = 'exercises_test.json'

        try:
            exer_json = self.exercise_def_container_client.download_blob(file_name).readall()
            self.exercise_def_container_client.close()

            exer_dict = json.loads(exer_json)

            return exer_dict
        
        except Exception as ex:
            self.logger.error("AzureConn: Problem downloading exercise definitions:%s",ex)

    def upload_result(self,result):        
        try:
            # Ny container pr resultat, er det smart?

            result_json = json.dumps(result)

            result_file_name = result['exerName'] + str(result['startTime']) + ".json"

            blob_client = self.result_container_client.get_blob_client(blob=result_file_name)


            self.logger.info(f'Uploading result to Azure Storage as blob: {result_json}')

            # Upload the created file

            blob_client.upload_blob(result_json)
            blob_client.close()

        except Exception as ex:
            self.logger.error(f'Exception uploading result to Azure Storage: {ex}')