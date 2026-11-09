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
- `ativos.{TICKER}`: `{preco, var, dy, pvp, pl, ultimoRend: {valor, dataCom, pagamento}, data, obs, fonte, url, hist: [{d, p}], velas: [{d, o, h, l, c, v}]}` (no máximo 60 pontos em `hist` e 250 velas diárias em `velas`, da mais antiga para a mais nova)

`data/noticias.json`
- `atualizadoEm`, `itens[]`: `{id, data, tema: carteira|macro|politica, titulo, resumo, nota?, fonte, url, ativos[], tipo: fato|opiniao|rumor, tese: nao|observar|risco, confirma, contraponto?, leituras: [{quem, diz}, {quem, diz}]}` (7 dias, até 25 itens, da mais nova para a mais antiga)

As velas vêm da [brapi.dev](https://brapi.dev) (plano gratuito: velas diárias, até 3 meses por chamada, 1 ativo por vez):

```bash
python3 scripts/velas.py   # junta as velas novas em data/mercado.json; não mexe em preço nem em hist
```

O token não fica no repositório. Na sessão da tarefa agendada, o proxy de rede acrescenta a autorização; fora dela, rode com `BRAPI_TOKEN=... python3 scripts/velas.py`.

## Aba Gráfico

Velas diárias com volume e médias de 20 e 50 dias, feitas com [Lightweight Charts](https://github.com/tradingview/lightweight-charts) (TradingView). Abre pela aba ou tocando no código do ativo na Carteira (`#grafico/VALE3`).

- Sem token: usa as velas de `data/mercado.json`, gravadas nos dias úteis às 18h43.
- Com token da brapi guardado no aparelho (campo no fim da aba, fica só no `localStorage` daquele navegador): junta os últimos 3 meses e a vela de hoje se formando, com atraso de uns 15 minutos, e atualiza a cada minuto durante o pregão. Tempo real sem atraso exige dado pago da B3.

Antes de cada commit:

```bash
python3 scripts/validar.py
```

## Configuração (uma vez)

**Firebase** (console.firebase.google.com)
1. Criar um projeto (o Google Analytics pode ficar desligado).
2. Segurança › Authentication › Vamos começar › Método de login › Google › Ativar.
3. Segurança › Authentication › Configurações › Domínios autorizados › adicionar `SEU-USUARIO.github.io`.
4. Firestore Database › Criar banco de dados › modo de produção › região `southamerica-east1` (São Paulo).
5. Firestore › Regras: colar o conteúdo de `firestore.rules`, trocar o e-mail pelo seu e publicar.
6. Configurações do projeto › Seus apps › Web (`</>`) › registrar o app (sem Hosting) e copiar `apiKey`, `authDomain`, `projectId` e `appId` para `firebase-config.js`.

**GitHub Pages**: Settings › Pages › Deploy from a branch › `main` / `(root)`.

No primeiro acesso, entre com a conta Google liberada nas regras e cole o plano (JSON com as cinco fases) quando a página pedir.

## Testar localmente

```bash
python3 -m http.server 8000
```

Abra http://localhost:8000. Para o login funcionar em `localhost`, adicione `localhost` aos domínios autorizados do Firebase (Segurança › Authentication › Configurações › Domínios autorizados). Em projetos criados depois de abril de 2025 ele não vem liberado.
