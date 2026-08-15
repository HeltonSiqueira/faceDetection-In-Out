from flask import Flask, render_template, request, jsonify

import base64
import cv2
import numpy as np


app = Flask(__name__)


# ============================================================
# CARREGA O DETECTOR FACIAL
# ============================================================

caminho_detector = (
    cv2.data.haarcascades
    + "haarcascade_frontalface_default.xml"
)

detector = cv2.CascadeClassifier(caminho_detector)


if detector.empty():
    print("ERRO: não foi possível carregar o detector facial")
else:
    print("Detector facial carregado com sucesso")


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
# CONVERTER BASE64 PARA IMAGEM OPENCV
# ============================================================

def converter_base64_para_imagem(imagem_base64):

    try:

        if not imagem_base64:
            return None

        if "," not in imagem_base64:
            return None

        _, dados = imagem_base64.split(",", 1)

        imagem_bytes = base64.b64decode(dados)

        np_array = np.frombuffer(
            imagem_bytes,
            dtype=np.uint8
        )

        imagem = cv2.imdecode(
            np_array,
            cv2.IMREAD_COLOR
        )

        return imagem

    except Exception as erro:

        print(
            "Erro ao converter imagem:",
            erro
        )

        return None


# ============================================================
# VERIFICAR ROSTO
# ============================================================

@app.route(
    "/verificar-rosto",
    methods=["POST"]
)
def verificar_rosto():

    try:

        dados = request.get_json()

        if not dados:

            return jsonify({
                "posicionado": False,
                "rosto_detectado": False,
                "mensagem": "Dados não recebidos"
            }), 400

        if "imagem" not in dados:

            return jsonify({
                "posicionado": False,
                "rosto_detectado": False,
                "mensagem": "Imagem não recebida"
            }), 400

        imagem = converter_base64_para_imagem(
            dados["imagem"]
        )

        if imagem is None:

            return jsonify({
                "posicionado": False,
                "rosto_detectado": False,
                "mensagem": "Imagem inválida"
            }), 400

        # ====================================================
        # CONVERTE PARA CINZA
        # ====================================================

        imagem_cinza = cv2.cvtColor(
            imagem,
            cv2.COLOR_BGR2GRAY
        )

        # ====================================================
        # DETECTA ROSTOS
        # ====================================================

        rostos = detector.detectMultiScale(
            imagem_cinza,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100)
        )

        # ====================================================
        # NÃO EXISTE ROSTO
        # ====================================================

        if len(rostos) == 0:

            return jsonify({
                "posicionado": False,
                "rosto_detectado": False,
                "mensagem": "Posicione seu rosto"
            })

        # ====================================================
        # PEGA O MAIOR ROSTO
        # ====================================================

        rosto = max(
            rostos,
            key=lambda r:
                int(r[2]) * int(r[3])
        )

        x = int(rosto[0])
        y = int(rosto[1])

        largura_rosto = int(
            rosto[2]
        )

        altura_rosto = int(
            rosto[3]
        )

        altura_imagem, largura_imagem = (
            imagem.shape[:2]
        )

        # ====================================================
        # CENTRO DO ROSTO
        # ====================================================

        centro_rosto_x = (
            x + largura_rosto / 2
        )

        centro_rosto_y = (
            y + altura_rosto / 2
        )

        # ====================================================
        # CENTRO DA IMAGEM
        # ====================================================

        centro_imagem_x = (
            largura_imagem / 2
        )

        centro_imagem_y = (
            altura_imagem / 2
        )

        # ====================================================
        # MARGENS ACEITÁVEIS
        # ====================================================

        margem_x = (
            largura_imagem * 0.20
        )

        margem_y = (
            altura_imagem * 0.20
        )

        # ====================================================
        # CENTRALIZAÇÃO
        # ====================================================

        centralizado_x = bool(
            abs(
                centro_rosto_x
                - centro_imagem_x
            )
            <= margem_x
        )

        centralizado_y = bool(
            abs(
                centro_rosto_y
                - centro_imagem_y
            )
            <= margem_y
        )

        # ====================================================
        # TAMANHO DO ROSTO
        # ====================================================

        proporcao_rosto = float(
            largura_rosto
            / largura_imagem
        )

        tamanho_adequado = bool(
            proporcao_rosto
            >= 0.25
        )

        # ====================================================
        # POSICIONAMENTO FINAL
        # ====================================================

        posicionado = bool(
            centralizado_x
            and centralizado_y
            and tamanho_adequado
        )

        # ====================================================
        # MENSAGEM
        # ====================================================

        if not tamanho_adequado:

            mensagem = (
                "Aproxime-se da câmera"
            )

        elif not centralizado_x:

            mensagem = (
                "Centralize seu rosto"
            )

        elif not centralizado_y:

            mensagem = (
                "Centralize seu rosto"
            )

        else:

            mensagem = (
                "Rosto bem posicionado"
            )

        # ====================================================
        # DEBUG
        # ====================================================

        print(
            "Rosto detectado:",
            "X =", x,
            "Y =", y,
            "L =", largura_rosto,
            "A =", altura_rosto,
            "| Proporção =",
            round(proporcao_rosto, 2),
            "| Posicionado =",
            posicionado
        )

        return jsonify({
            "posicionado": bool(posicionado),
            "rosto_detectado": True,
            "mensagem": mensagem
        })

    except Exception as erro:

        print(
            "Erro na verificação:",
            erro
        )

        return jsonify({
            "posicionado": False,
            "rosto_detectado": False,
            "mensagem": "Erro na verificação"
        }), 500


# ============================================================
# CAPTURAR ROSTO
# ============================================================

@app.route(
    "/capturar-rosto",
    methods=["POST"]
)
def capturar_rosto():

    try:

        dados = request.get_json()

        if not dados:

            return jsonify({
                "sucesso": False,
                "mensagem": "Dados não recebidos"
            }), 400

        if "imagem" not in dados:

            return jsonify({
                "sucesso": False,
                "mensagem": "Imagem não recebida"
            }), 400

        imagem = converter_base64_para_imagem(
            dados["imagem"]
        )

        if imagem is None:

            return jsonify({
                "sucesso": False,
                "mensagem": "Imagem inválida"
            }), 400

        # ====================================================
        # SALVA A CAPTURA
        # ====================================================

        sucesso = cv2.imwrite(
            "captura.jpg",
            imagem
        )

        if not sucesso:

            return jsonify({
                "sucesso": False,
                "mensagem":
                    "Não foi possível salvar a imagem"
            }), 500

        print(
            "Imagem salva em captura.jpg"
        )

        return jsonify({
            "sucesso": True,
            "mensagem":
                "Rosto capturado com sucesso"
        })

    except Exception as erro:

        print(
            "Erro ao capturar:",
            erro
        )

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Erro ao capturar imagem"
        }), 500


# ============================================================
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
