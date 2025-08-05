# Steam Account Checker – Uso Educacional

> **Aviso**: este projeto tem **propósitos estritamente educacionais**.
> Não o utilize para violar Termos de Serviço da Steam nem para atividades
> não autorizadas. O autor/colaborador não assume qualquer responsabilidade
> por uso indevido.

## Visão geral

`steam_check.py` é um script em Python que testa listas de contas Steam
utilizando proxies rotativos. Ele automatiza o login via Selenium em modo
móvel (UA e viewport de dispositivos populares) e classifica cada conta
como **válida** ou **inválida**:

- **valid_accounts.txt** – credenciais que acessaram a página
  `https://store.steampowered.com/account/` com sucesso.
- **invalid_accounts.txt** – credenciais que falharam.

## Como funciona

1. **Leitura de arquivos**
   - `accounts.txt`: cada linha no formato `usuario:senha`.
   - `proxies.txt`: proxies HTTP(S) no formato `user:pass@host:port`.

2. **Rotação de proxy**
   - Usa `itertools.cycle` para aplicar um proxy diferente a cada conta.

3. **Emulação móvel**
   - A cada execução do driver é escolhido aleatoriamente um device
     (`Pixel 2`, `iPhone X`, `Galaxy S5`).

4. **Fluxo de login**
   - Acessa a página de login e envia credenciais.
   - Aguarda 3 s e navega para `/account` para verificar sucesso.

5. **Rate-limit**
   - Após **3** tentativas o script pausa **2 min** para reduzir risco de
     bloqueio.

## Pré-requisitos

- Python 3.8+
- Google Chrome instalado (driver gerenciado automaticamente)

Instale as dependências:

```bash
pip install selenium webdriver-manager
```

## Uso

1. Preencha `accounts.txt` e `proxies.txt`.
2. Execute:
   ```bash
   python steam_check.py
   ```
3. Consulte `valid_accounts.txt` e `invalid_accounts.txt` após a execução.

## Estrutura dos arquivos

```
├─ steam_check.py         # Script principal
├─ accounts.txt           # Lista de contas Steam
├─ proxies.txt            # Lista de proxies HTTP(S)
├─ valid_accounts.txt     # Saída: credenciais válidas
└─ invalid_accounts.txt   # Saída: credenciais inválidas
```

## Observações de segurança

- O Chrome é iniciado em modo incógnito e encerrado a cada conta; nenhum
  cookie é reutilizado.
- As credenciais de proxy são injetadas via extensão temporária, evitando
  pop-ups de autenticação.
- Ajuste o tempo de rate-limit ou o número de tentativas conforme sua
  infraestrutura.

---
**Licença**: MIT – consulte o arquivo LICENSE se fornecido.
