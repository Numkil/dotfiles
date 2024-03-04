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

    -- nvim-cmp supports additional completion capabilities, so broadcast that to servers
    local capabilities = vim.lsp.protocol.make_client_capabilities()
    capabilities = vim.tbl_deep_extend('force', capabilities, require('cmp_nvim_lsp').default_capabilities())

    for server_name, server_settings in pairs(require 'config.lsp-servers') do
      server_settings.capabilities = vim.tbl_deep_extend('force', {}, capabilities, server_settings.capabilities or {})
      require('lspconfig')[server_name].setup {
        capabilities = server_settings.capabilities,
        settings = server_settings,
        filetypes = (server_settings or {}).filetypes,
        init_options = (server_settings or {}).init_options,
      }
    end


    -- Ensure the servers in 'config.lsp-servers' are installed
    require('mason-lspconfig').setup {
      ensure_installed = vim.tbl_keys(require 'config.lsp-servers'),
      handlers = {

      }
    }

    -- Setup the debug adapters
    require('mason-nvim-dap').setup {
      ensure_installed = require 'config.debug-adapters',
    }
  end,
}
