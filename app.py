from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_from_directory,
    url_for
)

import base64
import cv2
import numpy as np

from pathlib import Path
from datetime import datetime


# ============================================================
# BANCO
# ============================================================

from banco import (
    criar_tabelas,
    listar_embeddings,
    pessoa_esta_presente,
    registrar_entrada,
    registrar_saida,
    criar_visitante,
    atualizar_foto_visitante,
    listar_visitantes_presentes,
    registrar_saida_visitante,
    listar_presentes,
    listar_historico,
    listar_visitantes,
    contar_presentes,
    contar_visitantes_presentes
)


# ============================================================
# RECONHECIMENTO
# ============================================================

from reconhecimento import (
    verificar_modelos,
    criar_detector,
    criar_reconhecedor,
    detectar_rosto,
    reconhecer_identidade,
    embedding_para_bytes
)


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)


# ============================================================
# CAMINHOS
# ============================================================

PASTA_PROJETO = (
    Path(__file__)
    .resolve()
    .parent
)


PASTA_VISITANTES = (
    PASTA_PROJETO
    / "visitantes"
)


PASTA_VISITANTES.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# INICIALIZAÇÃO
# ============================================================

criar_tabelas()

verificar_modelos()

detector = criar_detector()

reconhecedor = criar_reconhecedor()


# ============================================================
# FORMATAR DATA/HORA
# ============================================================

def formatar_data_hora(
    valor
):

    if not valor:
        return "-"

    try:

        data = datetime.fromisoformat(
            valor
        )

        return data.strftime(
            "%d/%m/%Y - %H:%M"
        )

    except Exception:

        return str(
            valor
        )


# ============================================================
# FILTRO JINJA
# ============================================================

@app.template_filter(
    "data_br"
)
def filtro_data_br(
    valor
):

    return formatar_data_hora(
        valor
    )


# ============================================================
# NORMALIZAR CAMINHO DA FOTO
# ============================================================

def normalizar_caminho_foto(
    caminho
):

    if not caminho:
        return None

    caminho = str(
        caminho
    ).replace(
        "\\",
        "/"
    )

    if caminho.startswith(
        "visitantes/"
    ):

        caminho = caminho[
            len("visitantes/"):
        ]

    return caminho


# ============================================================
# PÁGINA PADRÃO
# ============================================================

@app.route("/")
def pagina_inicial():

    return render_template(
        "index.html",
        modo_terminal="ENTRADA"
    )


# ============================================================
# TERMINAL DE ENTRADA
# ============================================================

@app.route("/entrada")
def pagina_entrada():

    return render_template(
        "index.html",
        modo_terminal="ENTRADA"
    )


# ============================================================
# TERMINAL DE SAÍDA
# ============================================================

@app.route("/saida")
def pagina_saida():

    return render_template(
        "index.html",
        modo_terminal="SAIDA"
    )


# ============================================================
# PAINEL ADMINISTRATIVO
# ============================================================

@app.route("/admin")
def painel_admin():

    return render_template(
        "admin.html"
    )


# ============================================================
# API DO PAINEL ADMINISTRATIVO
# ============================================================

@app.route(
    "/api/admin/dados"
)
def api_admin_dados():

    try:

        # ====================================================
        # DADOS DO BANCO
        # ====================================================

        presentes_banco = (
            listar_presentes()
        )

        visitantes_banco = (
            listar_visitantes()
        )

        historico_banco = (
            listar_historico()
        )

        total_presentes = (
            contar_presentes()
        )

        total_visitantes = (
            contar_visitantes_presentes()
        )

        total_ambiente = (
            total_presentes
            +
            total_visitantes
        )

        # ====================================================
        # PRESENTES
        # ====================================================

        presentes = []

        for pessoa in presentes_banco:

            presentes.append({

                "id":
                    int(
                        pessoa["id"]
                    ),

                "nome":
                    pessoa["nome"],

                "entrada":
                    formatar_data_hora(
                        pessoa["entrada"]
                    )

            })

        # ====================================================
        # VISITANTES
        # ====================================================

        visitantes = []

        for visitante in visitantes_banco:

            caminho_foto = (
                normalizar_caminho_foto(
                    visitante["foto"]
                )
            )

            foto_url = None

            if caminho_foto:

                foto_url = url_for(

                    "foto_visitante",

                    nome_arquivo=caminho_foto

                )

            visitantes.append({

                "id":
                    int(
                        visitante["id"]
                    ),

                "codigo":
                    visitante["codigo"],

                "entrada":
                    formatar_data_hora(
                        visitante["entrada"]
                    ),

                "saida":
                    formatar_data_hora(
                        visitante["saida"]
                    )
                    if visitante["saida"]
                    else "-",

                "presente":
                    bool(
                        visitante["presente"]
                    ),

                "foto_url":
                    foto_url

            })

        # ====================================================
        # HISTÓRICO
        # ====================================================

        historico = []

        for registro in historico_banco:

            historico.append({

                "id":
                    int(
                        registro["id"]
                    ),

                "pessoa_id":
                    int(
                        registro["pessoa_id"]
                    ),

                "nome":
                    registro["nome"],

                "entrada":
                    formatar_data_hora(
                        registro["entrada"]
                    ),

                "saida":
                    formatar_data_hora(
                        registro["saida"]
                    )
                    if registro["saida"]
                    else None

            })

        # ====================================================
        # RESPOSTA
        # ====================================================

        return jsonify({

            "sucesso":
                True,

            "resumo": {

                "total_ambiente":
                    total_ambiente,

                "total_presentes":
                    total_presentes,

                "total_visitantes":
                    total_visitantes

            },

            "presentes":
                presentes,

            "visitantes":
                visitantes,

            "historico":
                historico

        })

    except Exception as erro:

        print(
            "Erro na API administrativa:",
            erro
        )

        return jsonify({

            "sucesso":
                False,

            "mensagem":
                "Erro ao carregar dados do painel"

        }), 500


# ============================================================
# SERVIR FOTOS DOS VISITANTES
# ============================================================

@app.route(
    "/visitantes/<path:nome_arquivo>"
)
def foto_visitante(
    nome_arquivo
):

    return send_from_directory(

        PASTA_VISITANTES,

        nome_arquivo

    )


# ============================================================
# CONVERTER BASE64 PARA IMAGEM
# ============================================================

def converter_base64_para_imagem(
    imagem_base64
):

    try:

        if not imagem_base64:

            return None

        if "," not in imagem_base64:

            return None

        _, dados = (
            imagem_base64.split(
                ",",
                1
            )
        )

        imagem_bytes = (
            base64.b64decode(
                dados
            )
        )

        array = np.frombuffer(

            imagem_bytes,

            dtype=np.uint8

        )

        imagem = cv2.imdecode(

            array,

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
# VERIFICAR POSICIONAMENTO DO ROSTO
# ============================================================

@app.route(
    "/verificar-rosto",
    methods=["POST"]
)
def verificar_rosto():

    try:

        dados = request.get_json()

        if (
            not dados
            or
            "imagem" not in dados
        ):

            return jsonify({

                "rosto_detectado":
                    False,

                "posicionado":
                    False,

                "mensagem":
                    "Imagem não recebida"

            }), 400

        imagem = (
            converter_base64_para_imagem(
                dados["imagem"]
            )
        )

        if imagem is None:

            return jsonify({

                "rosto_detectado":
                    False,

                "posicionado":
                    False,

                "mensagem":
                    "Imagem inválida"

            }), 400

        face = detectar_rosto(
            imagem,
            detector
        )

        if face is None:

            return jsonify({

                "rosto_detectado":
                    False,

                "posicionado":
                    False,

                "mensagem":
                    "Posicione seu rosto"

            })

        altura, largura = (
            imagem.shape[:2]
        )

        x = float(
            face[0]
        )

        y = float(
            face[1]
        )

        largura_rosto = float(
            face[2]
        )

        altura_rosto = float(
            face[3]
        )

        # ====================================================
        # CENTRO DO ROSTO
        # ====================================================

        centro_rosto_x = (
            x
            +
            largura_rosto / 2
        )

        centro_rosto_y = (
            y
            +
            altura_rosto / 2
        )

        # ====================================================
        # CENTRO DA IMAGEM
        # ====================================================

        centro_imagem_x = (
            largura / 2
        )

        centro_imagem_y = (
            altura / 2
        )

        # ====================================================
        # MARGENS
        # ====================================================

        margem_x = (
            largura * 0.20
        )

        margem_y = (
            altura * 0.20
        )

        centralizado_x = bool(

            abs(
                centro_rosto_x
                -
                centro_imagem_x
            )
            <=
            margem_x

        )

        centralizado_y = bool(

            abs(
                centro_rosto_y
                -
                centro_imagem_y
            )
            <=
            margem_y

        )

        # ====================================================
        # TAMANHO
        # ====================================================

        proporcao_rosto = float(

            largura_rosto
            /
            largura

        )

        tamanho_adequado = bool(

            proporcao_rosto
            >=
            0.25

        )

        posicionado = bool(

            centralizado_x
            and
            centralizado_y
            and
            tamanho_adequado

        )

        # ====================================================
        # MENSAGENS
        # ====================================================

        if not tamanho_adequado:

            mensagem = (
                "Aproxime-se da câmera"
            )

        elif (
            not centralizado_x
            or
            not centralizado_y
        ):

            mensagem = (
                "Centralize seu rosto"
            )

        else:

            mensagem = (
                "Rosto bem posicionado"
            )

        return jsonify({

            "rosto_detectado":
                True,

            "posicionado":
                posicionado,

            "mensagem":
                mensagem

        })

    except Exception as erro:

        print(
            "Erro na verificação:",
            erro
        )

        return jsonify({

            "rosto_detectado":
                False,

            "posicionado":
                False,

            "mensagem":
                "Erro na verificação"

        }), 500


# ============================================================
# SALVAR FOTO TEMPORÁRIA DO VISITANTE
# ============================================================

def salvar_foto_visitante(
    imagem,
    codigo_temporario
):

    hoje = datetime.now().strftime(
        "%Y-%m-%d"
    )

    pasta_data = (
        PASTA_VISITANTES
        /
        hoje
    )

    pasta_data.mkdir(
        parents=True,
        exist_ok=True
    )

    nome_arquivo = (
        f"{codigo_temporario}.jpg"
    )

    caminho = (
        pasta_data
        /
        nome_arquivo
    )

    sucesso = cv2.imwrite(
        str(caminho),
        imagem
    )

    if not sucesso:

        return None

    return caminho


# ============================================================
# REGISTRAR NOVO VISITANTE
# ============================================================

def registrar_novo_visitante(
    imagem,
    embedding
):

    codigo_temporario = (
        "TEMP_"
        +
        datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )
    )

    caminho_temporario = (
        salvar_foto_visitante(
            imagem,
            codigo_temporario
        )
    )

    if caminho_temporario is None:

        return None

    embedding_bytes = (
        embedding_para_bytes(
            embedding
        )
    )

    caminho_relativo_temp = (
        caminho_temporario
        .relative_to(
            PASTA_PROJETO
        )
    )

    visitante = criar_visitante(

        embedding_bytes,

        str(
            caminho_relativo_temp
        )

    )

    codigo = visitante[
        "codigo"
    ]

    novo_caminho = (
        caminho_temporario
        .with_name(
            f"{codigo}.jpg"
        )
    )

    try:

        caminho_temporario.rename(
            novo_caminho
        )

        caminho_relativo = (
            novo_caminho
            .relative_to(
                PASTA_PROJETO
            )
        )

        atualizar_foto_visitante(

            visitante["id"],

            str(
                caminho_relativo
            )

        )

        visitante[
            "foto"
        ] = str(
            caminho_relativo
        )

    except Exception as erro:

        print(
            "Erro ao renomear foto:",
            erro
        )

    return visitante


# ============================================================
# PROCESSAR ACESSO
# ============================================================

@app.route(
    "/processar-acesso",
    methods=["POST"]
)
def processar_acesso():

    try:

        dados = request.get_json()

        if not dados:

            return jsonify({

                "sucesso":
                    False,

                "evento":
                    "ERRO",

                "mensagem":
                    "Dados não recebidos"

            }), 400

        modo = str(

            dados.get(
                "modo",
                ""
            )

        ).upper()

        if modo not in (
            "ENTRADA",
            "SAIDA"
        ):

            return jsonify({

                "sucesso":
                    False,

                "evento":
                    "ERRO",

                "mensagem":
                    "Modo inválido"

            }), 400

        imagem = (
            converter_base64_para_imagem(

                dados.get(
                    "imagem"
                )

            )
        )

        if imagem is None:

            return jsonify({

                "sucesso":
                    False,

                "evento":
                    "ERRO",

                "mensagem":
                    "Imagem inválida"

            }), 400

        # ====================================================
        # CARREGAR BASES
        # ====================================================

        embeddings_cadastrados = (
            listar_embeddings()
        )

        visitantes_presentes = (
            listar_visitantes_presentes()
        )

        # ====================================================
        # RECONHECIMENTO
        # ====================================================

        resultado = reconhecer_identidade(

            imagem,

            detector,

            reconhecedor,

            embeddings_cadastrados,

            visitantes_presentes

        )

        if not resultado[
            "rosto_detectado"
        ]:

            return jsonify({

                "sucesso":
                    False,

                "evento":
                    "SEM_ROSTO",

                "mensagem":
                    "Rosto não detectado"

            })

        # ====================================================
        # PESSOA CADASTRADA
        # ====================================================

        if (
            resultado["tipo"]
            ==
            "PESSOA"
        ):

            pessoa_id = (
                resultado[
                    "pessoa_id"
                ]
            )

            nome = (
                resultado[
                    "nome"
                ]
            )

            similaridade = float(
                resultado[
                    "similaridade"
                ]
            )

            presente = (
                pessoa_esta_presente(
                    pessoa_id
                )
            )

            # ------------------------------------------------
            # ENTRADA
            # ------------------------------------------------

            if modo == "ENTRADA":

                if presente:

                    return jsonify({

                        "sucesso":
                            True,

                        "tipo":
                            "PESSOA",

                        "evento":
                            "JA_PRESENTE",

                        "nome":
                            nome,

                        "similaridade":
                            similaridade,

                        "mensagem":
                            "Entrada já registrada"

                    })

                horario = registrar_entrada(
                    pessoa_id
                )

                return jsonify({

                    "sucesso":
                        True,

                    "tipo":
                        "PESSOA",

                    "evento":
                        "ENTRADA",

                    "nome":
                        nome,

                    "similaridade":
                        similaridade,

                    "horario":
                        horario,

                    "mensagem":
                        "Entrada registrada"

                })

            # ------------------------------------------------
            # SAÍDA
            # ------------------------------------------------

            if modo == "SAIDA":

                if not presente:

                    return jsonify({

                        "sucesso":
                            False,

                        "tipo":
                            "PESSOA",

                        "evento":
                            "ENTRADA_NAO_LOCALIZADA",

                        "nome":
                            nome,

                        "similaridade":
                            similaridade,

                        "mensagem":
                            "Entrada não localizada"

                    })

                horario = registrar_saida(
                    pessoa_id
                )

                return jsonify({

                    "sucesso":
                        True,

                    "tipo":
                        "PESSOA",

                    "evento":
                        "SAIDA",

                    "nome":
                        nome,

                    "similaridade":
                        similaridade,

                    "horario":
                        horario,

                    "mensagem":
                        "Saída registrada"

                })

        # ====================================================
        # VISITANTE PRESENTE
        # ====================================================

        if (
            resultado["tipo"]
            ==
            "VISITANTE"
        ):

            visitante_id = (
                resultado[
                    "visitante_id"
                ]
            )

            codigo = (
                resultado[
                    "codigo"
                ]
            )

            similaridade = float(
                resultado[
                    "similaridade"
                ]
            )

            # ------------------------------------------------
            # ENTRADA DUPLICADA
            # ------------------------------------------------

            if modo == "ENTRADA":

                return jsonify({

                    "sucesso":
                        True,

                    "tipo":
                        "VISITANTE",

                    "evento":
                        "VISITANTE_JA_PRESENTE",

                    "nome":
                        codigo,

                    "codigo":
                        codigo,

                    "similaridade":
                        similaridade,

                    "mensagem":
                        "Entrada já registrada"

                })

            # ------------------------------------------------
            # SAÍDA
            # ------------------------------------------------

            if modo == "SAIDA":

                horario = (
                    registrar_saida_visitante(
                        visitante_id
                    )
                )

                if horario is None:

                    return jsonify({

                        "sucesso":
                            False,

                        "tipo":
                            "VISITANTE",

                        "evento":
                            "ENTRADA_NAO_LOCALIZADA",

                        "mensagem":
                            "Entrada não localizada"

                    })

                return jsonify({

                    "sucesso":
                        True,

                    "tipo":
                        "VISITANTE",

                    "evento":
                        "SAIDA_VISITANTE",

                    "nome":
                        codigo,

                    "codigo":
                        codigo,

                    "similaridade":
                        similaridade,

                    "horario":
                        horario,

                    "mensagem":
                        "Saída registrada"

                })

        # ====================================================
        # DESCONHECIDO
        # ====================================================

        if (
            resultado["tipo"]
            ==
            "DESCONHECIDO"
        ):

            # ------------------------------------------------
            # NOVO VISITANTE
            # ------------------------------------------------

            if modo == "ENTRADA":

                visitante = (
                    registrar_novo_visitante(

                        imagem,

                        resultado[
                            "embedding"
                        ]

                    )
                )

                if visitante is None:

                    return jsonify({

                        "sucesso":
                            False,

                        "evento":
                            "ERRO_VISITANTE",

                        "mensagem":
                            "Não foi possível registrar visitante"

                    }), 500

                return jsonify({

                    "sucesso":
                        True,

                    "tipo":
                        "VISITANTE",

                    "evento":
                        "ENTRADA_VISITANTE",

                    "nome":
                        visitante[
                            "codigo"
                        ],

                    "codigo":
                        visitante[
                            "codigo"
                        ],

                    "horario":
                        visitante[
                            "entrada"
                        ],

                    "mensagem":
                        "Entrada registrada como visitante"

                })

            # ------------------------------------------------
            # DESCONHECIDO TENTANDO SAIR
            # ------------------------------------------------

            if modo == "SAIDA":

                return jsonify({

                    "sucesso":
                        False,

                    "tipo":
                        "DESCONHECIDO",

                    "evento":
                        "VISITANTE_NAO_LOCALIZADO",

                    "mensagem":
                        "Registro de entrada não localizado"

                })

        # ====================================================
        # FALLBACK
        # ====================================================

        return jsonify({

            "sucesso":
                False,

            "evento":
                "ERRO",

            "mensagem":
                "Não foi possível processar"

        })

    except Exception as erro:

        print(
            "Erro ao processar acesso:",
            erro
        )

        return jsonify({

            "sucesso":
                False,

            "evento":
                "ERRO",

            "mensagem":
                "Erro ao processar acesso"

        }), 500


# ============================================================
# INICIAR
# ============================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )
