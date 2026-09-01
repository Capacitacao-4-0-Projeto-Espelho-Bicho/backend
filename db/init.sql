-- =============================================================================
-- SCRIPT DE CRIAÇÃO DO BANCO DE DADOS
-- Projeto: Sistema de Recomendação para Desenvolvimento de Soft Skills
-- Autor: António Lopes (Entrega E4)
-- Dialeto: PostgreSQL (compatível com MySQL com pequenos ajustes)
-- =============================================================================

-- =============================================================================
-- PASSO 1: LIMPEZA (na ordem correta: filhas antes dos pais)
-- =============================================================================
-- Isso permite rodar o script várias vezes sem dar erro de "tabela já existe".

DROP TABLE IF EXISTS execucao CASCADE;
DROP TABLE IF EXISTS recomendacao CASCADE;
DROP TABLE IF EXISTS atividade CASCADE;
DROP TABLE IF EXISTS competencia CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;

-- =============================================================================
-- PASSO 2: TABELA COMPETÊNCIA (pai de Atividade)
-- Guarda as 10 soft skills do Quadro SENAI
-- =============================================================================
CREATE TABLE competencia (
    id          SERIAL       PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    descricao   TEXT,
    data_criado TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    -- Evita duas competências com o mesmo nome
    CONSTRAINT uq_competencia_nome UNIQUE (nome)
);

COMMENT ON TABLE  competencia IS 'As 10 soft skills do Quadro SENAI.';
COMMENT ON COLUMN competencia.nome IS 'Ex: Empreendedorismo, Inteligência Emocional - Autoconhecimento.';

-- =============================================================================
-- PASSO 3: TABELA USUÁRIO (pai de Recomendação)
-- Guarda identificação + contexto declarado nas 4 dimensões
-- =============================================================================
CREATE TABLE usuario (
    id             SERIAL       PRIMARY KEY,
    nome           VARCHAR(150) NOT NULL,
    email          VARCHAR(150) NOT NULL,
    ambiente       VARCHAR(30)  NOT NULL,
    tempo          VARCHAR(30)  NOT NULL,
    recursos       VARCHAR(30)  NOT NULL,
    interlocutores VARCHAR(30)  NOT NULL,
    data_cadastro  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    -- Evita dois cadastros com o mesmo e-mail
    CONSTRAINT uq_usuario_email UNIQUE (email),

    -- Valida os valores fixos das 4 dimensões de contexto (seção 1.4)
    CONSTRAINT chk_usuario_ambiente CHECK (
        ambiente IN ('individual', 'em_aula', 'em_equipe', 'no_trabalho')
    ),
    CONSTRAINT chk_usuario_tempo CHECK (
        tempo IN ('ate_15_min', '15_a_45_min', 'mais_45_min')
    ),
    CONSTRAINT chk_usuario_recursos CHECK (
        recursos IN ('nenhum', 'papel_ou_celular', 'computador')
    ),
    CONSTRAINT chk_usuario_interlocutores CHECK (
        interlocutores IN ('sozinho', 'com_colega', 'com_grupo')
    )
);

COMMENT ON TABLE usuario IS 'Perfil do usuário com contexto declarado nas 4 dimensões (COM-B: oportunidade).';

-- =============================================================================
-- PASSO 4: TABELA ATIVIDADE (filha de Competência, pai de Recomendação)
-- Catálogo de microatividades com metadados para a cadeia de seleção
-- =============================================================================
CREATE TABLE atividade (
    id               SERIAL       PRIMARY KEY,
    nome             VARCHAR(200) NOT NULL,
    competencia_id   INTEGER      NOT NULL,
    dificuldade      SMALLINT     NOT NULL,
    duracao_min      INTEGER      NOT NULL,
    ambiente         VARCHAR(30)  NOT NULL,
    tempo            VARCHAR(30)  NOT NULL,
    recursos         VARCHAR(30)  NOT NULL,
    interlocutores   VARCHAR(30)  NOT NULL,
    evidencia_exigida VARCHAR(50) NOT NULL,
    descricao        TEXT,
    data_criado      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    -- Regra 5 de integridade: atividade só pode estar ligada a uma competência existente
    CONSTRAINT fk_atividade_competencia
        FOREIGN KEY (competencia_id) REFERENCES competencia(id)
        ON DELETE RESTRICT,

    -- Dificuldade entre 1 e 3
    CONSTRAINT chk_atividade_dificuldade CHECK (dificuldade BETWEEN 1 AND 3),

    -- Duração mínima positiva
    CONSTRAINT chk_atividade_duracao CHECK (duracao_min > 0),

    -- Mesmas validações de contexto do usuário
    CONSTRAINT chk_atividade_ambiente CHECK (
        ambiente IN ('individual', 'em_aula', 'em_equipe', 'no_trabalho')
    ),
    CONSTRAINT chk_atividade_tempo CHECK (
        tempo IN ('ate_15_min', '15_a_45_min', 'mais_45_min')
    ),
    CONSTRAINT chk_atividade_recursos CHECK (
        recursos IN ('nenhum', 'papel_ou_celular', 'computador')
    ),
    CONSTRAINT chk_atividade_interlocutores CHECK (
        interlocutores IN ('sozinho', 'com_colega', 'com_grupo')
    ),
    CONSTRAINT chk_atividade_evidencia CHECK (
        evidencia_exigida IN ('texto', 'arquivo', 'registro_conclusao')
    )
);

COMMENT ON TABLE atividade IS 'Catálogo de microatividades anotadas com metadados para a cadeia de seleção.';

-- =============================================================================
-- PASSO 5: TABELA RECOMENDAÇÃO (filha de Usuário e Atividade)
-- Registra cada atividade sugerida, com regra e status
-- =============================================================================
CREATE TABLE recomendacao (
    id             SERIAL       PRIMARY KEY,
    usuario_id     INTEGER      NOT NULL,
    atividade_id   INTEGER      NOT NULL,
    data_gerada    DATE         NOT NULL DEFAULT CURRENT_DATE,
    regra_usada    VARCHAR(100) NOT NULL,
    status         VARCHAR(20)  NOT NULL DEFAULT 'gerada',
    motivo_recusa  TEXT,
    data_decisao   TIMESTAMP,

    -- Regra 1 de integridade: recomendação precisa de usuário e atividade existentes
    CONSTRAINT fk_recomendacao_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuario(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_recomendacao_atividade
        FOREIGN KEY (atividade_id) REFERENCES atividade(id)
        ON DELETE RESTRICT,

    -- Regra 3 de integridade: usuário não pode ter duas recomendações da mesma atividade no mesmo dia
    CONSTRAINT uq_recomendacao_dia
        UNIQUE (usuario_id, atividade_id, data_gerada),

    -- Regra 4 de integridade: status só pode evoluir em uma direção
    CONSTRAINT chk_recomendacao_status CHECK (
        status IN ('gerada', 'apresentada', 'aceite', 'recusada', 'expirada')
    )
);

COMMENT ON TABLE recomendacao IS 'Atividade sugerida ao usuário, com rastreabilidade da regra aplicada.';

-- =============================================================================
-- PASSO 6: TABELA EXECUÇÃO (filha de Recomendação)
-- Registra a atividade efetivamente realizada e a evidência enviada
-- =============================================================================
CREATE TABLE execucao (
    id                   SERIAL       PRIMARY KEY,
    recomendacao_id      INTEGER      NOT NULL,
    evidencia_arquivo    VARCHAR(255),
    data_envio           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    feedback             TEXT,
    progresso_atualizado DECIMAL(5,2),

    -- Regra 2 de integridade: execução precisa estar ligada a uma recomendação existente
    CONSTRAINT fk_execucao_recomendacao
        FOREIGN KEY (recomendacao_id) REFERENCES recomendacao(id)
        ON DELETE CASCADE,

    -- Regra 2 reforçada: cada recomendação gera no máximo UMA execução (1 para 0..1)
    CONSTRAINT uq_execucao_recomendacao UNIQUE (recomendacao_id),

    -- Progresso entre 0 e 100%
    CONSTRAINT chk_execucao_progresso CHECK (
        progresso_atualizado IS NULL OR
        (progresso_atualizado >= 0 AND progresso_atualizado <= 100)
    )
);

COMMENT ON TABLE execucao IS 'Evidência da atividade realizada e feedback gerado automaticamente.';

-- =============================================================================
-- PASSO 7: ÍNDICES para performance da cadeia de seleção
-- =============================================================================
CREATE INDEX idx_atividade_competencia ON atividade(competencia_id);
CREATE INDEX idx_recomendacao_usuario  ON recomendacao(usuario_id);
CREATE INDEX idx_recomendacao_atividade ON recomendacao(atividade_id);
CREATE INDEX idx_execucao_recomendacao ON execucao(recomendacao_id);

-- Índice composto para a cadeia de seleção (filtro por competência + contexto)
CREATE INDEX idx_atividade_filtro
    ON atividade(competencia_id, ambiente, tempo, recursos, interlocutores);

-- =============================================================================
-- PASSO 8: DADOS INICIAIS — As 10 competências do Quadro SENAI
-- =============================================================================
INSERT INTO competencia (nome, descricao) VALUES
    ('Pensamento Crítico e Inovação',
     'Capacidade de analisar argumentos, questionar premissas e gerar soluções criativas.'),
    ('Aprendizagem Ativa e Estratégias de Aprendizagem',
     'Atitude proativa em relação à própria educação, buscando meios de desenvolver capacidades.'),
    ('Criatividade, Originalidade e Iniciativa',
     'Capacidade de gerar ideias novas, soluções originais e agir sem depender de instruções.'),
    ('Resolução de Problemas Complexos',
     'Habilidade de identificar causas, analisar alternativas e decidir com fundamentação.'),
    ('Liderança e Influência Social',
     'Processo de influenciar pessoas a buscar objetivos comuns de forma coerente.'),
    ('Empreendedorismo',
     'Intenção de gerar melhorias coletivas, detectando oportunidades e assumindo riscos calculados.'),
    ('Inteligência Emocional - Autoconhecimento',
     'Reconhecer as próprias emoções, valores, potencialidades e limitações.'),
    ('Inteligência Emocional - Autorregulação',
     'Regular emoções, pensamentos e comportamentos em diferentes situações.'),
    ('Inteligência Emocional - Percepção Social',
     'Interpretar o comportamento dos outros e o ambiente de trabalho.'),
    ('Inteligência Emocional - Habilidades de Relacionamento',
     'Cultivar relações positivas que gerem resultados edificantes.');

-- =============================================================================
-- FIM DO SCRIPT
-- =============================================================================
