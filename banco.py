import sqlite3
from pathlib import Path
from datetime import datetime


# ============================================================
# CAMINHOS
# ============================================================

PASTA_PROJETO = Path(__file__).resolve().parent

ARQUIVO_BANCO = (
    PASTA_PROJETO
    / "controle_acesso.db"
)


# ============================================================
# CONEXÃO
# ============================================================

def conectar():

    conexao = sqlite3.connect(
        ARQUIVO_BANCO
    )

    conexao.row_factory = sqlite3.Row

    conexao.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conexao


# ============================================================
# CRIAR TABELAS
# ============================================================

def criar_tabelas():

    conexao = conectar()

    cursor = conexao.cursor()

    # --------------------------------------------------------
    # PESSOAS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pessoas (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome TEXT NOT NULL,

            data_cadastro TEXT NOT NULL,

            ativo INTEGER NOT NULL DEFAULT 1

        )
        """
    )

    # --------------------------------------------------------
    # EMBEDDINGS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            pessoa_id INTEGER NOT NULL,

            embedding BLOB NOT NULL,

            data_cadastro TEXT NOT NULL,

            FOREIGN KEY (pessoa_id)
            REFERENCES pessoas(id)
            ON DELETE CASCADE

        )
        """
    )

    # --------------------------------------------------------
    # PRESENTES
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS presentes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            pessoa_id INTEGER NOT NULL UNIQUE,

            entrada TEXT NOT NULL,

            FOREIGN KEY (pessoa_id)
            REFERENCES pessoas(id)
            ON DELETE CASCADE

        )
        """
    )

    # --------------------------------------------------------
    # HISTÓRICO
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS historico (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            pessoa_id INTEGER NOT NULL,

            entrada TEXT NOT NULL,

            saida TEXT,

            FOREIGN KEY (pessoa_id)
            REFERENCES pessoas(id)
            ON DELETE CASCADE

        )
        """
    )

    # --------------------------------------------------------
    # VISITANTES
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS visitantes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            codigo TEXT UNIQUE,

            embedding BLOB NOT NULL,

            foto TEXT NOT NULL,

            entrada TEXT NOT NULL,

            saida TEXT,

            presente INTEGER NOT NULL DEFAULT 1

        )
        """
    )

    conexao.commit()

    conexao.close()

    print(
        "Banco de dados inicializado com sucesso."
    )


# ============================================================
# CADASTRAR PESSOA
# ============================================================

def cadastrar_pessoa(
    nome
):

    conexao = conectar()

    cursor = conexao.cursor()

    agora = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO pessoas (
            nome,
            data_cadastro,
            ativo
        )
        VALUES (?, ?, 1)
        """,
        (
            nome,
            agora
        )
    )

    pessoa_id = cursor.lastrowid

    conexao.commit()

    conexao.close()

    return pessoa_id


# ============================================================
# CADASTRAR EMBEDDING
# ============================================================

def cadastrar_embedding(
    pessoa_id,
    embedding_bytes
):

    conexao = conectar()

    cursor = conexao.cursor()

    agora = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO embeddings (
            pessoa_id,
            embedding,
            data_cadastro
        )
        VALUES (?, ?, ?)
        """,
        (
            pessoa_id,
            embedding_bytes,
            agora
        )
    )

    embedding_id = cursor.lastrowid

    conexao.commit()

    conexao.close()

    return embedding_id


# ============================================================
# LISTAR PESSOAS
# ============================================================

def listar_pessoas():

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT
            id,
            nome,
            data_cadastro,
            ativo

        FROM pessoas

        ORDER BY nome
        """
    )

    registros = cursor.fetchall()

    conexao.close()

    return registros


# ============================================================
# LISTAR EMBEDDINGS
# ============================================================

def listar_embeddings():

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT

            embeddings.id AS embedding_id,

            pessoas.id AS pessoa_id,

            pessoas.nome,

            embeddings.embedding

        FROM embeddings

        INNER JOIN pessoas
            ON pessoas.id = embeddings.pessoa_id

        WHERE pessoas.ativo = 1

        ORDER BY
            pessoas.id,
            embeddings.id
        """
    )

    registros = cursor.fetchall()

    conexao.close()

    return registros


# ============================================================
# VERIFICAR SE PESSOA ESTÁ PRESENTE
# ============================================================

def pessoa_esta_presente(
    pessoa_id
):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT id

        FROM presentes

        WHERE pessoa_id = ?
        """,
        (
            pessoa_id,
        )
    )

    registro = cursor.fetchone()

    conexao.close()

    return registro is not None


# ============================================================
# REGISTRAR ENTRADA
# ============================================================

def registrar_entrada(
    pessoa_id
):

    if pessoa_esta_presente(
        pessoa_id
    ):

        return None

    agora = datetime.now().isoformat()

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO presentes (
            pessoa_id,
            entrada
        )
        VALUES (?, ?)
        """,
        (
            pessoa_id,
            agora
        )
    )

    cursor.execute(
        """
        INSERT INTO historico (
            pessoa_id,
            entrada,
            saida
        )
        VALUES (?, ?, NULL)
        """,
        (
            pessoa_id,
            agora
        )
    )

    conexao.commit()

    conexao.close()

    return agora


# ============================================================
# REGISTRAR SAÍDA
# ============================================================

def registrar_saida(
    pessoa_id
):

    if not pessoa_esta_presente(
        pessoa_id
    ):

        return None

    agora = datetime.now().isoformat()

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        DELETE FROM presentes

        WHERE pessoa_id = ?
        """,
        (
            pessoa_id,
        )
    )

    cursor.execute(
        """
        UPDATE historico

        SET saida = ?

        WHERE id = (

            SELECT id

            FROM historico

            WHERE
                pessoa_id = ?
                AND saida IS NULL

            ORDER BY id DESC

            LIMIT 1
        )
        """,
        (
            agora,
            pessoa_id
        )
    )

    conexao.commit()

    conexao.close()

    return agora


# ============================================================
# CRIAR VISITANTE
# ============================================================

def criar_visitante(
    embedding_bytes,
    caminho_foto
):

    agora = datetime.now().isoformat()

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO visitantes (
            codigo,
            embedding,
            foto,
            entrada,
            saida,
            presente
        )
        VALUES (
            NULL,
            ?,
            ?,
            ?,
            NULL,
            1
        )
        """,
        (
            embedding_bytes,
            caminho_foto,
            agora
        )
    )

    visitante_id = cursor.lastrowid

    codigo = (
        f"VIS-{visitante_id:05d}"
    )

    cursor.execute(
        """
        UPDATE visitantes

        SET codigo = ?

        WHERE id = ?
        """,
        (
            codigo,
            visitante_id
        )
    )

    conexao.commit()

    conexao.close()

    return {
        "id": visitante_id,
        "codigo": codigo,
        "entrada": agora,
        "foto": caminho_foto
    }


# ============================================================
# ATUALIZAR FOTO DO VISITANTE
# ============================================================

def atualizar_foto_visitante(
    visitante_id,
    caminho_foto
):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        UPDATE visitantes

        SET foto = ?

        WHERE id = ?
        """,
        (
            caminho_foto,
            visitante_id
        )
    )

    conexao.commit()

    conexao.close()


# ============================================================
# VISITANTES PRESENTES
# ============================================================

def listar_visitantes_presentes():

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT

            id,
            codigo,
            embedding,
            foto,
            entrada,
            saida,
            presente

        FROM visitantes

        WHERE presente = 1

        ORDER BY entrada
        """
    )

    registros = cursor.fetchall()

    conexao.close()

    return registros


# ============================================================
# TODOS OS VISITANTES
# ============================================================

def listar_visitantes():

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT

            id,
            codigo,
            foto,
            entrada,
            saida,
            presente

        FROM visitantes

        ORDER BY id DESC
        """
    )

    registros = cursor.fetchall()

    conexao.close()

    return registros


# ============================================================
# REGISTRAR SAÍDA VISITANTE
# ============================================================

def registrar_saida_visitante(
    visitante_id
):

    agora = datetime.now().isoformat()

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        UPDATE visitantes

        SET
            saida = ?,
            presente = 0

        WHERE
            id = ?
            AND presente = 1
        """,
        (
            agora,
            visitante_id
        )
    )

    alterados = cursor.rowcount

    conexao.commit()

    conexao.close()

    if alterados == 0:

        return None

    return agora


# ============================================================
# LISTAR PRESENTES
# ============================================================

def listar_presentes():

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT

            pessoas.id,
            pessoas.nome,
            presentes.entrada

        FROM presentes

        INNER JOIN pessoas
            ON pessoas.id = presentes.pessoa_id

        ORDER BY presentes.entrada
        """
    )

    registros = cursor.fetchall()

    conexao.close()

    return registros


# ============================================================
# LISTAR HISTÓRICO
# ============================================================

def listar_historico():

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT

            historico.id,
            pessoas.id AS pessoa_id,
            pessoas.nome,
            historico.entrada,
            historico.saida

        FROM historico

        INNER JOIN pessoas
            ON pessoas.id = historico.pessoa_id

        ORDER BY historico.id DESC
        """
    )

    registros = cursor.fetchall()

    conexao.close()

    return registros


# ============================================================
# CONTAR CADASTRADOS PRESENTES
# ============================================================

def contar_presentes():

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS total

        FROM presentes
        """
    )

    resultado = cursor.fetchone()

    conexao.close()

    return int(
        resultado["total"]
    )


# ============================================================
# CONTAR VISITANTES PRESENTES
# ============================================================

def contar_visitantes_presentes():

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS total

        FROM visitantes

        WHERE presente = 1
        """
    )

    resultado = cursor.fetchone()

    conexao.close()

    return int(
        resultado["total"]
    )


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    criar_tabelas()
