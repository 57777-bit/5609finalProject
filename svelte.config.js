// import adapter from '@sveltejs/adapter-static';

// export default {
//   kit: {
//     adapter: adapter({
//       pages: 'build',
//       assets: 'build',
//       fallback: '404.html',
//       precompress: false,
//       strict: true
//     })
//   }
// };
import adapter from '@sveltejs/adapter-static';

const dev = process.argv.includes('dev');

const config = {
  kit: {
    adapter: adapter(),
    paths: {
      base: dev ? '' : '/5609finalProject'
    }
  }
};

export default config;