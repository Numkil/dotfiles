return {
  'echasnovski/mini.bracketed',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    require('mini.bracketed').setup()
  end,
}
