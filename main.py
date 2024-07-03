import logging
import os
import re
import sys
from fastapi import FastAPI, HTTPException, Request
from datetime import datetime
from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import uvicorn
import requests
from google.cloud import secretmanager

logging.basicConfig(level=os.getenv('LOG', 'WARNING'))
logger = logging.getLogger(__file__)

app = FastAPI()

def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

channel_secret = get_secret('LINE_CHANNEL_SECRET')
channel_access_token = get_secret('LINE_CHANNEL_ACCESS_TOKEN')

configuration = Configuration(access_token=channel_access_token)
async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)
parser = WebhookParser(channel_secret)

import google.generativeai as genai
from firebase import firebase
from utils import check_image_quake, check_location_in_message, get_current_weather, get_weather_data, simplify_data

firebase_url = os.getenv('FIREBASE_URL')
gemini_key = os.getenv('GEMINI_API_KEY')

# Initialize the Gemini Pro API
genai.configure(api_key=gemini_key)

@app.get("/health")
async def health():
    return 'ok'

@app.post("/webhooks/line")
async def handle_callback(request: Request):
    signature = request.headers['X-Line-Signature']
    body = await request.body()
    body = body.decode()

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        logging.info(event)
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessageContent):
            continue
        text = event.message.text
        user_id = event.source.user_id
        msg_type = event.message.type
        fdb = firebase.FirebaseApplication(firebase_url, None)
        if event.source.type == 'group':
            user_chat_path = f'chat/{event.source.group_id}'
        else:
            user_chat_path = f'chat/{user_id}'
            chat_state_path = f'state/{user_id}'
        chatgpt = fdb.get(user_chat_path, None)

        if msg_type == 'text':
            if chatgpt is None:
                messages = []
            else:
                messages = chatgpt

            bot_condition = {
                "清空": 'A',
                "摘要": 'B',
                "地震": 'C',
                "氣候": 'D',
                "其他": 'E'
            }

            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(
                f'請判斷 {text} 裡面的文字屬於 {bot_condition} 裡面的哪一項？符合條件請回傳對應的英文文字就好，不要有其他的文字與字元。')
            text_condition = re.sub(r'[^A-Za-z]', '', response.text)

            if text_condition == 'A':
                fdb.delete(user_chat_path, None)
                reply_msg = '已清空對話紀錄'
            elif text_condition == 'B':
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(
                    f'Summary the following message in Traditional Chinese by less 5 list points. \n{messages}')
                reply_msg = response.text
            elif text_condition == 'C':
                OPEN_API_KEY = os.getenv('OPEN_API_KEY')
                earth_res = requests.get(f'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/E-A0015-003?Authorization={OPEN_API_KEY}&downloadType=WEB&format=JSON')
                url = earth_res.json()["cwaopendata"]["Dataset"]["Resource"]["ProductURL"]
                reply_msg = check_image_quake(url) + f'\n\n{url}'
            elif text_condition == 'D':
                location_text = '台北市'
                location = check_location_in_message(location_text)
                weather_data = get_weather_data(location)
                simplified_data = simplify_data(weather_data)
                current_weather = get_current_weather(simplified_data)
                now = datetime.now()
                formatted_time = now.strftime("%Y/%m/%d %H:%M:%S")

                if current_weather is not None:
                    total_info = f'位置: {location}\n氣候: {current_weather["Wx"]}\n降雨機率: {current_weather["PoP"]}\n體感: {current_weather["CI"]}\n現在時間: {formatted_time}'

                response = model.generate_content(
                    f'你現在身處在台灣，相關資訊 {total_info}，我朋友說了「{text}」，請問是否有誇張、假裝的嫌疑？ 回答是或否。')
                reply_msg = response.text
            else:
                messages.append({'role': 'user', 'parts': [text]})
                response = model.generate_content(messages)
                messages.append({'role': 'model', 'parts': [text]})
                fdb.put_async(user_chat_path, None, messages)
                reply_msg = response.text

            await line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_msg)]
                ))

    return 'OK'

#功能介紹區
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = text=event.message.text
    if re.match('功能', message):
        buttons_template_message = TemplateSendMessage(
            alt_text='使用功能簡介',
            template=ButtonsTemplate(
                thumbnail_image_url='https://i.imgur.com/wpM584d.jpg',
                title='行銷搬進大程式',
                text='選單功能－TemplateSendMessage',
                actions=[
                    MessageAction(
                        label='什麼是FoMO？',
                        text='FOMO（Fear Of Missing Out，錯失恐懼症）由金融家Patrick McGinnis提出，指個體因害怕錯過機會或無法參與他人活動而產生的焦慮和恐懼。這種現象根植於人類基因，與歸屬感密切相關，代表著安全感和認同感。\n在社交媒體和快節奏生活中，人們通過與他人的連結獲取信息、得到認可和肯定，這促發了FOMO。\n 而社交平台的限時動態和短影音內容激發了FOMO心理，讓人渴望在短時間內獲取信息，並通過模仿行為來獲得更多關注和認同。然而，過度依賴他人的反應可能導致負面情緒，影響生活信念和態度。因此，需保持平衡，以避免FOMO帶來的負面影響。'
                    ),
                    URIAction(
                        label='測試網址',
                        uri='https://www.parenting.com.tw/article/5096067'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template_message)
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(message))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', default=8080))
    debug = True if os.environ.get('API_ENV', default='develop') == 'develop' else False
    logging.info('Application will start...')
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=debug)
