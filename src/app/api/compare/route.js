import { generateDiff } from '@/services/diffEngine';

export async function POST(req) {
  const data = await req.formData();
  const fileA = data.get('fileA');
  const fileB = data.get('fileB');

  const fileAText = await fileA.text();
  const fileBText = await fileB.text();

  const report = await generateDiff(fileAText, fileBText);

  return new Response(JSON.stringify(report), {
    headers: { 'Content-Type': 'application/json' },
  });
}
