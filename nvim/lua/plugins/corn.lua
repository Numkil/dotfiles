return {
  -- Configure UI for diagnostics
  'RaafatTurki/corn.nvim',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    -- turn off virtual text as we replace with lsp_lines
    vim.diagnostic.config {
      virtual_text = false,
      signs = {
        text = {
          [vim.diagnostic.severity.ERROR] = '✘',
          [vim.diagnostic.severity.WARN] = '▲',
          [vim.diagnostic.severity.HINT] = '⚑',
          [vim.diagnostic.severity.INFO] = '»',
        },
      },
    }

    -- Setup UI for diagnostics
    require('corn').setup {
      scope = 'file',
      icons = {
        error = '✘',
        warn = '▲',
        hint = '⚑',
        info = '»',
      },
      on_toggle = function()
        vim.diagnostic.config { virtual_text = not vim.diagnostic.config().virtual_text }
      end,
    }
  end,
}
