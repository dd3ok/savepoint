# New Session Handoff Skill

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/github/license/dd3ok/new-session-handoff-skill)](https://github.com/dd3ok/new-session-handoff-skill/blob/main/LICENSE)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/dd3ok/new-session-handoff-skill/validate.yml?branch=main)](https://github.com/dd3ok/new-session-handoff-skill/actions/workflows/validate.yml)

`new-session-handoff-skill`은 **AI 코딩 에이전트(AI Coding Agent)**가 새로운 세션에서 이전 작업을 원활하게 이어갈 수 있도록 검증된 `HANDOFF.md`를 생성하는 경량 스킬입니다. 이 스킬은 이전 채팅 기록에 의존하지 않고도 작업 컨텍스트를 안전하게 전달하여, **에이전트 세션 연속성(Agent Session Continuity)**과 **컨텍스트 관리(Context Management)**를 최적화합니다. `new-session-handoff`는 `/new`를 실행하거나, PTY를 제어하거나, 세션을 로테이션하거나, 핸드오프 생성 중에 애플리케이션 코드를 편집하지 않습니다. 대신 복구 가능한 핸드오프 아티팩트와 기계가 읽을 수 있는 준비 마커만 작성합니다.

기본 아티팩트:

```text
.new-session-handoff/HANDOFF.md
```

기본 핸드오프에는 `## Resume Prompt` 섹션이 포함됩니다.

다음 세션이 핸드오프를 읽고 현재 디스크/Git 상태와 비교한 뒤, `SAFE_FOR_NEW_SESSION: yes`인 핸드오프를 실제 resume/continue에 채택한 경우에만 선택된 추적되지 않는 generated handoff artifact를 삭제할 수 있습니다. inspect-only, tracked, stale, unsafe, external-path, user-authored artifact는 보존합니다.

## 한국어 사용 예시 (Usage Examples in Korean)

AI 에이전트에게 다음과 같은 프롬프트를 사용하여 `new-session-handoff-skill`을 활용할 수 있습니다:

*   **사용자**: `지금까지 작업한 내용을 바탕으로 핸드오프를 만들어줘.`
*   **에이전트**: `현재 디스크/Git 상태를 확인하고 .new-session-handoff/HANDOFF.md를 생성하거나 갱신합니다. 작업 컨텍스트가 HANDOFF.md에 저장되었습니다.`

*   **사용자**: `핸드오프를 읽고 이어서 작업해줘.`
*   **에이전트**: `HANDOFF.md를 읽고 현재 디스크/Git 상태와 비교합니다. 불일치하는 부분이 있으면 보고하고, SAFE_FOR_NEW_SESSION: yes 상태이며 구현 계속을 요청하시면 다음 작업을 진행합니다.`

## Canonical Contract

런타임 동작은 분산 스킬에 집중되어 있습니다:

- 스킬 라우터: `skills/new-session-handoff/SKILL.md`
- 아티팩트 계약: `skills/new-session-handoff/references/handoff-contract.md`
- 핸드오프 스켈레톤: `skills/new-session-handoff/references/handoff-template.md`
- 컨텍스트 패키징 원칙: `skills/new-session-handoff/references/context-packaging.md`
- 마커 스키마: `skills/new-session-handoff/schemas/handoff-automation-v1.schema.json`
- 휴대용 유효성 검사기: `skills/new-session-handoff/scripts/validate_handoff.py`

README는 맵입니다. 위의 계약 파일은 마커 의미론, `SAFE_FOR_NEW_SESSION`, 신뢰 순서, 확장된 아티팩트, 정리 및 재개 동작에 대한 진실의 원천입니다.

## Repository Layout

```text
.
├── README.md
├── SECURITY.md
├── CHANGELOG.md
├── AGENTS.md
├── skills/
│   └── new-session-handoff/
│       ├── SKILL.md
│       ├── LICENSE.txt
│       ├── agents/openai.yaml
│       ├── references/
│       │   ├── context-packaging.md
│       │   ├── handoff-contract.md
│       │   └── handoff-template.md
│       ├── schemas/handoff-automation-v1.schema.json
│       └── scripts/
│           ├── handoff_contract.py
│           └── validate_handoff.py
├── examples/
├── evals/
├── orchestrators/
└── scripts/
```

`skills/new-session-handoff/`는 휴대용 스킬 패키지입니다. 루트 레벨의 `examples/`, `evals`, `orchestrators/`, `scripts/validate-repo.py`는 유지보수자 자산입니다. 루트 `scripts/validate_handoff.py`는 휴대용 유효성 검사기 주변의 호환성 래퍼입니다.

## Installation / Vendoring

정식 스킬을 에이전트 환경에서 사용하는 위치로 복사, 벤더링 또는 심볼릭 링크하세요.

일반적인 위치:

- Codex 개인 스킬: `$HOME/.agents/skills/new-session-handoff/`
- Codex 리포지토리 스킬: `<repo>/.agents/skills/new-session-handoff/`
- Claude 개인 스킬: `$HOME/.claude/skills/new-session-handoff/`
- Claude 프로젝트 스킬: `<repo>/.claude/skills/new-session-handoff/`

예시 프로젝트 심볼릭 링크:

```bash
mkdir -p .agents/skills .claude/skills
ln -s ../../skills/new-session-handoff .agents/skills/new-session-handoff
ln -s ../../skills/new-session-handoff .claude/skills/new-session-handoff
```

## Examples

- `examples/compact-bugfix/`: 작은 버그 수정을 위한 컴팩트 핸드오프.
- `examples/expanded-architecture/`: 집중된 세부 아티팩트가 포함된 확장된 핸드오프.
- `examples/unsafe-handoff/`: `SAFE_FOR_NEW_SESSION: no`가 중요한 이유를 보여주는 의도적으로 안전하지 않은 핸드오프.

예시는 유지보수자/데모 자료입니다. 분산 스킬 패키지에는 필요하지 않습니다.

## Evals

`evals/`에는 스킬 계약을 유지하기 위한 경량 수동 시나리오가 포함되어 있습니다. `SKILL.md`, 템플릿, 마커 의미론, 예시, 유효성 검사기 또는 오케스트레이터 지침을 변경할 때 사용하세요.

- `evals/trigger-queries.json`: 스킬이 언제 trigger되어야 하고 언제 trigger되지 않아야 하는지 검증하는 query set.
- `evals/cases/context-state-bridge.md`: durable state file과 `HANDOFF.md`의 역할 분리를 검증합니다.
- `evals/cases/trigger-boundaries.md`: ordinary summary, docs, instruction-file authoring, session-control, code-fix 요청에서 skill이 과잉 trigger되지 않는지 검증합니다.

핵심 기대치:

- 생성 모드는 애플리케이션 코드를 수정하지 않습니다.
- 생성된 아티팩트에는 검증된 사실 또는 명시적인 미확인 정보가 포함됩니다.
- 기본 생성 모드는 `.new-session-handoff/HANDOFF.md`를 작성합니다.
- 기본 생성 모드는 `HANDOFF.md` 안에 `## Resume Prompt`를 임베드합니다.
- 재개 모드는 코딩 전에 디스크 상태를 확인합니다.
- 확장 모드는 컨텍스트 덤프 대신 집중된 세부 아티팩트를 사용합니다.
- 안전하지 않은 상태는 `SAFE_FOR_NEW_SESSION: yes`를 내보내지 않습니다.
- 비밀은 수정되거나 생략됩니다.
- 검증된 안전한 재개는 추적되지 않는 생성된 핸드오프 아티팩트만 삭제할 수 있습니다.

## Validation

변경 사항을 커밋하기 전에 다음을 실행하세요:

```bash
python3 scripts/check-frontmatter.py
python3 scripts/check-marker-block.py
python3 scripts/check-marker-semantics.py
python3 scripts/validate-examples.py
python3 scripts/validate-repo.py
```

생성된 핸드오프 아티팩트를 직접 유효성 검사하려면:

```bash
python3 scripts/validate_handoff.py .new-session-handoff/HANDOFF.md
```

루트 유효성 검사 명령은 `skills/new-session-handoff/scripts/` 내의 휴대용 유효성 검사기에 위임합니다.

## Orchestrators

외부 PTY 컨트롤러는 최종 마커 블록을 읽고 세션을 로테이션할지 여부를 결정할 수 있습니다. `orchestrators/session-rotation.md`를 참조하세요.

이 스킬은 핸드오프 아티팩트만 준비하고 소비합니다. 세션 재설정 명령, 컨텍스트 임계값 정책, PTY 입력 및 에이전트 CLI 오케스트레이션은 스킬 외부에 유지됩니다.

## Versioning

현재 핸드오프 스키마는 다음과 같습니다:

```text
HANDOFF_SCHEMA_VERSION: 1
```

마커 이름, 필수 섹션, 마커 의미 또는 세부 경로 해결에 대한 호환되지 않는 변경 사항은 스키마 버전을 증가시키고 예시, 평가, README, 유효성 검사기 및 오케스트레이터 지침을 함께 업데이트해야 합니다.
