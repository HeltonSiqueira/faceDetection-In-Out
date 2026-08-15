import cv2

from reconhecimento import (
    verificar_modelos,
    criar_detector,
    criar_reconhecedor,
    gerar_embedding_imagem
)


# ============================================================
# CARREGAR MODELOS
# ============================================================

verificar_modelos()

detector = criar_detector()

reconhecedor = (
    criar_reconhecedor()
)


# ============================================================
# CARREGAR IMAGEM
# ============================================================

imagem = cv2.imread(
    "captura.jpg"
)


if imagem is None:

    print(
        "ERRO: captura.jpg não encontrada."
    )

    exit()


# ============================================================
# GERAR EMBEDDING
# ============================================================

embedding = gerar_embedding_imagem(
    imagem,
    detector,
    reconhecedor
)


if embedding is None:

    print(
        "ERRO: nenhum rosto encontrado."
    )

    exit()


# ============================================================
# RESULTADO
# ============================================================

print()
print(
    "Rosto detectado com sucesso!"
)

print(
    "Formato do embedding:",
    embedding.shape
)

print()
print(
    "Primeiros valores:"
)

print(
    embedding[0][:10]
)
