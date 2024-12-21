return {
  'echasnovski/mini.indentscope',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    require('mini.indentscope').setup()
  end,
}
