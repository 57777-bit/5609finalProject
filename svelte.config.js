import adapter from '@sveltejs/adapter-static';

const repo = process.env.GITHUB_REPOSITORY?.split('/')[1] ?? '';
const defaultBase = repo && !repo.endsWith('.github.io') ? `/${repo}` : '';
const basePath = process.argv.includes('dev') ? '' : (process.env.BASE_PATH ?? defaultBase);

const config = {
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: '404.html',
      precompress: false,
      strict: true
    }),
    paths: {
      base: basePath
    }
  }
};

export default config;