return {
  -- Detect tabstop and shiftwidth automatically
  'NMAC427/guess-indent.nvim',
  lazy = false,
  priority = 1000,
  config = function()
    require('guess-indent').setup()
  end,
}
