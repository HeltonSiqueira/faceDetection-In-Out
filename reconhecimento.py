import cv2
import numpy as np

from pathlib import Path


# ============================================================
# CAMINHOS
# ============================================================

PASTA_PROJETO = Path(__file__).resolve().parent

PASTA_MODELOS = (
    PASTA_PROJETO
    / "modelos"
)


MODELO_DETECCAO = (
    PASTA_MODELOS
    / "face_detection_yunet_2026may.onnx"
)


MODELO_RECONHECIMENTO = (
    PASTA_MODELOS
    / "face_recognition_sface_2021dec.onnx"
)


# ============================================================
# LIMITES DE RECONHECIMENTO
# ============================================================

LIMITE_RECONHECIMENTO_PESSOA = 0.45

LIMITE_RECONHECIMENTO_VISITANTE = 0.45


# ============================================================
# VERIFICAR MODELOS
# ============================================================

def verificar_modelos():

    modelos = [
        MODELO_DETECCAO,
        MODELO_RECONHECIMENTO
    ]

    for modelo in modelos:

        if not modelo.exists():

            raise FileNotFoundError(
                f"Modelo não encontrado: {modelo}"
            )

        print(
            f"Modelo encontrado: {modelo.name}"
        )


# ============================================================
# CRIAR DETECTOR
# ============================================================

def criar_detector():

    print(
        "Carregando YuNet..."
    )

    detector = cv2.FaceDetectorYN.create(

        str(MODELO_DETECCAO),

        "",

        (320, 320),

        0.9,

        0.3,

        5000

    )

    print(
        "YuNet carregado com sucesso."
    )

    return detector


# ============================================================
# CRIAR RECONHECEDOR
# ============================================================

def criar_reconhecedor():

    print(
        "Carregando SFace..."
    )

    reconhecedor = (
        cv2.FaceRecognizerSF.create(

            str(MODELO_RECONHECIMENTO),

            ""

        )
    )

    print(
        "SFace carregado com sucesso."
    )

    return reconhecedor


# ============================================================
# DETECTAR ROSTO
# ============================================================

def detectar_rosto(
    frame,
    detector
):

    altura, largura = (
        frame.shape[:2]
    )

    detector.setInputSize(
        (
            largura,
            altura
        )
    )

    resultado = detector.detect(
        frame
    )

    if resultado is None:

        return None

    _, faces = resultado

    if (
        faces is None
        or len(faces) == 0
    ):

        return None

    # --------------------------------------------------------
    # PEGA O MAIOR ROSTO
    # --------------------------------------------------------

    maior_face = max(

        faces,

        key=lambda face:

            float(face[2])
            *
            float(face[3])

    )

    return maior_face


# ============================================================
# GERAR EMBEDDING
# ============================================================

def gerar_embedding(
    frame,
    face,
    reconhecedor
):

    rosto_alinhado = (
        reconhecedor.alignCrop(
            frame,
            face
        )
    )

    embedding = (
        reconhecedor.feature(
            rosto_alinhado
        )
    )

    return embedding.astype(
        np.float32
    )


# ============================================================
# GERAR EMBEDDING A PARTIR DE UMA IMAGEM
# ============================================================

def gerar_embedding_imagem(
    imagem,
    detector,
    reconhecedor
):

    face = detectar_rosto(
        imagem,
        detector
    )

    if face is None:

        return None

    embedding = gerar_embedding(
        imagem,
        face,
        reconhecedor
    )

    return embedding


# ============================================================
# COMPARAR DUAS FACES
# ============================================================

def comparar_faces(
    embedding_1,
    embedding_2,
    reconhecedor
):

    similaridade = (
        reconhecedor.match(

            embedding_1,

            embedding_2,

            cv2.FaceRecognizerSF_FR_COSINE

        )
    )

    return float(
        similaridade
    )


# ============================================================
# BLOB DO SQLITE -> NUMPY
# ============================================================

def bytes_para_embedding(
    embedding_bytes
):

    embedding = np.frombuffer(

        embedding_bytes,

        dtype=np.float32

    )

    embedding = embedding.reshape(
        1,
        -1
    )

    return embedding


# ============================================================
# NUMPY -> BYTES
# ============================================================

def embedding_para_bytes(
    embedding
):

    return (
        embedding
        .astype(np.float32)
        .tobytes()
    )


# ============================================================
# RECONHECER PESSOA CADASTRADA
# ============================================================

def reconhecer_pessoa_cadastrada(
    embedding_atual,
    registros_embeddings,
    reconhecedor,
    limite=LIMITE_RECONHECIMENTO_PESSOA
):

    if (
        embedding_atual is None
    ):

        return {
            "reconhecido": False,
            "pessoa_id": None,
            "nome": None,
            "similaridade": 0.0
        }

    if not registros_embeddings:

        return {
            "reconhecido": False,
            "pessoa_id": None,
            "nome": None,
            "similaridade": 0.0
        }

    melhor_similaridade = -1.0

    melhor_pessoa_id = None

    melhor_nome = None

    # --------------------------------------------------------
    # COMPARA COM TODOS OS EMBEDDINGS
    # --------------------------------------------------------

    for registro in registros_embeddings:

        embedding_banco = (
            bytes_para_embedding(
                registro["embedding"]
            )
        )

        similaridade = comparar_faces(

            embedding_atual,

            embedding_banco,

            reconhecedor

        )

        if (
            similaridade
            >
            melhor_similaridade
        ):

            melhor_similaridade = (
                similaridade
            )

            melhor_pessoa_id = int(
                registro["pessoa_id"]
            )

            melhor_nome = (
                registro["nome"]
            )

    reconhecido = bool(

        melhor_similaridade
        >=
        limite

    )

    if not reconhecido:

        melhor_pessoa_id = None

        melhor_nome = None

    return {

        "reconhecido":
            reconhecido,

        "pessoa_id":
            melhor_pessoa_id,

        "nome":
            melhor_nome,

        "similaridade":
            float(
                melhor_similaridade
            )

    }


# ============================================================
# RECONHECER VISITANTE PRESENTE
# ============================================================

def reconhecer_visitante_presente(
    embedding_atual,
    visitantes_presentes,
    reconhecedor,
    limite=LIMITE_RECONHECIMENTO_VISITANTE
):

    if (
        embedding_atual is None
    ):

        return {
            "reconhecido": False,
            "visitante_id": None,
            "codigo": None,
            "similaridade": 0.0
        }

    if not visitantes_presentes:

        return {
            "reconhecido": False,
            "visitante_id": None,
            "codigo": None,
            "similaridade": 0.0
        }

    melhor_similaridade = -1.0

    melhor_visitante_id = None

    melhor_codigo = None

    # --------------------------------------------------------
    # COMPARA COM VISITANTES PRESENTES
    # --------------------------------------------------------

    for visitante in visitantes_presentes:

        embedding_visitante = (
            bytes_para_embedding(
                visitante["embedding"]
            )
        )

        similaridade = comparar_faces(

            embedding_atual,

            embedding_visitante,

            reconhecedor

        )

        if (
            similaridade
            >
            melhor_similaridade
        ):

            melhor_similaridade = (
                similaridade
            )

            melhor_visitante_id = int(
                visitante["id"]
            )

            melhor_codigo = (
                visitante["codigo"]
            )

    reconhecido = bool(

        melhor_similaridade
        >=
        limite

    )

    if not reconhecido:

        melhor_visitante_id = None

        melhor_codigo = None

    return {

        "reconhecido":
            reconhecido,

        "visitante_id":
            melhor_visitante_id,

        "codigo":
            melhor_codigo,

        "similaridade":
            float(
                melhor_similaridade
            )

    }


# ============================================================
# RECONHECIMENTO COMPLETO
# ============================================================

def reconhecer_identidade(
    imagem,
    detector,
    reconhecedor,
    registros_embeddings,
    visitantes_presentes
):

    # --------------------------------------------------------
    # GERA EMBEDDING ATUAL
    # --------------------------------------------------------

    embedding_atual = (
        gerar_embedding_imagem(

            imagem,

            detector,

            reconhecedor

        )
    )

    if embedding_atual is None:

        return {

            "rosto_detectado": False,

            "tipo": None,

            "reconhecido": False,

            "pessoa_id": None,

            "nome": None,

            "visitante_id": None,

            "codigo": None,

            "similaridade": 0.0,

            "embedding": None

        }

    # ========================================================
    # PRIMEIRO: PESSOAS CADASTRADAS
    # ========================================================

    pessoa = reconhecer_pessoa_cadastrada(

        embedding_atual,

        registros_embeddings,

        reconhecedor

    )

    if pessoa["reconhecido"]:

        return {

            "rosto_detectado": True,

            "tipo": "PESSOA",

            "reconhecido": True,

            "pessoa_id":
                pessoa["pessoa_id"],

            "nome":
                pessoa["nome"],

            "visitante_id":
                None,

            "codigo":
                None,

            "similaridade":
                pessoa["similaridade"],

            "embedding":
                embedding_atual

        }

    # ========================================================
    # SEGUNDO: VISITANTES PRESENTES
    # ========================================================

    visitante = (
        reconhecer_visitante_presente(

            embedding_atual,

            visitantes_presentes,

            reconhecedor

        )
    )

    if visitante["reconhecido"]:

        return {

            "rosto_detectado": True,

            "tipo": "VISITANTE",

            "reconhecido": True,

            "pessoa_id": None,

            "nome": None,

            "visitante_id":
                visitante["visitante_id"],

            "codigo":
                visitante["codigo"],

            "similaridade":
                visitante["similaridade"],

            "embedding":
                embedding_atual

        }

    # ========================================================
    # NÃO RECONHECIDO
    # ========================================================

    melhor_similaridade = max(

        float(
            pessoa["similaridade"]
        ),

        float(
            visitante["similaridade"]
        )

    )

    return {

        "rosto_detectado": True,

        "tipo": "DESCONHECIDO",

        "reconhecido": False,

        "pessoa_id": None,

        "nome": None,

        "visitante_id": None,

        "codigo": None,

        "similaridade":
            melhor_similaridade,

        "embedding":
            embedding_atual

    }


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    verificar_modelos()

    detector = criar_detector()

    reconhecedor = criar_reconhecedor()

    print()
    print(
        "Sistema de reconhecimento carregado."
    )
