# Auditoria técnica — 2026-11-22

Ambiente: Windows 11, Python 3.11 (uv). Sem câmera, sem GPU, sem `models/behavior_detection_model.h5`.

## Estado anterior

| Item | Resultado |
|------|-----------|
| Finalidade | Monitoramento de vídeo (v2): detecção facial Haar Cascade, regra "> 10 rostos" ou modelo Keras opcional, registro de incidentes, notificação por webhook |
| Sobreposição | **Cópia byte a byte** de `LEGADO_v2.0.0/` do repositório `O-olho-de-DEUS` (código, testes, config, scripts; verificado com `cmp`). Nada foi unificado nem excluído |
| Instalação | `requirements.txt` com `opencv-python>=4.8.0` resolve hoje para **OpenCV 5.x, que não tem `cv2.CascadeClassifier`** → detecção facial quebrada em instalação nova; TensorFlow obrigatório (importado no topo) |
| Testes | sem TensorFlow: coleta falha. Com TensorFlow + OpenCV 5.1: 3 falhas (`CascadeClassifier`). Com TF + OpenCV 4.14: 13 passed |
| CI | Nenhum workflow (só o "Dependency Graph" automático) |
| Vulnerabilidades | `pip-audit -r requirements.txt` (após correção): nenhuma |
| Segredos | Nenhum (busca por padrões em todo o histórico). `upload-github-api.py` pede token interativamente (não armazena) |

## Problemas e correções

| # | Sev. | Problema | Evidência | Correção |
|---|------|----------|-----------|----------|
| 1 | P0 | OpenCV 5 sem `CascadeClassifier` → não detecta rostos | falhas acima; `test_haar_cascade_available` | `opencv-python>=4.8.0,<5` |
| 2 | P1 | TensorFlow obrigatório mesmo sem modelo comportamental | coleta falhava sem TF | import opcional; `requirements-ml.txt` |
| 3 | P1 | Webcam `"0"` aberta como arquivo (`VideoCapture("0")`) | `test_webcam_index_is_passed_as_int` | converte para `int` (inclusive na reconexão) |
| 4 | P1 | `rtsp://` documentado no README, mas sempre rejeitado | `test_rtsp_public_host_accepted` | aceita `rtsp://`/`rtsps://` com a mesma regra anti-SSRF de HTTP |
| 5 | P1 | **Notificação simulada passando por real**: email é placeholder, mas o log dizia "Notificação ... enviada" sempre (mesmo com webhook falhando) | `test_no_channel_means_nothing_sent`, `test_webhook_failure_is_not_reported_as_sent` | log/retorno informam os canais efetivamente enviados; email registra aviso de não implementado |
| 6 | P2 | Salt fixo e público no código | leitura | `SECURITY_HASH_SALT` (padrão mantido para compatibilidade) |
| 7 | P2 | Sem CI | — | workflow (ruff, compileall + import, pytest), `contents: read`, actions fixadas por SHA |
| 8 | P2 | README: tabela de cobertura sem medição, TF como obrigatório, sem aviso de limitações | leitura | README corrigido; benchmarks marcados como não verificados |

## Testes executados (resultados reais)

```
antes (TF + OpenCV 5.1.0):  python -m pytest -q  -> 3 failed, 10 passed
antes (sem TF):             -> erro de coleta
depois (sem TF, OpenCV 4.14): python -m pytest -q -p no:cacheprovider -> 22 passed
ruff check --select E9,F63,F7,F82 .  -> All checks passed!
pip-audit -r requirements.txt         -> No known vulnerabilities found
```

## Não executado / riscos residuais

- Câmera real, RTSP real e modelo Keras: não executados (sem hardware/modelo).
- Os scripts `deploy.py`, `deploy-gitpython.py`, `enviar-github.py`, `fix-and-push.py`, `ATUALIZAR-REPOSITORIO.bat` fazem **`git push --force` na `main`**, e `upload-github-api.py` recomenda token com escopo `delete_repo`. Não foram executados nem alterados. **Decisão do dono:** remover ou restringir.
- A regra anti-SSRF bloqueia câmeras em IP privado (caso comum em rede local, inclusive o exemplo do README). Mantida por ser regra de segurança; decisão do dono.
- Hashes de "faces" são de coordenadas da caixa, não de características faciais.
- Repositório duplicado de `O-olho-de-DEUS/LEGADO_v2.0.0`: correções aqui **não** foram replicadas lá.
