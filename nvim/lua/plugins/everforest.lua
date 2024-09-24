return {
  'neanias/everforest-nvim',
  lazy = false,
  priority = 1000,
  config = function()
    vim.o.background = 'light'

    require('everforest').setup()

    vim.cmd.colorscheme 'everforest'
  end,
}
