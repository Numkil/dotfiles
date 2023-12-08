return {
  'maxmx03/solarized.nvim',
  lazy = false,
  priority = 1000,
  config = function()
    vim.o.background = 'light'

    require('solarized').setup {
      theme = 'neo',
      styles = {
        comments = { italic = true, bold = false },
      },
    }

    vim.cmd.colorscheme 'solarized'
  end,
}
