import './course_gate.js';

const gate = globalThis.CourseGate;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const fields = [
  { id: 'boundary', minLength: 30, value: '本阶段负责订单只读查询，不负责退款执行；可信事实来自租户隔离的测试夹具。' },
  { id: 'implementation', minLength: 15, value: 'python -m pytest tests/test_runtime.py -q' },
  { id: 'happyPath', minLength: 20, value: '合法输入的预期状态为 passed；实际结果为 passed，并产生审计输出。' },
  { id: 'failurePath', minLength: 20, value: '缺少 tenant_id 的坏输入在契约校验处被阻断，回归测试通过。' },
  { id: 'artifact', minLength: 8, value: 'evidence/s0-report.json' },
];

for (const field of fields) assert(gate.validateEvidenceField(field, field.value).valid, `${field.id} valid evidence rejected`);
assert(!gate.validateEvidenceField(fields[0], 'x'.repeat(80)).valid, 'meaningless long evidence accepted');
assert(gate.validateEvidenceField(fields[1], 'token=super-secret-value-123456').sensitive, 'credential was not detected');

const completeGate = { implementationReady: true, preflightReady: true, quizReady: true, evidenceReady: true, memoryLabReady: true };
assert(gate.canPassStage(completeGate), 'complete gate should pass');
assert(!gate.canPassStage({ ...completeGate, implementationReady: false }), 'missing lab should block');
assert(gate.shouldDowngradePass({ ...completeGate, status: 'passed', gateVersion: 5, requiredGateVersion: 5, quizReady: false }), 'forged pass was trusted');
assert(gate.shouldDowngradePass({ ...completeGate, status: 'passed', gateVersion: 5, requiredGateVersion: 5, implementationReady: false }), 'unimplemented lab pass was trusted');
assert(!gate.shouldDowngradePass({ ...completeGate, status: 'passed', gateVersion: 5, requiredGateVersion: 5 }), 'valid pass was downgraded');

console.log('OK: evidence validation, sensitive-data guard, and forged-pass downgrade checks passed.');
