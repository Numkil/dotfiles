return {
  'echasnovski/mini.statusline',
  dependencies = {
    'echasnovski/mini.icons',
    'echasnovski/mini-git',
  },
  config = function()
    require('mini.icons').setup()
    require('mini.git').setup()
    require('mini.statusline').setup()
  end,
}
