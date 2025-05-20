return {
  'neanias/everforest-nvim',
  lazy = false,
  priority = 1000,
  config = function()
    vim.o.background = 'light'

    ---@diagnostic disable-next-line: missing-fields
    require('everforest').setup {
      background = 'hard',
      ui_contrast = 'high',
      dim_inactive_windows = true,
    }

    vim.cmd.colorscheme 'everforest'
  end,
}
