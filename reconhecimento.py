import cv2
from pathlib import Path


# ============================================================
# CAMINHOS DO PROJETO
# ============================================================

PASTA_PROJETO = Path(__file__).resolve().parent

PASTA_MODELOS = PASTA_PROJETO / "modelos"


MODELO_DETECCAO = (
    PASTA_MODELOS
    / "face_detection_yunet_2026may.onnx"
)


MODELO_RECONHECIMENTO = (
    PASTA_MODELOS
    / "face_recognition_sface_2021dec.onnx"
)


# ============================================================
# VERIFICAR MODELOS
# ============================================================

def verificar_modelos():

    """
    Verifica se os arquivos dos modelos existem.
    """

    modelos = [
        MODELO_DETECCAO,
        MODELO_RECONHECIMENTO
    ]

    for modelo in modelos:

        if not modelo.exists():

            raise FileNotFoundError(
                f"\nModelo não encontrado:\n{modelo}\n"
            )

        print(
            f"Modelo encontrado: {modelo.name}"
        )


# ============================================================
# CRIAR DETECTOR FACIAL
# ============================================================

def criar_detector():

    """
    Cria o detector facial YuNet.
    """

    print("\nCarregando YuNet...")

    detector = cv2.FaceDetectorYN.create(
        str(MODELO_DETECCAO),
        "",
        (320, 320),
        0.9,
        0.3,
        5000
    )

    print("YuNet carregado com sucesso.")

    return detector


# ============================================================
# CRIAR RECONHECEDOR FACIAL
# ============================================================

def criar_reconhecedor():

    """
    Cria o reconhecedor facial SFace.
    """

    print("\nCarregando SFace...")

    reconhecedor = cv2.FaceRecognizerSF.create(
        str(MODELO_RECONHECIMENTO),
        ""
    )

    print("SFace carregado com sucesso.")

    return reconhecedor


# ============================================================
# GERAR EMBEDDING
# ============================================================

def gerar_embedding(
    frame,
    face,
    reconhecedor
):

    """
    Gera a assinatura facial.

    Primeiro o rosto é alinhado.
    Depois o SFace gera o embedding.
    """

    rosto_alinhado = reconhecedor.alignCrop(
        frame,
        face
    )

    embedding = reconhecedor.feature(
        rosto_alinhado
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

    """
    Compara dois embeddings usando
    similaridade de cosseno.

    Quanto maior o valor,
    maior a semelhança entre as faces.
    """

    similaridade = reconhecedor.match(
        embedding_1,
        embedding_2,
        cv2.FaceRecognizerSF_FR_COSINE
    )

    return similaridade