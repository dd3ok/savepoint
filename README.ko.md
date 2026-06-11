# Savepoint

코딩 에이전트를 위한 continue/load 시스템입니다.

Savepoint는 새 에이전트 세션이 이전 채팅 context에 의존하지 않고 현재 코딩 작업을 이어서 불러오도록 돕습니다.

## Slash-style prompts

| Prompt | 의미 |
|---|---|
| `/savepoint save` | `.savepoint/SAVEPOINT.md` 생성/갱신 |
| `/savepoint load` | 기존 Savepoint 검증/로드. 요청됐고 안전할 때만 이어서 작업 |
| `/savepoint text` | 파일 없이 복붙용 텍스트 인계 생성 |

이 slash-style prompt는 하나의 skill 이름 뒤에 mode를 붙이는 구조입니다.

네이티브 slash-command 지원 여부는 클라이언트마다 다를 수 있습니다. 클라이언트가 custom slash prompt를 모델에 전달하지 않으면 `$savepoint로 저장해줘`, `$savepoint로 로드해줘`, `$savepoint 복붙용 텍스트로 만들어줘`처럼 자연어로 사용합니다.

[English README](README.md)

코딩 세션 상태, repo/Git 상태, 검증, redaction, 안전한 resume이 중요하면 기본적으로 파일 기반 **Savepoint**를 사용합니다. 기존 `.savepoint/SAVEPOINT.md`에서 이어갈 때는 `/savepoint load`를 사용합니다.

`복붙용`, `텍스트`, `파일 없이`처럼 파일 없는 전달을 명시한 경우에만 `/savepoint text`를 사용합니다.

## 사용 사례

- context window가 가득 찬 코딩 에이전트 세션을 새 세션에서 이어가기
- 자동 context compaction 이후 또는 의도적인 session reset 전에 복구 가능한 상태 남기기
- Codex 또는 Claude 세션 사이에서 repo/Git 상태 전달하기
- 단발성 작업을 위한 `/savepoint text` 복붙용 인계 만들기

짧은 단순 요약만 필요하면 일반 요약이 더 저렴할 수 있습니다. 구조화된 코딩 작업 전달이나 복구가 중요할 때 savepoint를 사용하세요.

## Savepoint Artifact

Savepoint는 아래 파일을 씁니다.

```text
.savepoint/SAVEPOINT.md
```

`SAVEPOINT.md`는 `## Resume Prompt`와 마지막 `SAVEPOINT_V1` marker block을 포함합니다. field schema는 `skills/savepoint/schemas/savepoint-v1.schema.json`, marker semantics는 `docs/reference/savepoint-contract.md`에 있습니다.

## Maintainer Validation

생성된 Savepoint artifact에는 `scripts/validate_savepoint.py`를 사용합니다. 이 도구는 `SAVEPOINT.md` 파일을 검증하는 portable runtime check입니다.

`scripts/validate-repo.py`는 이 저장소를 유지보수할 때만 사용합니다. packaging, examples, trigger evals, marker/schema contract를 확인합니다.

저장소 변경을 커밋하기 전에는 아래 검증을 실행합니다.

```bash
python3 scripts/check-frontmatter.py
python3 scripts/check-marker-block.py
python3 scripts/check-marker-semantics.py
python3 scripts/validate-examples.py
python3 scripts/validate-repo.py
python3 scripts/check-savepoint-renderer.py
python3 scripts/check-install-helper.py
python3 scripts/validate_savepoint.py --allow-example-paths examples/SAVEPOINT.filled.example.md examples/file-bugfix/SAVEPOINT.md examples/file-architecture/SAVEPOINT.md examples/unsafe-savepoint/SAVEPOINT.md
git diff --check
```
