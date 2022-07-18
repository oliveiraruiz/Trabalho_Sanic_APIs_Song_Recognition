from sanic import Sanic, response
from sanic.response import text, HTTPResponse, json
from sanic.request import Request
from requests.auth import HTTPBasicAuth
import base64
import hashlib
import hmac
import os
import time
import requests
import ast
import aiofiles


app = Sanic("meuApp")

appConfig = {}
appConfig["mp3"] = "./"

@app.get("/")
async def UP(request):
    return text("Server is up!")

@app.route("/search", methods=["POST"])
async def busca(request:Request):
#LIMPAR ARQUIVOS JÁ USADOS
    dir_name = "./"
    test = os.listdir(dir_name)

    for item in test:
        if item.endswith(".mp3"):
            os.remove(os.path.join(dir_name, item))

#CHAVES DE ACESSO OBTIDAS NO ACRCLOUD>>> https://console-v2.acrcloud.com/avr?region=eu-west-1#/projects/online
    access_key = "COLOQUE SUA CHAVE AQUI"
    access_secret = "COLOQUE SEU SEGREDO AQUI"
    requrl = "http://identify-eu-west-1.acrcloud.com/v1/identify"

#CONFIGURAÇÃO DA MENSAGEM
    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = time.time()
    string_to_sign = http_method + "\n" + http_uri + "\n" + access_key + "\n" + data_type + "\n" + signature_version + "\n" + str(timestamp)
    sign = base64.b64encode(hmac.new(access_secret.encode('ascii'), string_to_sign.encode('ascii'), digestmod=hashlib.sha1).digest()).decode('ascii')

#CONFIGURAÇÃO DO ARQUIVO MP3 (MENOR QUE 1MB E INFERIOR A 15 SEGUNDOS DE DURAÇÃO)
    if len(request.body) == 0:
        return response.json({"status": "error", "message": "No Query Parameters"}, status=400)
    if not os.path.exists(appConfig["mp3"]):
        os.makedirs(appConfig["mp3"])
    async with aiofiles.open(appConfig["mp3"]+"/"+request.files["mp3"][0].name, 'wb') as f:
        await f.write(request.files["mp3"][0].body)
    f.close()
    fileDir = r"./"
    fileExt = r".mp3"
    path = [_ for _ in os.listdir(fileDir) if _.endswith(fileExt)]
    path = path[0]
    sample_bytes = os.path.getsize(path)
    files = [('sample', ('test.mp3', open(path, 'rb'), 'audio/mpeg'))]

#DADOS DO ARQUIVO DE AUDIO A SER ENVIADO
    data = {'access_key': access_key,
            'sample_bytes': sample_bytes,
            'timestamp': str(timestamp),
            'signature': sign,
            'data_type': data_type,
            "signature_version": signature_version}

#MONTAGEM DO PACOTE DE POST
    r = requests.post(requrl, files=files, data=data)

#TRATAMENTO DOS DADOS
    r.encoding = "utf-8"
    r = r.text
    convertedDict = ast.literal_eval(r)

#ATRIBUIÇÃO DE VARIÁVEIS
    musica = convertedDict['metadata']['music'][0]['title']
    artista = convertedDict['metadata']['music'][0]['artists'][0]['name']
    album = convertedDict['metadata']['music'][0]['album']['name']
#LETRA DA MUSICA
    url = "http://api.musixmatch.com/ws/1.1/matcher.lyrics.get"
    q_track = musica
    q_artist = artista
    apikey = "COLOQUE SUA OUTRA CHAVE AQUI"

    params = {'q_track':q_track, 'q_artist':q_artist, 'apikey':apikey}
    resp = requests.get(url, params=params)
    resp.encoding = "utf-8"
    l = resp.text
    conv = ast.literal_eval(l)
    letra = conv['message']['body']['lyrics']['lyrics_body']
    letra = letra.replace("\n", " ")

#MANDA A RESPOSTA PARA O USUÁRIO   
    return response.json({"status": "ok", "musica": str(musica), "artista": str(artista), "album": str(album), "letra": str(letra)}, status=201)