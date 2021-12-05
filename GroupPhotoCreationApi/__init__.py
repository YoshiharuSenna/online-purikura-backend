import logging
import json
import tensorflow as tf
from tf_bodypix.api import download_model, load_model, BodyPixModelPaths
import cv2
import numpy as np
from PIL import Image, ImageFilter
import base64
from io import BytesIO

import azure.functions as func
from azure.storage.blob import BlobServiceClient

CNNECT_STR='DefaultEndpointsProtocol=https;AccountName=onlinepurikuraapi;AccountKey=vdbQ9QZt7wPk4MtSav6u5vd5tVALcUTpNL0vQFklh8tg/PUmw5krxQ6i2nLHBCIRa3bsnJqHJ+t82jzZe2bH4Q==;EndpointSuffix=core.windows.net'
CONTAINER_NAME='background-image'

def getBackgroundImage(style):
    container_client = BlobServiceClient.from_connection_string(CNNECT_STR).get_container_client(CONTAINER_NAME)
    blob_client = container_client.get_blob_client(blob=str(style) + ".txt")
    imageData = blob_client.download_blob().readall()
    return imageData.decode('utf-8')

def changeImage(base64text):
    base64Data = base64.b64decode(base64text)
    bytesData = BytesIO(base64Data)
    image = Image.open(bytesData)
    return image

def changeNdarray(base64text):
    imgData = base64.b64decode(base64text.encode())
    imgNp = np.fromstring(imgData, np.uint8)
    return cv2.imdecode(imgNp, cv2.IMREAD_ANYCOLOR)

def make_mask(inputImage):
    bodypix_model = load_model(download_model(
        BodyPixModelPaths.MOBILENET_FLOAT_50_STRIDE_16
    ))

    image = changeImage(inputImage)
    image_array = tf.keras.preprocessing.image.img_to_array(image)
    result = bodypix_model.predict_single(image_array)
    mask = result.get_mask(threshold=0.75)
    mask_img = tf.keras.preprocessing.image.array_to_img(mask, scale=True)
    return np.array(mask_img, dtype=np.uint8)
    
def groupPhotoCreater(imageListInput, backgroundImageInput):
    left = 0
    bottom = 0
    imagewidth = 400
    kasanari = 1/3
    bg_img = changeNdarray(backgroundImageInput)
    imageh, imagew, ch = bg_img.shape
    for j, imageInputString in enumerate(imageListInput):
        fg_img = changeNdarray(imageInputString)
        mask = make_mask(imageInputString)
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        h, w = mask.shape
        
        contours = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
        # 輪郭の座標をリストに代入していく
        x1 = [] #x座標の最小値
        y1 = [] #y座標の最小値
        x2 = [] #x座標の最大値
        y2 = [] #y座標の最大値
        for i in range(1, len(contours)):# i = 1 は画像全体の外枠になるのでカウントに入れない
            ret = cv2.boundingRect(contours[i])
            x1.append(ret[0])
            y1.append(ret[1])
            x2.append(ret[0] + ret[2])
            y2.append(ret[1] + ret[3])

        # 輪郭の一番外枠を切り抜き
        x1_min = min(x1)
        y1_min = min(y1)
        x2_max = max(x2)
        y2_max = max(y2)
        cv2.rectangle(mask, (x1_min, y1_min), (x2_max, y2_max), (0, 255, 0), 3)

        crop_mask = mask[y1_min:y2_max, x1_min:x2_max]
        crop_img = fg_img[y1_min:y2_max, x1_min:x2_max]
        height = crop_img.shape[0]
        width = crop_img.shape[1]
        crop_mask = cv2.resize(crop_mask , (imagewidth, int(height*imagewidth/width)))
        crop_img = cv2.resize(crop_img , (imagewidth, int(height*imagewidth/width)))
        
        x, y = left+j*(imagewidth-int(imagewidth*kasanari)), imageh-int(height*imagewidth/width)-bottom  # 貼り付け位置

        # 幅、高さは前景画像と背景画像の共通部分をとる
        w = min(crop_img.shape[1], bg_img.shape[1] - x)
        h = min(crop_img.shape[0], bg_img.shape[0] - y)

        # 合成する領域
        fg_roi = crop_img[:h, :w]  # 前傾画像のうち、合成する領域
        bg_roi = bg_img[y : y + h, x : x + w]  # 背景画像のうち、合成する領域
        # 合成する。
        bg_roi[:] = np.where(crop_mask[:h, :w, np.newaxis] == 0, bg_roi, fg_roi)
        bg_img[y : y + h, x : x + w] = bg_roi
    ret, dst_data = cv2.imencode('.jpg', bg_img)
    dst_str = base64.b64encode(dst_data)
    return dst_str.decode('utf-8')

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

    backgroundImage = groupPhotoCreater(image, backgroundImage)
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
