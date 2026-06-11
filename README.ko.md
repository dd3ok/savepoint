# Savepoint

코딩 에이전트를 위한 continue/load 시스템입니다.

Savepoint는 새 에이전트 세션이 이전 채팅 context에 의존하지 않고 현재 코딩 작업을 이어서 불러오도록 돕습니다.

- **Quick Save**: 작은 전달을 위한 응답 텍스트입니다.
- **Savepoint**: repo/Git 상태를 복구할 수 있는 파일 checkpoint입니다.

전달이 작으면 Quick Save를 사용합니다.
디스크 상태, 검증, redaction, 안전한 resume이 중요하면 Savepoint를 사용합니다.

[English README](README.md)

이 저장소는 `$savepoint` 스킬 하나와 세 가지 사용자 흐름을 제공합니다.

| 필요 | 말하기 | 출력 |
|---|---|---|
| Savepoint | `세이브포인트 만들어줘`, `세이브포인트 파일 만들어줘`, `SAVEPOINT.md 만들어줘` | `.savepoint/SAVEPOINT.md` |
| Load / Resume Savepoint | `세이브포인트 로드해줘`, `세이브포인트 읽어줘`, `세이브포인트 이어서 해줘` | 상태 검증/보고 후, 요청했고 안전할 때만 이어서 작업 |
| Quick Save | `세이브포인트 텍스트로 만들어줘`, `세이브포인트 복붙용으로 만들어줘`, `세이브포인트 파일 없이 만들어줘` | 응답 텍스트 |

코딩 세션 상태를 보존할 때는 기본적으로 **Savepoint**를 사용합니다. 기존 `.savepoint/SAVEPOINT.md`에서 이어갈 때는 **Load / Resume Savepoint**를 사용합니다.

`복붙용`, `텍스트`, `파일 없이`처럼 파일 없는 전달을 명시한 경우에만 **Quick Save**를 사용합니다.

## 사용 사례

- context window가 가득 찬 코딩 에이전트 세션을 새 세션에서 이어가기
- 자동 context compaction 이후 또는 의도적인 session reset 전에 복구 가능한 상태 남기기
- Codex 또는 Claude 세션 사이에서 repo/Git 상태 전달하기
- 단발성 작업을 위한 복붙용 Quick Save 만들기

짧은 단순 요약만 필요하면 일반 요약이 더 저렴할 수 있습니다. 구조화된 코딩 작업 전달이나 복구가 중요할 때 savepoint를 사용하세요.

## Savepoint Artifact

Savepoint는 아래 파일을 씁니다.

```text
.savepoint/SAVEPOINT.md
```

`SAVEPOINT.md`는 `## Resume Prompt`와 마지막 `SAVEPOINT_V1` marker block을 포함합니다. field schema는 `skills/savepoint/schemas/savepoint-v1.schema.json`, marker semantics는 `skills/savepoint/references/savepoint-contract.md`에 있습니다.

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
python3 scripts/check-savepoint-stub.py
python3 scripts/check-install-helper.py
python3 scripts/validate_savepoint.py --allow-example-paths examples/SAVEPOINT.filled.example.md examples/file-bugfix/SAVEPOINT.md examples/file-architecture/SAVEPOINT.md examples/unsafe-savepoint/SAVEPOINT.md
git diff --check
```
