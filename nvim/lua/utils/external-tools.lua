local M = {}

M.lsps = {
  -- scripting LSP
  phpactor = {
    init_options = {
      ['language_server_worse_reflection.inlay_hints.enable'] = true,
      ['language_server_worse_reflection.inlay_hints.params'] = true,
      ['language_server_configuration.auto_config'] = false,
      ['code_transform.import_globals'] = true,
      ['language_server_php_cs_fixer.enabled'] = true,
      ['language_server_phpstan.enabled'] = false,
    },
  },
  vtsls = {},
  lua_ls = {
    settings = {
      Lua = {
        completion = {
          callSnippet = 'Replace',
        },
        diagnostics = { disable = { 'missing-fields' } },
      },
    },
  },
  bashls = {},
  -- templating LSP
  twiggy_language_server = {
    settings = {
      twiggy = {
        framework = 'craft',
        phpExecutable = '/opt/homebrew/bin/php',
      },
    },
  },
  html = {
    filetypes = { 'twig', 'html' },
  },
  tailwindcss = {
    filetypes = { 'twig', 'html' },
  },
  htmx = {
    filetypes = { 'twig', 'html' },
  },
}

M.debug_adapters = {
  'php-debug-adapter',
  'js-debug-adapter',
}

M.formatters_by_ft = {
  javascript = { 'prettierd', 'prettier' },
  typescript = { 'prettierd', 'prettier' },
  html = { 'prettierd', 'prettier' },
  twig = { 'ludtwig' },
  css = { 'prettierd', 'prettier' },
  scss = { 'prettierd', 'prettier' },
  less = { 'prettierd', 'prettier' },
  json = { 'prettierd', 'prettier' },
  yaml = { 'prettierd', 'prettier' },
  rust = { 'rustfmt' },
  lua = { 'stylua' },
  php = { 'php_cs_fixer' },
}

M.parsers = {
  'php_only',
  'php',
  'lua',
  'twig',
  'html',
  'json',
  'markdown',
  'typescript',
  'javascript',
  'tsx',
  'vimdoc',
  'vim',
  'regex',
  'markdown_inline',
  'css',
  'comment',
  'query',
  'gitcommit',
  'gitignore',
  'regex',
}

return M
