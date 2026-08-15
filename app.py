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

    cadastrar_pessoa,
    buscar_pessoa_por_nome,
    excluir_pessoa,

    cadastrar_embedding,
    contar_embeddings_pessoa,
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
    gerar_embedding_imagem,
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
# DATA/HORA BR
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


@app.template_filter("data_br")
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
# PÁGINAS
# ============================================================

@app.route("/")
def pagina_inicial():

    return render_template(
        "index.html",
        modo_terminal="ENTRADA"
    )


@app.route("/entrada")
def pagina_entrada():

    return render_template(
        "index.html",
        modo_terminal="ENTRADA"
    )


@app.route("/saida")
def pagina_saida():

    return render_template(
        "index.html",
        modo_terminal="SAIDA"
    )


@app.route("/admin")
def painel_admin():

    return render_template(
        "admin.html"
    )


@app.route("/admin/cadastrar")
def pagina_cadastrar_pessoa():

    return render_template(
        "cadastro.html"
    )


# ============================================================
# API ADMIN
# ============================================================

@app.route("/api/admin/dados")
def api_admin_dados():

    try:

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

            caminho = (
                normalizar_caminho_foto(
                    visitante["foto"]
                )
            )

            foto_url = None

            if caminho:

                foto_url = url_for(
                    "foto_visitante",
                    nome_arquivo=caminho
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
            "Erro API admin:",
            erro
        )

        return jsonify({

            "sucesso":
                False,

            "mensagem":
                "Erro ao carregar painel"

        }), 500


# ============================================================
# INICIAR CADASTRO DE PESSOA
# ============================================================

@app.route(
    "/api/cadastro/iniciar",
    methods=["POST"]
)
def iniciar_cadastro_pessoa():

    try:

        dados = (
            request.get_json()
            or {}
        )

        nome = str(
            dados.get(
                "nome",
                ""
            )
        ).strip()

        if len(nome) < 2:

            return jsonify({

                "sucesso":
                    False,

                "mensagem":
                    "Informe o nome da pessoa"

            }), 400

        pessoa_existente = (
            buscar_pessoa_por_nome(
                nome
            )
        )

        if pessoa_existente:

            return jsonify({

                "sucesso":
                    False,

                "mensagem":
                    "Já existe uma pessoa com esse nome"

            }), 409

        pessoa_id = (
            cadastrar_pessoa(
                nome
            )
        )

        return jsonify({

            "sucesso":
                True,

            "pessoa_id":
                pessoa_id,

            "nome":
                nome

        })

    except Exception as erro:

        print(
            "Erro ao iniciar cadastro:",
            erro
        )

        return jsonify({

            "sucesso":
                False,

            "mensagem":
                "Erro ao iniciar cadastro"

        }), 500


# ============================================================
# SALVAR AMOSTRA DE PESSOA
# ============================================================

@app.route(
    "/api/cadastro/amostra",
    methods=["POST"]
)
def cadastrar_amostra_pessoa():

    try:

        dados = (
            request.get_json()
            or {}
        )

        pessoa_id = int(
            dados.get(
                "pessoa_id"
            )
        )

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

                "mensagem":
                    "Imagem inválida"

            }), 400

        embedding = (
            gerar_embedding_imagem(

                imagem,

                detector,

                reconhecedor

            )
        )

        if embedding is None:

            return jsonify({

                "sucesso":
                    False,

                "mensagem":
                    "Rosto não detectado"

            }), 400

        embedding_bytes = (
            embedding_para_bytes(
                embedding
            )
        )

        cadastrar_embedding(
            pessoa_id,
            embedding_bytes
        )

        total = (
            contar_embeddings_pessoa(
                pessoa_id
            )
        )

        return jsonify({

            "sucesso":
                True,

            "total":
                total

        })

    except Exception as erro:

        print(
            "Erro ao cadastrar amostra:",
            erro
        )

        return jsonify({

            "sucesso":
                False,

            "mensagem":
                "Erro ao salvar amostra"

        }), 500


# ============================================================
# CANCELAR CADASTRO
# ============================================================

@app.route(
    "/api/cadastro/cancelar",
    methods=["POST"]
)
def cancelar_cadastro_pessoa():

    try:

        dados = (
            request.get_json()
            or {}
        )

        pessoa_id = int(
            dados.get(
                "pessoa_id"
            )
        )

        excluir_pessoa(
            pessoa_id
        )

        return jsonify({
            "sucesso": True
        })

    except Exception as erro:

        print(
            "Erro ao cancelar cadastro:",
            erro
        )

        return jsonify({
            "sucesso": False
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
# BASE64 -> OPENCV
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
# VERIFICAR ROSTO
# ============================================================

@app.route(
    "/verificar-rosto",
    methods=["POST"]
)
def verificar_rosto():

    try:

        dados = (
            request.get_json()
            or {}
        )

        imagem = (
            converter_base64_para_imagem(
                dados.get(
                    "imagem"
                )
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

            })

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

        centro_imagem_x = (
            largura / 2
        )

        centro_imagem_y = (
            altura / 2
        )

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

        proporcao_rosto = (
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
            "Erro verificar rosto:",
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

    pasta = (
        PASTA_VISITANTES
        /
        hoje
    )

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho = (
        pasta
        /
        f"{codigo_temporario}.jpg"
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

    # --------------------------------------------------------
    # NOME TEMPORÁRIO
    # --------------------------------------------------------

    temporario = (
        "TEMP_"
        +
        datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )
    )

    caminho_temp = (
        salvar_foto_visitante(
            imagem,
            temporario
        )
    )

    if caminho_temp is None:

        return None

    # --------------------------------------------------------
    # EMBEDDING -> BYTES
    # --------------------------------------------------------

    embedding_bytes = (
        embedding_para_bytes(
            embedding
        )
    )

    # --------------------------------------------------------
    # CAMINHO TEMPORÁRIO RELATIVO
    # --------------------------------------------------------

    caminho_relativo_temp = (
        caminho_temp
        .relative_to(
            PASTA_PROJETO
        )
    )

    # --------------------------------------------------------
    # CRIA O VISITANTE NO BANCO
    #
    # O BANCO GERA:
    # VIS-00001
    # VIS-00002
    # ...
    # --------------------------------------------------------

    visitante = (
        criar_visitante(

            embedding_bytes,

            str(
                caminho_relativo_temp
            )

        )
    )

    # --------------------------------------------------------
    # CÓDIGO DEFINITIVO
    # --------------------------------------------------------

    codigo = (
        visitante[
            "codigo"
        ]
    )

    # --------------------------------------------------------
    # CAMINHO DEFINITIVO
    # --------------------------------------------------------

    novo_caminho = (
        caminho_temp
        .with_name(
            f"{codigo}.jpg"
        )
    )

    try:

        # ====================================================
        # RENOMEIA:
        #
        # TEMP_xxx.jpg
        #
        # PARA:
        #
        # VIS-00001.jpg
        # ====================================================

        caminho_temp.rename(
            novo_caminho
        )

        # ====================================================
        # CAMINHO RELATIVO DEFINITIVO
        # ====================================================

        caminho_relativo = (
            novo_caminho
            .relative_to(
                PASTA_PROJETO
            )
        )

        caminho_relativo_str = str(
            caminho_relativo
        )

        # ====================================================
        # IMPORTANTE:
        #
        # ATUALIZA O CAMINHO NO SQLITE.
        #
        # ISSO CORRIGE O PROBLEMA DOS TEMP_*.jpg
        # ====================================================

        atualizar_foto_visitante(

            visitante[
                "id"
            ],

            caminho_relativo_str

        )

        # ====================================================
        # ATUALIZA TAMBÉM O OBJETO LOCAL
        # ====================================================

        visitante[
            "foto"
        ] = caminho_relativo_str

        print(
            "Foto visitante:",
            caminho_relativo_str
        )

    except Exception as erro:

        print(
            "Erro ao renomear/atualizar foto do visitante:",
            erro
        )

        # Se deu erro depois de salvar TEMP,
        # ainda retornamos o visitante.
        # Isso evita derrubar o fluxo de acesso.

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

        dados = (
            request.get_json()
            or {}
        )

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

        resultado = (
            reconhecer_identidade(

                imagem,

                detector,

                reconhecedor,

                listar_embeddings(),

                listar_visitantes_presentes()

            )
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

                        "evento":
                            "JA_PRESENTE",

                        "nome":
                            nome,

                        "mensagem":
                            "Entrada já registrada"

                    })

                horario = (
                    registrar_entrada(
                        pessoa_id
                    )
                )

                return jsonify({

                    "sucesso":
                        True,

                    "evento":
                        "ENTRADA",

                    "nome":
                        nome,

                    "horario":
                        horario,

                    "mensagem":
                        "Entrada registrada"

                })

            # ------------------------------------------------
            # SAÍDA
            # ------------------------------------------------

            if not presente:

                return jsonify({

                    "sucesso":
                        False,

                    "evento":
                        "ENTRADA_NAO_LOCALIZADA",

                    "nome":
                        nome,

                    "mensagem":
                        "Entrada não localizada"

                })

            horario = (
                registrar_saida(
                    pessoa_id
                )
            )

            return jsonify({

                "sucesso":
                    True,

                "evento":
                    "SAIDA",

                "nome":
                    nome,

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

            codigo = (
                resultado[
                    "codigo"
                ]
            )

            visitante_id = (
                resultado[
                    "visitante_id"
                ]
            )

            # ------------------------------------------------
            # ENTRADA DUPLICADA
            # ------------------------------------------------

            if modo == "ENTRADA":

                return jsonify({

                    "sucesso":
                        True,

                    "evento":
                        "VISITANTE_JA_PRESENTE",

                    "nome":
                        codigo,

                    "codigo":
                        codigo,

                    "mensagem":
                        "Entrada já registrada"

                })

            # ------------------------------------------------
            # SAÍDA
            # ------------------------------------------------

            horario = (
                registrar_saida_visitante(
                    visitante_id
                )
            )

            if horario is None:

                return jsonify({

                    "sucesso":
                        False,

                    "evento":
                        "ENTRADA_NAO_LOCALIZADA",

                    "nome":
                        codigo,

                    "mensagem":
                        "Entrada não localizada"

                })

            return jsonify({

                "sucesso":
                    True,

                "evento":
                    "SAIDA_VISITANTE",

                "nome":
                    codigo,

                "codigo":
                    codigo,

                "horario":
                    horario,

                "mensagem":
                    "Saída registrada"

            })

        # ====================================================
        # DESCONHECIDO
        # ====================================================

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
                        "Erro ao registrar visitante"

                }), 500

            return jsonify({

                "sucesso":
                    True,

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

        # ====================================================
        # DESCONHECIDO TENTANDO SAIR
        # ====================================================

        return jsonify({

            "sucesso":
                False,

            "evento":
                "VISITANTE_NAO_LOCALIZADO",

            "mensagem":
                "Registro de entrada não localizado"

        })

    except Exception as erro:

        print(
            "Erro processar acesso:",
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
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )
