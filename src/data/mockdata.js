export const mockReport = {
  riskScore: 82,
  diffs: [
    {
      clause: 'Confidentiality Clause',
      oldText: 'Party A agrees to maintain confidentiality.',
      newText: 'Party A must maintain confidentiality at all times.',
      severity: 'High',
      explanation: 'Stronger obligation on Party A.',
    },
    {
      clause: 'Termination Clause',
      oldText: 'Either party may terminate with 30 days notice.',
      newText: 'Either party may terminate with 60 days notice.',
      severity: 'Medium',
      explanation: 'Extended notice period impacts flexibility.',
    },
  ],
  pdfUrl: '/mock-reports/sample-report.pdf',
};
