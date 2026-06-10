# Savepoint Skill

`savepoint`는 Codex, Claude 같은 코딩 에이전트를 위한 text/file 체크포인트 스킬입니다. 컨텍스트가 다 찬 세션을 새 세션으로 인계하고, 저장소/Git 상태를 보존해 `.savepoint/SAVEPOINT.md`에서 안전하게 이어갈 수 있게 합니다.

[English README](README.md)

이 저장소는 하나의 스킬 `$savepoint`와 세 가지 사용자 워크플로를 제공합니다.

| 필요 | 말하기 | 출력 |
|---|---|---|
| File Savepoint | `세이브포인트 만들어줘`, `세이브포인트 파일 만들어줘`, `SAVEPOINT.md 만들어줘` | `.savepoint/SAVEPOINT.md` |
| Load / Resume Savepoint | `세이브포인트 로드해줘`, `세이브포인트 읽어줘`, `세이브포인트 이어서 해줘` | 상태를 검증/보고하고, 요청됐고 안전할 때만 이어서 작업 |
| Text Savepoint | `세이브포인트 텍스트로 만들어줘`, `세이브포인트 복붙용으로 만들어줘`, `세이브포인트 파일 없이 만들어줘` | 응답 텍스트 |

코딩 세션 상태를 보존할 때는 기본적으로 **File Savepoint**를 사용합니다. 기존 `.savepoint/SAVEPOINT.md`에서 이어갈 때는 기본적으로 **Load / Resume Savepoint**를 사용합니다.

`복붙용`, `텍스트`, `파일 없이`처럼 파일 없는 전달을 명시한 경우에만 **Text Savepoint**를 사용합니다.

이 스킬은 일반 대화 요약기가 아닙니다. `/new`, `/status`, PTY 제어, 세션 회전, 컨텍스트 임계값 선택, 애플리케이션 코드 수정을 수행하지 않습니다.

## 사용 사례

- 컨텍스트가 다 찬 코딩 에이전트 세션을 새 세션에서 이어가기
- Codex 또는 Claude 세션 간 저장소/Git 상태 인계하기
- 단발성 작업을 위한 복붙용 Text Savepoint 만들기

## 기본 아티팩트

File Savepoint는 아래 파일을 씁니다.

```text
.savepoint/SAVEPOINT.md
```

`SAVEPOINT.md`는 `## Resume Prompt`와 파일 끝의 `SAVEPOINT_V1` 블록을 포함합니다. 정확한 필드 스키마는 `skills/savepoint/schemas/savepoint-v1.schema.json`에 있고, `SAVEPOINT_V1` 필드 의미는 `skills/savepoint/references/savepoint-contract.md`에 있습니다.

## Canonical Contract

정식 계약 파일은 다음과 같습니다.

- Skill router: `skills/savepoint/SKILL.md`
- Artifact contract: `skills/savepoint/references/savepoint-contract.md`
- Savepoint skeleton: `skills/savepoint/references/savepoint-template.md`
- 토큰 절약형 초안 helper: `skills/savepoint/scripts/create_savepoint_stub.py`
- Context packaging: `skills/savepoint/references/context-packaging.md`
- Marker schema: `skills/savepoint/schemas/savepoint-v1.schema.json`
- Portable validator: `skills/savepoint/scripts/validate_savepoint.py`

root의 `examples/`, `evals/`, `orchestrators/`, `scripts/validate-repo.py`는 프로젝트 유지보수에 쓰는 파일입니다. root의 `scripts/validate_savepoint.py`는 portable validator로 전달합니다.

## Validation

커밋 전 아래 검증을 실행합니다.

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
