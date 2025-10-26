module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/eslint-recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:prettier/recommended'
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    project: 'tsconfig.json',
    sourceType: 'module'
  },
  plugins: ['@typescript-eslint'],
  rules: {
    '@typescript-eslint/naming-convention': [
      'error',
      {
        selector: 'interface',
        format: ['PascalCase'],
        custom: {
          regex: '^I[A-Z]',
          match: true
        }
      }
    ],
    '@typescript-eslint/no-unused-vars': [
      'warn',
      {
        args: 'none'
      }
    ],
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/no-namespace': 'off',
    '@typescript-eslint/no-use-before-define': 'off',
    '@typescript-eslint/quotes': 'off',
    curly: 'off',
    eqeqeq: 'error',
    'prefer-arrow-callback': 'error',
    'prettier/prettier': 'off'
  },
  overrides: [
    {
      files: ['.eslintrc.js'],
      parserOptions: {
        project: null
      }
    }
  ]
};
