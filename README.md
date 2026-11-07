# Lydia

Painel de fim de dia: indicadores, carteira-alvo, renda fixa e notícias. Não é recomendação de investimento.

- **Página:** `index.html`, servida pelo GitHub Pages.
- **Dados do mercado:** `data/mercado.json` e `data/noticias.json`. Uma tarefa agendada grava esses arquivos nos dias úteis e faz push. Eles são públicos, como as fontes de onde vêm.
- **Dados pessoais:** ficam no Firestore e só o dono lê e grava (veja `firestore.rules`):
  - `painel/carteira`: quantidade de cada ativo, fase atual e aporte do mês.
  - `painel/plano`: as cinco fases do plano. É colado na própria página no primeiro acesso e nunca entra neste repositório.

## Formato dos arquivos

`data/mercado.json`
- `fechamento` (AAAA-MM-DD), `atualizadoEm` (ISO com -03:00)
- `indicadores.{selic, cdi, ipca12m, usdbrl, ibov, ust10}`: `{valor, var?, data, fonte, url}`
- `tesouro`: `{data, fonte, url, titulos: [{nome, tipo: selic|selic100|pre|ipca, taxa}]}`
- `ativos.{TICKER}`: `{preco, var, dy, pvp, pl, ultimoRend: {valor, dataCom, pagamento}, data, obs, fonte, url, hist: [{d, p}]}` (no máximo 60 pontos em `hist`)

`data/noticias.json`
- `atualizadoEm`, `itens[]`: `{id, data, tema: carteira|macro|politica, titulo, resumo, nota?, fonte, url, ativos[], tipo: fato|opiniao|rumor, tese: nao|observar|risco, confirma, contraponto?, leituras: [{quem, diz}, {quem, diz}]}` (7 dias, até 25 itens, da mais nova para a mais antiga)

Antes de cada commit:

```bash
python3 scripts/validar.py
```

## Configuração (uma vez)

**Firebase** (console.firebase.google.com)
1. Criar um projeto (o Google Analytics pode ficar desligado).
2. Authentication › Começar › Método de login › Google › Ativar.
3. Authentication › Configurações › Domínios autorizados › adicionar `SEU-USUARIO.github.io`.
4. Firestore Database › Criar banco de dados › modo de produção › região `southamerica-east1` (São Paulo).
5. Firestore › Regras: colar o conteúdo de `firestore.rules`, trocar o e-mail pelo seu e publicar.
6. Configurações do projeto › Seus apps › Web (`</>`) › registrar o app (sem Hosting) e copiar `apiKey`, `authDomain`, `projectId` e `appId` para `firebase-config.js`.

**GitHub Pages**: Settings › Pages › Deploy from a branch › `main` / `(root)`.

No primeiro acesso, entre com a conta Google liberada nas regras e cole o plano (JSON com as cinco fases) quando a página pedir.

## Testar localmente

```bash
python3 -m http.server 8000
```

Abra http://localhost:8000. Para o login funcionar em `localhost`, ele precisa estar entre os domínios autorizados do Firebase (vem liberado por padrão).
