-- NOTE: this sets up mason to ensure all our lps / debug-adapters / etc are installed
return {
  'williamboman/mason.nvim',
  dependencies = {
    -- Automatically install LSPs to stdpath for neovim
    'williamboman/mason-lspconfig.nvim',

    -- Installs debug adapters for you
    'jay-babu/mason-nvim-dap.nvim',
  },
  config = function()
    -- mason-lspconfig requires that these setup functions are called in this order
    -- before setting up the servers.
    require('mason').setup()

    -- Ensure the servers in 'config.lsp-servers' are installed
    require('mason-lspconfig').setup {
      ensure_installed = vim.tbl_keys(require 'config.lsp-servers'),
    }

    -- Setup the debug adapters
    require('mason-nvim-dap').setup {
      ensure_installed = require 'config.debug-adapters',
    }
  end,
}
