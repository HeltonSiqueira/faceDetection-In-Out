// ============================================================
// CONFIGURAÇÃO
// ============================================================

const INTERVALO_ATUALIZACAO = 2000;


// ============================================================
// ELEMENTOS
// ============================================================

const totalAmbiente =
    document.getElementById(
        "total-ambiente"
    );


const totalPresentes =
    document.getElementById(
        "total-presentes"
    );


const totalVisitantes =
    document.getElementById(
        "total-visitantes"
    );


const tabelaPresentes =
    document.getElementById(
        "tabela-presentes"
    );


const tabelaVisitantes =
    document.getElementById(
        "tabela-visitantes"
    );


const tabelaHistorico =
    document.getElementById(
        "tabela-historico"
    );


const indicadorOnline =
    document.getElementById(
        "indicador-online"
    );


const textoAtualizacao =
    document.getElementById(
        "texto-atualizacao"
    );


// ============================================================
// ESCAPAR TEXTO
// ============================================================

function escaparHTML(
    valor
) {

    if (
        valor === null
        ||
        valor === undefined
    ) {

        return "";

    }


    return String(valor)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );

}


// ============================================================
// CARREGAR DADOS
// ============================================================

async function carregarDados() {

    try {

        const resposta =
            await fetch(
                "/api/admin/dados",
                {
                    cache: "no-store"
                }
            );


        if (!resposta.ok) {

            throw new Error(
                "Erro HTTP "
                +
                resposta.status
            );

        }


        const dados =
            await resposta.json();


        if (!dados.sucesso) {

            throw new Error(
                dados.mensagem
                ||
                "Erro ao carregar painel"
            );

        }


        atualizarResumo(
            dados.resumo
        );


        atualizarPresentes(
            dados.presentes
        );


        atualizarVisitantes(
            dados.visitantes
        );


        atualizarHistorico(
            dados.historico
        );


        definirOnline();

    }

    catch (erro) {

        console.error(
            "Erro ao atualizar painel:",
            erro
        );


        definirOffline();

    }

}


// ============================================================
// RESUMO
// ============================================================

function atualizarResumo(
    resumo
) {

    totalAmbiente.textContent =
        resumo.total_ambiente;


    totalPresentes.textContent =
        resumo.total_presentes;


    totalVisitantes.textContent =
        resumo.total_visitantes;

}


// ============================================================
// PESSOAS PRESENTES
// ============================================================

function atualizarPresentes(
    pessoas
) {

    if (
        !pessoas
        ||
        pessoas.length === 0
    ) {

        tabelaPresentes.innerHTML = `
            <tr>
                <td
                    colspan="4"
                    class="vazio"
                >
                    Nenhuma pessoa cadastrada está presente.
                </td>
            </tr>
        `;

        return;

    }


    let html = "";


    for (
        const pessoa
        of pessoas
    ) {

        html += `
            <tr>

                <td>
                    ${escaparHTML(pessoa.id)}
                </td>

                <td class="nome">
                    ${escaparHTML(pessoa.nome)}
                </td>

                <td>
                    ${escaparHTML(pessoa.entrada)}
                </td>

                <td>
                    <span class="badge presente">
                        Presente
                    </span>
                </td>

            </tr>
        `;

    }


    tabelaPresentes.innerHTML =
        html;

}


// ============================================================
// VISITANTES
// ============================================================

function atualizarVisitantes(
    visitantes
) {

    if (
        !visitantes
        ||
        visitantes.length === 0
    ) {

        tabelaVisitantes.innerHTML = `
            <tr>
                <td
                    colspan="5"
                    class="vazio"
                >
                    Nenhum visitante registrado.
                </td>
            </tr>
        `;

        return;

    }


    let html = "";


    for (
        const visitante
        of visitantes
    ) {

        let foto = "-";


        if (
            visitante.foto_url
        ) {

            const url =
                escaparHTML(
                    visitante.foto_url
                );


            foto = `
                <a
                    href="${url}"
                    target="_blank"
                    rel="noopener"
                >
                    <img
                        class="foto-visitante"
                        src="${url}"
                        alt="Foto do visitante"
                    >
                </a>
            `;

        }


        let situacao;


        if (
            visitante.presente
        ) {

            situacao = `
                <span class="badge presente">
                    Presente
                </span>
            `;

        }

        else {

            situacao = `
                <span class="badge saiu">
                    Saiu
                </span>
            `;

        }


        html += `
            <tr>

                <td>
                    ${foto}
                </td>

                <td class="codigo">
                    ${escaparHTML(visitante.codigo)}
                </td>

                <td>
                    ${escaparHTML(visitante.entrada)}
                </td>

                <td>
                    ${escaparHTML(visitante.saida)}
                </td>

                <td>
                    ${situacao}
                </td>

            </tr>
        `;

    }


    tabelaVisitantes.innerHTML =
        html;

}


// ============================================================
// HISTÓRICO
// ============================================================

function atualizarHistorico(
    historico
) {

    if (
        !historico
        ||
        historico.length === 0
    ) {

        tabelaHistorico.innerHTML = `
            <tr>
                <td
                    colspan="4"
                    class="vazio"
                >
                    Nenhum histórico registrado.
                </td>
            </tr>
        `;

        return;

    }


    let html = "";


    for (
        const registro
        of historico
    ) {

        let saida;


        if (
            registro.saida
        ) {

            saida =
                escaparHTML(
                    registro.saida
                );

        }

        else {

            saida = `
                <span class="badge presente">
                    Presente
                </span>
            `;

        }


        html += `
            <tr>

                <td>
                    ${escaparHTML(registro.id)}
                </td>

                <td class="nome">
                    ${escaparHTML(registro.nome)}
                </td>

                <td>
                    ${escaparHTML(registro.entrada)}
                </td>

                <td>
                    ${saida}
                </td>

            </tr>
        `;

    }


    tabelaHistorico.innerHTML =
        html;

}


// ============================================================
// STATUS ONLINE
// ============================================================

function definirOnline() {

    indicadorOnline.classList.remove(
        "offline"
    );


    indicadorOnline.classList.add(
        "online"
    );


    textoAtualizacao.textContent =
        "Atualização automática";

}


// ============================================================
// STATUS OFFLINE
// ============================================================

function definirOffline() {

    indicadorOnline.classList.remove(
        "online"
    );


    indicadorOnline.classList.add(
        "offline"
    );


    textoAtualizacao.textContent =
        "Falha na atualização";

}


// ============================================================
// PRIMEIRA CARGA
// ============================================================

carregarDados();


// ============================================================
// ATUALIZAÇÃO AUTOMÁTICA
// ============================================================

setInterval(

    carregarDados,

    INTERVALO_ATUALIZACAO

);