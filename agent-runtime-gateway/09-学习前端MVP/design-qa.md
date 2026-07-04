# Design QA

final result: passed

## Scope

- Project: `H:\Creat A Agent\agent-runtime-gateway\09-学习前端MVP`
- URL: `http://127.0.0.1:3000`
- Browser: Chrome headless through Playwright Core
- Viewports: desktop `1440x950`, mobile `390x844`
- Date: 2026-07-03

## Brief Match

The MVP matches the confirmed brief:

- Chinese-first learning console for industrial Agent + RAG design.
- Product UI register, not a marketing landing page.
- Top boundary bar, left learning rail, main learning workspace, right evidence panel.
- Visible learning boundaries: 学习模式, 模拟数据, 不执行真实操作, 来源文件.
- No real refund, approval, publish, production connection, or tool execution entry.
- Agnes calls are routed through `/api/agnes/tutor`; browser code reads no API key.

## Visual Evidence

- Desktop home: `浏览器QA截图/desktop-home-final.png`
- Desktop after score: `浏览器QA截图/desktop-after-score-final.png`
- Mobile home: `浏览器QA截图/mobile-home-final.png`
- Mobile after score: `浏览器QA截图/mobile-after-score-final.png`
- Machine report: `浏览器QA截图/browser-qa-report-final.json`

## Checks

| Check | Result | Evidence |
|---|---:|---|
| 13 P0 topic buttons visible | passed | desktop and mobile topic count: 13 |
| Boundary text visible | passed | all four boundary labels found |
| Valid answer can be scored | passed | score reaches pass threshold |
| Next topic unlocks after pass | passed | active topic changes to Runtime 状态 |
| Low-score answer stays blocked | passed | 0/5 keeps 进入下一题 disabled |
| Desktop horizontal scroll | passed | none |
| Mobile horizontal scroll | passed | none |
| Button/text overflow | passed | none detected |
| Images load | passed | 4 images loaded per viewport |
| Console errors/warnings | passed | 0 |
| Failed network requests | passed | 0 |
| Real production action buttons | passed | none detected outside learning navigation |

## Notes

The first QA pass flagged the topic title `建议与执行分离` as risky because the generic detector matched the word `执行`. This was a false positive: it is a course topic, not an operation button. The final QA checks risky production actions only outside the learning navigation and passed.

The mobile layout is intentionally long because it preserves the teaching sequence and evidence panels. It remains readable and has no horizontal overflow.

## Remaining P3 Follow-ups

- Add a compact mobile tab switcher for evidence panels if the course expands beyond the current MVP.
- Add persistent learning backlog export once low-score records become part of the broader course loop.
- Add Playwright test files later if this MVP becomes a maintained app instead of a design-learning artifact.
