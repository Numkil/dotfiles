local opts = {
  formatters = {
    php_cs_fixer = {
      inherit = true,
      command = 'php-cs-fixer',
    },
    ludtwig = {
      inherit = false,
      command = 'ludtwig',
      args = { '-f', '$FILENAME' },
      stdin = false,
    },
  },
  formatters_by_ft = require('utils.external-tools').formatters_by_ft,
  format_on_save = function(bufnr)
    -- Disable autoformat on certain filetypes
    local ignore_filetypes = { 'sql' }
    if vim.tbl_contains(ignore_filetypes, vim.bo[bufnr].filetype) then
      return
    end

    -- Disable autoformat for files in a certain path
    local bufname = vim.api.nvim_buf_get_name(bufnr)
    if bufname:match '/node_modules/' or bufname:match '/vendor/' then
      return
    end

    return { timeout_ms = 500, lsp_format = 'fallback' }
  end,
}

return {
  'stevearc/conform.nvim',
  event = 'BufWritePre',
  config = function()
    require('conform').setup(opts)
  end,
}
