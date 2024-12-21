-- NOTE: This is where your plugins related to LSP can be installed.
return {
  -- LSP Configuration & Plugins
  'neovim/nvim-lspconfig',
  dependencies = {
    -- `lazydev` configures Lua LSP for your Neovim config, runtime and plugins
    -- used for completion, annotations and signatures of Neovim apis
    {
      'folke/lazydev.nvim',
      opts = {
        library = {
          -- Load luvit types when the `vim.uv` word is found
          { path = 'luvit-meta/library', words = { 'vim%.uv' } },
        },
      },
    },
    'Bilal2453/luvit-meta',
    'https://git.sr.ht/~whynothugo/lsp_lines.nvim',
  },
  event = 'BufEnter',
  config = function()
    require('lazydev').setup {}
    require('lsp_lines').setup()

    --  This function gets run when an LSP connects to a particular buffer.
    vim.api.nvim_create_autocmd('LspAttach', {
      group = vim.api.nvim_create_augroup('kickstart-lsp-attach', { clear = true }),
      callback = function(event)
        local builtin = require 'fzf-lua'
        local bufnr = event.buf

        require('utils').keymapSetList({
          { 'n', '<leader>rn', vim.lsp.buf.rename, { desc = '[R]e[n]ame' } },
          { { 'n', 'x' }, '<leader>ca', vim.lsp.buf.code_action, { desc = '[C]ode [A]ction' } },
          {
            'n',
            'gd',
            builtin.lsp_definitions,
            { desc = '[G]oto [D]efinition' },
          },
          {
            'n',
            '<leader>ds',
            builtin.lsp_document_symbols,
            { desc = '[D]ocument [S]ymbols' },
          },
          {
            'n',
            'gI',
            builtin.lsp_implementations,
            { desc = '[G]oto [I]mplementation' },
          },
          {
            'n',
            'gr',
            builtin.lsp_references,
            { desc = '[G]oto [R]eferences' },
          },
          {
            'n',
            '<leader>D',
            builtin.lsp_typedefs,
            { desc = 'Type [D]efinition' },
          },
          -- See `:help K` for why this keymap
          { 'n', 'K', vim.lsp.buf.hover, { desc = 'Hover Documentation' } },
          { { 'n', 'i' }, '<leader>k', vim.lsp.buf.signature_help, { desc = 'Signature Documentation' } },
          { 'n', '<leader>K', '<cmd>norm! K<cr>', { desc = 'Run keywordprg' } },
        }, bufnr, 'LSP: ')

        -- Enable inlay hints globaly
        local client = vim.lsp.get_client_by_id(event.data.client_id)
        if client and client.supports_method(vim.lsp.protocol.Methods.textDocument_inlayHint) then
          require('utils').keymapSet('n', '<leader>th', function()
            vim.lsp.inlay_hint.enable(not vim.lsp.inlay_hint.is_enabled { bufnr = bufnr })
          end, { desc = '[T]oggle Inlay [H]ints' }, bufnr, 'LSP: ')
        end

        -- Create a command `:Format` local to the LSP buffer
        vim.api.nvim_create_user_command('Format', function(args)
          local range = nil
          if args.count ~= -1 then
            local end_line = vim.api.nvim_buf_get_lines(0, args.line2 - 1, args.line2, true)[1]
            range = {
              start = { args.line1, 0 },
              ['end'] = { args.line2, end_line:len() },
            }
          end
          require('conform').format { async = true, lsp_fallback = true, range = range }
        end, { range = true })
      end,
    })
  end,
}
