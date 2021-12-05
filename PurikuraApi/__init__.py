import logging
import json
import cv2
import base64 
import numpy as np

import azure.functions as func
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

connect_str = "DefaultEndpointsProtocol=https;AccountName=onlinepurikuraapi;AccountKey=vdbQ9QZt7wPk4MtSav6u5vd5tVALcUTpNL0vQFklh8tg/PUmw5krxQ6i2nLHBCIRa3bsnJqHJ+t82jzZe2bH4Q==;EndpointSuffix=core.windows.net"
container_name = "haarcascade"

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request. Purikura')

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

    # ここに処理を記述
    # 以下の"image"部分はレスポンスで返す変数に置き換えて使用してください
    if image:
        src = Base64ToNdarry(image)
        convert_image = convert_purikura(src)
        base64image = cv_to_base64(convert_image)
        return func.HttpResponse(
            json.dumps({
            'image': base64image
            }) 
        )
    else:
        return func.HttpResponse(
             "no image",
             status_code=200
        )

def Base64ToNdarry(img_base64):
    img_data = base64.b64decode(img_base64)
    img_np = np.fromstring(img_data, np.uint8)
    src = cv2.imdecode(img_np, cv2.IMREAD_ANYCOLOR)

    return src

def cv_to_base64(img):
    _, encoded = cv2.imencode(".jpg", img)
    img_str = base64.b64encode(encoded).decode("ascii")

    return img_str

def convert_purikura(src):
    logging.info('aaaaa')
    # blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    # container_client = blob_service_client.get_container_client(container_name)
    # blob_list = container_client.list_blobs()
    # for blob in blob_list:
    #     print("\t" + blob.name)
    
    # face_cascade_path = blob_service_client.get_blob_client(container_name,"haarcascade_frontalface_default.xml").download_blob()
    # eye_cascade_path = blob_service_client.get_blob_client(container_name,"haarcascade_eye.xml").download_blob()
    face_cascade_path = "./haarcascade_frontalface_default.xml"
    eye_cascade_path = "./haarcascade_eye.xml"
    
    logging.info('bbbb')
    face_cascade = cv2.CascadeClassifier(face_cascade_path)
    eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

    src_gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(src_gray)

    for x, y, w, h in faces:
        face = src[y: y + h, x: x + w]
        face_gray = src_gray[y: y + h, x: x + w]
        eyes = eye_cascade.detectMultiScale(face_gray)
        for (ex, ey, ew, eh) in eyes:
            img = face[ey: ey + eh, ex: ex + ew]
            height = img.shape[0]
            width = img.shape[1]
            img2 = cv2.resize(img , (int(width*1.2), int(height*1.2)))
            height = img2.shape[0]
            width = img2.shape[1]
            face[ey: ey + height, ex: ex + width] = img2

    return src
