const http = require('http');

http.get('http://127.0.0.1:8000/api/system/safety-matrix', (res) => {
  console.log('Status Code:', res.statusCode);
  console.log('Headers:', res.headers);
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => console.log('Body:', data));
}).on('error', err => console.error('Error:', err.message));
