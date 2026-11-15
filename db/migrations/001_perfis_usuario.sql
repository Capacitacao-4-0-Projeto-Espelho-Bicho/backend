ALTER TABLE capacitacao.usuario
    ADD COLUMN IF NOT EXISTS papel VARCHAR(20) NOT NULL DEFAULT 'usuario';
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'capacitacao.usuario'::regclass
          AND conname = 'chk_usuario_papel'
    ) THEN
        ALTER TABLE capacitacao.usuario ADD CONSTRAINT chk_usuario_papel
            CHECK (papel IN ('usuario', 'gestor', 'admin'));
    END IF;
END;
$$;
