import { viteSingleFile } from 'vite-plugin-singlefile';

export default {
  plugins: [viteSingleFile()],
  build: {
    cssCodeSplit: false,
    target: 'es2022',
  },
  test: {
    environment: 'node',
  },
};
