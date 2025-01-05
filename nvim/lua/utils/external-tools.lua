local M = {}

M.lsps = {
  -- scripting LSP
  phpactor = {
    init_options = {
      ['language_server_worse_reflection.inlay_hints.enable'] = true,
      ['language_server_worse_reflection.inlay_hints.params'] = false,
      ['language_server_worse_reflection.inlay_hints.types'] = true,
      ['language_server_configuration.auto_config'] = false,
      ['code_transform.import_globals'] = true,
      ['language_server_php_cs_fixer.enabled'] = true,
      ['language_server_phpstan.enabled'] = true,
    },
  },
  vtsls = { filetypes = { 'javascript', 'typescript', 'vue' } },
  lua_ls = {
    settings = {
      Lua = {
        workspace = {
          checkThirdParty = false,
        },
        codeLens = {
          enable = true,
        },
        completion = {
          callSnippet = 'Replace',
        },
        doc = {
          privateName = { '^_' },
        },
        hint = {
          enable = true,
          setType = false,
          paramType = true,
          paramName = 'Disable',
          semicolon = 'Disable',
          arrayIndex = 'Disable',
        },
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
