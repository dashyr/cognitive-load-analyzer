: squared dup * ;

: diag   ( x y z -- d )
  squared >r   \ z^2 -> return stack
  squared >r   \ y^2 -> return stack
  squared      \ x^2 on data stack
  r> +         \ add y^2
  r> + ;       \ add z^2

\ usage: 5 4 3 diag .
