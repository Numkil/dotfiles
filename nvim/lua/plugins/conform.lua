local opts = {
  formatters_by_ft = {
    javascript = { 'prettierd', 'prettier' },
    typescript = { 'prettierd', 'prettier' },
    html = { 'prettierd', 'prettier' },
    css = { 'prettierd', 'prettier' },
    scss = { 'prettierd', 'prettier' },
    less = { 'prettierd', 'prettier' },
    json = { 'prettierd', 'prettier' },
    yaml = { 'prettierd', 'prettier' },
    rust = { 'rustfmt' },
    lua = { 'stylua' },
    php = { 'php-cs-fixer' },
  },
  format_on_save = function(bufnr)
    -- Disable autoformat on certain filetypes
    local ignore_filetypes = { 'sql', 'twig' }
    if vim.tbl_contains(ignore_filetypes, vim.bo[bufnr].filetype) then
      return
    end

    -- Disable with a global or buffer-local variable
    if vim.g.disable_autoformat or vim.b[bufnr].disable_autoformat then
      return
    end

    -- Disable autoformat for files in a certain path
    local bufname = vim.api.nvim_buf_get_name(bufnr)
    if bufname:match '/node_modules/' or bufname:match '/vendor/' then
      return
    end

    -- ...additional logic...
    return { timeout_ms = 500, lsp_fallback = true }
  end,
}

return {
  'stevearc/conform.nvim',
  event = 'BufWritePre',
  dependencies = {
    -- If there are no formatters or lsp_fallback at least remove whitespace
    'cappyzawa/trim.nvim',
  },
  config = function()
    require('trim').setup {}
    require('conform').setup(opts)
  end,
}
