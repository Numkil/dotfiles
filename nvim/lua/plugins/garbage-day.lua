return {
  'zeioth/garbage-day.nvim',
  event = 'BufEnter',
  opts = {
    notifications = true,
    grace_period = 3 * 60,
  },
}
