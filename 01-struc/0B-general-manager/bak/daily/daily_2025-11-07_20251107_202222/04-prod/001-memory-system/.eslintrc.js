module.exports = {
  extends: [
    'eslint:recommended'
  ],
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module'
  },
  rules: {
    'no-unused-vars': 'error',
    'no-console': 'off',
    'no-undef': 'error'
  },
  env: {
    node: true,
    es2022: true
  }
};