import {defineConfig} from 'vite';
export default defineConfig({build:{rollupOptions:{output:{entryFileNames:'assets/app.js',assetFileNames:a=>a.names?.some(n=>n.endsWith('.css'))?'assets/style.css':'assets/[name]-[hash][extname]'}}}});
