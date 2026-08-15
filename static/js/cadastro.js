// ============================================================
// CONFIGURAÇÕES
// ============================================================

const TOTAL_AMOSTRAS =
    5;

const INTERVALO_AMOSTRAS =
    600;


// ============================================================
// ELEMENTOS
// ============================================================

const etapaNome =
    document.getElementById(
        "etapa-nome"
    );

const etapaCamera =
    document.getElementById(
        "etapa-camera"
    );

const campoNome =
    document.getElementById(
        "nome"
    );

const botaoIniciar =
    document.getElementById(
        "botao-iniciar"
    );

const erroNome =
    document.getElementById(
        "erro-nome"
    );

const video =
    document.getElementById(
        "video"
    );

const canvas =
    document.getElementById(
        "canvas"
    );

const moldura =
    document.getElementById(
        "moldura-rosto"
    );

const tituloCamera =
    document.getElementById(
        "titulo-camera"
    );

const mensagemCamera =
    document.getElementById(
        "mensagem-camera"
    );

const statusTexto =
    document.getElementById(
        "status-texto"
    );


// ============================================================
// ESTADOS
// ============================================================

let pessoaId =
    null;

let nomePessoa =
    null;

let processando =
    false;

let finalizado =
    false;

let streamCamera =
    null;

let intervaloVerificacao =
    null;


// ============================================================
// BOTÃO
// ============================================================

botaoIniciar.addEventListener(
    "click",
    iniciarCadastro
);


// ============================================================
// ENTER NO NOME
// ============================================================

campoNome.addEventListener(

    "keydown",

    function (
        evento
    ) {

        if (
            evento.key
            ===
            "Enter"
        ) {

            iniciarCadastro();

        }

    }

);


// ============================================================
// INICIAR CADASTRO
// ============================================================

async function iniciarCadastro() {

    erroNome.textContent =
        "";


    const nome =
        campoNome
            .value
            .trim();


    if (
        nome.length
        <
        2
    ) {

        erroNome.textContent =
            "Informe o nome da pessoa.";

        campoNome.focus();

        return;

    }


    botaoIniciar.disabled =
        true;


    try {

        const resposta =
            await fetch(

                "/api/cadastro/iniciar",

                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            nome
                        })
                }

            );


        const dados =
            await resposta.json();


        if (
            !dados.sucesso
        ) {

            erroNome.textContent =
                dados.mensagem
                ||
                "Não foi possível iniciar o cadastro.";


            botaoIniciar.disabled =
                false;


            return;

        }


        pessoaId =
            dados.pessoa_id;


        nomePessoa =
            dados.nome;


        etapaNome.classList.add(
            "oculto"
        );


        etapaCamera.classList.remove(
            "oculto"
        );


        await iniciarCamera();

    }

    catch (
        erro
    ) {

        console.error(
            erro
        );


        erroNome.textContent =
            "Erro ao iniciar cadastro.";


        botaoIniciar.disabled =
            false;

    }

}


// ============================================================
// CÂMERA
// ============================================================

async function iniciarCamera() {

    try {

        streamCamera =
            await navigator.mediaDevices.getUserMedia({

                video: {

                    facingMode:
                        "user",

                    width: {
                        ideal: 640
                    },

                    height: {
                        ideal: 480
                    }

                },

                audio:
                    false

            });


        video.srcObject =
            streamCamera;


        video.onloadedmetadata =
            function () {

                iniciarVerificacao();

            };

    }

    catch (
        erro
    ) {

        console.error(
            erro
        );


        await cancelarCadastro();


        tituloCamera.textContent =
            "Câmera indisponível";


        mensagemCamera.textContent =
            "Verifique a permissão da câmera";


        statusTexto.textContent =
            "Cadastro cancelado";

    }

}


// ============================================================
// VERIFICAÇÃO
// ============================================================

function iniciarVerificacao() {

    if (
        intervaloVerificacao
    ) {

        return;

    }


    intervaloVerificacao =
        setInterval(

            verificarPosicionamento,

            800

        );

}


// ============================================================
// VERIFICAR POSICIONAMENTO
// ============================================================

async function verificarPosicionamento() {

    if (
        finalizado
        ||
        processando
    ) {

        return;

    }


    const imagem =
        gerarImagemAtual();


    if (
        !imagem
    ) {

        return;

    }


    try {

        const resposta =
            await fetch(

                "/verificar-rosto",

                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            imagem

                        })

                }

            );


        const dados =
            await resposta.json();


        if (
            !dados.rosto_detectado
        ) {

            tituloCamera.textContent =
                "Posicione seu rosto";


            mensagemCamera.textContent =
                "Olhe para a câmera";


            statusTexto.textContent =
                "Aguardando";


            return;

        }


        if (
            !dados.posicionado
        ) {

            tituloCamera.textContent =
                "Posicione seu rosto";


            mensagemCamera.textContent =
                dados.mensagem;


            statusTexto.textContent =
                "Ajuste sua posição";


            return;

        }


        await capturarAmostras();

    }

    catch (
        erro
    ) {

        console.error(
            erro
        );

    }

}


// ============================================================
// GERAR IMAGEM
// ============================================================

function gerarImagemAtual() {

    if (
        !video.videoWidth
        ||
        !video.videoHeight
    ) {

        return null;

    }


    canvas.width =
        video.videoWidth;


    canvas.height =
        video.videoHeight;


    const contexto =
        canvas.getContext(
            "2d"
        );


    contexto.drawImage(

        video,

        0,
        0,

        canvas.width,
        canvas.height

    );


    return canvas.toDataURL(

        "image/jpeg",

        0.90

    );

}


// ============================================================
// CAPTURAR 5 AMOSTRAS
// ============================================================

async function capturarAmostras() {

    if (
        processando
        ||
        finalizado
    ) {

        return;

    }


    processando =
        true;


    moldura.classList.remove(
        "procurando"
    );


    moldura.classList.add(
        "processando"
    );


    tituloCamera.textContent =
        "Processando cadastro";


    mensagemCamera.textContent =
        "Mantenha o rosto posicionado";


    statusTexto.textContent =
        "Processando...";


    for (
        let numero = 1;
        numero <= TOTAL_AMOSTRAS;
        numero++
    ) {

        const imagem =
            gerarImagemAtual();


        if (
            !imagem
        ) {

            await falhaCadastro(
                "Não foi possível capturar a imagem"
            );


            return;

        }


        const resultado =
            await enviarAmostra(
                imagem
            );


        if (
            !resultado
            ||
            !resultado.sucesso
        ) {

            await falhaCadastro(

                resultado?.mensagem
                ||
                "Erro ao salvar amostra"

            );


            return;

        }


        if (
            numero
            <
            TOTAL_AMOSTRAS
        ) {

            await esperar(
                INTERVALO_AMOSTRAS
            );

        }

    }


    finalizado =
        true;


    processando =
        false;


    moldura.classList.remove(
        "processando"
    );


    moldura.classList.add(
        "concluido"
    );


    tituloCamera.textContent =
        "Cadastro concluído";


    mensagemCamera.textContent =
        nomePessoa
        +
        " foi cadastrado com sucesso";


    statusTexto.textContent =
        "Cadastro facial concluído";


    pararCamera();


    if (
        intervaloVerificacao
    ) {

        clearInterval(
            intervaloVerificacao
        );

    }


    await esperar(
        2000
    );


    window.location.href =
        "/admin";

}


// ============================================================
// ENVIAR AMOSTRA
// ============================================================

async function enviarAmostra(
    imagem
) {

    try {

        const resposta =
            await fetch(

                "/api/cadastro/amostra",

                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            pessoa_id:
                                pessoaId,

                            imagem

                        })

                }

            );


        return await resposta.json();

    }

    catch (
        erro
    ) {

        console.error(
            erro
        );


        return {

            sucesso:
                false,

            mensagem:
                "Erro ao salvar amostra"

        };

    }

}


// ============================================================
// FALHA NO CADASTRO
// ============================================================

async function falhaCadastro(
    texto
) {

    processando =
        false;


    finalizado =
        true;


    await cancelarCadastro();


    moldura.classList.remove(
        "processando"
    );


    moldura.classList.add(
        "erro"
    );


    tituloCamera.textContent =
        "Cadastro não concluído";


    mensagemCamera.textContent =
        texto;


    statusTexto.textContent =
        "Cadastro cancelado";


    pararCamera();

}


// ============================================================
// CANCELAR CADASTRO NO BANCO
// ============================================================

async function cancelarCadastro() {

    if (
        !pessoaId
    ) {

        return;

    }


    try {

        await fetch(

            "/api/cadastro/cancelar",

            {

                method:
                    "POST",

                headers: {

                    "Content-Type":
                        "application/json"

                },

                body:
                    JSON.stringify({

                        pessoa_id:
                            pessoaId

                    })

            }

        );

    }

    catch (
        erro
    ) {

        console.error(
            erro
        );

    }

}


// ============================================================
// PARAR CÂMERA
// ============================================================

function pararCamera() {

    if (
        !streamCamera
    ) {

        return;

    }


    streamCamera
        .getTracks()
        .forEach(

            function (
                track
            ) {

                track.stop();

            }

        );


    streamCamera =
        null;

}


// ============================================================
// ESPERA
// ============================================================

function esperar(
    tempo
) {

    return new Promise(

        function (
            resolve
        ) {

            setTimeout(

                resolve,

                tempo

            );

        }

    );

}