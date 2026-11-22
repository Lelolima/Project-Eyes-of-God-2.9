<p align="center">
  <img src="docs/assets/banner-legado.svg" alt="O-olho-de-DEUS v2 — versão legada. Versão mantida: Lelolima/O-olho-de-DEUS (v3)" width="900">
</p>

> **Esta é a versão 2, legada.** Ela é mantida funcionando, mas não recebe novos recursos.
> A versão atual (v3) está em **[Lelolima/O-olho-de-DEUS](https://github.com/Lelolima/O-olho-de-DEUS)**:
> analítica de intrusão em zona, contagem de pessoas, objeto abandonado, API com login seguro,
> revisão humana, cadeia de custódia e exemplos executáveis.
> Este repositório é idêntico ao diretório `LEGADO_v2.0.0/` de lá, com as correções de manutenção abaixo.

## O que é

Um script único (`src/security_system.py`) que lê uma ou mais fontes de vídeo, detecta rostos
com o Haar Cascade do OpenCV e registra um **incidente** (imagem JPEG + log JSON) quando há
**mais de 10 rostos** no quadro, ou quando um modelo Keras opcional
(`models/behavior_detection_model.h5`, não incluído) passa do limiar. Incidentes podem ser
enviados a um **webhook**. Não identifica pessoas, não tem banco de dados, API nem painel web.

<p align="center">
  <img src="docs/assets/fluxo-legado.svg" alt="Fluxo: fonte de vídeo → Haar → regra de suspeita → incidente → webhook" width="900">
</p>

## Instalação e uso

Python 3.10–3.12.

```bash
git clone https://github.com/Lelolima/Project-Eyes-of-God-2.9.git
cd Project-Eyes-of-God-2.9
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt                       # OpenCV (<5), numpy, requests
python src/security_system.py --config config.json
```

No Windows, `instalar.bat` faz o `pip install` e `validar.bat` confere a instalação.

O `config.json` define as fontes e os parâmetros:

```json
{
  "video_sources": ["0", "gravacao.mp4", "rtsp://camera.exemplo.com/stream"],
  "notification_webhook": "https://hooks.exemplo.com/incidentes",
  "confidence_threshold": 0.7,
  "incident_retention_days": 30
}
```

<details>
<summary><b>Detalhes de comportamento</b></summary>

- **Fontes:** índice de webcam (`"0"`), arquivo local, `http(s)://` ou `rtsp://`. Arquivos são
  processados até o fim e o programa encerra. Câmeras reconectam a cada 2 s.
- **Anti-SSRF:** URLs com IP privado (ex.: `192.168.x.x`) são recusadas, exceto
  `localhost`/`127.0.0.1`. Câmeras na rede local precisam de hostname.
- **Saídas:** `incidents/images/<id>.jpg`, `logs/incidents/AAAA-MM-DD.json` e
  `logs/security_system.log` (rotação de 10 MB).
- **Retenção:** imagens de incidentes com mais de `incident_retention_days` dias são apagadas ao
  encerrar o programa.
- **Variável opcional:** `SECURITY_HASH_SALT` substitui o salt padrão do hash das coordenadas
  dos rostos (o padrão é público no código).
- **Modelo comportamental:** só se `models/behavior_detection_model.h5` existir e o TensorFlow
  estiver instalado (`pip install -r requirements-ml.txt`).
- **Códigos de saída:** `0` ok, `2` nenhuma fonte configurada.
</details>

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest -q --cov=src          # 27 testes, 83% de cobertura (mínimo de 75% no CI)
ruff check . && ruff format --check .
```

Os testes usam vídeos sintéticos gravados em disco e não precisam de câmera nem de TensorFlow.
O CI roda lint, formatação, compilação e testes.

## Limitações

- A única regra sem modelo é "mais de 10 rostos". O Haar perde rostos pequenos ou de perfil.
- **E-mail não é enviado** (só registra um aviso); o webhook funciona.
- As imagens de incidente **não** têm rostos borrados. Para minimização de dados (LGPD), use a v3.
- Benchmarks de FPS e precisão de versões anteriores deste README nunca foram medidos e foram removidos.

## Privacidade (LGPD)

Imagens de pessoas são dados pessoais. Sinalize as áreas monitoradas, restrinja o acesso às
pastas `incidents/` e `logs/`, defina `incident_retention_days` de acordo com a sua política e
mantenha um canal para os titulares. A v3 oferece borramento de rostos, login com hash e
registro auditável de decisões.

## Licença

MIT. Desenvolvido por Wellington de Lima Catarina — lelolima806@gmail.com.
