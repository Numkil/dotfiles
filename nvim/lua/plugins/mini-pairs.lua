return {
  'echasnovski/mini.pairs',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    require('mini.pairs').setup()
  end,
}
