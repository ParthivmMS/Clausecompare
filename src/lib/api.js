export async function postData(url = '', data = {}) {
  const response = await fetch(url, {
    method: 'POST',
    body: data,  // FormData
  });
  return response.json();
}
