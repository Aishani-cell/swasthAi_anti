import os
p = 'frontend/app.py'
s = open(p, encoding='utf-8').read()
s = s.replace('onclick="st.switchPage(this, ', 'onclick="changePage(\'')
s = s.replace("'", "'", 1)  # only first quote
# The pattern is onclick="st.switchPage(this, 'pages/X')" -> onclick="changePage('pages/X')"
# Also need to remove the trailing ') after the closing quote.
s = s.replace("this, 'pages/", "this, 'pages/")  # now handled above
open(p, 'w', encoding='utf-8').write(s)
print('done', s.count('changePage('))
