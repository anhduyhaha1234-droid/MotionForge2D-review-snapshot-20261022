"""Review reference for Manager adoption; no launch, resume or acceptance authority.

R5 (2026-10-11): Binding.revision gains 'r5' (controlled addition). r4 records remain
valid and immutable; an r4 result can never bind an r5 dispatch (revision mismatch).
R6 (2026-10-12): Binding.revision gains 'r6' (controlled addition). r5/r4 records stay
valid and immutable; an r5 result can never bind an r6 dispatch (revision mismatch).

Validate a dedicated result file bound to one invocation. This checks structure
and artifact integrity, never visual quality. Both live consumers still need to
be patched and tested by Manager before the operational defect is closed.
"""
from pathlib import Path
from typing import Literal
from hashlib import sha256
import json
from pydantic import BaseModel, ConfigDict, Field, model_validator

ROWS = {f'Q{i:02}' for i in range(1, 13)}
REQUIRED = {'master', 'comparison', 'matrix', 'checkpoint', 'receipts'}
Hash = str

class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')

class Binding(StrictModel):
    run_id: Literal['20261005T1643Z-wan-long']
    task_id: Literal['MF-DEMO-LONG-01']
    revision: Literal['r4', 'r5', 'r6']  # R6 adds 'r6'; older revisions' records stay valid/immutable
    owner_sid: str = Field(min_length=1)
    invocation_id: str = Field(min_length=1)
    packet_sha256: Hash = Field(pattern=r'^[0-9a-f]{64}$')

class Artifact(StrictModel):
    kind: Literal['master', 'comparison', 'matrix', 'checkpoint', 'receipts', 'other']
    path: str = Field(min_length=1)
    sha256: Hash = Field(pattern=r'^[0-9a-f]{64}$')

class Result(Binding):
    schema_version: Literal['1.0']
    status: Literal['CONTINUE_REQUIRED', 'TASK_SUBMITTED', 'USER_STOP', 'BLOCKED']
    reason: str = Field(min_length=1)
    remaining_work: list[str]
    artifacts: list[Artifact]
    matrix: dict[str, Literal['PASS', 'FAIL', 'UNKNOWN']]

    @model_validator(mode='after')
    def check_claim(self):
        if self.status == 'CONTINUE_REQUIRED' and not self.remaining_work:
            raise ValueError('continuation requires an explicit next action')
        if self.status == 'TASK_SUBMITTED':
            if self.remaining_work or set(self.matrix) != ROWS:
                raise ValueError('submission requires no remaining work and exactly Q01-Q12')
            if any(v != 'PASS' for v in self.matrix.values()):
                raise ValueError('submission contains open matrix rows')
            kinds = [a.kind for a in self.artifacts]
            if any(kinds.count(k) != 1 for k in REQUIRED):
                raise ValueError('submission needs one of each required artifact kind')
        return self

def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result

def digest(path):
    h = sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def validate_result(result_file: Path, expected: Binding, allowed_root: Path,
                    *, invocation_terminal: bool, exit_code: int | None,
                    infrastructure_error: bool) -> dict:
    """Fail closed. Caller must reconcile owner + child lease before any resume.

    expected comes from the Manager's immutable dispatch receipt, never from
    the untrusted result. Terminal means launcher AND owned children reconciled.
    USER_STOP requires actual user authority; BLOCKED requires independent cause.
    """
    try:
        if not invocation_terminal or exit_code != 0 or infrastructure_error:
            raise ValueError('invocation/children not cleanly reconciled')
        root = allowed_root.resolve(strict=True)
        report_path = result_file.resolve(strict=True)
        if not report_path.is_relative_to(root):
            raise ValueError('result file outside allowed artifact root')
        if report_path.stat().st_size > 1024 * 1024:
            raise ValueError('result record too large; evidence belongs in files')
        result = Result.model_validate(json.loads(report_path.read_text(encoding='utf-8'), object_pairs_hook=no_duplicate_keys))
        for key, value in expected.model_dump().items():
            if getattr(result, key) != value:
                raise ValueError(f'invocation binding mismatch: {key}')
        seen = set()
        for artifact in result.artifacts:
            p = Path(artifact.path)
            if not p.is_absolute():
                raise ValueError('artifact path must be absolute')
            p = p.resolve(strict=True)
            if not p.is_relative_to(root) or not p.is_file() or p == report_path:
                raise ValueError('artifact outside scope, not a file, or self-reference')
            if p in seen:
                raise ValueError('one file cannot impersonate multiple deliverables')
            seen.add(p)
            if digest(p) != artifact.sha256:
                raise ValueError(f'artifact hash mismatch: {artifact.kind}')
            if artifact.kind == 'matrix':
                matrix = json.loads(p.read_text(encoding='utf-8'), object_pairs_hook=no_duplicate_keys)
                if matrix != {'rows': result.matrix}:
                    raise ValueError('result/matrix artifact disagree')
        action = {
            'CONTINUE_REQUIRED': 'PENDING_SAME_OWNER_CONTINUATION',
            'TASK_SUBMITTED': 'VERIFIABLE_SUBMISSION_PENDING_MANAGER_QA',
            'USER_STOP': 'VERIFY_USER_STOP_AUTHORITY',
            'BLOCKED': 'VERIFY_EXTERNAL_BLOCKER',
        }[result.status]
        return {'decision': action, 'quality_accepted': False, 'result': result.model_dump()}
    except (ValueError, OSError) as error:
        return {'decision': 'NEEDS_RECONCILIATION', 'quality_accepted': False, 'error': str(error)}
