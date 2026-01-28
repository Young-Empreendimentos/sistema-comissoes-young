-- Script para adicionar novas colunas na tabela regras_gatilho
-- Execute este script no Supabase Dashboard (SQL Editor)

-- Adicionar coluna tipo_regra (gatilho ou faturamento)
ALTER TABLE regras_gatilho 
ADD COLUMN IF NOT EXISTS tipo_regra VARCHAR(50) DEFAULT 'gatilho';

-- Adicionar coluna faturamento_minimo (valor mínimo para regra de faturamento)
ALTER TABLE regras_gatilho 
ADD COLUMN IF NOT EXISTS faturamento_minimo DECIMAL(15,2);

-- Adicionar coluna percentual_auditoria (percentual extra se passar na auditoria)
ALTER TABLE regras_gatilho 
ADD COLUMN IF NOT EXISTS percentual_auditoria DECIMAL(5,2);

-- Comentários nas colunas
COMMENT ON COLUMN regras_gatilho.tipo_regra IS 'Tipo da regra: gatilho (% do valor + ITBI) ou faturamento (valor mínimo de vendas)';
COMMENT ON COLUMN regras_gatilho.faturamento_minimo IS 'Valor mínimo de faturamento para ter direito à comissão (usado quando tipo_regra = faturamento)';
COMMENT ON COLUMN regras_gatilho.percentual_auditoria IS 'Percentual extra de comissão se o corretor passar na auditoria';

-- Verificar estrutura da tabela
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'regras_gatilho'
ORDER BY ordinal_position;

