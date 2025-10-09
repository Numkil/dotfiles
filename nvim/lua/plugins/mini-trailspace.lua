return {
  'nvim-mini/mini.trailspace',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    vim.cmd [[hi MiniTrailspace guibg=#b58900]]

    require('mini.trailspace').setup()

    -- trim any leftover whitespace if conform has not been able to do so
    vim.api.nvim_create_autocmd({ 'BufWrite' }, {
      callback = function()
        require('mini.trailspace').trim()
      end,
    })
  end,
}
