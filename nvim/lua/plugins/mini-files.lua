return {
  'echasnovski/mini.files',
  event = { 'BufEnter' },
  dependencies = {
    'nvim-tree/nvim-web-devicons',
  },
  config = function()
    local MiniFiles = require 'mini.files'
    local minifiles_toggle = function()
      if not MiniFiles.close() then
        MiniFiles.open(vim.api.nvim_buf_get_name(0))
      end
    end

    vim.keymap.set('n', '-', minifiles_toggle, { desc = 'Open parent directory' })

    require('mini.files').setup()
  end,
}
