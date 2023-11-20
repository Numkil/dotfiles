return {
  'echasnovski/mini.trailspace',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    vim.cmd [[hi MiniTrailspace guibg=#b58900]]
    require('mini.trailspace').setup()
  end,
}
