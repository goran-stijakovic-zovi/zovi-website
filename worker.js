export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname === 'demo.zoviconsulting.com') {
      const target = new URL(url.pathname + url.search, 'https://sourceflow-light.vercel.app');
      const upstreamResponse = await fetch(new Request(target.toString(), request));
      const response = new Response(upstreamResponse.body, upstreamResponse);
      response.headers.set('x-worker-routed', 'demo-subdomain');
      return response;
    }
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