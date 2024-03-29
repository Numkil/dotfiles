-- NOTE: This is where your plugins related to LSP can be installed.
return {
  -- LSP Configuration & Plugins
  'neovim/nvim-lspconfig',
  event = 'BufEnter',
  config = function()
    --  This function gets run when an LSP connects to a particular buffer.
    vim.api.nvim_create_autocmd('LspAttach', {
      group = vim.api.nvim_create_augroup('kickstart-lsp-attach', { clear = true }),
      callback = function(event)
        local MiniExtra = require 'mini.extra'
        local bufnr = event.buf

        require('utils').keymapSetList({
          { 'n', '<leader>rn', vim.lsp.buf.rename, { desc = '[R]e[n]ame' } },
          { 'n', '<leader>ca', vim.lsp.buf.code_action, { desc = '[C]ode [A]ction' } },
          {
            'n',
            'gD',
            function()
              MiniExtra.pickers.lsp { scope = 'declaration' }
            end,
            { desc = '[G]oto [D]eclaration' },
          },
          {
            'n',
            'gd',
            function()
              MiniExtra.pickers.lsp { scope = 'definition' }
            end,
            { desc = '[G]oto [D]efinition' },
          },
          {
            'n',
            '<leader>ds',
            function()
              MiniExtra.pickers.lsp { scope = 'document_symbol' }
            end,
            { desc = '[D]ocument [S]ymbols' },
          },
          {
            'n',
            'gI',
            function()
              MiniExtra.pickers.lsp { scope = 'implementation' }
            end,
            { desc = '[G]oto [I]mplementation' },
          },
          {
            'n',
            'gr',
            function()
              MiniExtra.pickers.lsp { scope = 'references' }
            end,
            { desc = '[G]oto [R]eferences' },
          },
          {
            'n',
            '<leader>D',
            function()
              MiniExtra.pickers.lsp { scope = 'type_definition' }
            end,
            { desc = 'Type [D]efinition' },
          },
          -- See `:help K` for why this keymap
          { 'n', 'K', vim.lsp.buf.hover, { desc = 'Hover Documentation' } },
          { { 'n', 'i' }, '<c-k>', vim.lsp.buf.signature_help, { desc = 'Signature Documentation' } },
          { 'n', '<leader>K', '<cmd>norm! K<cr>', { desc = 'Run keywordprg' } },
        }, bufnr, 'LSP: ')

        -- Create a command `:Format` local to the LSP buffer
        vim.api.nvim_buf_create_user_command(bufnr, 'Format', function(_)
          require('conform').format { bufnr = bufnr }
        end, { desc = 'Format current buffer with LSP' })
      end,
    })
  end,
}
