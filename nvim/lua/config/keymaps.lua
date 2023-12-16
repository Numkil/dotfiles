-- [[ Basic Keymaps ]]
-- Keymaps for better default experience

-- Alias :W with :w because I keep accidentally typing it
vim.cmd [[ cnoreabbrev <expr> W getcmdtype() == ":" && getcmdline() == "W" ? "w" : "W" ]]

-- See `:help vim.keymap.set()`
vim.keymap.set({ 'n', 'v' }, '<Space>', '<Nop>', { silent = true })
vim.keymap.set('', '<f1>', '<Nop>', { silent = true })

-- Remap for dealing with word wrap
vim.keymap.set('n', 'k', "v:count == 0 ? 'gk' : 'k'", { expr = true, silent = true })
vim.keymap.set('n', 'j', "v:count == 0 ? 'gj' : 'j'", { expr = true, silent = true })

-- More comfortably flip through buffers
vim.keymap.set('', '<leader>n', ':bnext<CR>', { desc = 'Next buffer', remap = true })
vim.keymap.set('', '<leader>N', ':bprevious<CR>', { desc = 'Previous buffer', remap = true })

-- Easier navigation in splits
vim.keymap.set('n', '<C-k>', ':wincmd k<CR>', { desc = 'navigate between split', remap = true, silent = true })
vim.keymap.set('n', '<C-j>', ':wincmd j<CR>', { desc = 'navigate between split', remap = true, silent = true })
vim.keymap.set('n', '<C-h>', ':wincmd h<CR>', { desc = 'navigate between split', remap = true, silent = true })
vim.keymap.set('n', '<C-l>', ':wincmd l<CR>', { desc = 'navigate between split', remap = true, silent = true })

-- scrolling remaps
vim.keymap.set('n', '<C-u>', '<C-u>zz', { desc = 'Scroll up', remap = true, silent = true })
vim.keymap.set('n', '<C-d>', '<C-d>zz', { desc = 'Scroll down', remap = true, silent = true })

-- Visual shifting ( does not exit Visual mode )
vim.keymap.set('v', '<', '<gv', { desc = 'Shift left without exiting V', remap = true, silent = true })
vim.keymap.set('v', '>', '>gv', { desc = 'Shift rightt without exiting V', remap = true, silent = true })

-- Diagnostic keymaps
vim.keymap.set('n', '[d', vim.diagnostic.goto_prev, { desc = 'Go to previous diagnostic message' })
vim.keymap.set('n', ']d', vim.diagnostic.goto_next, { desc = 'Go to next diagnostic message' })
vim.keymap.set('n', '<leader>e', vim.diagnostic.open_float, { desc = 'Open floating diagnostic message' })
vim.keymap.set('n', '<leader>q', vim.diagnostic.setloclist, { desc = 'Open diagnostics list' })

-- Clear notifications and search
vim.keymap.set('n', '<Esc>', function()
  require('notify').dismiss()
  vim.cmd 'Noice dismiss'
  vim.cmd 'nohl'
end)
