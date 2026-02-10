module.exports = {
  root: true,
  env: {
    node: true,
    'vue/setup-compiler-macros': true
  },
  extends: [
    'plugin:vue/vue3-essential',
    'eslint:recommended',
    '@vue/eslint-config-typescript',
  ],
  rules: {
    'vue/multi-word-component-names': 'off',
    'vue/no-unused-vars': 'error'
  }
}