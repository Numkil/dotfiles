return {
  'm4xshen/hardtime.nvim',
  lazy = false,
  dependencies = { 'MunifTanjim/nui.nvim' },
  opts = {
    restricted_keys = {
      ['h'] = { 'n', 'x' },
      ['j'] = { 'n', 'x' },
      ['k'] = { 'n', 'x' },
      ['l'] = { 'n', 'x' },
      ['+'] = { 'n', 'x' },
      ['gj'] = { 'n', 'x' },
      ['gk'] = { 'n', 'x' },
      ['<C-M>'] = { 'n', 'x' },
      ['<C-N>'] = false,
      ['<C-P>'] = { 'n', 'x' },
    },
  },
}
