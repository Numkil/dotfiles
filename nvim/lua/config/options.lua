-- [[ Setting options ]]
-- See `:help vim.o`

-- configure how line wrapping is displayed
vim.o.wrap = true
vim.o.linebreak = true
vim.o.wrapmargin = 5
vim.o.breakindent = true

-- I want to keep 7 lines above/below the cursor when scrolling
vim.o.scrolloff = 7

-- Set highlight on search
vim.o.hlsearch = true
vim.o.showmatch = true

-- Make line numbers default
vim.wo.number = true

-- Sync clipboard between OS and Neovim.
vim.o.clipboard = 'unnamedplus'

-- Fallback tabstop settings when sleuth fails me
vim.o.expandtab = false
vim.o.smartindent = true

-- fully disable mouse
vim.o.mouse = ''

-- Save undo history
vim.o.undofile = true

-- Turn off swap files
vim.o.swapfile = false
vim.o.backup = false

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

-- configure splits
vim.o.splitright = true
vim.o.splitkeep = 'screen'

-- highlight cursor position
vim.o.cursorline = true

-- if performing an operation that would fail due to unsaved changes in the buffer (like `:q`),
-- instead raise a dialog asking if you wish to save the current file(s)
-- See `:help 'confirm'`
vim.opt.confirm = true

vim.diagnostic.config {
  severity_sort = true,
  underline = { severity = vim.diagnostic.severity.ERROR },
  float = { border = 'rounded', source = 'if_many' },
  signs = {
    text = {
      [vim.diagnostic.severity.ERROR] = '✘',
      [vim.diagnostic.severity.WARN] = '▲',
      [vim.diagnostic.severity.HINT] = '⚑',
      [vim.diagnostic.severity.INFO] = '»',
    },
  },
  virtual_text = {
    source = 'if_many',
    spacing = 2,
    format = function(diagnostic)
      local diagnostic_message = {
        [vim.diagnostic.severity.ERROR] = diagnostic.message,
        [vim.diagnostic.severity.WARN] = diagnostic.message,
        [vim.diagnostic.severity.INFO] = diagnostic.message,
        [vim.diagnostic.severity.HINT] = diagnostic.message,
      }
      return diagnostic_message[diagnostic.severity]
    end,
  },
}
