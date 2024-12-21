return {
  'aliqyan-21/wit.nvim',
  config = function()
    require('wit').setup {
      engine = 'perplexity',
    }
  end,
}
