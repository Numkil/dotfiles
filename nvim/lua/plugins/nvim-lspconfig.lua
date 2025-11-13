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
          -- See the configuration section for more details
          -- Load luvit types when the `vim.uv` word is found
          { path = '${3rd}/luv/library', words = { 'vim%.uv' } },
        },
      },
    },
    'rachartier/tiny-code-action.nvim',
    'https://git.sr.ht/~whynothugo/lsp_lines.nvim',
  },
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    require('lazydev').setup {}
    require('lsp_lines').setup()

    --  This function gets run when an LSP connects to a particular buffer.
    vim.api.nvim_create_autocmd('LspAttach', {
      group = vim.api.nvim_create_augroup('kickstart-lsp-attach', { clear = true }),
      callback = function(event)
        local bufnr = event.buf

        require('utils').keymapSetList({
          { 'n', '<leader>rn', vim.lsp.buf.rename, { desc = '[R]e[n]ame' } },
          -- See `:help K` for why this keymap
          { 'n', 'K', vim.lsp.buf.hover, { desc = 'Hover Documentation' } },
          { { 'n', 'i' }, '<leader>k', vim.lsp.buf.signature_help, { desc = 'Signature Documentation' } },
          { 'n', '<leader>K', '<cmd>norm! K<cr>', { desc = 'Run keywordprg' } },
        }, bufnr, 'LSP: ')

        -- Enable inlay hints globaly
        local client = vim.lsp.get_client_by_id(event.data.client_id)
        if client and client:supports_method(vim.lsp.protocol.Methods.textDocument_inlayHint) then
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
