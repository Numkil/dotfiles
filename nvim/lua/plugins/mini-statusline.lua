return {
  'echasnovski/mini.statusline',
  dependencies = {
    'nvim-tree/nvim-web-devicons',
    'echasnovski/mini-git',
  },
  config = function()
    require('mini.git').setup()
    require('mini.statusline').setup()
  end,
}
