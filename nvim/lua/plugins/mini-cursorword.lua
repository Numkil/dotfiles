return {
  'echasnovski/mini.cursorword',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    require('mini.cursorword').setup()
  end,
}
