return {
  'echasnovski/mini.comment',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    require('mini.comment').setup()
  end,
}
