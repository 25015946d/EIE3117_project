const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 8081,
    host: '0.0.0.0',
    proxy: {
      '/auth': {
        target: process.env.VUE_APP_BACKEND_URL || 'http://localhost:8080',
        changeOrigin: true
      },
      '/notices': {
        target: process.env.VUE_APP_BACKEND_URL || 'http://localhost:8080',
        changeOrigin: true
      },
      '/notices/image': {
        target: process.env.VUE_APP_BACKEND_URL || 'http://localhost:8080',
        changeOrigin: true
      },
      '/api': {
        target: process.env.VUE_APP_BACKEND_URL || 'http://localhost:8080',
        changeOrigin: true
      }
    }
  }
})
