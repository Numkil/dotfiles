-- NOTE: this sets up mason to ensure all our lps / debug-adapters / etc are installed
return {
  'mason-org/mason.nvim',
  dependencies = {
    -- Automatically install LSPs to stdpath for neovim
    'mason-org/mason-lspconfig.nvim',
    'WhoIsSethDaniel/mason-tool-installer.nvim',
  },
  config = function()
    -- mason-lspconfig requires that these setup functions are called in this order
    -- before setting up the servers.
    require('mason').setup()

    -- Ensure all servers and debug adapters are installed
    local servers = require('utils.external-tools').lsps
    local ensure_installed = vim.tbl_keys(servers)
    vim.list_extend(ensure_installed, {
      'stylua', -- Used to format Lua code
    })
    require('mason-tool-installer').setup { ensure_installed = ensure_installed, auto_update = true }

    ---@type MasonLspconfigSettings
    ---@diagnostic disable-next-line: missing-fields
    require('mason-lspconfig').setup {
      automatic_enable = ensure_installed,
    }

    for server_name, config in pairs(servers) do
      vim.lsp.config(server_name, config)
    end
  end,
}
