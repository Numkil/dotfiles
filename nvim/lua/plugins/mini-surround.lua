return {
  'echasnovski/mini.surround',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    require('mini.surround').setup()
  end,
}
