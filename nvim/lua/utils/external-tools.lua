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
        symfonyConsolePath = 'bin/console',
        diagnostics = {
          twigCsFixer = true,
        },
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

-- NOTE: This tells mason which formatters/linters to install necessary because
-- the binary does not always match up with the formatter name
M.formatters = {
  'stylua',
  'vale',
  'twig-cs-fixer',
  'php-cs-fixer',
  'mdformat',
  'eslint_d',
  'luacheck',
}

-- NOTE: This tells conform which formatters to enable
M.formatters_by_ft = {
  lua = { 'stylua' },
  php = { 'php_cs_fixer' },
  twig = { 'twig-cs-fixer' },
  markdown = { 'mdformat' },
  javascript = { 'eslint_d' },
  typescript = { 'eslint_d' },
}

-- NOTE: this tells nvim-lint which linters to enable
M.linters_by_ft = {
  markdown = { 'vale' },
  php = { 'php' },
  twig = { 'twig-cs-fixer' },
  lua = { 'luacheck' },
  javascript = { 'eslint_d' },
  typescript = { 'eslint_d' },
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
