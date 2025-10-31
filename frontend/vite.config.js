import {defineConfig, loadEnv} from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default ({mode}) => {
    // eslint-disable-next-line no-undef
    process.env = {...process.env, ...loadEnv(mode, process.cwd())};
    return defineConfig({
        plugins: [react()],
        // eslint-disable-next-line no-undef
        base: process.env['VITE_BASE_PATH'],
        envDir: '../',
        build: {
            sourcemap: true
        }
    });
}
