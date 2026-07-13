(function attachCourseGate(root) {
  'use strict';

  const sensitivePatterns = [
    { label: 'private key', pattern: /-----BEGIN [A-Z ]*PRIVATE KEY-----/i },
    { label: 'API key', pattern: /\b(?:sk|rk|pk)-/ },
    { label: 'AWS access key', pattern: /\bAKIA/ },
    { label: 'Bearer token', pattern: /\bBearer\s+/i },
    { label: 'JWT', pattern: /\beyJ[A-Za-z0-9_-]{8,}\./ },
    { label: 'credential', pattern: /\b(?:password|passwd|secret|token|api[_-]?key)\s*[:=]/i },
    { label: 'mobile number', pattern: /(?:^|\D)1[3-9]\d{9}(?:\D|$)/ },
    { label: 'identity number', pattern: /(?:^|\D)\d{17}[0-9Xx](?:\D|$)/ },
  ];

  const signalChecks = {
    boundary: {
      reason: '需同时说明责任边界与事实来源',
      test: (value) => /(负责|不负责|边界|范围|禁止)/.test(value) && /(来源|事实|输入|可信|租户|审批)/.test(value),
    },
    implementation: {
      reason: '需包含命令、commit 或仓库文件路径',
      test: (value) => /(?:^|\s)(?:python|pytest|node|npm|pnpm|yarn|uv|git|docker|curl)\b|commit\s+[a-f0-9]{7,40}|(?:src|tests?|evidence|docs?)[\\/][\w./-]+/i.test(value),
    },
    happyPath: {
      reason: '需同时记录预期与实际结果',
      test: (value) => /(预期|expected|应当)/i.test(value) && /(实际|actual|结果|输出|passed|成功)/i.test(value),
    },
    failurePath: {
      reason: '需记录失败输入、阻断或回归结果',
      test: (value) => /(失败|攻击|坏输入|异常|拒绝|阻断|超时|回滚|回归|error|exception|timeout|blocked|denied)/i.test(value),
    },
    artifact: {
      reason: '需填写产物路径、文件名或公开 URL',
      test: (value) => /https?:\/\/|(?:^|[\s(])(?:[\w.-]+[\\/])+[\w./-]+|[\w.-]+\.(?:json|md|log|xml|txt|html|png|har|trace)(?:$|[\s)])/i.test(value),
    },
  };

  function detectSensitiveEvidence(value) {
    const text = String(value || '');
    return sensitivePatterns.find((item) => item.pattern.test(text))?.label || '';
  }

  function validateEvidenceField(field, value) {
    const text = String(value || '').trim();
    const sensitive = detectSensitiveEvidence(text);
    if (sensitive) return { valid: false, sensitive, reason: `疑似包含 ${sensitive}，未保存` };
    if (text.length < field.minLength) return { valid: false, sensitive: '', reason: `至少 ${field.minLength} 字` };
    const signalCheck = signalChecks[field.id];
    if (signalCheck && !signalCheck.test(text)) return { valid: false, sensitive: '', reason: signalCheck.reason };
    return { valid: true, sensitive: '', reason: '格式有效' };
  }

  function canPassStage(input) {
    return Boolean(input.implementationReady && input.preflightReady && input.quizReady && input.evidenceReady && input.memoryLabReady);
  }

  function shouldDowngradePass(input) {
    return input.status === 'passed' && (input.gateVersion !== input.requiredGateVersion || !canPassStage(input));
  }

  root.CourseGate = Object.freeze({ detectSensitiveEvidence, validateEvidenceField, canPassStage, shouldDowngradePass });
})(globalThis);
