import cv2

from reconhecimento import (
    verificar_modelos,
    criar_detector,
    criar_reconhecedor,
    gerar_embedding,
    comparar_faces
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

# Valor inicial para considerar duas faces
# como sendo da mesma pessoa.
#
# Depois podemos calibrar melhor esse valor.
LIMIAR_RECONHECIMENTO = 0.363


# ============================================================
# VARIÁVEL QUE GUARDA QUEM ESTÁ DENTRO
# ============================================================

# Nesta primeira versão vamos trabalhar
# com uma única pessoa.
#
# None significa:
# não existe ninguém registrado dentro.
embedding_entrada = None


# ============================================================
# INICIALIZAÇÃO
# ============================================================

print("=" * 60)
print("CONTROLE FACIAL - ENTRADA E SAIDA")
print("=" * 60)


# Verifica se os modelos existem.
verificar_modelos()


# Carrega YuNet.
detector = criar_detector()


# Carrega SFace.
reconhecedor = criar_reconhecedor()


# ============================================================
# ABRIR CÂMERA
# ============================================================

print("\nAbrindo câmera...")

camera = cv2.VideoCapture(0)


if not camera.isOpened():

    print("Erro ao abrir câmera.")

    exit()


print("Câmera aberta com sucesso.")


# ============================================================
# INSTRUÇÕES
# ============================================================

print("\n" + "=" * 60)

print("E = registrar ENTRADA")
print("S = registrar SAIDA")
print("Q = encerrar")

print("=" * 60)


# ============================================================
# LOOP PRINCIPAL
# ============================================================

while True:

    sucesso, frame = camera.read()


    if not sucesso:

        print("Erro ao capturar imagem.")

        break


    # --------------------------------------------------------
    # TAMANHO DO FRAME
    # --------------------------------------------------------

    altura, largura = frame.shape[:2]


    detector.setInputSize(
        (largura, altura)
    )


    # --------------------------------------------------------
    # DETECTAR ROSTOS
    # --------------------------------------------------------

    _, faces = detector.detect(frame)


    face_atual = None


    # --------------------------------------------------------
    # SE DETECTOU ROSTO
    # --------------------------------------------------------

    if faces is not None:

        # Nesta etapa usamos somente
        # o primeiro rosto detectado.
        face_atual = faces[0]


        x = int(face_atual[0])
        y = int(face_atual[1])

        largura_rosto = int(
            face_atual[2]
        )

        altura_rosto = int(
            face_atual[3]
        )


        # Desenha retângulo.
        cv2.rectangle(
            frame,
            (x, y),
            (
                x + largura_rosto,
                y + altura_rosto
            ),
            (0, 255, 0),
            2
        )


        # Texto.
        cv2.putText(
            frame,
            "ROSTO DETECTADO",
            (
                x,
                max(y - 10, 20)
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )


    # ========================================================
    # STATUS NA TELA
    # ========================================================

    if embedding_entrada is None:

        status = "Nenhuma pessoa registrada"

    else:

        status = "Pessoa registrada dentro"


    cv2.putText(
        frame,
        status,
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    cv2.putText(
        frame,
        "E = Entrada | S = Saida | Q = Sair",
        (20, altura - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )


    # ========================================================
    # MOSTRAR CÂMERA
    # ========================================================

    cv2.imshow(
        "Controle Facial",
        frame
    )


    # ========================================================
    # LEITURA DO TECLADO
    # ========================================================

    tecla = cv2.waitKey(1) & 0xFF


    # ========================================================
    # ENTRADA
    # ========================================================

    if tecla == ord("e"):

        # Se não existe rosto na câmera.
        if face_atual is None:

            print(
                "\nENTRADA NEGADA:"
                " nenhum rosto detectado."
            )

            continue


        # Se já existe alguém registrado.
        if embedding_entrada is not None:

            print()
            print("ATENCAO:")
            print(
                "Já existe uma pessoa registrada dentro."
            )

            continue


        # Gera o embedding da pessoa.
        embedding_entrada = gerar_embedding(
            frame,
            face_atual,
            reconhecedor
        )


        print()
        print("=" * 40)
        print("ENTRADA REGISTRADA")
        print("=" * 40)

        print(
            "Embedding armazenado na memória."
        )


    # ========================================================
    # SAÍDA
    # ========================================================

    elif tecla == ord("s"):

        # Se não existe rosto na câmera.
        if face_atual is None:

            print(
                "\nSAÍDA NEGADA:"
                " nenhum rosto detectado."
            )

            continue


        # Se ninguém entrou anteriormente.
        if embedding_entrada is None:

            print()
            print("!" * 40)
            print("ALERTA")
            print("NENHUMA ENTRADA REGISTRADA")
            print("!" * 40)

            continue


        # ----------------------------------------------------
        # GERAR EMBEDDING DA SAÍDA
        # ----------------------------------------------------

        embedding_saida = gerar_embedding(
            frame,
            face_atual,
            reconhecedor
        )


        # ----------------------------------------------------
        # COMPARAR ENTRADA E SAÍDA
        # ----------------------------------------------------

        similaridade = comparar_faces(
            embedding_entrada,
            embedding_saida,
            reconhecedor
        )


        print()
        print("-" * 40)

        print(
            f"Similaridade: {similaridade:.3f}"
        )

        print(
            f"Limiar:       {LIMIAR_RECONHECIMENTO:.3f}"
        )

        print("-" * 40)


        # ----------------------------------------------------
        # MESMA PESSOA
        # ----------------------------------------------------

        if similaridade >= LIMIAR_RECONHECIMENTO:

            print()
            print("=" * 40)
            print("SAIDA AUTORIZADA")
            print("MESMA PESSOA RECONHECIDA")
            print("=" * 40)


            # Remove a pessoa da memória.
            #
            # Isso significa que ela saiu
            # do ambiente.
            embedding_entrada = None


        # ----------------------------------------------------
        # PESSOA DIFERENTE
        # ----------------------------------------------------

        else:

            print()
            print("!" * 40)
            print("ALERTA")
            print("PESSOA NAO RECONHECIDA")
            print("SAIDA NAO AUTORIZADA")
            print("!" * 40)


    # ========================================================
    # ENCERRAR
    # ========================================================

    elif tecla == ord("q"):

        print("\nEncerrando sistema...")

        break


# ============================================================
# FINALIZAÇÃO
# ============================================================

camera.release()

cv2.destroyAllWindows()

print("Sistema encerrado.")