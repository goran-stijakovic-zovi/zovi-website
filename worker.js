export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname === 'app.zoviconsulting.com') {
      url.hostname = 'zoviconsulting.com';
      if (url.pathname === '/') url.pathname = '/app';
      const response = await env.ASSETS.fetch(new Request(url.toString(), request));
      const newResponse = new Response(response.body, response);
      newResponse.headers.set('x-worker-routed', 'app-subdomain');
      return newResponse;
    }
    return env.ASSETS.fetch(request);
  },
};