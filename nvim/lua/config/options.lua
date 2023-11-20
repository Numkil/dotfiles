-- [[ Setting options ]]
-- See `:help vim.o`

-- configure how line wrapping is displayed
vim.o.wrap = true
vim.o.linebreak = true
vim.o.wrapmargin = 5
vim.o.breakindent = true

-- Set highlight on search
vim.o.hlsearch = true
vim.o.showmatch = true

-- Make line numbers default
vim.wo.number = true

-- Sync clipboard between OS and Neovim.
--  Remove this option if you want your OS clipboard to remain independent.
--  See `:help 'clipboard'`
vim.o.clipboard = 'unnamedplus'

-- Fallback tabstop settings when sleuth fails me
vim.o.expandtab = false
vim.o.tabstop = 4
vim.o.shiftwidth = 4

-- fully disable mouse
vim.o.mouse = ''

-- Save undo history
vim.o.undofile = true

-- Case-insensitive searching UNLESS \C or capital in search
vim.o.ignorecase = true
vim.o.smartcase = true

-- Keep signcolumn on by default
vim.wo.signcolumn = 'yes'

-- Decrease update time
vim.o.updatetime = 250
vim.o.timeoutlen = 300

-- Set completeopt to have a better completion experience
vim.o.completeopt = 'menuone,noselect'

-- NOTE: You should make sure your terminal supports this
vim.o.termguicolors = true
