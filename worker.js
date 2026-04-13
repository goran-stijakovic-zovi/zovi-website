export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname === 'app.zoviconsulting.com' && url.pathname === '/') {
      url.pathname = '/app';
      return env.ASSETS.fetch(new Request(url.toString(), request));
    }
    return env.ASSETS.fetch(request);
  },
};