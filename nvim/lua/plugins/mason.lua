-- NOTE: this sets up mason to ensure all our lps / debug-adapters / etc are installed
return {
  'williamboman/mason.nvim',
  dependencies = {
    -- Automatically install LSPs to stdpath for neovim
    'williamboman/mason-lspconfig.nvim',
    'WhoIsSethDaniel/mason-tool-installer.nvim',

    -- Installs debug adapters for you
    'jay-babu/mason-nvim-dap.nvim',
  },
  config = function()
    -- mason-lspconfig requires that these setup functions are called in this order
    -- before setting up the servers.
    require('mason').setup()

    -- Ensure all servers and debug adapters are installed
    local servers = require 'config.lsp-servers'
    local ensure_installed = vim.tbl_extend('force', vim.tbl_keys(servers), require 'config.debug-adapters')
    require('mason-tool-installer').setup { ensure_installed = ensure_installed, auto_update = true }

    -- nvim-cmp supports additional completion capabilities, so broadcast that to servers
    local capabilities = vim.lsp.protocol.make_client_capabilities()
    capabilities = vim.tbl_deep_extend('force', capabilities, require('cmp_nvim_lsp').default_capabilities())

    -- Ensure the servers in 'config.lsp-servers' are installed
    require('mason-lspconfig').setup {
      handlers = {
        function(server_name)
          local server = servers[server_name] or {}
          server.capabilities = vim.tbl_deep_extend('force', {}, capabilities, server.capabilities or {})
          require('lspconfig')[server_name].setup(server)
        end,
      },
    }

    -- Setup the debug adapters
    require('mason-nvim-dap').setup {}
  end,
}
