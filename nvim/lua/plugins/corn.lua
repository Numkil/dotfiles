return {
  -- Configure UI for diagnostics
  'RaafatTurki/corn.nvim',
  config = function()
    -- turn off virtual text as we replace with lsp_lines
    vim.diagnostic.config {
      virtual_text = false,
      -- TODO enable this when vim 0.10.0 is released
      -- signs = {
      --   text = {
      --     [vim.diagnostic.severity.ERROR] = '✘',
      --     [vim.diagnostic.severity.WARN] = '▲',
      --     [vim.diagnostic.severity.HINT] = '⚑',
      --     [vim.diagnostic.severity.INFO] = '»',
      --   },
      -- },
    }

    -- Use neat icons for diagnostics
    -- TODO workaround until nvim 0.10.0 is released
    local function sign_define(args)
      vim.fn.sign_define(args.name, {
        texthl = args.name,
        text = args.text,
        numhl = '',
      })
    end

    sign_define { name = 'DiagnosticSignError', text = '✘' }
    sign_define { name = 'DiagnosticSignWarn', text = '▲' }
    sign_define { name = 'DiagnosticSignHint', text = '⚑' }
    sign_define { name = 'DiagnosticSignInfo', text = '»' }

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
