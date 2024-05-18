return {
  'catppuccin/nvim',
  lazy = false,
  priority = 1000,
  config = function()
    vim.o.background = 'light'

    require('catppuccin').setup()

    vim.cmd.colorscheme 'catppuccin'
  end,
}
