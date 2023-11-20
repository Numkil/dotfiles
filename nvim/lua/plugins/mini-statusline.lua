return {
  'echasnovski/mini.statusline',
  dependencies = {
    'nvim-tree/nvim-web-devicons',
  },
  config = function()
    require('mini.statusline').setup()
  end,
}
