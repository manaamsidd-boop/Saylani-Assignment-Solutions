# Findings - October cash shortfall

- **PKR 1,221,080 is missing** (due 9,473,780, collected 8,252,700) - `queries/q6.sql`. Finance should open a recovery case for the full amount on Monday and stop describing the gap as a timing difference.
- **PKR 1,102,440 of it is 114 delivered orders with no deposit at all** - `queries/q5.sql`. Finance should pull the delivery proof for those orders and chase the owning agents for the cash first, because this is 90% of the gap.
- **Five agents deposited PKR 118,640 less than they collected: A03, A07, A20, A23, A18** - `queries/q3.sql`. Finance should audit those five agents' remaining October deposits and hold their next float until reconciled.
- **PKR 122,000 was deposited against 20 orders that were never delivered** - `queries/q4.sql`. Finance should refund or re-allocate it, since netting it against the gap is what hid the shortfall.
