function redirect(location) {
  return {
    statusCode: 301,
    statusDescription: 'Moved Permanently',
    headers: { location: { value: location } },
  };
}

function handler(event) {
  const request = event.request;
  const host = request.headers.host ? request.headers.host.value : '';
  const uri = request.uri;

  if (!host.startsWith('www.')) {
    return redirect(`https://www.${host}${uri}`);
  }

  if (uri.startsWith('/assets/')) {
    request.uri = `/home${uri}`;
    return request;
  }

  if (uri.includes('.')) {
    return request;
  }

  if (uri === '/' || uri === '') {
    request.uri = '/home/index.html';
    return request;
  }

  if (!uri.endsWith('/')) {
    return redirect(`https://${host}${uri}/`);
  }

  request.uri = `${uri}index.html`;
  return request;
}
