# Savepoint

컨텍스트 압축, reset, handoff 이후 이어받기 위한 repo/Git savepoint artifact입니다.

Savepoint는 이전 대화 컨텍스트에 의존하지 않고 새 코딩 에이전트가 현재 repo/Git 상태에서 이어갈 수 있게 `.savepoint/SAVEPOINT.md`를 생성하거나 검증하는 skill입니다. 일반 요약이 놓치기 쉬운 repo snapshot, validation 상태, redaction 상태, resume prompt를 기록합니다.

Savepoint는 가벼운 대화 요약이 아닙니다. 복구 가능한 repo/Git checkpoint입니다. 파일 복구가 필요 없으면 `/savepoint text`나 일반 요약을 사용하세요.

## 30초 사용법

```text
/savepoint        .savepoint/SAVEPOINT.md를 생성하거나 갱신합니다.
/savepoint save   기본 동작과 같습니다.
/savepoint load   기존 savepoint를 검증하고 이어가기 안전 여부를 보고합니다.
/savepoint text   복붙용 텍스트만 출력합니다. 파일 복구 보장은 없습니다.
```

클라이언트가 custom slash prompt를 모델에 전달하지 않으면 `$savepoint로 저장해줘`, `$savepoint로 로드해줘`, `$savepoint 복붙용 텍스트로 만들어줘`처럼 자연어로 요청하세요.

[English README](README.md)

## 설치

먼저 dry-run으로 확인합니다.

```bash
# Claude user install
python3 scripts/install.py --target claude --scope user

# Codex repo install
python3 scripts/install.py --target codex --scope repo --repo-root /path/to/target-repo --add-gitignore
```

대상을 확인한 뒤 적용합니다.

```bash
python3 scripts/install.py --target claude --scope user --apply
python3 scripts/install.py --target codex --scope repo --repo-root /path/to/target-repo --apply --add-gitignore
```

helper는 기본 dry-run입니다. 기존 destination이 있으면 실패하고, 실제로 쓰려면 `--apply`가 필요합니다. repo-scope install에서 `--add-gitignore`를 주면 `.savepoint/`를 추가합니다.

repo-local quick check:

```bash
python3 scripts/savepoint.py validate --allow-example-paths examples/file-bugfix/SAVEPOINT.md
```

Windows에서는 install helper나 일반 Git clone/worktree를 권장합니다. 일부 archive extraction 도구는 symlink를 제대로 처리하지 못할 수 있습니다.

## 언제 쓰나

- context window가 차거나 자동 compaction이 예상될 때
- 코딩 에이전트 세션을 reset하거나 다른 세션으로 넘기기 전
- multi-file refactor 중 검증 가능한 재개 지점이 필요할 때
- Codex, Claude, Gemini, 외부 orchestrator 사이에 repo 상태를 넘길 때

## handoff 선택 기준

- repo 복구가 필요 없으면 일반 요약을 사용합니다.
- 파일 복구 없이 복붙용 note만 필요하면 `/savepoint text`를 사용합니다.
- 다음 에이전트가 disk/Git 상태를 확인하고 이어가야 하면 `/savepoint`를 사용합니다.

## 쓰지 않을 때

- 짧은 일반 요약이면 충분할 때
- SQL `SAVEPOINT` 설명 요청일 때
- `/status`, `/new`, compaction 정책, PTY 제어, session rotation 요청일 때
- checkpoint 의도 없는 직접 code/docs 수정이나 savepoint라는 이름의 기능 구현 요청일 때
- Git commit, stash, branch history가 맞는 도구일 때

## 보장하는 것

- file mode는 `.savepoint/SAVEPOINT.md`를 씁니다.
- artifact는 repo/Git snapshot, `## Resume Prompt`, 마지막 `SAVEPOINT_V1` marker block을 포함합니다.
- `REDACTION_CHECKED: yes` 전에 generated artifact를 pattern-based secret-like scan으로 검사합니다.
- bundled validator가 marker shape와 safe-resume 필드를 검사합니다.
- load 시 현재 disk state가 savepoint text보다 우선합니다.

## load report 예시

일반적인 `/savepoint load` 보고는 새 에이전트가 안전하게 이어갈 수 있는지 답합니다.

```text
Loaded: .savepoint/SAVEPOINT.md
Git root: matches
Branch: feature/auth matches
HEAD: matches
Working tree drift: none
Required files: present
Redaction: checked
Savepoint validation: passed
Project validation: passed
RESUME_READY: yes
Next action: run npm test -- tests/auth/session.test.ts
```

## 보장하지 않는 것

- 테스트 통과
- 코드 정답성
- 작업 완료
- 미래 충돌 없음
- text mode만으로 repo 상태를 복구할 수 있음

## 최소 CLI 흐름

portable skill entrypoint는 `skills/savepoint/scripts/savepoint.py`입니다. repository-local 명령은 `scripts/savepoint.py`를 사용합니다.

`inspect --json`은 파일과 marker가 valid이면 `0`, savepoint-like 파일을 읽었지만 invalid이면 `1`, 파일을 읽을 수 없거나 savepoint artifact가 아니면 `2`로 종료합니다.

최소 파일 흐름:

```bash
python3 scripts/savepoint.py init-input --output .savepoint/input.json
$EDITOR .savepoint/input.json
python3 scripts/savepoint.py save --input .savepoint/input.json --output .savepoint/SAVEPOINT.md --assert-no-active-commands --scan-redaction --validate
python3 scripts/savepoint.py inspect .savepoint/SAVEPOINT.md --json
```

`validation.project.status`는 `passed`, `failed-expected`, `failed-blocking`, `not-run-justified`, `not-run-unknown` 중 하나를 사용합니다. `--scan-redaction`을 쓰면 입력 JSON을 렌더 전에 스캔합니다. `.savepoint/input.json`에 raw secret을 넣지 마세요.

## Runtime boundary

일반 create/load에서는 다음만 사용합니다.

- `skills/savepoint/SKILL.md`
- `skills/savepoint/scripts/savepoint.py`
- 고급 edge case가 있을 때만 `skills/savepoint/references/*.md`
- marker schema를 debug할 때만 `skills/savepoint/schemas/savepoint-v1.schema.json`

examples, evals, maintainer docs, repository validation scripts는 일반 agent context가 아닙니다.

## Examples

- `examples/README.md`: scenario index
- `examples/file-bugfix/`: 작은 file savepoint
- `examples/file-architecture/`: `details/*.md` spillover가 있는 savepoint
- `examples/load-report/`: sample load reports
- `examples/text-note/`: response-only `/savepoint text` 예시
- `examples/unsafe-savepoint/`: 의도적으로 unsafe한 `RESUME_READY: no` artifact

## Maintainer docs

생성된 artifact는 `scripts/savepoint.py validate .savepoint/SAVEPOINT.md`로 검증합니다.

- repository 변경 검증: `AGENTS.md`
- marker와 safe-resume semantics: `docs/reference/savepoint-contract.md`
- compact packaging 기준: `docs/reference/context-packaging.md`
- 수동 artifact fallback: `docs/reference/savepoint-template.md`
