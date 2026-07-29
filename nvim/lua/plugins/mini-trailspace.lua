vim.cmd [[hi MiniTrailspace guibg=#b58900]]

require('mini.trailspace').setup()

-- Disable trailspace highlighting in non-editing buffers (terminal, nofile,
-- quickfix, help, ...).
vim.api.nvim_create_autocmd('TermOpen', {
  callback = function()
    vim.b.minitrailspace_disable = true
    pcall(require('mini.trailspace').unhighlight)
  end,
})

-- Snacks builds its dashboard buffer with 'eventignore=all' set (see
-- snacks/dashboard.lua D:init), so 'FileType'/'OptionSet' never fire for it --
-- any filetype- or buftype-keyed autocmd silently never runs. Its own
-- lifecycle event fires after 'eventignore' is restored, so use that instead.
-- Also explicitly clear any match, not just set the disable flag: a stray one
-- can already be there from mini.trailspace's own startup highlight pass, and
-- only unhighlight()/highlight() ever remove a match.
vim.api.nvim_create_autocmd('User', {
  pattern = { 'SnacksDashboardOpened', 'SnacksDashboardUpdatePost' },
  callback = function()
    vim.b.minitrailspace_disable = true
    pcall(require('mini.trailspace').unhighlight)
  end,
})

-- trim any leftover whitespace if conform has not been able to do so
vim.api.nvim_create_autocmd({ 'BufWrite' }, {
  callback = function()
    require('mini.trailspace').trim()
  end,
})
