-- NOTE: this sets up mason to ensure all our lps / debug-adapters / etc are installed
return {
  'williamboman/mason.nvim',
  dependencies = {
    -- Automatically install LSPs to stdpath for neovim
    'williamboman/mason-lspconfig.nvim',
    'WhoIsSethDaniel/mason-tool-installer.nvim',
  },
  config = function()
    -- mason-lspconfig requires that these setup functions are called in this order
    -- before setting up the servers.
    require('mason').setup()

    -- Ensure all servers and debug adapters are installed
    local servers = require('utils.external-tools').lsps
    local ensure_installed = vim.tbl_keys(servers)
    require('mason-tool-installer').setup { ensure_installed = ensure_installed, auto_update = true }

    local lspconfig = require 'lspconfig'
    local capabilities = vim.lsp.protocol.make_client_capabilities()
    capabilities = vim.tbl_deep_extend('force', capabilities, require('blink.cmp').get_lsp_capabilities())

    -- Ensure the servers in 'config.lsp-servers' are installed
    require('mason-lspconfig').setup {
      handlers = {
        function(server_name)
          local server = servers[server_name] or {}
          server.capabilities = vim.tbl_deep_extend('force', {}, capabilities, server.capabilities or {})
          lspconfig[server_name].setup(server)
        end,
      },
    }
  end,
}
