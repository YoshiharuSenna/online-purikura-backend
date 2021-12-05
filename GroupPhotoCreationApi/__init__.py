import logging
import json

import azure.functions as func
from azure.storage.blob import BlobServiceClient

CNNECT_STR='DefaultEndpointsProtocol=https;AccountName=onlinepurikuraapiv2;AccountKey=yE2SceVOOae3GSwX/6Y/OcF6sPg2LnvW/RoXuOCq+uVsWkkTpx3rnd63z897ZjlcfXnRuDo4YG0hkLAM0gJO5g==;EndpointSuffix=core.windows.net'
CONTAINER_NAME='background-image'

def getBackgroundImage(style):
    container_client = BlobServiceClient.from_connection_string(CNNECT_STR).get_container_client(CONTAINER_NAME)
    blob_client = container_client.get_blob_client(blob=str(style) + ".txt")
    imageData = blob_client.download_blob().readall()
    return imageData.decode('utf-8')

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    image = req.params.get('image')
    if not image:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            image = req_body.get('image')
    
    style = req.params.get('style')
    if not style:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            style = req_body.get('style')

    # 背景画像（Base64のString型）
    backgroundImage = getBackgroundImage(style)

    # ここに処理を記述
    # 以下の"image"部分はレスポンスで返す変数に置き換えて使用してください
    if backgroundImage:
        return func.HttpResponse(
            json.dumps({
            'image': backgroundImage
            }) 
        )
    else:
        return func.HttpResponse(
             "no image",
             status_code=200
        )
