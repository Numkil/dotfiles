vim.cmd [[hi MiniTrailspace guibg=#b58900]]

require('mini.trailspace').setup()

-- Disable trailspace highlighting in non-editing buffers
vim.api.nvim_create_autocmd('FileType', {
  pattern = { 'snacks_dashboard', 'snacks_notif', 'noice', 'lazy', 'mason' },
  callback = function()
    vim.b.minitrailspace_disable = true
  end,
})

-- trim any leftover whitespace if conform has not been able to do so
vim.api.nvim_create_autocmd({ 'BufWrite' }, {
  callback = function()
    require('mini.trailspace').trim()
  end,
})
